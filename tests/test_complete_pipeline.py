# tests/test_complete_pipeline.py
"""Test complete end-to-end pipeline"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.orchestrator.pipeline import MedicalReportPipeline
from config.logging_config import setup_logging

setup_logging()


def test_complete_pipeline():
    """Test the complete pipeline with a real report"""
    print("\n" + "="*60)
    print("COMPLETE PIPELINE TEST")
    print("="*60)
    
    # Initialize pipeline
    pipeline = MedicalReportPipeline(
        enable_llm=True,
        enable_audit=True
    )
    
    # Process a test report
    report_path = Path("data/synthetic_reports/02_mild_anemia.txt")
    
    if not report_path.exists():
        print(f"❌ Test report not found: {report_path}")
        return
    
    # Run complete pipeline
    result = pipeline.process_file(report_path)
    
    # Display results
    print("\n" + "="*60)
    print("PIPELINE RESULTS")
    print("="*60)
    
    print(f"\n📄 File: {result.filename}")
    print(f"⏱️  Processing time: {result.processing_time:.2f}s")
    print(f"🔐 Session ID: {result.session_id}")
    
    print(f"\n📊 Parsed Report:")
    print(f"   Patient ID: {result.parsed_report.patient_id}")
    print(f"   Report Date: {result.parsed_report.report_date}")
    print(f"   Report Type: {result.parsed_report.report_type.value}")
    print(f"   Lab: {result.parsed_report.lab_name}")
    
    print(f"\n🔬 Test Results ({len(result.parsed_report.tests)} total):")
    for test in result.parsed_report.tests[:5]:
        status = "🔴 ABNORMAL" if test.is_abnormal else "✅ Normal"
        flag = f" [{test.flag}]" if test.flag else ""
        print(f"   {status} {test.name}: {test.value} {test.unit}{flag}")
        print(f"      Normal range: {test.reference_range}")
    
    print(f"\n⚠️  Triage Assessment:")
    print(f"   Overall Urgency: {result.triage_result.overall_urgency}")
    print(f"   Critical Alerts: {result.triage_result.critical_count}")
    print(f"   High Priority: {result.triage_result.high_count}")
    print(f"   Moderate: {result.triage_result.moderate_count}")
    print(f"\n   Recommendation: {result.triage_result.recommendation}")
    
    print(f"\n📝 Next Steps:")
    for step in result.triage_result.next_steps[:5]:
        print(f"   {step}")
    
    print(f"\n💬 LLM Explanations ({len(result.explanations)} generated):")
    for test_name, explanation in list(result.explanations.items())[:2]:
        print(f"\n   --- {test_name} ---")
        print(f"   Sources: {', '.join(explanation.sources_used) if explanation.sources_used else 'General knowledge'}")
        print(f"   Explanation preview:")
        print(f"   {explanation.explanation_text[:300]}...")
    
    print("\n" + "="*60)
    print("✅ COMPLETE PIPELINE TEST PASSED!")
    print("="*60)


if __name__ == "__main__":
    from config.logging_config import setup_logging
    setup_logging()
    
    test_complete_pipeline()