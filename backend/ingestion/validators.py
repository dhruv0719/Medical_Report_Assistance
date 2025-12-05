# backend/ingestion/validators.py
"""
File upload validation utilities.
Checks file type, size, and content safety.
"""

from pathlib import Path
from typing import Tuple, Optional
import hashlib
from config.settings import UploadConfig

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class FileValidator:
    """Validates uploaded files before processing"""
    
    def __init__(self):
        self.max_size = UploadConfig.MAX_FILE_SIZE_BYTES
        self.allowed_extensions = UploadConfig.ALLOWED_EXTENSIONS
    
    def validate(self, filename: str, file_content: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate file before processing.
        
        Args:
            filename: Original filename
            file_content: File bytes
            
        Returns:
            (is_valid, error_message)
        """
        # Check file size
        file_size = len(file_content)
        if file_size > self.max_size:
            return False, f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds maximum allowed ({UploadConfig.MAX_FILE_SIZE_MB} MB)"
        
        if file_size == 0:
            return False, "File is empty"
        
        # Check file extension
        file_ext = Path(filename).suffix.lower().lstrip('.')
        if file_ext not in self.allowed_extensions:
            return False, f"File type '.{file_ext}' not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
        
        # Check for minimum content
        if file_ext == 'txt':
            try:
                text = file_content.decode('utf-8')
                if len(text.strip()) < 10:
                    return False, "Text file content is too short"
            except UnicodeDecodeError:
                return False, "Text file is not valid UTF-8"
        
        # PDF basic validation (check magic number)
        if file_ext == 'pdf':
            if not file_content.startswith(b'%PDF'):
                return False, "File does not appear to be a valid PDF"
        
        return True, None
    
    def get_file_hash(self, file_content: bytes) -> str:
        """
        Generate SHA-256 hash of file content for tracking.
        
        Args:
            file_content: File bytes
            
        Returns:
            Hex digest of file hash
        """
        return hashlib.sha256(file_content).hexdigest()
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Get just the filename, no path
        filename = Path(filename).name
        
        # Remove any suspicious characters
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.')
        sanitized = ''.join(c if c in safe_chars else '_' for c in filename)
        
        # Ensure it has an extension
        if '.' not in sanitized:
            sanitized += '.txt'
        
        return sanitized


# Convenience function
def validate_upload(filename: str, file_content: bytes) -> Tuple[bool, Optional[str], str]:
    """
    Validate uploaded file.
    
    Returns:
        (is_valid, error_message, file_hash)
    """
    validator = FileValidator()
    is_valid, error = validator.validate(filename, file_content)
    file_hash = validator.get_file_hash(file_content) if is_valid else ""
    
    return is_valid, error, file_hash


__all__ = [
    "FileValidator",
    "ValidationError",
    "validate_upload",
]