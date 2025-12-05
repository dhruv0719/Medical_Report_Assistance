# config/prompts.py
"""LLM prompt templates for medical report explanations.
All prompts are versioned and documented for reproducibility."""

from typing import Dict, List

class SystemPrompt:
    """System prompts that define LLM behavior"""

    MEDICAL_EXPLAINER_V1 = """You are a medical information assistant designed to explain laboratory test results to patients in clear, simple language.

YOUR ROLE:
- Explain what medical tests measure and what results mean
- Use plain language that a non-medical person can understand
- Provide context from trusted medical sources
- Be empathetic and reassuring while being accurate

YOU MUST NEVER:
- Diagnose medical conditions
- Recommend specific treatments or medications
- Replace the advice of a healthcare professional
- Make definitive claims about health status
- Cause unnecessary alarm

FORMATTING RULES:
1. Start explanations with "Based on medical guidelines..."
2. Explain what the test measures in 1-2 simple sentences
3. Note whether the value is within or outside the normal range
4. If abnormal, explain what it *might* indicate (use cautious language)
5. Always end with: "Please discuss these results with your healthcare provider"
6. Cite sources when providing medical information

TONE:
- Warm and supportive
- Clear and educational
- Non-alarmist but honest
- Respectful of patient concerns

Remember: You are providing information, NOT medical advice."""

    MEDICAL_EXPLAINER_V2 = """You are an AI medical report interpreter with expertise in clinical laboratory medicine.

CORE PRINCIPLES:
1. Patient Safety First - Never provide diagnoses or treatment advice
2. Evidence-Based - Only use information from trusted medical sources
3. Plain Language - Avoid jargon, explain technical terms
4. Appropriate Uncertainty - Use phrases like "may indicate" or "could suggest"
5. Always Defer to Professionals - Direct users to consult their doctor

YOUR TASK:
Given a lab test result and reference range, explain:
- What the test measures (purpose)
- What the specific result means
- Possible reasons for abnormal values (if applicable)
- General next steps (e.g., "Your doctor may recommend...")

MANDATORY DISCLAIMER:
Always include: "This explanation is for educational purposes only. Only your healthcare provider can interpret your results in the context of your complete medical history."

CITATION REQUIREMENT:
When stating medical facts, cite the source (e.g., "According to MedlinePlus..." or "Clinical guidelines indicate...")."""


class UserPromptTemplates:
    """Templates for constructing user prompts"""
    
    @staticmethod
    def explain_single_test(
        test_name: str,
        value: str,
        unit: str,
        reference_range: str,
        is_abnormal: bool,
        context_docs: List[Dict[str, str]]
    ) -> str:
        """Generate prompt for explaining a single test result"""
        
        status = "OUTSIDE normal range" if is_abnormal else "within normal range"
        
        # Format context documents
        context_text = "\n\n".join([
            f"Source: {doc.get('source', 'Unknown')}\n{doc.get('text', '')}"
            for doc in context_docs
        ])
        
        prompt = f"""Please explain this laboratory test result to a patient:

TEST INFORMATION:
- Test Name: {test_name}
- Result Value: {value} {unit}
- Reference Range: {reference_range}
- Status: {status}

RELEVANT MEDICAL INFORMATION:
{context_text}

Please provide a clear, patient-friendly explanation following these guidelines:
1. What does this test measure?
2. What does this specific result mean?
3. {"Why might this value be outside the normal range?" if is_abnormal else "This result is normal."}
4. What should the patient know or do next?

Keep your explanation concise (3-4 paragraphs) and use simple language."""

        return prompt
    
    @staticmethod
    def explain_multiple_tests(
        tests: List[Dict],
        report_type: str,
        impression: str,
        context_docs: List[Dict[str, str]]
    ) -> str:
        """Generate prompt for explaining a panel of tests"""
        
        # Format test results
        test_list = "\n".join([
            f"- {t['name']}: {t['value']} {t['unit']} "
            f"(Normal: {t['reference_range']}) "
            f"{'[ABNORMAL]' if t['is_abnormal'] else '[NORMAL]'}"
            for t in tests
        ])
        
        # Format context
        context_text = "\n\n".join([
            f"Source: {doc.get('source', 'Unknown')}\n{doc.get('text', '')}"
            for doc in context_docs
        ])
        
        prompt = f"""Please provide an overview explanation of this laboratory panel:

REPORT TYPE: {report_type}

TEST RESULTS:
{test_list}

CLINICAL IMPRESSION (from report):
{impression if impression else "None provided"}

RELEVANT MEDICAL INFORMATION:
{context_text}

Please provide:
1. A brief overview of what this panel tests for (1-2 sentences)
2. Summary of the results (which are normal, which are abnormal)
3. What the pattern of results might indicate (use cautious language)
4. Recommended next steps for the patient

Keep the explanation clear and under 5 paragraphs."""

        return prompt
    
    @staticmethod
    def generate_next_steps(
        abnormal_tests: List[Dict],
        urgency_level: str
    ) -> str:
        """Generate prompt for recommending next steps"""
        
        test_names = ", ".join([t['name'] for t in abnormal_tests])
        
        prompt = f"""Based on these abnormal test results: {test_names}
Urgency Level: {urgency_level}

Please suggest appropriate next steps for the patient. Include:
1. Whether they should contact their doctor (routine vs. urgent)
2. What additional tests might be recommended
3. General lifestyle or monitoring suggestions (if applicable)
4. Timeline for follow-up

Keep recommendations general and always emphasize consulting with their healthcare provider."""

        return prompt


