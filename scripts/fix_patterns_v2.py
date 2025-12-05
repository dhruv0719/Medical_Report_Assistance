"""Generate patterns.py file - line by line approach"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
target_file = PROJECT_ROOT / "backend" / "parser" / "patterns.py"

print(f"Creating {target_file}...")

# Write line by line to avoid escaping issues
lines = [
    "# backend/parser/patterns.py",
    '"""Regex patterns for extracting structured data from medical reports."""',
    "",
    "import re",
    "from typing import List, Pattern",
    "",
    "# Patient ID patterns",
    "PATIENT_ID_PATTERNS: List[Pattern] = [",
    "    re.compile(r'Patient\\s+ID[:\\s]+([A-Z0-9-]+)', re.IGNORECASE),",
    "    re.compile(r'MRN[:\\s]+([A-Z0-9-]+)', re.IGNORECASE),",
    "]",
    "",
    "# Date patterns",
    "DATE_PATTERNS: List[Pattern] = [",
    "    re.compile(r'Date\\s+of\\s+Collection[:\\s]+([\\d\\-/]+)', re.IGNORECASE),",
    "    re.compile(r'Collection\\s+Date[:\\s]+([\\d\\-/]+)', re.IGNORECASE),",
    "]",
    "",
    "# Lab name patterns",
    "LAB_NAME_PATTERNS: List[Pattern] = [",
    "    re.compile(r'Performing\\s+Lab[:\\s]+(.+?)(?:\\n|$)', re.IGNORECASE),",
    "]",
    "",
    "# Impression patterns",
    "IMPRESSION_PATTERNS: List[Pattern] = [",
    "    re.compile(r'IMPRESSION[:\\s]+(.*?)(?=\\n\\n|\\nPerforming|\\Z)', re.IGNORECASE | re.DOTALL),",
    "    re.compile(r'CONCLUSION[:\\s]+(.*?)(?=\\n\\n|\\nPerforming|\\Z)', re.IGNORECASE | re.DOTALL),",
    "]",
    "",
    "# Lab test pattern 1: Test Name: Value Unit (Range) [Flag]",
    "LAB_TEST_PATTERN_1 = re.compile(",
    "    r'^([A-Z][A-Za-z\\s]+?):\\s*([\\d.]+)\\s+([^\\s(]+)\\s*\KATEX_INLINE_OPEN([\\d.\\s\\-]+)\KATEX_INLINE_CLOSE(?:\\s*\```math
([HLhl]+)\```)?\\s*$',",
    "    re.MULTILINE",
    ")",
    "",
    "# Lab test pattern 2: Test Name Value (Range) Unit [Flag]",
    "LAB_TEST_PATTERN_2 = re.compile(",
    "    r'^([A-Z][A-Za-z\\s]+?)\\s+([\\d.]+)\\s+\KATEX_INLINE_OPEN([\\d.\\s\\-]+)\KATEX_INLINE_CLOSE\\s+([^\\s\```math
]+)(?:\\s*\```math
([HLhl]+)\```)?\\s*$',",
    "    re.MULTILINE",
    ")",
    "",
    "LAB_TEST_PATTERNS: List[Pattern] = [",
    "    LAB_TEST_PATTERN_1,",
    "    LAB_TEST_PATTERN_2,",
    "]",
    "",
    "def extract_with_pattern(text: str, patterns: List[Pattern]) -> str:",
    '    """Try multiple patterns and return first match."""',
    "    for pattern in patterns:",
    "        match = pattern.search(text)",
    "        if match:",
    "            return match.group(1).strip()",
    '    return ""',
    "",
    "def find_all_matches(text: str, patterns: List[Pattern]) -> list:",
    '    """Find all matches across multiple patterns."""',
    "    matches = []",
    "    for pattern in patterns:",
    "        matches.extend(pattern.finditer(text))",
    "    return matches",
    "",
    "__all__ = [",
    '    "PATIENT_ID_PATTERNS",',
    '    "DATE_PATTERNS",',
    '    "LAB_NAME_PATTERNS",',
    '    "LAB_TEST_PATTERNS",',
    '    "IMPRESSION_PATTERNS",',
    '    "extract_with_pattern",',
    '    "find_all_matches",',
    "]",
]

# Write the file
with open(target_file, 'w', encoding='utf-8', newline='\n') as f:
    f.write('\n'.join(lines))

print(f"✅ File created with {len(lines)} lines")
print(f"\nVerifying...")

# Verify
try:
    # Clear any cached imports
    if 'backend.parser.patterns' in sys.modules:
        del sys.modules['backend.parser.patterns']
    
    sys.path.insert(0, str(PROJECT_ROOT))
    from backend.parser.patterns import LAB_TEST_PATTERNS
    
    print(f"✅ Import successful!")
    print(f"✅ Found {len(LAB_TEST_PATTERNS)} test patterns")
    
    # Test
    test_line = "Hemoglobin: 11.2 g/dL (13.0-17.0) [L]"
    matched = False
    for i, pattern in enumerate(LAB_TEST_PATTERNS, 1):
        match = pattern.search(test_line)
        if match:
            print(f"✅ Pattern {i} matched!")
            print(f"   Groups: {match.groups()}")
            matched = True
            break
    
    if not matched:
        print(f"⚠️  No pattern matched test line")
        print(f"   Testing with multiline...")
        test_multiline = f"\n{test_line}\n"
        for i, pattern in enumerate(LAB_TEST_PATTERNS, 1):
            match = pattern.search(test_multiline)
            if match:
                print(f"✅ Pattern {i} matched with multiline!")
                print(f"   Groups: {match.groups()}")
                break
        
except SyntaxError as e:
    print(f"❌ SYNTAX ERROR: {e}")
    print(f"\nThe generated file has a syntax error.")
    print(f"Opening file to check...")
    with open(target_file, 'r') as f:
        lines_read = f.readlines()
        for i, line in enumerate(lines_read[30:40], 31):
            print(f"{i:3d}: {line.rstrip()}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\n" + "="*60)
print("Next step: python tests/debug_parser.py")