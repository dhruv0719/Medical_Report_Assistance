# tests/debug_parser.py
"""Debug script to see exactly what the parser sees"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.parser.normalizer import TextNormalizer
from backend.parser.patterns import LAB_TEST_PATTERNS
import re

# Sample text
test_text = """LABORATORY REPORT
=================

Patient ID: TEST001
Date of Collection: 2025-01-10
Test: Complete Blood Count (CBC)

RESULTS:
--------
Hemoglobin: 11.2 g/dL (13.0-17.0) [L]
White Blood Cell Count: 6.8 x10³/µL (4.0-11.0)
Platelet Count: 230 x10³/µL (150-400)

IMPRESSION:
Mild anemia noted.

Performing Lab: LabCorp
"""

print("="*60)
print("RAW TEXT:")
print("="*60)
print(repr(test_text[:200]))

# Normalize
normalizer = TextNormalizer()
normalized = normalizer.normalize(test_text)

print("\n" + "="*60)
print("NORMALIZED TEXT:")
print("="*60)
print(repr(normalized[:200]))

print("\n" + "="*60)
print("LINES IN RESULTS SECTION:")
print("="*60)
lines = normalized.split('\n')
for i, line in enumerate(lines):
    if 'RESULTS' in line or 'Hemoglobin' in line or 'White Blood' in line or 'Platelet' in line:
        print(f"{i:3d}: {repr(line)}")

print("\n" + "="*60)
print("TESTING PATTERNS:")
print("="*60)

# Test each pattern
for idx, pattern in enumerate(LAB_TEST_PATTERNS, 1):
    print(f"\nPattern {idx}:")
    print(f"  Regex: {pattern.pattern[:100]}...")
    matches = pattern.finditer(normalized)
    match_count = 0
    for match in matches:
        match_count += 1
        print(f"  Match {match_count}: {match.group()[:50]}...")
        print(f"    Groups: {match.groups()}")
    
    if match_count == 0:
        print(f"  ❌ No matches")

# Try a simpler manual regex
print("\n" + "="*60)
print("MANUAL TEST:")
print("="*60)

simple_pattern = re.compile(r'(\w[\w\s]+?):\s*([\d.]+)\s+([^\s(]+)\s+KATEX_INLINE_OPEN([\d.\-]+)KATEX_INLINE_CLOSE', re.MULTILINE)
matches = simple_pattern.finditer(normalized)
for match in matches:
    print(f"Match: {match.group()}")
    print(f"  Groups: {match.groups()}")