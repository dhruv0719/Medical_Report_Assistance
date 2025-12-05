# backend/safety/triage_engine.py
"""
Safety triage engine that evaluates lab results for urgency.
Uses the critical value rules from Phase 1.
"""

from typing import List, Dict
from backend.parser.entities import LabTest, ParsedReport
from backend.safety.rules import get_threshold, URGENCY_RULES, get_critical_message
from backend.safety.alerts import Alert, AlertLevel, AlertCategory, TriageResult, create_critical_alert, create_abnormal_alert
from config.logging_config import get_logger

logger = get_logger(__name__)


class TriageEngine:
    """Evaluates medical urgency based on lab test results"""
    
    def __init__(self):
        """Initialize triage engine"""
        logger.info("✅ Triage engine initialized")
    
    def evaluate_test(self, test: LabTest) -> Alert:
        """
        Evaluate a single lab test for urgency.
        
        Args:
            test: Lab test to evaluate
            
        Returns:
            Alert object with urgency classification
        """
        # Get threshold for this test
        threshold = get_threshold(test.name)
        
        if not threshold:
            # No threshold defined for this test - just check if abnormal
            if test.is_abnormal:
                return create_abnormal_alert(
                    test_name=test.name,
                    value=test.value,
                    unit=test.unit,
                    threshold=test.reference_range,
                    is_high=test.flag in ['H', 'HH'] if test.flag else True
                )
            else:
                return Alert(
                    level=AlertLevel.INFO,
                    category=AlertCategory.INFORMATION,
                    test_name=test.name,
                    value=test.value,
                    unit=test.unit,
                    threshold=test.reference_range,
                    message=f"{test.name} is within normal range",
                    action_required="No action needed",
                    urgency="ROUTINE"
                )
        
        # Get numeric value
        numeric_value = test.get_numeric_value()
        if numeric_value is None:
            logger.warning(f"Could not get numeric value for {test.name}: {test.value}")
            return Alert(
                level=AlertLevel.INFO,
                category=AlertCategory.INFORMATION,
                test_name=test.name,
                value=test.value,
                unit=test.unit,
                threshold=test.reference_range,
                message=f"{test.name} result recorded",
                action_required="Discuss with healthcare provider",
                urgency="ROUTINE"
            )
        
        # Classify the value
        classification = threshold.classify_value(numeric_value)
        
        # Create appropriate alert
        if classification in ['critical_low', 'critical_high']:
            # Critical value
            critical_message = get_critical_message(test.name, classification)
            if not critical_message:
                critical_message = f"Critical {test.name} value detected"
            
            return create_critical_alert(
                test_name=test.name,
                value=test.value,
                unit=test.unit,
                threshold=f"{threshold.low_normal}-{threshold.high_normal}",
                message=critical_message
            )
        
        elif classification in ['low', 'high']:
            # Abnormal but not critical
            return create_abnormal_alert(
                test_name=test.name,
                value=test.value,
                unit=test.unit,
                threshold=f"{threshold.low_normal}-{threshold.high_normal}",
                is_high=(classification == 'high')
            )
        
        else:
            # Normal
            return Alert(
                level=AlertLevel.INFO,
                category=AlertCategory.INFORMATION,
                test_name=test.name,
                value=test.value,
                unit=test.unit,
                threshold=f"{threshold.low_normal}-{threshold.high_normal}",
                message=f"{test.name} is within normal range",
                action_required="No action needed",
                urgency="ROUTINE"
            )
    
    def evaluate_report(self, report: ParsedReport) -> TriageResult:
        """
        Evaluate complete report and generate triage result.
        
        Args:
            report: Parsed medical report
            
        Returns:
            TriageResult with all alerts and recommendations
        """
        logger.info(f"Triaging report with {len(report.tests)} tests...")
        
        # Evaluate each test
        alerts = []
        for test in report.tests:
            alert = self.evaluate_test(test)
            alerts.append(alert)
        
        # Generate next steps
        next_steps = self._generate_next_steps(alerts)
        
        # Create triage result (it calculates overall urgency automatically)
        triage = TriageResult(
            overall_urgency="",  # Will be set by __post_init__
            alerts=alerts,
            next_steps=next_steps
        )
        
        logger.info(f"Triage complete: {triage.overall_urgency} urgency, {triage.critical_count} critical")
        
        return triage
    
    def _generate_next_steps(self, alerts: List[Alert]) -> List[str]:
        """
        Generate recommended next steps based on alerts.
        
        Args:
            alerts: List of alerts
            
        Returns:
            List of next step recommendations
        """
        next_steps = []
        
        # Count alert levels
        critical_count = sum(1 for a in alerts if a.level == AlertLevel.CRITICAL)
        high_count = sum(1 for a in alerts if a.level == AlertLevel.HIGH)
        moderate_count = sum(1 for a in alerts if a.level == AlertLevel.MODERATE)
        
        if critical_count > 0:
            next_steps.append("🚨 URGENT: Seek immediate medical attention or call emergency services")
            next_steps.append("Do not wait - some values require immediate intervention")
        elif high_count > 0:
            next_steps.append("⚠️ Contact your healthcare provider today")
            next_steps.append("These results need prompt medical evaluation")
        elif moderate_count > 0:
            next_steps.append("📞 Schedule an appointment with your healthcare provider within the week")
            next_steps.append("Discuss these findings at your next visit")
        else:
            next_steps.append("✅ Results look normal")
            next_steps.append("Discuss any questions at your next regular appointment")
        
        # Always add general advice
        next_steps.append("📋 Bring this report to your doctor appointment")
        next_steps.append("💬 Write down any questions you have for your doctor")
        
        return next_steps


__all__ = ["TriageEngine"]