# backend/ingestion/ocr_handler.py
"""
OCR handling using Tesseract.
Extracts text from PDF images and scanned documents.
"""

import io
import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image
from typing import Tuple, Optional
from config.settings import UploadConfig
from config.logging_config import get_logger
from backend.ingestion.image_quality_analyzer import ImageQualityAnalyzer
from backend.ingestion.preprocessing_strategies import OCRPreprocessor
from backend.ingestion.strategy_selector import OCRStrategySelector

logger = get_logger(__name__)

class OCRHandler:
    """Handles OCR operations using Tesseract"""
    
    def __init__(self):
        self.language = UploadConfig.OCR_LANGUAGE
        self.dpi = UploadConfig.OCR_DPI
        self.custom_config = UploadConfig.CUSTOM_OCR_CONFIG
        self.quality_analyzer = ImageQualityAnalyzer()
        self.strategy_selector = OCRStrategySelector()
        self.preprocessor = OCRPreprocessor()
    
    def extract_from_images(self, pdf_bytes: bytes) -> Tuple[str, dict]:
        """
        Extract text from PDF using OCR.
        
        Args:
            pdf_bytes: PDF file as bytes
            
        Returns:
            (extracted_text, metadata)
        """
        logger.info("Starting OCR extraction...")
        
        try:
            # Convert PDF to images
            images = convert_from_bytes(
                pdf_bytes,
                dpi=self.dpi,
                fmt='jpeg'
            )
            
            logger.info(f"Converted PDF to {len(images)} images")
            
            # Extract text from each page
            full_text = ""
            confidences = []
            
            for i, image in enumerate(images, 1):
                logger.info(f"Processing page {i}/{len(images)}...")

                metrics = self.quality_analyzer.analyze(image)

                selected_strategy = self.strategy_selector.choose_strategy(metrics)

                logger.info(f"Selected preprocessing strategy: {selected_strategy}")

                preprocessed_image = self.preprocessor.apply_strategy(
                    image,
                    selected_strategy
                )
                
                # Get OCR data with confidence
                ocr_data = pytesseract.image_to_data(
                    preprocessed_image,
                    lang=self.language,
                    config=self.custom_config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Extract text
                page_text = pytesseract.image_to_string(
                    preprocessed_image,
                    lang=self.language,
                    config=self.custom_config
                )
                
                full_text += f"\n--- Page {i} ---\n{page_text}"
                
                # Calculate average confidence for this page
                page_confidences = [
                    int(conf) for conf in ocr_data['conf'] 
                    if conf != '-1' and str(conf).isdigit()
                ]
                if page_confidences:
                    avg_confidence = sum(page_confidences) / len(page_confidences)
                    confidences.append(avg_confidence)
                    logger.info(f"Page {i} OCR confidence: {avg_confidence:.1f}%")
            
            # Calculate overall confidence
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            metadata = {
                "page_count": len(images),
                "ocr_confidence": round(overall_confidence, 2),
                "extraction_method": "ocr"
            }
            
            logger.info(f"OCR completed. Extracted {len(full_text)} characters with {overall_confidence:.1f}% confidence")
            
            return full_text, metadata
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise
    
    def extract_from_image_file(self, image: Image.Image) -> Tuple[str, float]:
        """
        Extract text from a single image.
        
        Args:
            image: PIL Image object
            
        Returns:
            (text, confidence)
        """
        try:
            # Get text
            metrics = self.quality_analyzer.analyze(image)

            selected_strategy = self.strategy_selector.choose_strategy(metrics)

            preprocessed_image = self.preprocessor.apply_strategy(
                image,
                selected_strategy
            )
            text = pytesseract.image_to_string(preprocessed_image, lang=self.language, config=self.custom_config)
            
            # Get confidence
            ocr_data = pytesseract.image_to_data(
                preprocessed_image,
                lang=self.language,
                config=self.custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            confidences = [
                int(conf) for conf in ocr_data['conf'] 
                if conf != '-1' and str(conf).isdigit()
            ]
            
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return text, avg_confidence
            
        except Exception as e:
            logger.error(f"Image OCR failed: {str(e)}")
            raise
    
    def is_text_extractable(self, pdf_bytes: bytes) -> bool:
        """
        Check if PDF has extractable text (not scanned image).
        
        Args:
            pdf_bytes: PDF file bytes
            
        Returns:
            True if text can be extracted directly
        """
        try:
            from PyPDF2 import PdfReader
            
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)
            
            # Check first page for text
            if len(reader.pages) > 0:
                first_page_text = reader.pages[0].extract_text()
                # If we got meaningful text, it's extractable
                return len(first_page_text.strip()) > 50
            
            return False
            
        except Exception as e:
            logger.warning(f"Could not check text extractability: {str(e)}")
            return False