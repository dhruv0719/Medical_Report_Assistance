# backend/ingestion/strategy_selector.py
"""
OCR preprocessing strategy selector.

This module decides which preprocessing pipeline
should be used based on image quality metrics.
"""

from typing import Dict


class OCRStrategySelector:
    """Selects the best OCR preprocessing strategy"""

    def __init__(self):
        pass

    def choose_strategy(self, metrics: Dict) -> str:
        """
        Choose preprocessing strategy based on image metrics.

        Args:
            metrics: Dictionary returned by ImageQualityAnalyzer

        Returns:
            Strategy name
        """

        width, height = metrics["resolution"]

        brightness = metrics["brightness"]
        contrast = metrics["contrast"]
        blurriness = metrics["blurriness"]
        noise = metrics["noise"]
        text_density = metrics["text_density"]

        # =====================================================
        # DEBUG LOGIC (OPTIONAL)
        # =====================================================

        print("\n========== IMAGE METRICS ==========")
        print(f"Resolution   : {width}x{height}")
        print(f"Brightness   : {brightness:.2f}")
        print(f"Contrast     : {contrast:.2f}")
        print(f"Blurriness   : {blurriness:.2f}")
        print(f"Noise        : {noise:.2f}")
        print(f"Text Density : {text_density:.4f}")
        print("===================================\n")

        # =====================================================
        # STRATEGY RULES
        # =====================================================

        # -----------------------------------------------------
        # VERY SMALL IMAGE
        # -----------------------------------------------------

        if width < 1000:
            return "low_resolution"

        # -----------------------------------------------------
        # VERY BLURRY IMAGE
        # -----------------------------------------------------

        if blurriness < 80:
            return "low_resolution"

        # -----------------------------------------------------
        # HIGH NOISE IMAGE
        # -----------------------------------------------------

        if noise > 12:
            return "noisy"

        # -----------------------------------------------------
        # LOW CONTRAST DOCUMENT
        # -----------------------------------------------------

        if contrast < 35:
            return "medical_report"

        # -----------------------------------------------------
        # VERY DARK IMAGE
        # -----------------------------------------------------

        if brightness < 80:
            return "medical_report"

        # -----------------------------------------------------
        # HIGH TEXT DENSITY
        # Likely structured document/report
        # -----------------------------------------------------

        if text_density > 0.15:
            return "medical_report"

        # -----------------------------------------------------
        # CLEAN DOCUMENT
        # -----------------------------------------------------

        return "light"