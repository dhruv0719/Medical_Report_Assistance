# backend/ingestion/adaptive_ocr_engine.py
"""
Adaptive multi-pass OCR engine.

Decision flow per image
───────────────────────
  1. Resolution ceiling check — log upfront if source image is small.
  2. Run RAW Tesseract (no preprocessing).
  3. Score the result with OCREvaluator.
  4. composite >= RAW_SKIP_THRESHOLD (85)  → return immediately.
  5. Otherwise: try preprocessing pipelines in priority order.
       • hint_strategy from OCRStrategySelector goes first.
       • Remaining FALLBACK_PIPELINES follow.
  6. After each pipeline: if composite >= PIPELINE_GOOD_ENOUGH_THRESHOLD (82)
       → stop immediately, skip remaining pipelines.
  7. Keep the running best across all pipelines tried.
  8. Warn if the best score is still below MIN_ACCEPTABLE_SCORE (60).
  9. Return best OCRResult.

Thresholds at a glance
───────────────────────
  RAW_SKIP_THRESHOLD             85  clean PDFs skip preprocessing entirely
  PIPELINE_GOOD_ENOUGH_THRESHOLD 82  first pipeline that clears this stops the loop
  MIN_ACCEPTABLE_SCORE           60  below this a warning is emitted
  LOW_RES_PIXEL_THRESHOLD    600000  ~800x750; below this a ceiling warning fires

Why PIPELINE_GOOD_ENOUGH_THRESHOLD matters
────────────────────────────────────────────
  Without it, the engine ran all four pipelines even after the first one
  already found the best result (low_resolution at 77.8 for a 526x739 image).
  The remaining three pipelines each cost ~1.5s and scored worse.
  With the threshold at 82: if any pipeline clears it, the loop stops and
  the remaining pipelines are skipped entirely.
  For genuinely low-res images that cannot clear 82, all pipelines still
  run — but the hit_resolution_ceiling flag communicates that the lower
  score is a hard physical limit, not a fixable failure.
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
        hit_resolution_ceiling: True if source image was below LOW_RES_PIXEL_THRESHOLD.
                                A lower composite score in this case is expected
                                behaviour — no pipeline can manufacture missing pixels.
        stopped_early:          True if a pipeline cleared PIPELINE_GOOD_ENOUGH_THRESHOLD
                                and remaining pipelines were intentionally skipped.
    """
    text:                   str
    score:                  OCRScore
    strategies_tried:       List[str]
    processing_time:        float
    skipped_preprocessing:  bool
    hit_resolution_ceiling: bool = False
    stopped_early:          bool = False

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

    All thresholds are class-level constants — override via subclass
    or direct assignment for testing without touching production defaults.
    """

    RAW_SKIP_THRESHOLD:             float = 85.0
    PIPELINE_GOOD_ENOUGH_THRESHOLD: float = 82.0
    MIN_ACCEPTABLE_SCORE:           float = 60.0
    LOW_RES_PIXEL_THRESHOLD:        int   = 600_000  # ~800x750 px

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
            hint_strategy:  Optional strategy name from OCRStrategySelector.
                            Used as a priority hint (placed first in the
                            pipeline order) — never forced; skipped entirely
                            if raw OCR is already good enough.

        Returns:
            OCRResult with the best text and full scoring metadata.
        """
        t_start = time.time()
        strategies_tried: List[str] = []

        # ----------------------------------------------------------------
        # Step 1 – Resolution ceiling check
        # ----------------------------------------------------------------
        w, h = image.size
        hit_ceiling = (w * h) < self.LOW_RES_PIXEL_THRESHOLD

        if hit_ceiling:
            logger.info(
                f"[AdaptiveOCR] source image {w}x{h} "
                f"({w * h:,} px) < LOW_RES_PIXEL_THRESHOLD "
                f"({self.LOW_RES_PIXEL_THRESHOLD:,} px) — "
                f"resolution ceiling applies; lower composite score is expected"
            )

        # ----------------------------------------------------------------
        # Step 2 – Raw OCR
        # ----------------------------------------------------------------
        raw_text, raw_conf = self._run_tesseract(image)
        raw_score = self.evaluator.score(raw_text, raw_conf, strategy="raw")
        strategies_tried.append("raw")

        logger.info(
            f"[AdaptiveOCR] raw → tess={raw_conf:.1f}%, "
            f"composite={raw_score.composite:.1f}"
        )

        # ----------------------------------------------------------------
        # Step 3 – Early exit: raw is already good enough
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
                hit_resolution_ceiling=hit_ceiling,
                stopped_early=False,
            )

        # ----------------------------------------------------------------
        # Step 4 – Try preprocessing pipelines
        # ----------------------------------------------------------------
        logger.info(
            f"[AdaptiveOCR] composite {raw_score.composite:.1f} "
            f"< {self.RAW_SKIP_THRESHOLD} → running preprocessing pipelines"
        )

        pipelines     = self._build_pipeline_order(hint_strategy)
        best_score    = raw_score
        stopped_early = False

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

                # Early exit: good enough — no point running more pipelines
                if best_score.composite >= self.PIPELINE_GOOD_ENOUGH_THRESHOLD:
                    remaining = [p for p in pipelines if p not in strategies_tried]
                    stopped_early = True
                    logger.info(
                        f"[AdaptiveOCR] composite {best_score.composite:.1f} "
                        f">= {self.PIPELINE_GOOD_ENOUGH_THRESHOLD} "
                        f"→ stopping early, skipping {remaining}"
                    )
                    break

            except Exception as exc:
                logger.warning(
                    f"[AdaptiveOCR] strategy {strategy!r} failed: {exc}"
                )
                continue

        # ----------------------------------------------------------------
        # Step 5 – Quality gate
        # ----------------------------------------------------------------
        if best_score.composite < self.MIN_ACCEPTABLE_SCORE:
            ceiling_note = " (resolution ceiling — expected)" if hit_ceiling else ""
            logger.warning(
                f"[AdaptiveOCR] best composite {best_score.composite:.1f} "
                f"< {self.MIN_ACCEPTABLE_SCORE}{ceiling_note} — "
                f"document may be too degraded for reliable OCR "
                f"(winning strategy: {best_score.strategy!r})"
            )

        elapsed = round(time.time() - t_start, 3)
        logger.info(
            f"[AdaptiveOCR] done in {elapsed}s — "
            f"winner={best_score.strategy!r}, "
            f"composite={best_score.composite:.1f}, "
            f"tried={strategies_tried}, "
            f"stopped_early={stopped_early}, "
            f"hit_ceiling={hit_ceiling}"
        )

        return OCRResult(
            text=best_score.text,
            score=best_score,
            strategies_tried=strategies_tried,
            processing_time=elapsed,
            skipped_preprocessing=(best_score.strategy == "raw"),
            hit_resolution_ceiling=hit_ceiling,
            stopped_early=stopped_early,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _run_tesseract(self, image: Image.Image) -> Tuple[str, float]:
        """
        Run Tesseract and return (text, average_confidence).

        Confidence is the mean of per-word confidence values.
        Tesseract emits -1 for non-word segments; those are excluded.
        Zero-confidence words are also excluded (below Tesseract threshold).
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

        confs = [
            int(c) for c in ocr_data["conf"]
            if str(c).lstrip("-").isdigit() and int(c) >= 0
        ]
        confidence = sum(confs) / len(confs) if confs else 0.0

        return text, confidence

    def _build_pipeline_order(self, hint: Optional[str]) -> List[str]:
        """
        Return an ordered list of pipelines to try.

        The hint goes first (highest prior probability of being correct).
        If hint is "raw" or not in FALLBACK_PIPELINES, the default order
        is used unchanged.
        """
        pipelines = list(self.FALLBACK_PIPELINES)

        if hint and hint != "raw" and hint in pipelines:
            pipelines.remove(hint)
            pipelines.insert(0, hint)

        return pipelines