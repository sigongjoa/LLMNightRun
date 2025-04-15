"""
Unit tests for vector database functionality.
"""

import os
import unittest
import tempfile
import shutil
import numpy as np
from pathlib import Path

# Add parent directory to path to import vector_db
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from vector_db.vector_store import VectorDB, Document
from vector_db.encoders import DefaultEncoder


class TestDocument(unittest.TestCase):
    """Test the Document class."""
    
    def test_document_creation(self):
        """Test document creation and properties."""
        print("Testing document creation")
        
        # Create document with minimal info
        doc1 = Document(text="Test document")
        self.assertEqual(doc1.text, "Test document")
        self.assertIsNotNone(doc1.id)
        self.assertEqual(doc1.metadata, {})
        
        # Create document with all attributes
        doc2 = Document(
            text="Test with metadata",
            metadata={"source": "unit_test", "importance": "high"},
            id="test-123"
        )
        self.assertEqual(doc2.text, "Test with metadata")
        self.assertEqual(doc2.id, "test-123")
        self.assertEqual(doc2.metadata["source"], "unit_test")
        self.assertEqual(doc2.metadata["importance"], "high")
    
    def test_document_serialization(self):
        """Test document serialization and deserialization."""
        print("Testing document serialization")
        
        # Create original document
        original = Document(
            text="Serialization test",
            metadata={"test_type": "serialization"},
            id="ser-123"
        )
        
        # Convert to dict
        doc_dict = original.to_dict()
        
        # Convert back to Document
        reconstructed = Document.from_dict(doc_dict)
        
        # Verify all properties match
        self.assertEqual(reconstructed.id, original.id)
        self.assertEqual(reconstructed.text, original.text)
        self.assertEqual(reconstructed.metadata, original.metadata)


class TestVectorDB(unittest.TestCase):
    """Test the VectorDB class."""
    
    def setUp(self):
        """Create temporary directory for test database."""
        self.temp_dir = tempfile.mkdtemp()
        print(f"Created temp directory: {self.temp_dir}")
        
        # Create in-memory database for most tests
        self.db = VectorDB(encoder=DefaultEncoder(dimension=64))
        
        # Sample documents for testing
        self.sample_docs = [
            "Python is a programming language that's easy to learn and use.",
            "Natural language processing helps computers understand human language.",
            "Vector databases use embeddings to find similar documents.",
            "Machine learning algorithms learn patterns from data.",
            "Artificial intelligence aims to create smart machines."
        ]
        
        # Add sample documents
        self.doc_ids = []
        for doc in self.sample_docs:
            doc_id = self.db.add(doc, metadata={"source": "test"})
            self.doc_ids.append(doc_id)
    
    def tearDown(self):
        """Remove temporary directory after tests."""
        shutil.rmtree(self.temp_dir)
        print(f"Removed temp directory: {self.temp_dir}")
    
    def test_add_documents(self):
        """Test adding documents to the database."""
        print("Testing document addition")
        
        # Check document count
        self.assertEqual(self.db.count(), len(self.sample_docs))
        
        # Add one more document
        new_id = self.db.add("Another test document", metadata={"new": True})
        
        # Check updated count
        self.assertEqual(self.db.count(), len(self.sample_docs) + 1)
        
        # Verify document exists
        doc = self.db.get(new_id)
        self.assertIsNotNone(doc)
        self.assertEqual(doc.text, "Another test document")
        self.assertTrue(doc.metadata["new"])
    
    def test_add_batch(self):
        """Test adding documents in batch."""
        print("Testing batch document addition")
        
        # Create new database
        db = VectorDB()
        
        # Add batch of documents
        batch_docs = ["Doc 1", "Doc 2", "Doc 3"]
        batch_metadata = [
            {"index": 0, "batch": True},
            {"index": 1, "batch": True},
            {"index": 2, "batch": True}
        ]
        
        doc_ids = db.add_batch(batch_docs, metadatas=batch_metadata)
        
        # Check count
        self.assertEqual(db.count(), len(batch_docs))
        
        # Check all documents exist with correct metadata
        for i, doc_id in enumerate(doc_ids):
            doc = db.get(doc_id)
            self.assertEqual(doc.text, batch_docs[i])
            self.assertEqual(doc.metadata["index"], i)
            self.assertTrue(doc.metadata["batch"])
    
    def test_search(self):
        """Test searching for similar documents."""
        print("Testing document search")
        
        # Search for documents similar to a query
        query = "How do computers understand language?"
        results = self.db.search(query, k=2)
        
        # Check result count
        self.assertEqual(len(results), 2)
        
        # Check results are tuples of (Document, score)
        self.assertIsInstance(results[0][0], Document)
        self.assertIsInstance(results[0][1], float)
        
        # Check scores are between 0 and 1
        for _, score in results:
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
        
        # Verify most similar document is about NLP
        # (This is probabilistic with the default encoder, but should generally work)
        expected_content = "Natural language processing"
        self.assertTrue(any(expected_content in doc.text for doc, _ in results))
    
    def test_metadata_filter(self):
        """Test metadata filtering in search."""
        print("Testing metadata filtering")
        
        # Add documents with different metadata
        self.db.add("Document with category A", metadata={"category": "A"})
        self.db.add("Document with category B", metadata={"category": "B"})
        self.db.add("Another document with category A", metadata={"category": "A"})
        
        # Search with metadata filter
        results = self.db.search("document", filter_metadata={"category": "A"})
        
        # Check all results have category A
        for doc, _ in results:
            self.assertEqual(doc.metadata["category"], "A")
    
    def test_update_document(self):
        """Test updating documents."""
        print("Testing document updates")
        
        # Get first document ID
        doc_id = self.doc_ids[0]
        
        # Original document
        original = self.db.get(doc_id)
        
        # Update text
        new_text = "Updated document text"
        self.db.update(doc_id, text=new_text)
        
        # Check text was updated
        updated = self.db.get(doc_id)
        self.assertEqual(updated.text, new_text)
        
        # Update metadata
        new_metadata = {"updated": True, "version": 2}
        self.db.update(doc_id, metadata=new_metadata)
        
        # Check metadata was updated
        updated = self.db.get(doc_id)
        self.assertEqual(updated.metadata, new_metadata)
        
        # Update both text and metadata
        self.db.update(doc_id, text="Both updated", metadata={"both": True})
        updated = self.db.get(doc_id)
        self.assertEqual(updated.text, "Both updated")
        self.assertTrue(updated.metadata["both"])
    
    def test_delete_document(self):
        """Test deleting documents."""
        print("Testing document deletion")
        
        # Initial count
        initial_count = self.db.count()
        
        # Delete first document
        first_id = self.doc_ids[0]
        self.db.delete(first_id)
        
        # Check count decreased
        self.assertEqual(self.db.count(), initial_count - 1)
        
        # Check document no longer exists
        self.assertIsNone(self.db.get(first_id))
        
        # Delete non-existent document
        result = self.db.delete("non-existent-id")
        self.assertFalse(result)
    
    def test_clear_database(self):
        """Test clearing the database."""
        print("Testing database clearing")
        
        # Initial count
        self.assertGreater(self.db.count(), 0)
        
        # Clear database
        self.db.clear()
        
        # Check count is zero
        self.assertEqual(self.db.count(), 0)
        
        # Check first document no longer exists
        self.assertIsNone(self.db.get(self.doc_ids[0]))
    
    def test_persistence(self):
        """Test database persistence."""
        print("Testing database persistence")
        
        # Create database with storage
        storage_path = os.path.join(self.temp_dir, "test_db")
        db1 = VectorDB(storage_dir=storage_path)
        
        # Add documents
        doc_ids = []
        for i, doc in enumerate(self.sample_docs):
            doc_id = db1.add(doc, metadata={"index": i})
            doc_ids.append(doc_id)
        
        # Create new database instance pointing to same storage
        db2 = VectorDB(storage_dir=storage_path)
        
        # Check documents exist in new instance
        self.assertEqual(db2.count(), len(self.sample_docs))
        
        # Check document content
        for i, doc_id in enumerate(doc_ids):
            doc = db2.get(doc_id)
            self.assertEqual(doc.text, self.sample_docs[i])
            self.assertEqual(doc.metadata["index"], i)


