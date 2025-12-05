# backend/safety/next_steps.py
"""
Generate specific next-step recommendations based on test results.
"""

from typing import List, Dict
from backend.parser.entities import LabTest
from backend.safety.alerts import TriageResult
from config.logging_config import get_logger

logger = get_logger(__name__)


class NextStepsGenerator:
    """Generates specific next-step recommendations"""
    
    # Test-specific recommendations
    TEST_RECOMMENDATIONS = {
        "hemoglobin": {
            "low": [
                "Consider iron-rich foods (red meat, spinach, beans)",
                "Ask your doctor about iron supplements",
                "May need additional tests: iron studies, vitamin B12, folate"
            ],
            "high": [
                "Ensure adequate hydration",
                "Discuss any smoking history with your doctor",
                "May need additional tests to determine cause"
            ]
        },
        "potassium": {
            "low": [
                "Include potassium-rich foods (bananas, oranges, potatoes)",
                "Review medications with your doctor (some diuretics lower potassium)",
                "Avoid excessive sweating or dehydration"
            ],
            "high": [
                "Review all medications and supplements with your doctor",
                "May need dietary changes - your doctor will advise",
                "Follow up testing may be needed"
            ]
        },
        "glucose": {
            "low": [
                "Keep fast-acting glucose sources available (juice, candy)",
                "Eat regular meals and snacks",
                "Review diabetes medications with your doctor if applicable"
            ],
            "high": [
                "Monitor blood sugar regularly if you have diabetes supplies",
                "Increase physical activity (with doctor approval)",
                "Discuss dietary changes and medications with your doctor"
            ]
        }
    }
    
    @classmethod
    def get_test_specific_steps(cls, test_name: str, is_high: bool) -> List[str]:
        """
        Get test-specific recommendations.
        
        Args:
            test_name: Name of the test
            is_high: Whether the value is high (vs low)
            
        Returns:
            List of recommendations
        """
        test_lower = test_name.lower()
        
        for key, recommendations in cls.TEST_RECOMMENDATIONS.items():
            if key in test_lower:
                direction = "high" if is_high else "low"
                return recommendations.get(direction, [])
        
        return []
    
    @classmethod
    def generate_for_triage(cls, triage: TriageResult, tests: List[LabTest]) -> List[str]:
        """
        Generate comprehensive next steps based on triage result.
        
        Args:
            triage: Triage result
            tests: Original lab tests
            
        Returns:
            List of next step recommendations
        """
        steps = list(triage.next_steps)  # Copy existing steps
        
        # Add test-specific recommendations for abnormal tests
        abnormal_tests = [t for t in tests if t.is_abnormal]
        
        if abnormal_tests:
            steps.append("\n📝 Specific Recommendations:")
            
            for test in abnormal_tests[:3]:  # Limit to top 3 abnormal tests
                is_high = test.flag in ['H', 'HH'] if test.flag else True
                test_steps = cls.get_test_specific_steps(test.name, is_high)
                
                if test_steps:
                    steps.append(f"\nFor {test.name}:")
                    steps.extend([f"  • {step}" for step in test_steps])
        
        return steps


__all__ = ["NextStepsGenerator"]