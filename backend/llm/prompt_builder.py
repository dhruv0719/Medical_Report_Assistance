# backend/llm/prompt_builder.py
"""
Builds prompts for LLM from templates and data.
Handles context injection, formatting, and safety constraints.
"""

from typing import List, Dict
from backend.parser.entities import LabTest
from backend.rag.retriever import RetrievedContext
from config.prompts import SystemPrompt, PromptConstants
from config.logging_config import get_logger

logger = get_logger(__name__)


class PromptBuilder:
    """Constructs prompts for medical explanations"""
    
    @staticmethod
    def build_explanation_prompt(
        test: LabTest,
        context: RetrievedContext,
        include_sources: bool = True
    ) -> tuple[str, str]:
        """
        Build system and user prompts for explaining a lab test.
        
        Args:
            test: Lab test to explain
            context: Retrieved medical knowledge
            include_sources: Whether to include source citations
            
        Returns:
            (system_prompt, user_prompt) tuple
        """
        # System prompt with safety instructions
        system_prompt = SystemPrompt.MEDICAL_EXPLAINER_V2
        
        # Build user prompt with context
        status = "abnormal" if test.is_abnormal else "normal"
        flag_text = f" (flagged as {test.flag})" if test.flag else ""
        
        # Format retrieved context
        if context.documents:
            context_text = "\n\n".join([
                f"Reference {i+1}:\n{doc}"
                for i, doc in enumerate(context.documents[:3])
            ])
        else:
            context_text = "No specific medical references available for this test."
        
        user_prompt = f"""Please explain this laboratory test result to a patient:

TEST RESULT:
- Test Name: {test.name}
- Patient's Value: {test.value} {test.unit}
- Reference Range: {test.reference_range}
- Status: This value is {status}{flag_text}

MEDICAL REFERENCE INFORMATION:
{context_text}

Please provide a clear, patient-friendly explanation that includes:
1. What this test measures and why it's important
2. What this specific result means
3. {"Possible causes of this abnormal value" if test.is_abnormal else "What this normal result indicates"}
4. What the patient should do next

Keep the explanation concise (3-4 paragraphs), use simple language, and always remind the patient to discuss results with their healthcare provider."""

        if include_sources and context.metadatas:
            sources = set([m.get('source', 'Unknown') for m in context.metadatas])
            user_prompt += f"\n\nBased on: {', '.join(sources)}"
        
        return system_prompt, user_prompt
    
    @staticmethod
    def build_summary_prompt(
        tests: List[LabTest],
        report_type: str,
        impression: str
    ) -> tuple[str, str]:
        """
        Build prompts for summarizing a complete report.
        
        Args:
            tests: List of lab tests
            report_type: Type of report (CBC, BMP, etc.)
            impression: Clinical impression from report
            
        Returns:
            (system_prompt, user_prompt) tuple
        """
        system_prompt = SystemPrompt.MEDICAL_EXPLAINER_V2
        
        # Summarize test results
        normal_tests = [t for t in tests if not t.is_abnormal]
        abnormal_tests = [t for t in tests if t.is_abnormal]
        
        test_summary = f"""
REPORT TYPE: {report_type}

SUMMARY:
- Total tests: {len(tests)}
- Normal results: {len(normal_tests)}
- Abnormal results: {len(abnormal_tests)}

ABNORMAL RESULTS:
"""
        
        for test in abnormal_tests:
            flag = f"[{test.flag}]" if test.flag else ""
            test_summary += f"- {test.name}: {test.value} {test.unit} (Normal: {test.reference_range}) {flag}\n"
        
        if impression:
            test_summary += f"\nCLINICAL IMPRESSION:\n{impression}"
        
        user_prompt = f"""{test_summary}

Please provide a brief overview of this lab report for the patient:
1. What type of tests were done and why
2. Summary of the findings (normal vs abnormal)
3. What the abnormal results might indicate
4. Recommended next steps

Keep it concise and reassuring while being accurate."""

        return system_prompt, user_prompt
    
    @staticmethod
    def add_safety_footer(explanation: str) -> str:
        """
        Add safety disclaimers to an explanation.
        
        Args:
            explanation: Generated explanation
            
        Returns:
            Explanation with safety disclaimers
        """
        return (
            explanation + 
            PromptConstants.SAFETY_DISCLAIMER + 
            PromptConstants.ENCOURAGEMENT
        )
    
    @staticmethod
    def add_critical_warning(explanation: str) -> str:
        """
        Add critical value warning to explanation.
        
        Args:
            explanation: Generated explanation
            
        Returns:
            Explanation with critical warning
        """
        return PromptConstants.CRITICAL_VALUE_NOTICE + "\n\n" + explanation


__all__ = ["PromptBuilder"]