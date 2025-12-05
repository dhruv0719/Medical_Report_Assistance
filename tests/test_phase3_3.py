# tests/test_phase3_3.py
"""Test Phase 3.3: LLM Integration"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.llm.groq_client import GroqClient
from backend.llm.prompt_builder import PromptBuilder
from backend.llm.explainer import MedicalExplainer
from backend.parser.entities import create_lab_test
from backend.rag.retriever import KnowledgeRetriever
from config.logging_config import setup_logging

setup_logging()


def test_groq_client():
    """Test Groq API connection"""
    print("\n" + "="*60)
    print("TEST 1: GROQ CLIENT")
    print("="*60)
    
    try:
        client = GroqClient()
        
        # Test connection
        success = client.test_connection()
        assert success, "Groq connection failed"
        
        print("✅ Groq client initialized")
        print(f"   Model: {client.model}")
        
        # Test simple completion
        response = client.generate_explanation(
            system_prompt="You are a helpful assistant.",
            user_prompt="Explain what hemoglobin is in one sentence.",
            temperature=0.3
        )
        
        print(f"\n✅ Test completion:")
        print(f"   {response[:150]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure GROQ_API_KEY is set in your .env file")
        raise


def test_prompt_builder():
    """Test prompt construction"""
    print("\n" + "="*60)
    print("TEST 2: PROMPT BUILDER")
    print("="*60)
    
    # Create a test result
    test = create_lab_test(
        name="Hemoglobin",
        value="11.2",
        unit="g/dL",
        reference_range="13.0-17.0",
        flag="L"
    )
    
    # Get context
    retriever = KnowledgeRetriever()
    context = retriever.retrieve_for_test("hemoglobin", is_abnormal=True)
    
    # Build prompts
    builder = PromptBuilder()
    system_prompt, user_prompt = builder.build_explanation_prompt(test, context)
    
    print("✅ System prompt created")
    print(f"   Length: {len(system_prompt)} chars")
    
    print(f"\n✅ User prompt created")
    print(f"   Length: {len(user_prompt)} chars")
    print(f"   Preview:\n{user_prompt[:300]}...")


def test_medical_explainer():
    """Test complete explanation generation"""
    print("\n" + "="*60)
    print("TEST 3: MEDICAL EXPLAINER")
    print("="*60)
    
    # Create test results
    test_normal = create_lab_test(
        name="White Blood Cell Count",
        value="7.2",
        unit="x10³/µL",
        reference_range="4.0-11.0"
    )
    
    test_abnormal = create_lab_test(
        name="Hemoglobin",
        value="11.2",
        unit="g/dL",
        reference_range="13.0-17.0",
        flag="L"
    )
    
    # Initialize explainer
    explainer = MedicalExplainer()
    
    # Generate explanations
    print("\n📝 Generating explanation for NORMAL test...")
    explanation_normal = explainer.explain_test(test_normal)
    
    print(f"✅ Explanation generated:")
    print(f"   Test: {explanation_normal.test_name}")
    print(f"   Abnormal: {explanation_normal.is_abnormal}")
    print(f"   Sources: {explanation_normal.sources_used}")
    print(f"\n   Explanation:\n{explanation_normal.explanation_text[:300]}...\n")
    
    print("\n📝 Generating explanation for ABNORMAL test...")
    explanation_abnormal = explainer.explain_test(test_abnormal)
    
    print(f"✅ Explanation generated:")
    print(f"   Test: {explanation_abnormal.test_name}")
    print(f"   Abnormal: {explanation_abnormal.is_abnormal}")
    print(f"   Sources: {explanation_abnormal.sources_used}")
    print(f"\n   Explanation:\n{explanation_abnormal.explanation_text[:300]}...\n")


if __name__ == "__main__":
    print("="*60)
    print("TESTING PHASE 3.3: LLM INTEGRATION")
    print("="*60)
    
    test_groq_client()
    test_prompt_builder()
    test_medical_explainer()
    
    print("\n" + "="*60)
    print("✅ ALL PHASE 3.3 TESTS PASSED!")
    print("="*60)
    print("\nNext: Phase 3.4 - Safety Triage Engine")