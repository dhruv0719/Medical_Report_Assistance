# backend/ingestion/document_processor.py
"""
Main document processing module.
Orchestrates text extraction from various file formats.
"""

import io
import time
from typing import Tuple, Dict
from PyPDF2 import PdfReader
from config.logging_config import get_logger
from backend.ingestion.ocr_handler import OCRHandler
from backend.ingestion.validators import FileValidator
from backend.parser.entities import ExtractionMetadata

logger = get_logger(__name__)

class DocumentProcessor:
    """Main class for processing uploaded documents"""
    
    def __init__(self):
        self.validator = FileValidator()
        self.ocr_handler = OCRHandler()
    
    def process(self, filename: str, file_content: bytes) -> Tuple[str, ExtractionMetadata]:
        """
        Process uploaded document and extract text.
        
        Args:
            filename: Original filename
            file_content: File bytes
            
        Returns:
            (extracted_text, metadata)
        """
        start_time = time.time()
        
        # Validate file
        is_valid, error = self.validator.validate(filename, file_content)
        if not is_valid:
            raise ValueError(f"File validation failed: {error}")
        
        # Sanitize filename
        safe_filename = self.validator.sanitize_filename(filename)
        
        # Determine file type
        file_ext = safe_filename.split('.')[-1].lower()
        file_size = len(file_content)
        
        logger.info(f"Processing file: {safe_filename} ({file_size / 1024:.2f} KB, type: {file_ext})")
        
        # Extract text based on file type
        if file_ext == 'txt':
            text, metadata = self._process_text_file(file_content)
        elif file_ext == 'pdf':
            text, metadata = self._process_pdf_file(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create metadata object
        extraction_metadata = ExtractionMetadata(
            filename=safe_filename,
            file_type=file_ext,
            file_size_bytes=file_size,
            extraction_method=metadata['extraction_method'],
            page_count=metadata.get('page_count', 1),
            extraction_time_seconds=round(processing_time, 2),
            ocr_confidence=metadata.get('ocr_confidence')
        )
        
        logger.info(
            f"Extraction complete: {len(text)} characters extracted "
            f"via {metadata['extraction_method']} in {processing_time:.2f}s"
        )
        
        return text, extraction_metadata
    
    def _process_text_file(self, file_content: bytes) -> Tuple[str, Dict]:
        """Process plain text file"""
        try:
            text = file_content.decode('utf-8')
            metadata = {
                'extraction_method': 'text',
                'page_count': 1
            }
            return text, metadata
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode text file: {str(e)}")
            raise ValueError("Text file is not valid UTF-8")
    
    def _process_pdf_file(self, file_content: bytes) -> Tuple[str, Dict]:
        """
        Process PDF file.
        Try text extraction first, fall back to OCR if needed.
        """
        # First, try text-based extraction
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            page_count = len(reader.pages)
            
            logger.info(f"PDF has {page_count} pages")
            
            # Extract text from all pages
            text = ""
            for i, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {i} ---\n{page_text}"
            
            # Check if we got meaningful text
            if len(text.strip()) > 100:
                logger.info(f"Successfully extracted text from PDF ({len(text)} chars)")
                metadata = {
                    'extraction_method': 'text',
                    'page_count': page_count
                }
                return text, metadata
            else:
                logger.info("PDF text extraction yielded minimal content, falling back to OCR")
        
        except Exception as e:
            logger.warning(f"PDF text extraction failed: {str(e)}, falling back to OCR")
        
        # Fall back to OCR
        try:
            text, ocr_metadata = self.ocr_handler.extract_from_images(file_content)
            return text, ocr_metadata
        except Exception as e:
            logger.error(f"OCR extraction also failed: {str(e)}")
            raise ValueError(f"Could not extract text from PDF: {str(e)}")


__all__ = [
    "DocumentProcessor",
]