class TestDefaultEncoder(unittest.TestCase):
    """Test the DefaultEncoder class."""
    
    def setUp(self):
        """Create encoder for tests."""
        self.encoder = DefaultEncoder(dimension=128)
    
    def test_encode(self):
        """Test encoding a single text."""
        print("Testing single text encoding")
        
        # Encode text
        text = "This is a test document"
        embedding = self.encoder.encode(text)
        
        # Check shape
        self.assertEqual(embedding.shape, (128,))
        
        # Check vector is normalized
        norm = np.linalg.norm(embedding)
        self.assertAlmostEqual(norm, 1.0, places=6)
        
        # Check determinism (same text should give same embedding)
        embedding2 = self.encoder.encode(text)
        np.testing.assert_array_almost_equal(embedding, embedding2)
        
        # Different text should give different embedding
        different = self.encoder.encode("This is a different text")
        self.assertFalse(np.array_equal(embedding, different))
    
    def test_encode_batch(self):
        """Test encoding multiple texts."""
        print("Testing batch text encoding")
        
        # Encode batch
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = self.encoder.encode_batch(texts)
        
        # Check shape
        self.assertEqual(embeddings.shape, (len(texts), 128))
        
        # Check individual encodings match
        for i, text in enumerate(texts):
            single_embedding = self.encoder.encode(text)
            np.testing.assert_array_equal(embeddings[i], single_embedding)
    
    def test_empty_text(self):
        """Test encoding empty text."""
        print("Testing empty text encoding")
        
        # Encode empty text
        embedding = self.encoder.encode("")
        
        # Should be zero vector
        expected = np.zeros(128)
        np.testing.assert_array_equal(embedding, expected)
        
        # Batch with empty text
        texts = ["Text 1", "", "Text 3"]
        embeddings = self.encoder.encode_batch(texts)
        
        # Check second embedding is zero vector
        np.testing.assert_array_equal(embeddings[1], expected)


if __name__ == "__main__":
    unittest.main()
