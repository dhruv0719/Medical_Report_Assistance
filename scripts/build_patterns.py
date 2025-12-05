"""Build patterns.py using character codes to avoid corruption"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
target_file = PROJECT_ROOT / "backend" / "parser" / "patterns.py"

# Build the regex strings character by character
# Pattern 1: Test Name: Value Unit (Range) [Flag]
# We need to include literal ( and ) and [ and ]

# Start with the base pattern parts
parts1 = [
    "r'^([A-Z][A-Za-z",
    chr(92), "s]+?):",  # \s
    chr(92), "s*([",    # \s
    chr(92), "d.]+)",   # \d
    chr(92), "s+([^",   # \s
    chr(92), "s(]+)",   # \s
    chr(92), "s*",      # \s
    chr(92), "(",       # Literal (
    "([",
    chr(92), "d.",      # \d
    chr(92), "s",       # \s
    chr(92), "-]+)",    # \-
    chr(92), ")",       # Literal )
    "(?:",
    chr(92), "s*",      # \s
    chr(92), "[([HLhl]+)", # ```math

    chr(92), "])?",     # ```
    chr(92), "s*$'"     # \s
]
pattern1_str = ''.join(parts1)

# Pattern 2: Test Name Value (Range) Unit [Flag]
parts2 = [
    "r'^([A-Z][A-Za-z",
    chr(92), "s]+?)",   # \s
    chr(92), "s+([",    # \s
    chr(92), "d.]+)",   # \d
    chr(92), "s+",      # \s
    chr(92), "(",       # Literal (
    "([",
    chr(92), "d.",      # \d
    chr(92), "s",       # \s
    chr(92), "-]+)",    # \-
    chr(92), ")",       # Literal )
    chr(92), "s+([^",   # \s
    chr(92), "s",       # \s
    chr(92), "[]+)(?:", # ```math

    chr(92), "s*",      # \s
    chr(92), "[([HLhl]+)", # ```math

    chr(92), "])?",     # ```
    chr(92), "s*$'"     # \s
]
pattern2_str = ''.join(parts2)

print(f"Pattern 1: {pattern1_str}")
print(f"Pattern 2: {pattern2_str}")
print()

# Now build the full file content
lines = [
    "# backend/parser/patterns.py",
    '"""Regex patterns for extracting structured data."""',
    "",
    "import re",
    "from typing import List, Pattern",
    "",
    "PATIENT_ID_PATTERNS: List[Pattern] = [",
    "    re.compile(r'Patient" + chr(92) + "s+ID[:" + chr(92) + "s]+([A-Z0-9-]+)', re.IGNORECASE),",
    "    re.compile(r'MRN[:" + chr(92) + "s]+([A-Z0-9-]+)', re.IGNORECASE),",
    "]",
    "",
    "DATE_PATTERNS: List[Pattern] = [",
    "    re.compile(r'Date" + chr(92) + "s+of" + chr(92) + "s+Collection[:" + chr(92) + "s]+([" + chr(92) + "d" + chr(92) + "-/]+)', re.IGNORECASE),",
    "    re.compile(r'Collection" + chr(92) + "s+Date[:" + chr(92) + "s]+([" + chr(92) + "d" + chr(92) + "-/]+)', re.IGNORECASE),",
    "]",
    "",
    "LAB_NAME_PATTERNS: List[Pattern] = [",
    "    re.compile(r'Performing" + chr(92) + "s+Lab[:" + chr(92) + "s]+(.+?)(?:" + chr(92) + "n|$)', re.IGNORECASE),",
    "]",
    "",
    "IMPRESSION_PATTERNS: List[Pattern] = [",
    "    re.compile(r'IMPRESSION[:" + chr(92) + "s]+(.*?)(?=" + chr(92) + "n" + chr(92) + "n|" + chr(92) + "nPerforming|" + chr(92) + "Z)', re.IGNORECASE | re.DOTALL),",
    "    re.compile(r'CONCLUSION[:" + chr(92) + "s]+(.*?)(?=" + chr(92) + "n" + chr(92) + "n|" + chr(92) + "nPerforming|" + chr(92) + "Z)', re.IGNORECASE | re.DOTALL),",
    "]",
    "",
    "LAB_TEST_PATTERN_1 = re.compile(",
    "    " + pattern1_str + ",",
    "    re.MULTILINE",
    ")",
    "",
    "LAB_TEST_PATTERN_2 = re.compile(",
    "    " + pattern2_str + ",",
    "    re.MULTILINE",
    ")",
    "",
    "LAB_TEST_PATTERNS: List[Pattern] = [LAB_TEST_PATTERN_1, LAB_TEST_PATTERN_2]",
    "",
    "def extract_with_pattern(text: str, patterns: List[Pattern]) -> str:",
    "    for pattern in patterns:",
    "        match = pattern.search(text)",
    "        if match:",
    "            return match.group(1).strip()",
    "    return ''",
    "",
    "def find_all_matches(text: str, patterns: List[Pattern]) -> list:",
    "    matches = []",
    "    for pattern in patterns:",
    "        matches.extend(pattern.finditer(text))",
    "    return matches",
    "",
    "__all__ = ['PATIENT_ID_PATTERNS', 'DATE_PATTERNS', 'LAB_NAME_PATTERNS', 'LAB_TEST_PATTERNS', 'IMPRESSION_PATTERNS', 'extract_with_pattern', 'find_all_matches']",
]

# Write file
with open(target_file, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))

print(f"✅ Created {target_file}")

# Verify
try:
    if 'backend.parser.patterns' in sys.modules:
        del sys.modules['backend.parser.patterns']
    
    sys.path.insert(0, str(PROJECT_ROOT))
    from backend.parser.patterns import LAB_TEST_PATTERNS
    
    print(f"✅ Import successful! Found {len(LAB_TEST_PATTERNS)} patterns")
    
    test_line = "Hemoglobin: 11.2 g/dL (13.0-17.0) [L]"
    for i, pattern in enumerate(LAB_TEST_PATTERNS, 1):
        match = pattern.search(test_line)
        if match:
            print(f"✅ Pattern {i} matched: {match.groups()}")
            break
    else:
        print(f"⚠️ No pattern matched")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()