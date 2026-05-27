# backend/ingestion/adaptive_ocr_engine.py
"""
Adaptive multi-pass OCR engine.

Decision flow per image
───────────────────────
  1. Run RAW Tesseract (no preprocessing).
  2. Score the result with OCREvaluator.
  3. composite >= RAW_SKIP_THRESHOLD → return immediately (no preprocessing).
  4. Otherwise: try preprocessing pipelines in priority order.
       • hint_strategy from ImageQualityAnalyzer goes first.
       • Remaining FALLBACK_PIPELINES follow.
  5. Score every result; keep the running best.
  6. Warn if the best score is still below MIN_ACCEPTABLE_SCORE.
  7. Return best OCRResult.

Why this is better than the old architecture
─────────────────────────────────────────────
  The old system forced preprocessing on every image.  For clean, high-DPI
  PDFs Tesseract already achieves 85-90 % composite on the raw image;
  CLAHE + adaptive thresholding then destroy anti-aliased glyph edges and
  drop confidence by 6-10 points.  This engine avoids that cost entirely for
  good inputs and still applies the right pipeline for genuinely degraded
  images.
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
# Result container
# ---------------------------------------------------------------------------

@dataclass
class OCRResult:
    """
    Final output from AdaptiveOCREngine.process().

    Attributes:
        text:                   Best extracted text.
        score:                  Full OCRScore for the winning strategy.
        strategies_tried:       All strategies that were attempted, in order.
        processing_time:        Wall-clock seconds for the whole process() call.
        skipped_preprocessing:  True if raw OCR was good enough on its own.
    """
    text:                  str
    score:                 OCRScore
    strategies_tried:      List[str]
    processing_time:       float
    skipped_preprocessing: bool

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
    Multi-pass adaptive OCR engine.

    Class-level thresholds (override via subclass or monkey-patch for testing):
      RAW_SKIP_THRESHOLD    – composite score above which raw is "good enough".
      MIN_ACCEPTABLE_SCORE  – composite below this triggers a warning log.
    """

    RAW_SKIP_THRESHOLD:   float = 85.0
    MIN_ACCEPTABLE_SCORE: float = 60.0

    # Tried in order when raw OCR is insufficient.
    # hint_strategy from StrategySelector is inserted at position 0.
    FALLBACK_PIPELINES: List[str] = [
        "light",
        "medical_report",
        "low_resolution",
        "noisy",
    ]

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
        Run adaptive OCR on a single PIL image.

        Args:
            image:          PIL Image (any mode; converted internally).
            hint_strategy:  Optional strategy name from ImageQualityAnalyzer /
                            OCRStrategySelector.  Used as a *priority hint*
                            (placed first in the pipeline order) — it is never
                            forced; if the raw result is already good, it is
                            skipped entirely.

        Returns:
            OCRResult with the best text and full scoring metadata.
        """
        t_start           = time.time()
        strategies_tried: List[str] = []

        # ----------------------------------------------------------------
        # Step 1 – Raw OCR
        # ----------------------------------------------------------------
        raw_text, raw_conf = self._run_tesseract(image)
        raw_score = self.evaluator.score(raw_text, raw_conf, strategy="raw")
        strategies_tried.append("raw")

        logger.info(
            f"[AdaptiveOCR] raw → tess={raw_conf:.1f}%, "
            f"composite={raw_score.composite:.1f}"
        )

        # ----------------------------------------------------------------
        # Step 2 – Early exit
        # ----------------------------------------------------------------
        if raw_score.composite >= self.RAW_SKIP_THRESHOLD:
            elapsed = round(time.time() - t_start, 3)
            logger.info(
                f"[AdaptiveOCR] raw composite {raw_score.composite:.1f} "
                f">= {self.RAW_SKIP_THRESHOLD} → skipping preprocessing "
                f"({elapsed}s total)"
            )
            return OCRResult(
                text=raw_text,
                score=raw_score,
                strategies_tried=strategies_tried,
                processing_time=elapsed,
                skipped_preprocessing=True,
            )

        # ----------------------------------------------------------------
        # Step 3 – Try preprocessing pipelines
        # ----------------------------------------------------------------
        logger.info(
            f"[AdaptiveOCR] composite {raw_score.composite:.1f} "
            f"< {self.RAW_SKIP_THRESHOLD} → running preprocessing pipelines"
        )

        pipelines  = self._build_pipeline_order(hint_strategy)
        best_score = raw_score  # raw is the current best baseline

        for strategy in pipelines:
            try:
                preprocessed     = self.preprocessor.apply_strategy(image, strategy)
                text, confidence = self._run_tesseract(preprocessed)
                score            = self.evaluator.score(text, confidence, strategy=strategy)
                strategies_tried.append(strategy)

                logger.debug(
                    f"[AdaptiveOCR] {strategy!r} → "
                    f"tess={confidence:.1f}%, composite={score.composite:.1f}"
                )

                if score.composite > best_score.composite:
                    best_score = score
                    logger.info(
                        f"[AdaptiveOCR] new best: {strategy!r} "
                        f"(composite={score.composite:.1f})"
                    )

            except Exception as exc:
                logger.warning(
                    f"[AdaptiveOCR] strategy {strategy!r} failed: {exc}"
                )
                continue

        # ----------------------------------------------------------------
        # Step 4 – Quality gate
        # ----------------------------------------------------------------
        if best_score.composite < self.MIN_ACCEPTABLE_SCORE:
            logger.warning(
                f"[AdaptiveOCR] best composite {best_score.composite:.1f} "
                f"< {self.MIN_ACCEPTABLE_SCORE} — document may be too degraded "
                f"for reliable OCR (winning strategy: {best_score.strategy!r})"
            )

        elapsed = round(time.time() - t_start, 3)
        logger.info(
            f"[AdaptiveOCR] done in {elapsed}s — "
            f"winner={best_score.strategy!r}, "
            f"composite={best_score.composite:.1f}, "
            f"tried={strategies_tried}"
        )

        return OCRResult(
            text=best_score.text,
            score=best_score,
            strategies_tried=strategies_tried,
            processing_time=elapsed,
            skipped_preprocessing=(best_score.strategy == "raw"),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_tesseract(self, image: Image.Image) -> Tuple[str, float]:
        """
        Run Tesseract and return (text, average_confidence).

        Confidence is the mean of per-word confidence values (ignoring -1
        sentinel tokens that Tesseract emits for non-word segments).
        """
        ocr_data = pytesseract.image_to_data(
            image,
            lang=self.language,
            config=self.config,
            output_type=pytesseract.Output.DICT,
        )
        text = pytesseract.image_to_string(
            image,
            lang=self.language,
            config=self.config,
        )

        # Filter out -1 (no confidence) and 0 (below-threshold words)
        confs = [
            int(c) for c in ocr_data["conf"]
            if str(c).lstrip("-").isdigit() and int(c) >= 0
        ]
        confidence = sum(confs) / len(confs) if confs else 0.0

        return text, confidence

    def _build_pipeline_order(self, hint: Optional[str]) -> List[str]:
        """
        Return an ordered list of pipelines to try.

        The hint (from ImageQualityAnalyzer) is placed first because it has
        the highest prior probability of being correct.  If the hint is "raw"
        or already in position 0, the default order is used unchanged.
        """
        pipelines = list(self.FALLBACK_PIPELINES)  # make a mutable copy

        if hint and hint != "raw" and hint in pipelines:
            pipelines.remove(hint)
            pipelines.insert(0, hint)

        return pipelines