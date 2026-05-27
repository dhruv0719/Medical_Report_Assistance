# tests/ocr_testing.py

import sys
import time
from pathlib import Path

from PIL import Image
from pdf2image import convert_from_path

# =========================================================
# ADD PROJECT ROOT TO PATH
# =========================================================

sys.path.insert(0, str(Path(__file__).parent.parent))

# =========================================================
# IMPORT OCR HANDLER
# =========================================================

from backend.ingestion.ocr_handler import OCRHandler


class OCRTester:
    """
    OCR Testing Utility

    Features:
    - Test OCR on images
    - Test OCR on PDFs
    - Show image quality metrics
    - Show selected strategy
    - Save processed images
    - Save OCR text
    - Measure OCR performance
    """

    def __init__(self):

        self.ocr = OCRHandler()

        # =====================================================
        # DEBUG DIRECTORIES
        # =====================================================

        Path("debug").mkdir(exist_ok=True)

        Path("debug/preprocessed").mkdir(
            parents=True,
            exist_ok=True
        )

        Path("debug/raw").mkdir(
            parents=True,
            exist_ok=True
        )

    # =========================================================
    # IMAGE TESTING
    # =========================================================

    def test_image(self, image_path: str):

        print("\n" + "=" * 80)
        print(f"TESTING IMAGE: {image_path}")
        print("=" * 80)

        try:

            # =================================================
            # LOAD IMAGE
            # =================================================

            image = Image.open(image_path)

            print(f"[INFO] Original image size: {image.size}")

            # =================================================
            # ANALYZE IMAGE
            # =================================================

            metrics = self.ocr.quality_analyzer.analyze(image)

            print("\n[IMAGE METRICS]")
            print("-" * 50)

            for key, value in metrics.items():

                if isinstance(value, float):
                    print(f"{key:<15}: {value:.2f}")
                else:
                    print(f"{key:<15}: {value}")

            # =================================================
            # SELECT STRATEGY
            # =================================================

            selected_strategy = (
                self.ocr.strategy_selector.choose_strategy(metrics)
            )

            print("\n[SELECTED STRATEGY]")
            print("-" * 50)

            print(selected_strategy)

            # =================================================
            # APPLY PREPROCESSING
            # =================================================

            processed_image = (
                self.ocr.preprocessor.apply_strategy(
                    image,
                    selected_strategy
                )
            )

            # =================================================
            # SAVE PREPROCESSED IMAGE
            # =================================================

            debug_image_path = (
                f"debug/preprocessed/"
                f"{Path(image_path).stem}_"
                f"{selected_strategy}.png"
            )

            processed_image.save(debug_image_path)

            print(f"\n[INFO] Saved processed image:")
            print(debug_image_path)

            # =================================================
            # RUN OCR
            # =================================================

            start_time = time.time()

            text, confidence = (
                self.ocr.extract_from_image_file(image)
            )

            end_time = time.time()

            processing_time = round(
                end_time - start_time,
                2
            )

            # =================================================
            # RESULTS
            # =================================================

            print("\n[RESULTS]")
            print("-" * 50)

            print(f"OCR Confidence : {confidence:.2f}%")
            print(f"Processing Time: {processing_time} sec")

            # =================================================
            # TEXT PREVIEW
            # =================================================

            print("\n[TEXT PREVIEW]")
            print("-" * 80)

            preview = text[:3000]

            print(preview)

            print("-" * 80)

            # =================================================
            # SAVE OCR OUTPUT
            # =================================================

            output_text_path = (
                f"debug/"
                f"{Path(image_path).stem}_ocr_output.txt"
            )

            with open(
                output_text_path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(text)

            print(f"\n[INFO] OCR text saved:")
            print(output_text_path)

        except Exception as e:

            print(f"\n[ERROR] {str(e)}")

    # =========================================================
    # PDF TESTING
    # =========================================================

    def test_pdf(self, pdf_path: str):

        print("\n" + "=" * 80)
        print(f"TESTING PDF: {pdf_path}")
        print("=" * 80)

        try:

            # =================================================
            # LOAD PDF
            # =================================================

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # =================================================
            # CHECK TEXT EXTRACTABILITY
            # =================================================

            extractable = (
                self.ocr.is_text_extractable(pdf_bytes)
            )

            print(f"[INFO] Native Text Extractable: {extractable}")

            # =================================================
            # CONVERT PDF TO IMAGES FOR DEBUGGING
            # =================================================

            images = convert_from_path(pdf_path)

            print(f"[INFO] Total Pages: {len(images)}")

            # =================================================
            # ANALYZE EACH PAGE
            # =================================================

            for i, image in enumerate(images, 1):

                print("\n" + "-" * 80)
                print(f"PAGE {i}")
                print("-" * 80)

                # =============================================
                # ANALYZE IMAGE
                # =============================================

                metrics = (
                    self.ocr.quality_analyzer.analyze(image)
                )

                print("\n[IMAGE METRICS]")
                print("-" * 50)

                for key, value in metrics.items():

                    if isinstance(value, float):
                        print(f"{key:<15}: {value:.2f}")
                    else:
                        print(f"{key:<15}: {value}")

                # =============================================
                # SELECT STRATEGY
                # =============================================

                selected_strategy = (
                    self.ocr.strategy_selector.choose_strategy(
                        metrics
                    )
                )

                print("\n[SELECTED STRATEGY]")
                print("-" * 50)

                print(selected_strategy)

                # =============================================
                # APPLY PREPROCESSING
                # =============================================

                processed_image = (
                    self.ocr.preprocessor.apply_strategy(
                        image,
                        selected_strategy
                    )
                )

                # =============================================
                # SAVE PROCESSED IMAGE
                # =============================================

                debug_image_path = (
                    f"debug/preprocessed/"
                    f"{Path(pdf_path).stem}_"
                    f"page_{i}_"
                    f"{selected_strategy}.png"
                )

                processed_image.save(debug_image_path)

                print(f"\n[INFO] Saved processed image:")
                print(debug_image_path)

            # =================================================
            # RUN OCR
            # =================================================

            start_time = time.time()

            text, metadata = (
                self.ocr.extract_from_images(pdf_bytes)
            )

            end_time = time.time()

            processing_time = round(
                end_time - start_time,
                2
            )

            # =================================================
            # RESULTS
            # =================================================

            print("\n[RESULTS]")
            print("-" * 50)

            print(f"Pages           : {metadata['page_count']}")
            print(f"OCR Confidence  : {metadata['ocr_confidence']}%")
            print(f"Processing Time : {processing_time} sec")

            # =================================================
            # TEXT PREVIEW
            # =================================================

            print("\n[TEXT PREVIEW]")
            print("-" * 80)

            preview = text[:3000]

            print(preview)

            print("-" * 80)

            # =================================================
            # SAVE OCR OUTPUT
            # =================================================

            output_text_path = (
                f"debug/"
                f"{Path(pdf_path).stem}_ocr_output.txt"
            )

            with open(
                output_text_path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(text)

            print(f"\n[INFO] OCR text saved:")
            print(output_text_path)

        except Exception as e:

            print(f"\n[ERROR] {str(e)}")


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    tester = OCRTester()

    # =========================================================
    # TEST IMAGE
    # =========================================================

    # tester.test_image(r"D:\Medical_Assitance\sample\Images\Report_2.png")

    # =========================================================
    # TEST PDF
    # =========================================================

    tester.test_pdf(r"sample\pdfs\Report_1.pdf")