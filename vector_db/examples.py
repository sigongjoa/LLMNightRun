"""
Examples of using VectorDB.
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from .vector_store import VectorDB, Document
from .encoders import DefaultEncoder

# Create temporary directory for examples
TEMP_DIR = Path("temp_vector_db")
os.makedirs(TEMP_DIR, exist_ok=True)

def basic_usage_example():
    """
    Basic usage of VectorDB.
    """
    print("\n=== Basic VectorDB Usage Example ===")
    
    # Create a new vector database
    db = VectorDB(storage_dir=str(TEMP_DIR / "basic_example"))
    
    # Add some documents
    docs = [
        "Python is a programming language that lets you work quickly and integrate systems more effectively.",
        "Vector databases store and retrieve vectors efficiently, enabling semantic search.",
        "Machine learning models can be trained on large datasets to perform various tasks.",
        "Natural language processing deals with the interaction between computers and human language.",
        "Data science combines domain expertise, programming skills, and statistics to extract insights."
    ]
    
    # Add documents with metadata
    for i, doc in enumerate(docs):
        db.add(doc, metadata={"category": "tech", "index": i})
    
    print(f"Added {db.count()} documents to the database")
    
    # Search for similar documents
    query = "How do computers understand human language?"
    results = db.search(query, k=3)
    
    print(f"\nSearch results for: '{query}'")
    for i, (doc, score) in enumerate(results):
        print(f"{i+1}. Score: {score:.4f} - {doc.text[:100]}...")
        print(f"   Metadata: {doc.metadata}")
    
    # Update a document
    first_doc_id = db.list_documents(limit=1)[0].id
    db.update(first_doc_id, 
             text="Python is a high-level, interpreted programming language known for its readability and versatility.",
             metadata={"category": "programming", "index": 0, "updated": True})
    
    print("\nUpdated the first document")
    
    # Retrieve the updated document
    updated_doc = db.get(first_doc_id)
    print(f"Updated document: {updated_doc.text}")
    print(f"Updated metadata: {updated_doc.metadata}")
    
    # Delete a document
    db.delete(first_doc_id)
    print(f"\nDeleted document. Remaining count: {db.count()}")
    
    # Clear the database
    db.clear()
    print(f"Cleared database. Document count: {db.count()}")


def metadata_filtering_example():
    """
    Example of using metadata filtering.
    """
    print("\n=== Metadata Filtering Example ===")
    
    # Create a new vector database
    db = VectorDB(storage_dir=str(TEMP_DIR / "metadata_example"))
    
    # Add documents with different categories
    categories = ["science", "technology", "history", "art", "science"]
    docs = [
        "Quantum mechanics is a fundamental theory in physics that describes nature at the atomic and subatomic scales.",
        "Artificial intelligence is revolutionizing various industries including healthcare, finance, and transportation.",
        "The Renaissance was a period in European history marking the transition from the Middle Ages to modernity.",
        "Impressionism is an art movement characterized by small, thin, visible brush strokes and emphasis on light.",
        "Biology is the scientific study of life and living organisms, including their structure, function, growth, and evolution."
    ]
    
    # Add documents with metadata
    for i, (doc, category) in enumerate(zip(docs, categories)):
        db.add(doc, metadata={"category": category, "index": i})
    
    print(f"Added {db.count()} documents with different categories")
    
    # Search with metadata filter
    query = "scientific studies and research"
    results = db.search(query, k=5, filter_metadata={"category": "science"})
    
    print(f"\nSearch results for '{query}' filtered by category='science':")
    for i, (doc, score) in enumerate(results):
        print(f"{i+1}. Score: {score:.4f} - {doc.text[:100]}...")
        print(f"   Metadata: {doc.metadata}")


def persistence_example():
    """
    Example demonstrating persistence across instances.
    """
    print("\n=== Persistence Example ===")
    storage_path = str(TEMP_DIR / "persistence_example")
    
    # Create and populate first instance
    print("Creating first database instance and adding documents...")
    db1 = VectorDB(storage_dir=storage_path)
    
    docs = [
        "The quick brown fox jumps over the lazy dog",
        "To be or not to be, that is the question",
        "All that glitters is not gold"
    ]
    
    for i, doc in enumerate(docs):
        db1.add(doc, metadata={"source": "famous_phrases", "index": i})
    
    print(f"Added {db1.count()} documents to first instance")
    
    # Create second instance pointing to same storage
    print("\nCreating second database instance with same storage location...")
    db2 = VectorDB(storage_dir=storage_path)
    
    print(f"Second instance loaded {db2.count()} documents")
    
    # List documents from second instance
    print("\nDocuments in second instance:")
    for doc in db2.list_documents():
        print(f"- {doc.text} (ID: {doc.id})")
    
    # Add a document to the second instance
    new_id = db2.add("Life is what happens when you're busy making other plans", 
                    metadata={"source": "quotes", "author": "John Lennon"})
    
    print(f"\nAdded new document to second instance. Count: {db2.count()}")
    
    # Verify first instance can see the new document after reloading
    db1 = VectorDB(storage_dir=storage_path)
    print(f"First instance after reload sees {db1.count()} documents")
    
    # Clean up
    db1.clear()
    print(f"Cleared database. Document count: {db1.count()}")


def run_all_examples():
    """Run all examples."""
    basic_usage_example()
    metadata_filtering_example()
    persistence_example()
    
    print("\nExamples completed.")


if __name__ == "__main__":
    run_all_examples()
