# backend/ingestion/adaptive_ocr_engine.py
"""
Adaptive OCR engine — 3-call maximum architecture.

Exactly three OCR attempts per image, hard cap, no exceptions.

Step 1 — Raw OCR
    Always runs. If composite >= RAW_SKIP_THRESHOLD (85): done, return.
    Clean PDFs never go further. Cost: 1 call.

Step 2 — Hint strategy
    Preprocessing strategy suggested by OCRStrategySelector.
    If composite >= PIPELINE_GOOD_ENOUGH_THRESHOLD (82): done, return.
    If image is at resolution ceiling: done, return best of step 1 & 2.
    Cost: 2 calls total.

Step 3 — One best fallback
    Single pipeline chosen from FALLBACK_AFTER_HINT map — no loop,
    no extra computation. Return best of all three attempts.
    Cost: 3 calls total, hard cap.

Why not more attempts?
    Running all 4 pipelines costs 4-10 seconds per image. In practice,
    the hint strategy (derived from image metrics) wins the majority of
    cases on the first try. If raw fails and hint also fails AND the image
    is genuinely low-resolution, a 4th/5th attempt won't recover detail
    that isn't in the source pixels. The 3-call cap reflects this reality.

Call cost per scenario
    Clean PDF                        → 1 call  (~1.5s)
    Low-res image, hint wins         → 2 calls (~3s)
    Degraded image, needs fallback   → 3 calls (~4.5s)
    (Previously: up to 10 calls, ~15s)
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pytesseract
from PIL import Image

from config.logging_config import get_logger
from config.settings import UploadConfig
from backend.ingestion.ocr_evaluator import OCREvaluator, OCRScore
from backend.ingestion.preprocessing_strategies import OCRPreprocessor

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# If hint strategy fails, this map picks the single best follow-up.
# Chosen based on what each hint strategy did NOT address:
#   low_resolution  upscaled + sharpened  → noise may still remain → noisy
#   noisy           denoised + threshed   → contrast may be off    → medical_report
#   light           minimal CLAHE         → wasn't enough, go hard  → medical_report
#   medical_report  CLAHE + thresh        → too aggressive          → light
FALLBACK_AFTER_HINT: dict = {
    "low_resolution": "noisy",
    "noisy":          "medical_report",
    "light":          "medical_report",
    "medical_report": "light",
}

# Pixel area below which preprocessing cannot recover missing detail.
# 526×739 = 389,014 px  (your low-res test images sit here)
# 800×750 = 600,000 px  (threshold)
LOW_RES_PIXEL_THRESHOLD: int = 600_000


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class OCRResult:
    """
    Output from AdaptiveOCREngine.process().

    Attributes:
        text:                   Best extracted text.
        score:                  Full OCRScore for the winning strategy.
        strategies_tried:       Ordered list of strategies attempted.
        calls_made:             Number of Tesseract calls (1, 2, or 3).
        processing_time:        Wall-clock seconds for the whole call.
        skipped_preprocessing:  True if raw OCR was good enough (step 1 exit).
        hit_resolution_ceiling: True if source image was below
                                LOW_RES_PIXEL_THRESHOLD. A lower composite
                                score is a physics limit, not a fixable bug.
    """
    text:                   str
    score:                  OCRScore
    strategies_tried:       List[str]
    calls_made:             int
    processing_time:        float
    skipped_preprocessing:  bool
    hit_resolution_ceiling: bool

    @property
    def winning_strategy(self) -> str:
        return self.score.strategy

    @property
    def composite_score(self) -> float:
        return self.score.composite


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class AdaptiveOCREngine:
    """
    3-call-maximum adaptive OCR engine.

    All thresholds are class-level — override via subclass for testing.
    """

    RAW_SKIP_THRESHOLD:             float = 85.0
    PIPELINE_GOOD_ENOUGH_THRESHOLD: float = 82.0
    MIN_ACCEPTABLE_SCORE:           float = 60.0

    def __init__(self) -> None:
        self.evaluator    = OCREvaluator()
        self.preprocessor = OCRPreprocessor()
        self.language     = UploadConfig.OCR_LANGUAGE
        self.config       = UploadConfig.CUSTOM_OCR_CONFIG

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process(
        self,
        image: Image.Image,
        hint_strategy: Optional[str] = None,
    ) -> OCRResult:
        """
        Run adaptive OCR. Maximum 3 Tesseract calls regardless of input.

        Args:
            image:          PIL Image (any mode).
            hint_strategy:  Strategy name from OCRStrategySelector.
                            Used as step 2. Falls back to "light" if None.

        Returns:
            OCRResult with best text, score breakdown, and call metadata.
        """
        t_start          = time.time()
        strategies_tried = []
        hint             = hint_strategy or "light"

        # ----------------------------------------------------------------
        # Resolution ceiling — checked once, used in steps 2 and 3
        # ----------------------------------------------------------------
        w, h        = image.size
        hit_ceiling = (w * h) < LOW_RES_PIXEL_THRESHOLD

        if hit_ceiling:
            logger.info(
                f"[AdaptiveOCR] {w}x{h} ({w*h:,}px) below resolution "
                f"threshold ({LOW_RES_PIXEL_THRESHOLD:,}px) — "
                f"ceiling applies, lower score expected"
            )

        # ================================================================
        # STEP 1 — Raw OCR
        # ================================================================
        raw_text, raw_conf = self._tesseract(image)
        raw_score          = self.evaluator.score(raw_text, raw_conf, strategy="raw")
        strategies_tried.append("raw")

        logger.info(
            f"[AdaptiveOCR] step1/raw → "
            f"tess={raw_conf:.1f}%, composite={raw_score.composite:.1f}"
        )

        if raw_score.composite >= self.RAW_SKIP_THRESHOLD:
            logger.info(
                f"[AdaptiveOCR] step1 exit — "
                f"composite {raw_score.composite:.1f} >= {self.RAW_SKIP_THRESHOLD} "
                f"(1 call, {round(time.time()-t_start,2)}s)"
            )
            return self._result(
                best=raw_score,
                strategies_tried=strategies_tried,
                calls_made=1,
                t_start=t_start,
                skipped_preprocessing=True,
                hit_ceiling=hit_ceiling,
            )

        # ================================================================
        # STEP 2 — Hint strategy
        # ================================================================
        hint_image        = self.preprocessor.apply_strategy(image, hint)
        hint_text, hint_conf = self._tesseract(hint_image)
        hint_score        = self.evaluator.score(hint_text, hint_conf, strategy=hint)
        strategies_tried.append(hint)

        best = hint_score if hint_score.composite > raw_score.composite else raw_score

        logger.info(
            f"[AdaptiveOCR] step2/{hint} → "
            f"tess={hint_conf:.1f}%, composite={hint_score.composite:.1f} "
            f"(best so far: {best.composite:.1f})"
        )

        if best.composite >= self.PIPELINE_GOOD_ENOUGH_THRESHOLD:
            logger.info(
                f"[AdaptiveOCR] step2 exit — "
                f"composite {best.composite:.1f} >= {self.PIPELINE_GOOD_ENOUGH_THRESHOLD} "
                f"(2 calls, {round(time.time()-t_start,2)}s)"
            )
            return self._result(
                best=best,
                strategies_tried=strategies_tried,
                calls_made=2,
                t_start=t_start,
                skipped_preprocessing=False,
                hit_ceiling=hit_ceiling,
            )

        # Resolution ceiling — no point in a 3rd call, pixels don't exist
        if hit_ceiling:
            logger.info(
                f"[AdaptiveOCR] step2 exit (resolution ceiling) — "
                f"best composite {best.composite:.1f}, skipping step 3 "
                f"(2 calls, {round(time.time()-t_start,2)}s)"
            )
            self._warn_if_poor(best, ceiling=True)
            return self._result(
                best=best,
                strategies_tried=strategies_tried,
                calls_made=2,
                t_start=t_start,
                skipped_preprocessing=False,
                hit_ceiling=True,
            )

        # ================================================================
        # STEP 3 — One best fallback (hard cap)
        # ================================================================
        fallback       = FALLBACK_AFTER_HINT.get(hint, "light")
        fallback_image = self.preprocessor.apply_strategy(image, fallback)
        fb_text, fb_conf = self._tesseract(fallback_image)
        fb_score       = self.evaluator.score(fb_text, fb_conf, strategy=fallback)
        strategies_tried.append(fallback)

        if fb_score.composite > best.composite:
            best = fb_score

        logger.info(
            f"[AdaptiveOCR] step3/{fallback} → "
            f"tess={fb_conf:.1f}%, composite={fb_score.composite:.1f} "
            f"(best so far: {best.composite:.1f})"
        )

        self._warn_if_poor(best, ceiling=False)

        logger.info(
            f"[AdaptiveOCR] done — winner={best.strategy!r}, "
            f"composite={best.composite:.1f} "
            f"(3 calls, {round(time.time()-t_start,2)}s)"
        )

        return self._result(
            best=best,
            strategies_tried=strategies_tried,
            calls_made=3,
            t_start=t_start,
            skipped_preprocessing=False,
            hit_ceiling=hit_ceiling,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _tesseract(self, image: Image.Image) -> Tuple[str, float]:
        """
        Single Tesseract call using image_to_data only.

        image_to_data returns everything image_to_string returns, plus
        per-word confidence scores. Calling both on the same image is
        redundant — this method reconstructs full text from image_to_data,
        halving the Tesseract call count vs the naive approach.
        """
        ocr_data = pytesseract.image_to_data(
            image,
            lang=self.language,
            config=self.config,
            output_type=pytesseract.Output.DICT,
        )

        # Reconstruct text preserving line structure
        lines: dict = {}
        for page, block, par, line, word_text, conf in zip(
            ocr_data["page_num"],
            ocr_data["block_num"],
            ocr_data["par_num"],
            ocr_data["line_num"],
            ocr_data["text"],
            ocr_data["conf"],
        ):
            if str(conf) == "-1" or not str(word_text).strip():
                continue
            key = (page, block, par, line)
            lines.setdefault(key, []).append(str(word_text))

        text = "\n".join(" ".join(words) for words in lines.values())

        # Confidence: mean of all non-sentinel word scores
        confs = [
            int(c) for c in ocr_data["conf"]
            if str(c).lstrip("-").isdigit() and int(c) >= 0
        ]
        confidence = sum(confs) / len(confs) if confs else 0.0

        return text, confidence

    def _result(
        self,
        best: OCRScore,
        strategies_tried: List[str],
        calls_made: int,
        t_start: float,
        skipped_preprocessing: bool,
        hit_ceiling: bool,
    ) -> OCRResult:
        """Build OCRResult from the winning score."""
        return OCRResult(
            text=best.text,
            score=best,
            strategies_tried=strategies_tried,
            calls_made=calls_made,
            processing_time=round(time.time() - t_start, 3),
            skipped_preprocessing=skipped_preprocessing,
            hit_resolution_ceiling=hit_ceiling,
        )

    def _warn_if_poor(self, best: OCRScore, ceiling: bool) -> None:
        """Emit a warning if the best result is still below acceptable threshold."""
        if best.composite < self.MIN_ACCEPTABLE_SCORE:
            note = " (resolution ceiling — expected)" if ceiling else ""
            logger.warning(
                f"[AdaptiveOCR] best composite {best.composite:.1f} "
                f"< {self.MIN_ACCEPTABLE_SCORE}{note} — "
                f"document may be too degraded for reliable OCR "
                f"(strategy: {best.strategy!r})"
            )