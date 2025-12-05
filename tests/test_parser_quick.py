# tests/test_parser_quick.py
"""Quick test for parser fixes"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.parser.medical_parser import MedicalReportParser
from config.logging_config import setup_logging

setup_logging()

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

parser = MedicalReportParser()
report = parser.parse(test_text)

print(f"\n{'='*60}")
print(f"PARSER TEST RESULTS")
print(f"{'='*60}")
print(f"\nPatient ID: {report.patient_id}")
print(f"Date: {report.report_date}")
print(f"Report Type: {report.report_type.value}")
print(f"Lab: {report.lab_name}")
print(f"\nTests Found: {len(report.tests)}")

for test in report.tests:
    flag = f" [{test.flag}]" if test.flag else ""
    status = "🔴 ABNORMAL" if test.is_abnormal else "✅ Normal"
    print(f"  {status} {test.name}: {test.value} {test.unit} (Ref: {test.reference_range}){flag}")

print(f"\nImpression: {report.impression[:100]}...")

if len(report.tests) > 0:
    print(f"\n{'='*60}")
    print(f"✅ PARSER TEST PASSED!")
    print(f"{'='*60}")
else:
    print(f"\n{'='*60}")
    print(f"❌ PARSER TEST FAILED - No tests extracted")
    print(f"{'='*60}")