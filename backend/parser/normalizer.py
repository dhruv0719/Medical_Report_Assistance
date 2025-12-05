# backend/parser/normalizer.py
"""
Text normalization utilities.
Cleans and standardizes extracted text before parsing.
"""

import re
from typing import Dict

class TextNormalizer:
    """Normalizes extracted text for better parsing"""
    
    @staticmethod
    def normalize(text: str) -> str:
        """
        Apply all normalization steps.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Normalized text
        """
        text = TextNormalizer.remove_excessive_whitespace(text)
        text = TextNormalizer.standardize_line_breaks(text)
        text = TextNormalizer.normalize_special_chars(text)
        text = TextNormalizer.fix_common_ocr_errors(text)
        return text
    
    @staticmethod
    def remove_excessive_whitespace(text: str) -> str:
        """Remove extra spaces while preserving structure"""
        # Remove multiple spaces
        text = re.sub(r' +', ' ', text)
        # Remove spaces at line start/end
        text = re.sub(r'^ +', '', text, flags=re.MULTILINE)
        text = re.sub(r' +$', '', text, flags=re.MULTILINE)
        return text
    
    @staticmethod
    def standardize_line_breaks(text: str) -> str:
        """Standardize line breaks"""
        # Convert all line breaks to \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Remove excessive line breaks (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text
    
    @staticmethod
    def normalize_special_chars(text: str) -> str:
        """Normalize special characters"""
        replacements = {
            '–': '-',   # En dash to hyphen
            '—': '-',   # Em dash to hyphen
            ''': "'",   # Smart quote
            ''': "'",   # Smart quote
            '"': '"',   # Smart quote
            '"': '"',   # Smart quote
            '…': '...',  # Ellipsis
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    @staticmethod
    def fix_common_ocr_errors(text: str) -> str:
        """Fix common OCR misreads"""
        # Common OCR mistakes
        fixes = {
            r'\bO\b(?=\d)': '0',  # Letter O → Number 0 before digits
            r'(?<=\d)O\b': '0',   # Letter O → Number 0 after digits
            r'\bl\b(?=\d)': '1',  # Letter l → Number 1 before digits
        }
        
        for pattern, replacement in fixes.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    @staticmethod
    def normalize_units(unit: str) -> str:
        """
        Normalize unit representations.
        
        Args:
            unit: Raw unit string
            
        Returns:
            Standardized unit
        """
        unit = unit.strip()
        
        # Common unit normalizations
        unit_map = {
            'g/dl': 'g/dL',
            'gm/dl': 'g/dL',
            'mg/dl': 'mg/dL',
            'meq/l': 'mEq/L',
            'mmol/l': 'mmol/L',
            'x10^3/ul': 'x10³/µL',
            'x10^3/µl': 'x10³/µL',
            'k/ul': 'x10³/µL',
            'k/µl': 'x10³/µL',
            'cells/ul': 'cells/µL',
            'u/l': 'U/L',
            'iu/l': 'IU/L',
        }
        
        unit_lower = unit.lower()
        return unit_map.get(unit_lower, unit)
    
    @staticmethod
    def normalize_test_name(name: str) -> str:
        """
        Normalize test names.
        
        Args:
            name: Raw test name
            
        Returns:
            Standardized test name
        """
        name = name.strip()
        
        # Remove trailing colons
        name = name.rstrip(':')
        
        # Capitalize properly
        # Don't use title() as it messes up abbreviations
        name = name.strip()
        
        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name)
        
        return name


__all__ = [
    "TextNormalizer",
]