class PromptConstants:
    """Reusable prompt fragments"""
    
    SAFETY_DISCLAIMER = (
        "\n\n⚠️ IMPORTANT: This explanation is for informational purposes only. "
        "It does not constitute medical advice. Always consult your healthcare "
        "provider for interpretation of your specific results."
    )
    
    CRITICAL_VALUE_NOTICE = (
        "\n\n🚨 CRITICAL VALUE ALERT: This result is significantly outside the "
        "normal range and may require immediate medical attention. Please contact "
        "your healthcare provider or seek emergency care right away."
    )
    
    SOURCES_FOOTER = (
        "\n\nInformation sources: MedlinePlus (NIH), StatPearls (NCBI), "
        "and clinical laboratory guidelines."
    )
    
    ENCOURAGEMENT = (
        "\n\nRemember: Having questions about your lab results is completely normal. "
        "Your healthcare provider is the best person to help you understand what "
        "these results mean for your specific health situation."
    )


class PromptValidation:
    """Validate and sanitize prompts"""
    
    MAX_PROMPT_LENGTH = 7500  # characters
    MAX_CONTEXT_DOCS = 5
    
    @staticmethod
    def truncate_context(context_docs: List[Dict], max_chars: int = 2000) -> List[Dict]:
        """Truncate context documents to fit within token limits"""
        truncated = []
        total_chars = 0
        
        for doc in context_docs:
            text = doc.get('text', '')
            if total_chars + len(text) <= max_chars:
                truncated.append(doc)
                total_chars += len(text)
            else:
                # Add partial document
                remaining = max_chars - total_chars
                if remaining > 100:  # Only add if meaningful amount remains
                    truncated.append({
                        **doc,
                        'text': text[:remaining] + "..."
                    })
                break
        
        return truncated
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Remove potentially harmful content from user inputs"""
        # Remove potential prompt injection attempts
        dangerous_patterns = [
            "ignore previous instructions",
            "ignore all previous",
            "disregard previous",
            "you are now",
            "new instructions",
        ]
        
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if pattern in text_lower:
                # Log suspicious activity
                print(f"⚠️  Suspicious prompt detected: {pattern}")
                text = text.replace(pattern, "[REDACTED]")
        
        return text


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "SystemPrompts",
    "UserPromptTemplates",
    "PromptConstants",
    "PromptValidation",
]

# Backwards compatibility: some modules/tests expect `SystemPrompts`
SystemPrompts = SystemPrompt