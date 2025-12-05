# backend/parser/patterns.py
"""Regex patterns for extracting structured data."""

import re
from typing import List, Pattern

PATIENT_ID_PATTERNS: List[Pattern] = [
    re.compile(r'Patient\s+ID[:\s]+([A-Z0-9-]+)', re.IGNORECASE),
    re.compile(r'MRN[:\s]+([A-Z0-9-]+)', re.IGNORECASE),
]

DATE_PATTERNS: List[Pattern] = [
    re.compile(r'Date\s+of\s+Collection[:\s]+([\d\-/]+)', re.IGNORECASE),
    re.compile(r'Collection\s+Date[:\s]+([\d\-/]+)', re.IGNORECASE),
]

LAB_NAME_PATTERNS: List[Pattern] = [
    re.compile(r'Performing\s+Lab[:\s]+(.+?)(?:\n|$)', re.IGNORECASE),
]

IMPRESSION_PATTERNS: List[Pattern] = [
    re.compile(r'IMPRESSION[:\s]+(.*?)(?=\n\n|\nPerforming|\Z)', re.IGNORECASE | re.DOTALL),
    re.compile(r'CONCLUSION[:\s]+(.*?)(?=\n\n|\nPerforming|\Z)', re.IGNORECASE | re.DOTALL),
]

LAB_TEST_PATTERN_1 = re.compile(
    r'^([A-Z][A-Za-z\s]+?):\s*([\d.]+)\s+([^\s(]+)\s*\(([\d.\s\-]+)\)(?:\s*\[([HLhl]+)\])?\s*$',
    re.MULTILINE
)

LAB_TEST_PATTERN_2 = re.compile(
    r'^([A-Z][A-Za-z\s]+?)\s+([\d.]+)\s+\(([\d.\s\-]+)\)\s+([^\s\[]+)(?:\s*\[([HLhl]+)\])?\s*$',
    re.MULTILINE
)

LAB_TEST_PATTERNS: List[Pattern] = [LAB_TEST_PATTERN_1, LAB_TEST_PATTERN_2]

def extract_with_pattern(text: str, patterns: List[Pattern]) -> str:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return ''

def find_all_matches(text: str, patterns: List[Pattern]) -> list:
    matches = []
    for pattern in patterns:
        matches.extend(pattern.finditer(text))
    return matches

__all__ = ['PATIENT_ID_PATTERNS', 'DATE_PATTERNS', 'LAB_NAME_PATTERNS', 'LAB_TEST_PATTERNS', 'IMPRESSION_PATTERNS', 'extract_with_pattern', 'find_all_matches']