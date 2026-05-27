# tests/raw_ocr_testing.py
import sys
import time
from pathlib import Path

from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes

# Add workspace root to path so backend module can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import UploadConfig


class RawOCRTester:
    """
    Tests OCR WITHOUT preprocessing.

    Purpose:
    - Compare raw OCR vs preprocessed OCR
    - Benchmark improvements
    - Detect over-processing problems
    """

    def __init__(self):
        self.language = UploadConfig.OCR_LANGUAGE
        self.custom_config = UploadConfig.CUSTOM_OCR_CONFIG
        self.dpi = UploadConfig.OCR_DPI

        Path("debug/raw").mkdir(parents=True, exist_ok=True)

    def test_image(self, image_path: str):

        print("\n" + "=" * 80)
        print(f"RAW OCR TEST - IMAGE: {image_path}")
        print("=" * 80)

        try:
            image = Image.open(image_path)

            print(f"[INFO] Image size: {image.size}")

            # =========================
            # OCR Timing
            # =========================
            start_time = time.time()

            # OCR DATA
            ocr_data = pytesseract.image_to_data(
                image,
                lang=self.language,
                config=self.custom_config,
                output_type=pytesseract.Output.DICT
            )

            # OCR TEXT
            text = pytesseract.image_to_string(
                image,
                lang=self.language,
                config=self.custom_config
            )

            end_time = time.time()

            processing_time = round(end_time - start_time, 2)

            # =========================
            # CONFIDENCE
            # =========================
            confidences = []

            for conf in ocr_data["conf"]:
                try:
                    conf_value = float(conf)

                    if conf_value > 0:
                        confidences.append(conf_value)

                except:
                    continue

            avg_confidence = (
                sum(confidences) / len(confidences)
                if confidences else 0
            )

            # =========================
            # RESULTS
            # =========================
            print("\n[RESULTS]")
            print(f"OCR Confidence : {avg_confidence:.2f}%")
            print(f"Processing Time: {processing_time} sec")

            print("\n[TEXT PREVIEW]")
            print("-" * 80)

            print(text[:3000])

            print("-" * 80)

            # Save text output
            output_path = (
                f"debug/raw/"
                f"{Path(image_path).stem}_raw_ocr.txt"
            )

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"\n[INFO] Saved OCR output: {output_path}")

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")

    def test_pdf(self, pdf_path: str):

        print("\n" + "=" * 80)
        print(f"RAW OCR TEST - PDF: {pdf_path}")
        print("=" * 80)

        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # Convert PDF to images
            images = convert_from_bytes(
                pdf_bytes,
                dpi=self.dpi,
                fmt="jpeg"
            )

            print(f"[INFO] Total pages: {len(images)}")

            full_text = ""
            all_confidences = []

            start_time = time.time()

            for i, image in enumerate(images, 1):

                print(f"\n[INFO] Processing page {i}")

                # OCR DATA
                ocr_data = pytesseract.image_to_data(
                    image,
                    lang=self.language,
                    config=self.custom_config,
                    output_type=pytesseract.Output.DICT
                )

                # OCR TEXT
                page_text = pytesseract.image_to_string(
                    image,
                    lang=self.language,
                    config=self.custom_config
                )

                full_text += f"\n--- Page {i} ---\n{page_text}"

                # Confidence calculation
                for conf in ocr_data["conf"]:
                    try:
                        conf_value = float(conf)

                        if conf_value > 0:
                            all_confidences.append(conf_value)

                    except:
                        continue

            end_time = time.time()

            processing_time = round(end_time - start_time, 2)

            avg_confidence = (
                sum(all_confidences) / len(all_confidences)
                if all_confidences else 0
            )

            # =========================
            # RESULTS
            # =========================
            print("\n[RESULTS]")
            print(f"OCR Confidence : {avg_confidence:.2f}%")
            print(f"Processing Time: {processing_time} sec")

            print("\n[TEXT PREVIEW]")
            print("-" * 80)

            print(full_text[:3000])

            print("-" * 80)

            # Save OCR output
            output_path = (
                f"debug/raw/"
                f"{Path(pdf_path).stem}_raw_ocr.txt"
            )

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_text)

            print(f"\n[INFO] Saved OCR output: {output_path}")

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")


if __name__ == "__main__":

    tester = RawOCRTester()

    # ==================================
    # IMAGE TEST
    # ==================================
    # tester.test_image(r"D:\Medical_Assitance\sample\Images\Report_2.png")

    # ==================================
    # PDF TEST
    # ==================================
    tester.test_pdf(r"sample\pdfs\Report_1.pdf")