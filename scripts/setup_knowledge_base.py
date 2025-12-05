# scripts/setup_knowledge_base.py
"""
Populate the knowledge base with medical information.
Run this once to set up the RAG system.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.rag.knowledge_base import KnowledgeBase
from config.settings import Paths, RAGConfig
from config.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    chunk_size = chunk_size or RAGConfig.CHUNK_SIZE
    overlap = overlap or RAGConfig.CHUNK_OVERLAP
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def load_medical_knowledge_file(file_path: Path) -> list:
    """
    Load medical knowledge from a text file.
    File format: Sections separated by "# Topic Name"
    
    Returns:
        List of (text, metadata) tuples
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    documents = []
    metadatas = []
    
    # Split by topic headers (lines starting with #)
    sections = content.split('\n# ')
    
    for section in sections:
        if not section.strip():
            continue
        
        # First line is the topic name
        lines = section.strip().split('\n', 1)
        if len(lines) < 2:
            continue
        
        topic = lines[0].strip('# ').strip()
        text = lines[1].strip()
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        for para in paragraphs:
            if len(para) > 100:  # Only add substantial paragraphs
                documents.append(para)
                metadatas.append({
                    'source': 'Medical Knowledge Base',
                    'topic': topic.lower(),
                    'type': 'explanation'
                })
    
    logger.info(f"Loaded {len(documents)} documents from {file_path.name}")
    return documents, metadatas


def setup_knowledge_base(reset: bool = False, file_path: Path = None):
    """
    Set up the knowledge base with medical information.
    
    Args:
        reset: If True, clear existing data before adding new
        file_path: Optional Path to a medical knowledge text file. If None, uses
                   the default path.
    """
    logger.info("Setting up knowledge base...")
    
    # Initialize knowledge base
    kb = KnowledgeBase()
    
    # Reset if requested
    if reset:
        logger.warning("Resetting knowledge base...")
        kb.reset()
    
    # Determine knowledge file to load
    if file_path:
        knowledge_file = Path(file_path)
        if not knowledge_file.is_absolute():
            knowledge_file = PROJECT_ROOT / knowledge_file
    else:
        knowledge_file = Paths.DATA / "knowledge_base" / "sample_medical_knowledge.txt"

    
    if not knowledge_file.exists():
        logger.error(f"Knowledge file not found: {knowledge_file}")
        logger.info("Please create the file with medical knowledge")
        return
    
    documents, metadatas = load_medical_knowledge_file(knowledge_file)
    
    # Add to knowledge base
    logger.info(f"Adding {len(documents)} documents to knowledge base...")
    kb.add_documents(documents, metadatas)
    
    # Show stats
    total = kb.get_count()
    logger.info(f"✅ Knowledge base setup complete!")
    logger.info(f"   Total documents: {total}")
    
    # Test a query
    logger.info("\nTesting knowledge retrieval...")
    results = kb.query("What causes low hemoglobin?", n_results=2)
    
    logger.info(f"   Query returned {len(results['documents'])} results")
    if results['documents']:
        logger.info(f"   Top result: {results['documents'][0][:100]}...")
    
    return kb


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup medical knowledge base")
    parser.add_argument('--reset', action='store_true', help="Reset knowledge base before loading")
    parser.add_argument('--file', '-f', type=str, help="Path to medical knowledge text file (relative to project root or absolute)")
    args = parser.parse_args()
    
    print("="*60)
    print("SETTING UP KNOWLEDGE BASE")
    print("="*60)
    print()
    
    kb = setup_knowledge_base(reset=args.reset, file_path=Path(args.file) if args.file else None)
    
    if kb:
        print()
        print("="*60)
        print("✅ KNOWLEDGE BASE READY!")
        print("="*60)
        print(f"\nTotal documents: {kb.get_count()}")
        print(f"Collection: {kb.collection_name}")
        print(f"Location: {kb.persist_directory}")