# scripts/test_retriever.py
import sys
from pathlib import Path
import argparse

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.retriever import KnowledgeRetriever
from config.logging_config import setup_logging

setup_logging()

parser = argparse.ArgumentParser(description="Test the knowledge retriever.")
parser.add_argument("query", type=str, help="The query to search for.")
args = parser.parse_args()

print(f"Querying knowledge base for: '{args.query}'")
print("-" * 40)

retriever = KnowledgeRetriever()
context = retriever.retrieve(query=args.query)

stats = retriever.get_knowledge_stats()

print(f"Found {len(context.documents)} relevant documents (threshold: {stats['similarity_threshold']}):")

for i, (doc, meta, score) in enumerate(zip(context.documents, context.metadatas, context.relevance_scores)):
    print(f"\n--- Result {i+1} (Relevance: {score:.3f}) ---")
    print(f"Source: {meta.get('source')} | Topic: {meta.get('topic')}")
    print(doc)