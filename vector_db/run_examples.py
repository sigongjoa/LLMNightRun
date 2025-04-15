"""
Example script for using VectorDB in LLMNightRun project.
Run this file to see VectorDB in action.
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import json

from vector_db import VectorDB, Document, DefaultEncoder

# Try to import SentenceTransformer encoder
try:
    from vector_db.encoders import SentenceTransformerEncoder
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMER_AVAILABLE = False

# 디버그용 로그 출력 설정
DEBUG = True

# Create a temp directory for examples
TEMP_DIR = Path("temp_vector_db_examples")
os.makedirs(TEMP_DIR, exist_ok=True)


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def basic_example() -> None:
    """Basic VectorDB usage example."""
    print_header("Basic VectorDB Example")
    
    # Create a database
    db = VectorDB()
    
    # Add some sample documents
    docs = [
        "Artificial intelligence (AI) is intelligence demonstrated by machines.",
        "Machine learning is a subset of AI focused on data-based learning.",
        "Natural language processing (NLP) helps computers understand human language.",
        "Computer vision enables machines to interpret and process visual information.",
        "Neural networks are computing systems inspired by biological neural networks."
    ]
    
    print("Adding documents to the database...")
    doc_ids = []
    for i, doc in enumerate(docs):
        doc_id = db.add(doc, metadata={"index": i, "topic": "AI"})
        doc_ids.append(doc_id)
        print(f"  Added document {i+1}: ID={doc_id}")
    
    print(f"\nDatabase now contains {db.count()} documents")
    
    # Search for similar documents
    query = "How do computers understand human language?"
    print(f"\nSearching for: '{query}'")
    
    results = db.search(query, k=3)
    
    print("\nTop 3 results:")
    for i, (doc, score) in enumerate(results):
        print(f"  Result {i+1}: (Score: {score:.4f})")
        print(f"  ID: {doc.id}")
        print(f"  Text: {doc.text}")
        print(f"  Metadata: {doc.metadata}")
        print()
    
    # Get a specific document
    print(f"Getting document with ID: {doc_ids[0]}")
    doc = db.get(doc_ids[0])
    print(f"  Text: {doc.text}")
    print(f"  Metadata: {doc.metadata}")
    
    # Update a document
    print(f"\nUpdating document with ID: {doc_ids[0]}")
    db.update(
        doc_ids[0],
        text="Artificial intelligence (AI) is the simulation of human intelligence in machines that are programmed to think and learn like humans.",
        metadata={"index": 0, "topic": "AI", "updated": True}
    )
    
    # Get the updated document
    updated_doc = db.get(doc_ids[0])
    print("Updated document:")
    print(f"  Text: {updated_doc.text}")
    print(f"  Metadata: {updated_doc.metadata}")
    
    # Delete a document
    print(f"\nDeleting document with ID: {doc_ids[-1]}")
    db.delete(doc_ids[-1])
    print(f"Database now contains {db.count()} documents")
    
    # Clean up
    print("\nClearing the database")
    db.clear()
    print(f"Database now contains {db.count()} documents")


def persistence_example() -> None:
    """Example demonstrating persistence across instances."""
    print_header("Persistence Example")
    
    storage_path = TEMP_DIR / "persistence_example"
    os.makedirs(storage_path, exist_ok=True)
    
    # Create first database instance
    print("Creating first database instance...")
    db1 = VectorDB(storage_dir=str(storage_path))
    
    # Add some documents
    print("Adding documents to first instance...")
    docs = [
        "The quick brown fox jumps over the lazy dog.",
        "All that glitters is not gold.",
        "To be or not to be, that is the question."
    ]
    
    for i, doc in enumerate(docs):
        db1.add(doc, metadata={"source": "famous_phrases", "index": i})
    
    print(f"First instance contains {db1.count()} documents")
    
    # Create second instance pointing to same storage
    print("\nCreating second database instance with same storage location...")
    db2 = VectorDB(storage_dir=str(storage_path))
    
    print(f"Second instance contains {db2.count()} documents")
    
    # List documents from second instance
    print("\nDocuments in second instance:")
    for i, doc in enumerate(db2.list_documents()):
        print(f"  Document {i+1}:")
        print(f"  ID: {doc.id}")
        print(f"  Text: {doc.text}")
        print(f"  Metadata: {doc.metadata}")
        print()
    
    # Add a document to second instance
    print("Adding a new document to second instance...")
    new_id = db2.add(
        "Life is what happens when you're busy making other plans.",
        metadata={"source": "quotes", "author": "John Lennon"}
    )
    
    print(f"Second instance now contains {db2.count()} documents")
    
    # Create new instance of first database to see the change
    print("\nReloading first instance...")
    db1 = VectorDB(storage_dir=str(storage_path))
    print(f"First instance now contains {db1.count()} documents")
    
    # Clean up
    print("\nClearing database from first instance...")
    db1.clear()
    print(f"First instance now contains {db1.count()} documents")
    
    # Check second instance after clearing
    print("\nChecking second instance after clearing...")
    db2 = VectorDB(storage_dir=str(storage_path))
    print(f"Second instance now contains {db2.count()} documents")


def metadata_filtering_example() -> None:
    """Example demonstrating metadata filtering."""
    print_header("Metadata Filtering Example")
    
    # Create a database
    db = VectorDB()
    
    # Add documents with different categories
    print("Adding documents with different categories...")
    
    # Science documents
    science_docs = [
        "Quantum mechanics is a fundamental theory in physics describing nature at atomic scales.",
        "DNA carries genetic information that determines the development of organisms.",
        "The periodic table organizes chemical elements based on their properties."
    ]
    
    # Technology documents
    tech_docs = [
        "Machine learning algorithms learn patterns from data without explicit programming.",
        "Cloud computing delivers computing services over the internet.",
        "Cybersecurity protects systems, networks, and programs from digital attacks."
    ]
    
    # Adding science documents
    for i, doc in enumerate(science_docs):
        db.add(doc, metadata={"category": "science", "index": i})
    
    # Adding technology documents
    for i, doc in enumerate(tech_docs):
        db.add(doc, metadata={"category": "technology", "index": i})
    
    print(f"Added {db.count()} documents to the database")
    
    # Search all documents
    print("\nSearching all documents for 'how systems work':")
    all_results = db.search("how systems work", k=6)
    
    for i, (doc, score) in enumerate(all_results):
        print(f"  Result {i+1}: (Score: {score:.4f})")
        print(f"  Category: {doc.metadata['category']}")
        print(f"  Text: {doc.text[:100]}...")
        print()
    
    # Search with category filter
    print("\nSearching only 'science' category documents:")
    science_results = db.search(
        "how systems work", 
        k=6, 
        filter_metadata={"category": "science"}
    )
    
    for i, (doc, score) in enumerate(science_results):
        print(f"  Result {i+1}: (Score: {score:.4f})")
        print(f"  Category: {doc.metadata['category']}")
        print(f"  Text: {doc.text[:100]}...")
        print()
    
    # Clean up
    print("\nClearing the database")
    db.clear()


def sentence_transformer_example() -> None:
    """Example using the SentenceTransformer encoder for better embeddings."""
    print_header("SentenceTransformer Example")
    
    if not SENTENCE_TRANSFORMER_AVAILABLE:
        print("SentenceTransformer is not available.")
        print("Please install it with: pip install sentence-transformers")
        return
    
    try:
        # Create a database with SentenceTransformer encoder
        print("Creating database with SentenceTransformer encoder...")
        encoder = SentenceTransformerEncoder(model_name="all-MiniLM-L6-v2")
        db = VectorDB(encoder=encoder)
        
        # Add semantically related documents
        print("\nAdding documents with semantic relationships...")
        docs = [
            "The cat sits on the mat.",
            "A feline is resting on a rug.",
            "The dog runs in the park.",
            "A canine is jogging in a garden.",
            "Python is a programming language.",
            "JavaScript is used for web development."
        ]
        
        for doc in docs:
            db.add(doc)
        
        print(f"Added {db.count()} documents")
        
        # Search for semantically similar documents
        print("\nSearching for 'A cat lounging on a carpet':")
        results = db.search("A cat lounging on a carpet", k=3)
        
        for i, (doc, score) in enumerate(results):
            print(f"  Result {i+1}: (Score: {score:.4f})")
            print(f"  Text: {doc.text}")
            print()
        
        print("\nSearching for 'Programming languages for software development':")
        results = db.search("Programming languages for software development", k=3)
        
        for i, (doc, score) in enumerate(results):
            print(f"  Result {i+1}: (Score: {score:.4f})")
            print(f"  Text: {doc.text}")
            print()
        
        # Clean up
        print("\nClearing the database")
        db.clear()
        
    except Exception as e:
        print(f"Error in sentence transformer example: {str(e)}")


def batch_operations_example() -> None:
    """Example demonstrating batch operations."""
    print_header("Batch Operations Example")
    
    # Create a database
    db = VectorDB()
    
    # Prepare batch of documents
    print("Preparing batch of documents...")
    batch_docs = [
        "The first document in the batch.",
        "This is the second document.",
        "Here is the third document with different content.",
        "Document number four with some unique text.",
        "The fifth and final document in our batch."
    ]
    
    batch_metadata = [
        {"index": 0, "batch": 1, "priority": "high"},
        {"index": 1, "batch": 1, "priority": "medium"},
        {"index": 2, "batch": 1, "priority": "low"},
        {"index": 3, "batch": 1, "priority": "medium"},
        {"index": 4, "batch": 1, "priority": "high"}
    ]
    
    # Add batch of documents
    print("Adding batch of documents...")
    start_time = time.time()
    doc_ids = db.add_batch(batch_docs, metadatas=batch_metadata)
    end_time = time.time()
    
    print(f"Added {len(doc_ids)} documents in {end_time - start_time:.4f} seconds")
    print(f"Database now contains {db.count()} documents")
    
    # List all documents
    print("\nListing all documents:")
    for i, doc in enumerate(db.list_documents()):
        print(f"  Document {i+1}:")
        print(f"  ID: {doc.id}")
        print(f"  Priority: {doc.metadata['priority']}")
        print(f"  Text: {doc.text}")
        print()
    
    # Search with metadata filter
    print("\nSearching for high priority documents:")
    results = db.search(
        "unique content", 
        k=5, 
        filter_metadata={"priority": "high"}
    )
    
    for i, (doc, score) in enumerate(results):
        print(f"  Result {i+1}: (Score: {score:.4f})")
        print(f"  Priority: {doc.metadata['priority']}")
        print(f"  Text: {doc.text}")
        print()
    
    # Clean up
    print("\nClearing the database")
    db.clear()


def run_all_examples() -> None:
    """Run all examples."""
    try:
        basic_example()
        persistence_example()
        metadata_filtering_example()
        batch_operations_example()
        
        # Run sentence transformer example if available
        if SENTENCE_TRANSFORMER_AVAILABLE:
            sentence_transformer_example()
    except Exception as e:
        print(f"Error running examples: {str(e)}")
    finally:
        # Optional: clean up temp directory
        # import shutil
        # shutil.rmtree(TEMP_DIR, ignore_errors=True)
        # print(f"\nRemoved temporary directory: {TEMP_DIR}")
        pass


if __name__ == "__main__":
    print("VectorDB Examples")
    print("----------------")
    
    # Check if a specific example was requested
    if len(sys.argv) > 1:
        example_name = sys.argv[1]
        
        if example_name == "basic":
            basic_example()
        elif example_name == "persistence":
            persistence_example()
        elif example_name == "metadata":
            metadata_filtering_example()
        elif example_name == "sentence_transformer":
            sentence_transformer_example()
        elif example_name == "batch":
            batch_operations_example()
        else:
            print(f"Unknown example: {example_name}")
            print("Available examples: basic, persistence, metadata, sentence_transformer, batch")
    else:
        # Run all examples
        run_all_examples()
    
    print("\nExamples completed.")
