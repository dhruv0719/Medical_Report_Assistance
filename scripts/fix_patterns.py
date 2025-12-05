"""Generate patterns.py file to avoid copy-paste corruption"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# The file content - using raw strings and proper escaping
file_content = """# backend/parser/patterns.py
\"\"\"Regex patterns for extracting structured data from medical reports.\"\"\"

import re
from typing import List, Pattern

# Patient ID patterns
PATIENT_ID_PATTERNS: List[Pattern] = [
    re.compile(r'Patient\\s+ID[:\\s]+([A-Z0-9-]+)', re.IGNORECASE),
    re.compile(r'MRN[:\\s]+([A-Z0-9-]+)', re.IGNORECASE),
]

# Date patterns  
DATE_PATTERNS: List[Pattern] = [
    re.compile(r'Date\\s+of\\s+Collection[:\\s]+([\\d\\-/]+)', re.IGNORECASE),
    re.compile(r'Collection\\s+Date[:\\s]+([\\d\\-/]+)', re.IGNORECASE),
]

# Lab name patterns
LAB_NAME_PATTERNS: List[Pattern] = [
    re.compile(r'Performing\\s+Lab[:\\s]+(.+?)(?:\\n|$)', re.IGNORECASE),
]

# Impression patterns
IMPRESSION_PATTERNS: List[Pattern] = [
    re.compile(r'IMPRESSION[:\\s]+(.*?)(?=\\n\\n|\\nPerforming|\\Z)', re.IGNORECASE | re.DOTALL),
    re.compile(r'CONCLUSION[:\\s]+(.*?)(?=\\n\\n|\\nPerforming|\\Z)', re.IGNORECASE | re.DOTALL),
]

# Lab test patterns
# Pattern 1: "Test Name: Value Unit (Range) [Flag]"
# Example: "Hemoglobin: 11.2 g/dL (13.0-17.0) [L]"
LAB_TEST_PATTERN_1 = re.compile(
    r'^([A-Z][A-Za-z\\s]+?):\\s*([\\d.]+)\\s+([^\\s(]+)\\s*\KATEX_INLINE_OPEN([\\d.\\s\\-]+)\KATEX_INLINE_CLOSE(?:\\s*\```math
([HLhl]+)\```)?\\s*$',
    re.MULTILINE
)

# Pattern 2: "Test Name Value (Range) Unit [Flag]"
# Example: "WBC 8.5 (4.0-11.0) x10^3/uL"
LAB_TEST_PATTERN_2 = re.compile(
    r'^([A-Z][A-Za-z\\s]+?)\\s+([\\d.]+)\\s+\KATEX_INLINE_OPEN([\\d.\\s\\-]+)\KATEX_INLINE_CLOSE\\s+([^\\s\```math
]+)(?:\\s*\```math
([HLhl]+)\```)?\\s*$',
    re.MULTILINE
)

LAB_TEST_PATTERNS: List[Pattern] = [
    LAB_TEST_PATTERN_1,
    LAB_TEST_PATTERN_2,
]

# Helper functions
def extract_with_pattern(text: str, patterns: List[Pattern]) -> str:
    \"\"\"Try multiple patterns and return first match.\"\"\"
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return ""

def find_all_matches(text: str, patterns: List[Pattern]) -> list:
    \"\"\"Find all matches across multiple patterns.\"\"\"
    matches = []
    for pattern in patterns:
        matches.extend(pattern.finditer(text))
    return matches

__all__ = [
    "PATIENT_ID_PATTERNS",
    "DATE_PATTERNS",
    "LAB_NAME_PATTERNS",
    "LAB_TEST_PATTERNS",
    "IMPRESSION_PATTERNS",
    "extract_with_pattern",
    "find_all_matches",
]
"""

# Write the file
target_file = PROJECT_ROOT / "backend" / "parser" / "patterns.py"

print(f"Creating {target_file}...")

with open(target_file, 'w', encoding='utf-8', newline='\n') as f:
    f.write(file_content)

print(f"✅ File created successfully!")
print(f"\nVerifying...")

# Verify it can be imported
try:
    sys.path.insert(0, str(PROJECT_ROOT))
    from backend.parser.patterns import LAB_TEST_PATTERNS
    
    print(f"✅ Import successful!")
    print(f"✅ Found {len(LAB_TEST_PATTERNS)} test patterns")
    
    # Test a sample line
    test_line = "Hemoglobin: 11.2 g/dL (13.0-17.0) [L]"
    for i, pattern in enumerate(LAB_TEST_PATTERNS, 1):
        match = pattern.search(test_line)
        if match:
            print(f"✅ Pattern {i} matched test line!")
            print(f"   Groups: {match.groups()}")
            break
    else:
        print(f"⚠️  Warning: No pattern matched test line")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()