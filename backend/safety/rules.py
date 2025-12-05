# backend/safety/rules.py
"""
Critical value thresholds and safety rules for lab test triage.
Based on clinical laboratory guidelines and standards.

Sources:
- ARUP Consult Critical Values
- CAP (College of American Pathologists) Guidelines
- Clinical Laboratory Standards Institute (CLSI)
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ThresholdRange:
    """
    Represents normal and critical thresholds for a lab test.
    
    Attributes:
        low_critical: Value below which is critically low
        low_normal: Lower bound of normal range
        high_normal: Upper bound of normal range
        high_critical: Value above which is critically high
        unit: Unit of measurement
    """
    low_critical: Optional[float]
    low_normal: float
    high_normal: float
    high_critical: Optional[float]
    unit: str
    
    def classify_value(self, value: float) -> str:
        """
        Classify a value based on thresholds.
        
        Returns:
            'critical_low', 'low', 'normal', 'high', or 'critical_high'
        """
        if self.low_critical is not None and value < self.low_critical:
            return 'critical_low'
        elif value < self.low_normal:
            return 'low'
        elif value > self.high_normal:
            if self.high_critical is not None and value > self.high_critical:
                return 'critical_high'
            return 'high'
        else:
            return 'normal'


# =============================================================================
# CRITICAL VALUE THRESHOLDS (Top 20 Most Common Tests)
# =============================================================================

CRITICAL_THRESHOLDS: Dict[str, ThresholdRange] = {
    # Electrolytes
    "potassium": ThresholdRange(
        low_critical=2.5,
        low_normal=3.5,
        high_normal=5.0,
        high_critical=6.5,
        unit="mEq/L"
    ),
    "sodium": ThresholdRange(
        low_critical=120,
        low_normal=135,
        high_normal=145,
        high_critical=160,
        unit="mEq/L"
    ),
    "calcium": ThresholdRange(
        low_critical=6.0,
        low_normal=8.5,
        high_normal=10.5,
        high_critical=13.0,
        unit="mg/dL"
    ),
    "magnesium": ThresholdRange(
        low_critical=1.0,
        low_normal=1.7,
        high_normal=2.2,
        high_critical=4.0,
        unit="mg/dL"
    ),
    
    # Glucose
    "glucose": ThresholdRange(
        low_critical=40,
        low_normal=70,
        high_normal=100,  # Fasting
        high_critical=500,
        unit="mg/dL"
    ),
    
    # Hematology
    "hemoglobin": ThresholdRange(
        low_critical=7.0,
        low_normal=13.0,  # Male reference
        high_normal=17.0,
        high_critical=20.0,
        unit="g/dL"
    ),
    "hematocrit": ThresholdRange(
        low_critical=20.0,
        low_normal=38.0,
        high_normal=50.0,
        high_critical=60.0,
        unit="%"
    ),
    "wbc": ThresholdRange(
        low_critical=2.0,
        low_normal=4.0,
        high_normal=11.0,
        high_critical=30.0,
        unit="x10³/µL"
    ),
    "platelet": ThresholdRange(
        low_critical=50,
        low_normal=150,
        high_normal=400,
        high_critical=1000,
        unit="x10³/µL"
    ),
    
    # Renal Function
    "creatinine": ThresholdRange(
        low_critical=None,
        low_normal=0.6,
        high_normal=1.2,
        high_critical=5.0,
        unit="mg/dL"
    ),
    "bun": ThresholdRange(
        low_critical=None,
        low_normal=7,
        high_normal=20,
        high_critical=100,
        unit="mg/dL"
    ),
    
    # Liver Function
    "bilirubin_total": ThresholdRange(
        low_critical=None,
        low_normal=0.1,
        high_normal=1.2,
        high_critical=15.0,
        unit="mg/dL"
    ),
    "alt": ThresholdRange(
        low_critical=None,
        low_normal=7,
        high_normal=56,
        high_critical=1000,
        unit="U/L"
    ),
    "ast": ThresholdRange(
        low_critical=None,
        low_normal=10,
        high_normal=40,
        high_critical=1000,
        unit="U/L"
    ),
    
    # Cardiac
    "troponin": ThresholdRange(
        low_critical=None,
        low_normal=0.0,
        high_normal=0.04,
        high_critical=0.4,  # Suggests MI
        unit="ng/mL"
    ),
    
    # Coagulation
    "inr": ThresholdRange(
        low_critical=None,
        low_normal=0.8,
        high_normal=1.2,
        high_critical=5.0,
        unit="ratio"
    ),
    "pt": ThresholdRange(
        low_critical=None,
        low_normal=11.0,
        high_normal=13.5,
        high_critical=50.0,
        unit="seconds"
    ),
    
    # Thyroid
    "tsh": ThresholdRange(
        low_critical=0.01,
        low_normal=0.4,
        high_normal=4.0,
        high_critical=20.0,
        unit="mIU/L"
    ),
    
    # Lipids (not typically critical, but important)
    "cholesterol_total": ThresholdRange(
        low_critical=None,
        low_normal=0,
        high_normal=200,
        high_critical=None,
        unit="mg/dL"
    ),
    "ldl": ThresholdRange(
        low_critical=None,
        low_normal=0,
        high_normal=100,
        high_critical=None,
        unit="mg/dL"
    ),
}


# =============================================================================
# TEST NAME ALIASES (for matching variations)
# =============================================================================

TEST_NAME_ALIASES: Dict[str, str] = {
    # Potassium variations
    "k": "potassium",
    "k+": "potassium",
    "serum potassium": "potassium",
    
    # Sodium variations
    "na": "sodium",
    "na+": "sodium",
    "serum sodium": "sodium",
    
    # Glucose variations
    "glu": "glucose",
    "blood sugar": "glucose",
    "fasting glucose": "glucose",
    "random glucose": "glucose",
    
    # Hemoglobin variations
    "hgb": "hemoglobin",
    "hb": "hemoglobin",
    
    # Hematocrit variations
    "hct": "hematocrit",
    
    # WBC variations
    "white blood cell": "wbc",
    "leukocyte": "wbc",
    "white cell count": "wbc",
    
    # Platelet variations
    "plt": "platelet",
    "platelet count": "platelet",
    
    # Creatinine variations
    "cr": "creatinine",
    "creat": "creatinine",
    "serum creatinine": "creatinine",
    
    # BUN variations
    "blood urea nitrogen": "bun",
    "urea nitrogen": "bun",
    
    # Bilirubin variations
    "total bilirubin": "bilirubin_total",
    "t bili": "bilirubin_total",
    
    # Troponin variations
    "troponin i": "troponin",
    "troponin t": "troponin",
    "cardiac troponin": "troponin",
    
    # TSH variations
    "thyroid stimulating hormone": "tsh",
    "thyrotropin": "tsh",
    
    # Cholesterol variations
    "total cholesterol": "cholesterol_total",
    "chol": "cholesterol_total",
    
    # LDL variations
    "ldl cholesterol": "ldl",
    "low density lipoprotein": "ldl",
}


# =============================================================================
# URGENCY LEVEL DETERMINATION
# =============================================================================

class UrgencyLevel:
    """Urgency levels for triage"""
    CRITICAL = "critical"      # Immediate medical attention required
    HIGH = "high"              # Contact doctor same day
    MODERATE = "moderate"      # Schedule appointment within week
    ROUTINE = "routine"        # Discuss at next regular visit


URGENCY_RULES = {
    'critical_low': UrgencyLevel.CRITICAL,
    'critical_high': UrgencyLevel.CRITICAL,
    'low': UrgencyLevel.MODERATE,
    'high': UrgencyLevel.MODERATE,
    'normal': UrgencyLevel.ROUTINE,
}


# =============================================================================
# CRITICAL VALUE MESSAGES
# =============================================================================

CRITICAL_MESSAGES = {
    "potassium": {
        "critical_low": "Critically low potassium (hypokalemia) can cause dangerous heart rhythm problems. Seek immediate medical attention.",
        "critical_high": "Critically high potassium (hyperkalemia) can cause life-threatening heart rhythm problems. Seek immediate medical attention.",
    },
    "glucose": {
        "critical_low": "Severely low blood sugar (hypoglycemia) requires immediate treatment. If symptomatic, consume fast-acting carbohydrates and seek emergency care.",
        "critical_high": "Extremely high blood sugar may indicate diabetic emergency. Seek immediate medical attention.",
    },
    "hemoglobin": {
        "critical_low": "Severely low hemoglobin indicates severe anemia. This requires urgent medical evaluation.",
        "critical_high": "Critically elevated hemoglobin requires medical evaluation to determine cause.",
    },
    "troponin": {
        "critical_high": "Elevated troponin strongly suggests heart muscle damage. This may indicate a heart attack. Seek emergency care immediately.",
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_test_name(test_name: str) -> str:
    """
    Normalize test name to standard form.
    
    Args:
        test_name: Original test name
        
    Returns:
        Normalized test name
    """
    test_lower = test_name.lower().strip()
    
    # Check if it's an alias
    if test_lower in TEST_NAME_ALIASES:
        return TEST_NAME_ALIASES[test_lower]
    
    # Check if it contains a known test name
    for alias, standard in TEST_NAME_ALIASES.items():
        if alias in test_lower:
            return standard
    
    return test_lower


def get_threshold(test_name: str) -> Optional[ThresholdRange]:
    """
    Get threshold range for a test.
    
    Args:
        test_name: Test name (will be normalized)
        
    Returns:
        ThresholdRange if found, None otherwise
    """
    normalized = normalize_test_name(test_name)
    return CRITICAL_THRESHOLDS.get(normalized)


def get_critical_message(test_name: str, classification: str) -> Optional[str]:
    """
    Get critical value message for a test.
    
    Args:
        test_name: Test name
        classification: Value classification
        
    Returns:
        Message string if available
    """
    normalized = normalize_test_name(test_name)
    test_messages = CRITICAL_MESSAGES.get(normalized, {})
    return test_messages.get(classification)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "ThresholdRange",
    "CRITICAL_THRESHOLDS",
    "TEST_NAME_ALIASES",
    "UrgencyLevel",
    "URGENCY_RULES",
    "CRITICAL_MESSAGES",
    "normalize_test_name",
    "get_threshold",
    "get_critical_message",
]