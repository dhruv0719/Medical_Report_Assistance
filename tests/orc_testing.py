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
    OCR Testing Utility — updated for AdaptiveOCREngine.

    Key changes from the old version:
    - preprocessor is accessed via ocr.engine.preprocessor
      (OCRHandler no longer exposes it directly)
    - Strategy shown as [HINT STRATEGY] — it is a priority hint,
      not a binding decision.  The engine may skip it entirely if
      raw OCR is already good enough.
    - After OCR runs, [ADAPTIVE RESULT] shows what the engine
      actually decided: winning strategy, composite score, and
      whether preprocessing was skipped.
    - PDF metadata now includes per-page breakdown; printed in full.
    - "OCR Confidence" label replaced with "Composite Score" to
      reflect that it is the OCREvaluator composite (0-100), not
      raw Tesseract confidence.
    """

    def __init__(self):

        self.ocr = OCRHandler()

        Path("debug").mkdir(exist_ok=True)
        Path("debug/preprocessed").mkdir(parents=True, exist_ok=True)
        Path("debug/raw").mkdir(parents=True, exist_ok=True)

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
            # ANALYZE IMAGE QUALITY
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
            # HINT STRATEGY
            # Strategy selector output is now a priority HINT
            # passed to AdaptiveOCREngine — not a forced decision.
            # The engine may skip preprocessing entirely if raw
            # OCR composite score >= RAW_SKIP_THRESHOLD (85).
            # =================================================

            hint_strategy = self.ocr.strategy_selector.choose_strategy(metrics)

            print("\n[HINT STRATEGY]")
            print("-" * 50)
            print(f"{hint_strategy}  (hint only — engine decides final strategy)")

            # =================================================
            # SAVE HINT-STRATEGY PREPROCESSED IMAGE (debug only)
            # This shows what the hint pipeline would produce.
            # It does NOT mean the engine used this pipeline.
            # =================================================

            processed_image = self.ocr.engine.preprocessor.apply_strategy(
                image,
                hint_strategy
            )

            debug_image_path = (
                f"debug/preprocessed/"
                f"{Path(image_path).stem}_"
                f"hint_{hint_strategy}.png"
            )
            processed_image.save(debug_image_path)

            print(f"\n[INFO] Hint-strategy preprocessed image saved:")
            print(f"       {debug_image_path}")
            print(f"       (for visual debugging only — engine may not have used this)")

            # =================================================
            # RUN ADAPTIVE OCR
            # =================================================

            start_time = time.time()
            text, composite_score = self.ocr.extract_from_image_file(image)
            processing_time = round(time.time() - start_time, 2)

            # =================================================
            # RESULTS
            # =================================================

            print("\n[RESULTS]")
            print("-" * 50)
            print(f"Composite Score : {composite_score:.2f} / 100")
            print(f"Processing Time : {processing_time} sec")

            # =================================================
            # TEXT PREVIEW
            # =================================================

            print("\n[TEXT PREVIEW]")
            print("-" * 80)
            print(text[:3000])
            print("-" * 80)

            # =================================================
            # SAVE OCR OUTPUT
            # =================================================

            output_text_path = (
                f"debug/"
                f"{Path(image_path).stem}_ocr_output.txt"
            )

            with open(output_text_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"\n[INFO] OCR text saved: {output_text_path}")

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            raise

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
            # CHECK NATIVE TEXT EXTRACTABILITY
            # =================================================

            extractable = self.ocr.is_text_extractable(pdf_bytes)
            print(f"[INFO] Native Text Extractable: {extractable}")

            # =================================================
            # CONVERT TO IMAGES FOR PER-PAGE DEBUG ANALYSIS
            # (separate from the OCR run below)
            # =================================================

            images = convert_from_path(pdf_path)
            print(f"[INFO] Total Pages: {len(images)}")

            for i, image in enumerate(images, 1):

                print("\n" + "-" * 80)
                print(f"PAGE {i} — PRE-RUN ANALYSIS")
                print("-" * 80)

                # Image metrics
                metrics = self.ocr.quality_analyzer.analyze(image)

                print("\n[IMAGE METRICS]")
                print("-" * 50)
                for key, value in metrics.items():
                    if isinstance(value, float):
                        print(f"{key:<15}: {value:.2f}")
                    else:
                        print(f"{key:<15}: {value}")

                # Hint strategy
                hint_strategy = self.ocr.strategy_selector.choose_strategy(metrics)

                print("\n[HINT STRATEGY]")
                print("-" * 50)
                print(f"{hint_strategy}  (hint only — engine decides final strategy)")

                # Save hint-preprocessed image for visual debugging
                processed_image = self.ocr.engine.preprocessor.apply_strategy(
                    image,
                    hint_strategy
                )

                debug_image_path = (
                    f"debug/preprocessed/"
                    f"{Path(pdf_path).stem}_"
                    f"page_{i}_"
                    f"hint_{hint_strategy}.png"
                )
                processed_image.save(debug_image_path)

                print(f"\n[INFO] Hint-strategy preprocessed image saved:")
                print(f"       {debug_image_path}")

            # =================================================
            # RUN ADAPTIVE OCR (full document)
            # =================================================

            start_time = time.time()
            text, metadata = self.ocr.extract_from_images(pdf_bytes)
            wall_time = round(time.time() - start_time, 2)

            # =================================================
            # SUMMARY RESULTS
            # =================================================

            print("\n" + "=" * 80)
            print("ADAPTIVE OCR RESULTS")
            print("=" * 80)

            print(f"\n[SUMMARY]")
            print("-" * 50)
            print(f"Pages             : {metadata['page_count']}")
            print(f"Mean Composite    : {metadata['ocr_confidence']} / 100")
            print(f"Engine Time       : {metadata['total_time_sec']} sec")
            print(f"Wall-clock Time   : {wall_time} sec")

            # =================================================
            # PER-PAGE ADAPTIVE DECISIONS
            # Shows what the engine actually decided for each page,
            # which may differ from the hint shown above.
            # =================================================

            print(f"\n[PER-PAGE ADAPTIVE DECISIONS]")
            print("-" * 50)

            for page in metadata.get("page_details", []):
                skipped  = page["skipped_preprocessing"]
                ceiling  = page.get("hit_resolution_ceiling", False)
                early    = page.get("stopped_early", False)

                badges = []
                if skipped:
                    badges.append("SKIPPED PREPROCESSING")
                if ceiling:
                    badges.append("RESOLUTION CEILING")
                if early:
                    badges.append("STOPPED EARLY")
                badge_str = " | ".join(badges) if badges else "PREPROCESSED"

                print(
                    f"  Page {page['page']:<3} "
                    f"winner={page['winning_strategy']:<16} "
                    f"composite={page['composite_score']:>5.1f}  "
                    f"tess={page['tesseract_confidence']:>5.1f}  "
                    f"[{badge_str}]"
                )
                print(
                    f"         tried: {page['strategies_tried']}"
                )

            # =================================================
            # TEXT PREVIEW
            # =================================================

            print("\n[TEXT PREVIEW]")
            print("-" * 80)
            print(text[:3000])
            print("-" * 80)

            # =================================================
            # SAVE OCR OUTPUT
            # =================================================

            output_text_path = (
                f"debug/"
                f"{Path(pdf_path).stem}_ocr_output.txt"
            )

            with open(output_text_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"\n[INFO] OCR text saved: {output_text_path}")

        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            raise


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    tester = OCRTester()

    # =========================================================
    # TEST IMAGE
    # =========================================================

    tester.test_image(r"D:\Medical_Assitance\sample\Images\Report_2.png")

    # =========================================================
    # TEST PDF
    # =========================================================

    # tester.test_pdf(r"sample\pdfs\Report_2.pdf")