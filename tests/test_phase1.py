# tests/test_phase1.py
"""Test Phase 1: Foundation components"""

# When running this test file directly (python tests/test_phase1.py) the
# interpreter sets sys.path[0] to the tests/ folder which prevents imports
# like `config.settings` from resolving. Insert the repository root into
# sys.path so package-style imports work both when running the file
# directly and when running tests from the project root.
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

def test_config_imports():
    """Test that all config files can be imported"""
    from config.settings import settings, Paths, ModelConfig
    from config.prompts import SystemPrompts, UserPromptTemplates
    from config.logging_config import setup_logging, get_logger
    
    print("✅ All config modules imported successfully")
    assert settings.ENVIRONMENT in ['development', 'production']
    assert Paths.BASE.exists()
    print(f"✅ Environment: {settings.ENVIRONMENT}")
    print(f"✅ Base path: {Paths.BASE}")


def test_entities():
    """Test entity creation"""
    from backend.parser.entities import LabTest, ParsedReport, create_lab_test
    
    # Create a test
    test = create_lab_test(
        name="Hemoglobin",
        value="11.5",
        unit="g/dL",
        reference_range="13.0-17.0",
        flag="L"
    )
    
    assert test.name == "Hemoglobin"
    assert test.is_abnormal == True
    print("✅ LabTest created successfully")
    print(f"   {test.name}: {test.value} {test.unit} (Normal: {test.reference_range})")
    
    # Create a report
    report = ParsedReport(
        patient_id="TEST001",
        report_date="2024-01-01",
        tests=[test]
    )
    
    assert len(report.tests) == 1
    assert len(report.get_abnormal_tests()) == 1
    print("✅ ParsedReport created successfully")
    print(f"\n{report.summary()}")


def test_safety_rules():
    """Test safety rules"""
    from backend.safety.rules import (
        get_threshold,
        normalize_test_name,
        CRITICAL_THRESHOLDS
    )
    
    # Test normalization
    assert normalize_test_name("K+") == "potassium"
    assert normalize_test_name("Hgb") == "hemoglobin"
    print("✅ Test name normalization works")
    
    # Test thresholds
    k_threshold = get_threshold("potassium")
    assert k_threshold is not None
    assert k_threshold.unit == "mEq/L"
    print(f"✅ Potassium threshold: {k_threshold.low_normal}-{k_threshold.high_normal} {k_threshold.unit}")
    
    print(f"✅ Total critical thresholds defined: {len(CRITICAL_THRESHOLDS)}")


def test_alerts():
    """Test alert creation"""
    from backend.safety.alerts import (
        create_critical_alert,
        create_abnormal_alert,
        TriageResult,
        AlertLevel
    )
    
    # Create critical alert
    alert = create_critical_alert(
        test_name="Potassium",
        value="7.2",
        unit="mEq/L",
        threshold="3.5-5.0",
        message="Critically high potassium"
    )
    
    assert alert.level == AlertLevel.CRITICAL
    assert alert.is_critical()
    print("✅ Critical alert created")
    print(f"   {alert.test_name}: {alert.value} {alert.unit}")
    print(f"   Message: {alert.message}")
    
    # Create triage result
    triage = TriageResult(
        overall_urgency="CRITICAL",
        alerts=[alert]
    )
    
    assert triage.critical_count == 1
    assert triage.has_critical_alerts()
    print("✅ Triage result created")
    print(f"\n{triage.summary()}")


def test_logging():
    """Test logging setup"""
    from config.logging_config import setup_logging, get_logger
    
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Test log message")
    logger.warning("Test warning")
    
    print("✅ Logging configured (check logs/ directory)")


if __name__ == "__main__":
    print("="*60)
    print("TESTING PHASE 1: FOUNDATION")
    print("="*60)
    
    test_config_imports()
    print()
    
    test_entities()
    print()
    
    test_safety_rules()
    print()
    
    test_alerts()
    print()
    
    test_logging()
    print()
    
    print("="*60)
    print("✅ ALL PHASE 1 TESTS PASSED!")
    print("="*60)