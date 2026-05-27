# backend/ingestion/preprocessing_strategies.py

"""
OCR preprocessing strategies.
"""

import cv2
import numpy as np
from PIL import Image


class OCRPreprocessor:
    """Applies preprocessing strategies for OCR"""

    def __init__(self):
        pass

    # =========================================================
    # MAIN ENTRY
    # =========================================================

    def apply_strategy(self, image: Image.Image, strategy: str) -> Image.Image:
        """
        Apply preprocessing strategy.
        """

        strategies = {
            "raw": self.raw_pipeline,
            "light": self.light_pipeline,
            "low_resolution": self.low_resolution_pipeline,
            "noisy": self.noisy_pipeline,
            "medical_report": self.medical_report_pipeline
        }

        processor = strategies.get(strategy, self.light_pipeline)

        return processor(image)

    # =========================================================
    # RAW PIPELINE
    # =========================================================

    def raw_pipeline(self, image: Image.Image) -> Image.Image:
        """Return image without preprocessing"""
        return image

    # =========================================================
    # LIGHT PIPELINE
    # =========================================================

    def light_pipeline(self, image: Image.Image) -> Image.Image:
        """
        Minimal preprocessing.
        Good for already-clean documents.
        """

        gray = self._to_gray(image)

        # Light contrast enhancement
        clahe = cv2.createCLAHE(
            clipLimit=1.5,
            tileGridSize=(8, 8)
        )

        enhanced = clahe.apply(gray)

        return Image.fromarray(enhanced)

    # =========================================================
    # LOW RESOLUTION PIPELINE
    # =========================================================

    def low_resolution_pipeline(self, image: Image.Image) -> Image.Image:
        """
        For tiny/blurry text.
        """

        gray = self._to_gray(image)

        # Upscale
        upscaled = cv2.resize(
            gray,
            None,
            fx=2,
            fy=2,
            interpolation=cv2.INTER_CUBIC
        )

        # Sharpen
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])

        sharpened = cv2.filter2D(upscaled, -1, kernel)

        return Image.fromarray(sharpened)

    # =========================================================
    # NOISY PIPELINE
    # =========================================================

    def noisy_pipeline(self, image: Image.Image) -> Image.Image:
        """
        For noisy scans/photos.
        """

        gray = self._to_gray(image)

        denoised = cv2.fastNlMeansDenoising(
            gray,
            None,
            h=10
        )

        thresh = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            15
        )

        return Image.fromarray(thresh)

    # =========================================================
    # MEDICAL REPORT PIPELINE
    # =========================================================

    def medical_report_pipeline(self, image: Image.Image) -> Image.Image:
        """
        Optimized for medical reports/tables.
        """

        gray = self._to_gray(image)

        # Contrast enhancement
        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        )

        contrast = clahe.apply(gray)

        # Thresholding
        thresh = cv2.adaptiveThreshold(
            contrast,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            15
        )

        # Light sharpening
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])

        sharpened = cv2.filter2D(thresh, -1, kernel)

        return Image.fromarray(sharpened)

    # =========================================================
    # UTILITIES
    # =========================================================

    def _to_gray(self, image: Image.Image):
        """Convert PIL image to grayscale OpenCV image"""

        img = np.array(image)

        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        else:
            gray = img

        return gray