# backend/ingestion/image_quality_analyzer.py

"""
Image quality analyzer for OCR suitability.
"""

import cv2
import numpy as np
from PIL import Image


class ImageQualityAnalyzer:
    """Analyzes image quality for OCR suitability"""

    def __init__(self):
        pass

    def analyze(self, image: Image.Image) -> dict:
        """
        Analyze image quality metrics.

        Returns:
            Dictionary containing image quality metrics.
        """

        gray = self._to_gray(image)

        metrics = {
            "resolution": self.calculate_resolution(image),
            "brightness": self.calculate_brightness(gray),
            "contrast": self.calculate_contrast(gray),
            "blurriness": self.estimate_blurriness(gray),
            "noise": self.estimate_noise(gray),
            "text_density": self.estimate_text_density(gray)
        }

        return metrics

    def _to_gray(self, image: Image.Image):
        """Convert PIL image to grayscale OpenCV image"""
        opencv_image = np.array(image)

        if len(opencv_image.shape) == 3:
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2GRAY)
        else:
            gray = opencv_image

        return gray

    def calculate_resolution(self, image: Image.Image) -> tuple:
        """Calculate image resolution"""
        return image.size

    def calculate_brightness(self, gray) -> float:
        """Calculate average brightness"""
        return float(np.mean(gray))

    def calculate_contrast(self, gray) -> float:
        """Calculate image contrast"""
        return float(np.std(gray))

    def estimate_blurriness(self, gray) -> float:
        """
        Estimate blurriness using variance of Laplacian.

        Lower value = blurrier image
        """
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def estimate_noise(self, gray) -> float:
        """
        Estimate image noise.

        Higher value = more noise
        """
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        noise = np.mean(cv2.absdiff(gray, blur))

        return float(noise)

    def estimate_text_density(self, gray) -> float:
        """
        Estimate how much text exists in image.
        """

        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            31,
            15
        )

        text_pixels = np.sum(thresh > 0)
        total_pixels = thresh.size

        density = text_pixels / total_pixels

        return float(density)