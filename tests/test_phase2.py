# tests/test_phase2.py
"""Test Phase 2: Ingestion, Parsing, Audit"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_document_ingestion():
    """Test document processing"""
    from backend.ingestion.document_processor import DocumentProcessor
    
    processor = DocumentProcessor()
    
    # Test with synthetic report
    report_path = Path("data/synthetic_reports/01_normal_cbc.txt")
    
    if not report_path.exists():
        print(f"⚠️  Synthetic report not found: {report_path}")
        print("   Run: python scripts/generate_synthetic_data.py first")
        return False
    
    with open(report_path, 'rb') as f:
        content = f.read()
    
    text, metadata = processor.process(report_path.name, content)
    
    assert len(text) > 100
    assert metadata.extraction_method == "text"
    
    print("✅ Document ingestion works")
    print(f"   Extracted {len(text)} characters")
    print(f"   Method: {metadata.extraction_method}")
    print(f"   Time: {metadata.extraction_time_seconds}s")
    return True


def test_parser():
    """Test medical report parsing"""
    from backend.parser.medical_parser import MedicalReportParser
    from backend.ingestion.document_processor import DocumentProcessor
    
    # Load a synthetic report
    report_path = Path("data/synthetic_reports/02_mild_anemia.txt")
    
    if not report_path.exists():
        print("⚠️  Create synthetic reports first")
        print("   Run: python scripts/generate_synthetic_data.py")
        return False
    
    # Extract text
    processor = DocumentProcessor()
    with open(report_path, 'rb') as f:
        text, _ = processor.process(report_path.name, f.read())
    
    # Parse
    parser = MedicalReportParser()
    report = parser.parse(text)
    
    assert report.patient_id is not None
    assert len(report.tests) > 0
    
    print("✅ Medical report parser works")
    print(f"\n{report.summary()}")
    
    # Show parsed tests
    print("\nParsed Tests:")
    for test in report.tests[:5]:  # Show first 5
        status = "🔴 ABNORMAL" if test.is_abnormal else "✅ Normal"
        print(f"  {status} {test.name}: {test.value} {test.unit} (Ref: {test.reference_range})")
    
    return True


def test_audit_logging():
    """Test audit logging"""
    from backend.audit.audit_logger import AuditLogger
    from backend.audit.database import init_db, get_db_session
    from backend.audit.models import AuditLog
    
    # Initialize database
    init_db()
    
    # Create logger
    audit = AuditLogger()
    
    # Log some events
    audit.log_upload("test.pdf", "abc123", 1024)
    audit.log_parse(10, 2)
    audit.log_alert("HIGH", "Glucose", "185")
    
    # Verify logs were created
    with get_db_session() as db:
        count = db.query(AuditLog).filter_by(session_id=audit.session_id).count()
        assert count == 3
    
    print("✅ Audit logging works")
    print(f"   Session ID: {audit.session_id}")
    print(f"   Events logged: {count}")
    
    # Show recent logs
    with get_db_session() as db:
        recent_logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(3).all()
        print("\n   Recent logs:")
        for log in recent_logs:
            print(f"   - {log.event_type} at {log.created_at}")
    
    return True


def test_full_pipeline():
    """Test complete pipeline: upload → extract → parse → audit"""
    from backend.ingestion.document_processor import DocumentProcessor
    from backend.parser.medical_parser import MedicalReportParser
    from backend.audit.audit_logger import AuditLogger
    from backend.ingestion.validators import FileValidator
    
    print("\n" + "="*60)
    print("FULL PIPELINE TEST")
    print("="*60)
    
    # Use critical potassium report
    report_path = Path("data/synthetic_reports/03_critical_potassium.txt")
    
    if not report_path.exists():
        print("⚠️  Synthetic reports not found")
        return False
    
    # Step 1: Validate
    validator = FileValidator()
    with open(report_path, 'rb') as f:
        content = f.read()
    
    is_valid, error = validator.validate(report_path.name, content)
    file_hash = validator.get_file_hash(content)
    
    print(f"\n1. Validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    print(f"   File hash: {file_hash[:16]}...")
    
    # Step 2: Extract
    processor = DocumentProcessor()
    text, metadata = processor.process(report_path.name, content)
    
    print(f"\n2. Extraction: ✅ COMPLETE")
    print(f"   Method: {metadata.extraction_method}")
    print(f"   Characters: {len(text)}")
    
    # Step 3: Parse
    parser = MedicalReportParser()
    report = parser.parse(text)
    
    print(f"\n3. Parsing: ✅ COMPLETE")
    print(f"   Tests found: {len(report.tests)}")
    print(f"   Abnormal: {len(report.get_abnormal_tests())}")
    print(f"   Critical: {len(report.get_critical_tests())}")
    
    # Step 4: Audit
    audit = AuditLogger()
    audit.log_upload(report_path.name, file_hash, len(content))
    audit.log_extraction(metadata.extraction_method, len(text), metadata.extraction_time_seconds)
    audit.log_parse(len(report.tests), len(report.get_abnormal_tests()))
    
    print(f"\n4. Audit Logging: ✅ COMPLETE")
    print(f"   Session ID: {audit.session_id}")
    
    # Show critical tests
    if report.get_critical_tests():
        print("\n⚠️  CRITICAL VALUES DETECTED:")
        for test in report.get_critical_tests():
            print(f"   🚨 {test.name}: {test.value} {test.unit}")
    
    return True


if __name__ == "__main__":
    from config.logging_config import setup_logging
    setup_logging()
    
    print("="*60)
    print("TESTING PHASE 2: INGESTION, PARSING, AUDIT")
    print("="*60)
    print()
    
    success = True
    
    success &= test_document_ingestion()
    print()
    
    success &= test_parser()
    print()
    
    success &= test_audit_logging()
    print()
    
    success &= test_full_pipeline()
    print()
    
    if success:
        print("="*60)
        print("✅ ALL PHASE 2 TESTS PASSED!")
        print("="*60)
        print("\nNext steps:")
        print("  1. Review the parsed data above")
        print("  2. Check audit.db for logged events")
        print("  3. Ready for Phase 3 (RAG + LLM)!")
    else:
        print("="*60)
        print("❌ SOME TESTS FAILED")
        print("="*60)