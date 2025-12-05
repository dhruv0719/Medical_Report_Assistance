# backend/llm/explainer.py
"""
Medical explainer that combines RAG retrieval with LLM generation.
Main interface for generating patient-friendly explanations.
"""

from typing import Optional, Dict
from dataclasses import dataclass

from backend.parser.entities import LabTest
from backend.rag.retriever import KnowledgeRetriever
from backend.llm.groq_client import GroqClient
from backend.llm.prompt_builder import PromptBuilder
from config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class Explanation:
    """Container for a generated explanation"""
    test_name: str
    explanation_text: str
    sources_used: list
    is_abnormal: bool
    is_critical: bool
    confidence: float = 0.0


class MedicalExplainer:
    """Generates patient-friendly explanations for lab tests using RAG + LLM"""
    
    def __init__(
        self,
        retriever: Optional[KnowledgeRetriever] = None,
        llm_client: Optional[GroqClient] = None
    ):
        """
        Initialize explainer.
        
        Args:
            retriever: Knowledge retriever (creates new if not provided)
            llm_client: LLM client (creates new if not provided)
        """
        self.retriever = retriever or KnowledgeRetriever()
        self.llm_client = llm_client or GroqClient()
        self.prompt_builder = PromptBuilder()
        
        logger.info("✅ Medical explainer initialized")

    @staticmethod
    def clean_llm_output(text: str) -> str:
        """
        Clean LLM output by removing reasoning tags and artifacts.
        
        Args:
            text: Raw LLM output
            
        Returns:
            Cleaned text
        """
        import re
        
        # Remove <think>...</think> tags (used by Qwen models)
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # Remove other common artifacts
        text = re.sub(r'</?think>', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        
        return text
    
    def explain_test(
        self,
        test: LabTest,
        include_context: bool = True
    ) -> Explanation:
        """
        Generate explanation for a single lab test.
        
        Args:
            test: Lab test to explain
            include_context: Whether to retrieve and use medical context
            
        Returns:
            Explanation object
        """
        logger.info(f"Generating explanation for {test.name}...")
        
        # Retrieve relevant medical knowledge
        if include_context:
            context = self.retriever.retrieve_for_test(
                test.name,
                is_abnormal=test.is_abnormal
            )
            logger.debug(f"Retrieved {len(context.documents)} context documents")
        else:
            from backend.rag.retriever import RetrievedContext
            context = RetrievedContext(
                query="",
                documents=[],
                metadatas=[],
                relevance_scores=[]
            )
        
        # Build prompts
        system_prompt, user_prompt = self.prompt_builder.build_explanation_prompt(
            test, context
        )
        
        # Generate explanation
        explanation_text = self.llm_client.generate_explanation(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3  # Low temperature for consistency
        )

        # Clean LLM output (remove <think> tags, etc.)
        explanation_text = self.clean_llm_output(explanation_text) 
        
        # Add safety disclaimers
        explanation_text = self.prompt_builder.add_safety_footer(explanation_text)
        
        # Add critical warning if needed
        if test.is_critical():
            explanation_text = self.prompt_builder.add_critical_warning(explanation_text)
        
        # Extract sources
        sources = list(set([
            m.get('source', 'Unknown') 
            for m in context.metadatas
        ])) if context.metadatas else []
        
        logger.info(f"✅ Generated explanation for {test.name}")
        
        return Explanation(
            test_name=test.name,
            explanation_text=explanation_text,
            sources_used=sources,
            is_abnormal=test.is_abnormal,
            is_critical=test.is_critical()
        )
    
    def batch_explain(self, tests: list[LabTest]) -> Dict[str, Explanation]:
        """
        Generate explanations for multiple tests.
        
        Args:
            tests: List of lab tests
            
        Returns:
            Dictionary mapping test names to explanations
        """
        explanations = {}
        
        for test in tests:
            try:
                explanation = self.explain_test(test)
                explanations[test.name] = explanation
            except Exception as e:
                logger.error(f"Failed to explain {test.name}: {str(e)}")
                # Continue with other tests
        
        logger.info(f"✅ Generated {len(explanations)}/{len(tests)} explanations")
        
        return explanations


__all__ = ["MedicalExplainer", "Explanation"]