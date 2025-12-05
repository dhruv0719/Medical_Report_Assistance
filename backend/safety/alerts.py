# backend/safety/alerts.py
"""
Data classes and utilities for safety alerts and triage.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AlertLevel(Enum):
    """Severity levels for alerts"""
    INFO = "info"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Categories of alerts"""
    VALUE_CRITICAL = "value_critical"        # Critical lab value
    VALUE_ABNORMAL = "value_abnormal"        # Abnormal but not critical
    PATTERN_CONCERN = "pattern_concern"      # Pattern of abnormalities
    FOLLOW_UP_NEEDED = "follow_up_needed"    # Needs follow-up testing
    INFORMATION = "information"              # General information


@dataclass
class Alert:
    """
    Represents a safety alert generated from lab results.
    
    Attributes:
        level: Severity level
        category: Type of alert
        test_name: Name of the test that triggered alert
        value: The concerning value
        unit: Unit of measurement
        threshold: Normal/critical threshold
        message: Human-readable message
        action_required: Recommended action
        urgency: How quickly to act
        timestamp: When alert was generated
    """
    level: AlertLevel
    category: AlertCategory
    test_name: str
    value: str
    unit: str
    threshold: str
    message: str
    action_required: str
    urgency: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['level'] = self.level.value
        data['category'] = self.category.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    def is_critical(self) -> bool:
        """Check if this is a critical alert"""
        return self.level == AlertLevel.CRITICAL
    
    def requires_immediate_action(self) -> bool:
        """Check if immediate action is required"""
        return self.urgency.lower() in ['immediate', 'emergency', 'critical']


@dataclass
class TriageResult:
    """
    Complete triage result for a report.
    
    Attributes:
        overall_urgency: Highest urgency level found
        alerts: List of all alerts
        critical_count: Number of critical alerts
        high_count: Number of high-priority alerts
        recommendation: Overall recommendation
        next_steps: List of recommended actions
    """
    overall_urgency: str
    alerts: List[Alert] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    moderate_count: int = 0
    recommendation: str = ""
    next_steps: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Calculate counts after initialization"""
        self.critical_count = sum(1 for a in self.alerts if a.level == AlertLevel.CRITICAL)
        self.high_count = sum(1 for a in self.alerts if a.level == AlertLevel.HIGH)
        self.moderate_count = sum(1 for a in self.alerts if a.level == AlertLevel.MODERATE)
        
        # Set overall recommendation
        if self.critical_count > 0:
            self.overall_urgency = "CRITICAL"
            self.recommendation = "Seek immediate medical attention or call emergency services."
        elif self.high_count > 0:
            self.overall_urgency = "HIGH"
            self.recommendation = "Contact your healthcare provider today."
        elif self.moderate_count > 0:
            self.overall_urgency = "MODERATE"
            self.recommendation = "Schedule an appointment with your healthcare provider within the week."
        else:
            self.overall_urgency = "ROUTINE"
            self.recommendation = "Discuss results at your next regular appointment."
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'overall_urgency': self.overall_urgency,
            'alerts': [alert.to_dict() for alert in self.alerts],
            'critical_count': self.critical_count,
            'high_count': self.high_count,
            'moderate_count': self.moderate_count,
            'recommendation': self.recommendation,
            'next_steps': self.next_steps,
            'timestamp': self.timestamp.isoformat(),
        }
    
    def has_critical_alerts(self) -> bool:
        """Check if there are any critical alerts"""
        return self.critical_count > 0
    
    def get_critical_alerts(self) -> List[Alert]:
        """Get all critical alerts"""
        return [a for a in self.alerts if a.level == AlertLevel.CRITICAL]
    
    def summary(self) -> str:
        """Generate a text summary"""
        return (
            f"Urgency: {self.overall_urgency}\n"
            f"Critical Alerts: {self.critical_count}\n"
            f"High Priority: {self.high_count}\n"
            f"Moderate: {self.moderate_count}\n"
            f"Recommendation: {self.recommendation}"
        )


# =============================================================================
# ALERT FACTORY FUNCTIONS
# =============================================================================

def create_critical_alert(
    test_name: str,
    value: str,
    unit: str,
    threshold: str,
    message: str
) -> Alert:
    """Create a critical value alert"""
    return Alert(
        level=AlertLevel.CRITICAL,
        category=AlertCategory.VALUE_CRITICAL,
        test_name=test_name,
        value=value,
        unit=unit,
        threshold=threshold,
        message=message,
        action_required="Seek immediate medical attention",
        urgency="IMMEDIATE"
    )


def create_abnormal_alert(
    test_name: str,
    value: str,
    unit: str,
    threshold: str,
    is_high: bool
) -> Alert:
    """Create an abnormal (non-critical) value alert"""
    direction = "above" if is_high else "below"
    return Alert(
        level=AlertLevel.MODERATE,
        category=AlertCategory.VALUE_ABNORMAL,
        test_name=test_name,
        value=value,
        unit=unit,
        threshold=threshold,
        message=f"{test_name} is {direction} the normal range",
        action_required="Discuss with your healthcare provider",
        urgency="MODERATE"
    )


def create_pattern_alert(
    test_names: List[str],
    pattern_description: str,
    recommendation: str
) -> Alert:
    """Create an alert for a concerning pattern of results"""
    return Alert(
        level=AlertLevel.HIGH,
        category=AlertCategory.PATTERN_CONCERN,
        test_name=", ".join(test_names),
        value="Multiple abnormalities",
        unit="",
        threshold="",
        message=pattern_description,
        action_required=recommendation,
        urgency="HIGH"
    )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "Alert",
    "AlertLevel",
    "AlertCategory",
    "TriageResult",
    "create_critical_alert",
    "create_abnormal_alert",
    "create_pattern_alert",
]