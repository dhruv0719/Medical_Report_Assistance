# backend/ingestion/ocr_handler.py
"""
OCR handler — public entry point for the ingestion pipeline.

Delegates all image-level OCR decisions to AdaptiveOCREngine.
ImageQualityAnalyzer / OCRStrategySelector are retained as *hint* providers,
not as binding decision-makers.
"""

import io
from typing import Tuple

from pdf2image import convert_from_bytes
from PIL import Image

from config.logging_config import get_logger
from config.settings import UploadConfig
from backend.ingestion.image_quality_analyzer import ImageQualityAnalyzer
from backend.ingestion.strategy_selector import OCRStrategySelector
from backend.ingestion.adaptive_ocr_engine import AdaptiveOCREngine, OCRResult

logger = get_logger(__name__)


class OCRHandler:
    """
    Public OCR interface used by the rest of the application.

    Key design changes vs the previous version
    -------------------------------------------
    • Preprocessing is no longer forced on every image.
    • OCRStrategySelector output is passed as a hint to AdaptiveOCREngine,
      which tries raw OCR first and only preprocesses if needed.
    • The returned confidence / score is now the composite OCREvaluator score
      (0-100) rather than raw Tesseract confidence — it is a better signal
      of actual extraction quality.

    Public methods
    --------------
    extract_from_images(pdf_bytes)  → (full_text, metadata_dict)
    extract_from_image_file(image)  → (text, composite_score)
    is_text_extractable(pdf_bytes)  → bool
    """

    def __init__(self) -> None:
        self.dpi              = UploadConfig.OCR_DPI
        self.quality_analyzer = ImageQualityAnalyzer()
        self.strategy_selector = OCRStrategySelector()
        self.engine           = AdaptiveOCREngine()

    # ------------------------------------------------------------------
    # PDF extraction
    # ------------------------------------------------------------------

    def extract_from_images(self, pdf_bytes: bytes) -> Tuple[str, dict]:
        """
        Extract text from every page of a PDF using adaptive OCR.

        Args:
            pdf_bytes: Raw PDF file bytes.

        Returns:
            (full_text, metadata) where metadata contains:
              page_count          – number of pages processed
              ocr_confidence      – mean composite score across pages (0-100)
              extraction_method   – always "adaptive_ocr"
              total_time_sec      – wall-clock seconds for the whole call
              page_details        – list of per-page dicts with score breakdown
        """
        logger.info("[OCRHandler] Starting adaptive PDF extraction")

        images = convert_from_bytes(pdf_bytes, dpi=self.dpi, fmt="jpeg")
        logger.info(f"[OCRHandler] PDF has {len(images)} page(s)")

        full_text    = ""
        page_details = []
        total_time   = 0.0

        for i, image in enumerate(images, 1):
            logger.info(f"[OCRHandler] Processing page {i}/{len(images)}")

            hint   = self._get_hint(image)
            result = self.engine.process(image, hint_strategy=hint)

            full_text  += f"\n--- Page {i} ---\n{result.text}"
            total_time += result.processing_time

            page_details.append({
                "page":                   i,
                "winning_strategy":       result.winning_strategy,
                "composite_score":        round(result.composite_score, 2),
                "tesseract_confidence":   round(result.score.tesseract_confidence, 2),
                "skipped_preprocessing":  result.skipped_preprocessing,
                "hit_resolution_ceiling": result.hit_resolution_ceiling,
                "stopped_early":          result.stopped_early,
                "strategies_tried":       result.strategies_tried,
                "time_sec":               result.processing_time,
            })

            logger.info(
                f"[OCRHandler] Page {i} → strategy={result.winning_strategy!r}, "
                f"composite={result.composite_score:.1f}, "
                f"skipped_preprocessing={result.skipped_preprocessing}"
            )

        mean_score = (
            sum(p["composite_score"] for p in page_details) / len(page_details)
            if page_details else 0.0
        )

        metadata = {
            "page_count":        len(images),
            "ocr_confidence":    round(mean_score, 2),
            "extraction_method": "adaptive_ocr",
            "total_time_sec":    round(total_time, 3),
            "page_details":      page_details,
        }

        logger.info(
            f"[OCRHandler] Extraction complete — "
            f"pages={len(images)}, mean_score={mean_score:.1f}, "
            f"total_time={total_time:.2f}s"
        )

        return full_text, metadata

    # ------------------------------------------------------------------
    # Single-image extraction
    # ------------------------------------------------------------------

    def extract_from_image_file(self, image: Image.Image) -> Tuple[str, float]:
        """
        Extract text from a single PIL Image using adaptive OCR.

        Args:
            image: PIL Image object (any mode).

        Returns:
            (text, composite_score)  — score is 0-100 (OCREvaluator composite).
        """
        hint   = self._get_hint(image)
        result = self.engine.process(image, hint_strategy=hint)

        logger.info(
            f"[OCRHandler] Image OCR → strategy={result.winning_strategy!r}, "
            f"composite={result.composite_score:.1f}"
        )

        return result.text, result.composite_score

    # ------------------------------------------------------------------
    # Native text check
    # ------------------------------------------------------------------

    def is_text_extractable(self, pdf_bytes: bytes) -> bool:
        """
        Return True if the PDF has embedded (selectable) text on the first page.

        Uses this to decide whether the caller should use a native text extractor
        instead of (or in addition to) OCR.
        """
        try:
            from PyPDF2 import PdfReader

            reader     = PdfReader(io.BytesIO(pdf_bytes))
            first_page = reader.pages[0] if reader.pages else None

            if first_page is None:
                return False

            extracted = first_page.extract_text() or ""
            return len(extracted.strip()) > 50

        except Exception as exc:
            logger.warning(f"[OCRHandler] Could not check text extractability: {exc}")
            return False

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _get_hint(self, image: Image.Image) -> str:
        """
        Derive a strategy hint from image quality metrics.

        The hint is passed to AdaptiveOCREngine as a *priority* hint — it
        influences pipeline ordering but does not force preprocessing if the
        raw result is already good enough.
        """
        metrics = self.quality_analyzer.analyze(image)
        return self.strategy_selector.choose_strategy(metrics)