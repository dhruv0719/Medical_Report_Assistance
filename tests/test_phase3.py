# tests/test_phase3_1.py
"""Test Phase 3.1: RAG Foundation"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.embeddings import EmbeddingGenerator
from backend.rag.knowledge_base import KnowledgeBase
from backend.rag.retriever import KnowledgeRetriever
from config.logging_config import setup_logging

setup_logging()

def test_embeddings():
    """Test embedding generation"""
    print("\n" + "="*60)
    print("TEST 1: EMBEDDING GENERATION")
    print("="*60)
    
    gen = EmbeddingGenerator()
    
    # Test single text
    text = "Hemoglobin measures oxygen-carrying capacity of blood"
    embedding = gen.generate_single(text)
    
    print(f"✅ Generated embedding")
    print(f"   Dimension: {len(embedding)}")
    print(f"   Shape: {embedding.shape}")
    
    # Test similarity
    text1 = "Low hemoglobin indicates anemia"
    text2 = "Anemia is caused by low hemoglobin levels"
    text3 = "High blood pressure is hypertension"
    
    sim_related = gen.compute_similarity(text1, text2)
    sim_unrelated = gen.compute_similarity(text1, text3)
    
    print(f"\n✅ Similarity test:")
    print(f"   Related texts: {sim_related:.3f}")
    print(f"   Unrelated texts: {sim_unrelated:.3f}")
    
    assert sim_related > sim_unrelated, "Related texts should be more similar"
    print("   ✅ Similarity working correctly!")


def test_knowledge_base():
    """Test knowledge base operations"""
    print("\n" + "="*60)
    print("TEST 2: KNOWLEDGE BASE")
    print("="*60)
    
    kb = KnowledgeBase()
    
    # Reset to start fresh
    kb.reset()
    
    # Add sample medical knowledge
    documents = [
        "Hemoglobin (Hgb) is a protein in red blood cells that carries oxygen from the lungs to the body's tissues and returns carbon dioxide from the tissues back to the lungs.",
        "Low hemoglobin levels may indicate anemia. Common causes include iron deficiency, vitamin B12 deficiency, bleeding, or chronic disease.",
        "Normal hemoglobin ranges are typically 13.0-17.0 g/dL for men and 12.0-15.5 g/dL for women.",
        "Potassium is an electrolyte that helps regulate heart rhythm and muscle function. Normal range is 3.5-5.0 mEq/L.",
        "High potassium (hyperkalemia) above 6.0 mEq/L is a medical emergency and can cause dangerous heart rhythms.",
    ]
    
    metadatas = [
        {"source": "MedlinePlus", "topic": "hemoglobin"},
        {"source": "MedlinePlus", "topic": "anemia"},
        {"source": "Clinical Guidelines", "topic": "hemoglobin_reference"},
        {"source": "MedlinePlus", "topic": "potassium"},
        {"source": "Clinical Guidelines", "topic": "hyperkalemia"},
    ]
    
    kb.add_documents(documents, metadatas)
    
    print(f"✅ Added {len(documents)} documents")
    print(f"   Total in KB: {kb.get_count()}")
    
    # Test query
    results = kb.query("What causes low hemoglobin?", n_results=2)
    
    print(f"\n✅ Query test:")
    print(f"   Found {len(results['documents'])} results")
    for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
        print(f"\n   Result {i+1}:")
        print(f"   Source: {meta.get('source', 'Unknown')}")
        print(f"   Text: {doc[:100]}...")


def test_retriever():
    """Test knowledge retriever"""
    print("\n" + "="*60)
    print("TEST 3: KNOWLEDGE RETRIEVER")
    print("="*60)
    
    retriever = KnowledgeRetriever()
    
    # Test retrieval for a lab test
    context = retriever.retrieve_for_test("hemoglobin", is_abnormal=True)
    
    print(f"✅ Retrieved context:")
    print(f"   Query: {context.query}")
    print(f"   Documents found: {len(context.documents)}")
    print(f"   Avg relevance: {sum(context.relevance_scores)/len(context.relevance_scores) if context.relevance_scores else 0:.3f}")
    
    # Test formatted context
    formatted = context.get_formatted_context(max_docs=2)
    print(f"\n✅ Formatted context:")
    print(f"   Length: {len(formatted)} chars")
    print(f"   Preview:\n{formatted[:200]}...")
    
    # Get stats
    stats = retriever.get_knowledge_stats()
    print(f"\n✅ Knowledge base stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    print("="*60)
    print("TESTING PHASE 3.1: RAG FOUNDATION")
    print("="*60)
    
    test_embeddings()
    test_knowledge_base()
    test_retriever()
    
    print("\n" + "="*60)
    print("✅ ALL PHASE 3.1 TESTS PASSED!")
    print("="*60)
    print("\nNext: Phase 3.2 - Knowledge Ingestion")