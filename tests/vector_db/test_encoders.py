"""
Unit tests for encoders module.
"""

import unittest
import numpy as np
from pathlib import Path

# Add parent directory to path to import vector_db
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from vector_db.encoders import DefaultEncoder


class TestDefaultEncoder(unittest.TestCase):
    """Test the DefaultEncoder class functionality."""
    
    def setUp(self):
        """Create encoder instances for testing."""
        # Create encoders with different dimensions
        self.default_encoder = DefaultEncoder(dimension=128)
        self.small_encoder = DefaultEncoder(dimension=32)
        self.large_encoder = DefaultEncoder(dimension=512)
        
        # Test data
        self.test_text = "This is a test sentence for encoding."
        self.test_batch = [
            "First test sentence.",
            "Second test sentence, a bit longer.",
            "Third and final test sentence with some additional text."
        ]
        
        print("Set up encoder test")
    
    def test_encoder_dimensions(self):
        """Test that encoders produce vectors with the correct dimensions."""
        print("Testing encoder dimensions")
        
        # Check default encoder dimension
        embedding = self.default_encoder.encode(self.test_text)
        self.assertEqual(embedding.shape, (128,))
        
        # Check small encoder dimension
        small_embedding = self.small_encoder.encode(self.test_text)
        self.assertEqual(small_embedding.shape, (32,))
        
        # Check large encoder dimension
        large_embedding = self.large_encoder.encode(self.test_text)
        self.assertEqual(large_embedding.shape, (512,))
    
    def test_vector_normalization(self):
        """Test that encoded vectors are normalized (unit vectors)."""
        print("Testing vector normalization")
        
        # Encode text
        embedding = self.default_encoder.encode(self.test_text)
        
        # Check that the norm is approximately 1
        norm = np.linalg.norm(embedding)
        self.assertAlmostEqual(norm, 1.0, places=6)
        
        # Check all vectors in a batch are normalized
        batch_embeddings = self.default_encoder.encode_batch(self.test_batch)
        for embedding in batch_embeddings:
            norm = np.linalg.norm(embedding)
            self.assertAlmostEqual(norm, 1.0, places=6)
    
    def test_encode_batch_consistency(self):
        """Test that batch encoding gives the same results as individual encoding."""
        print("Testing batch encoding consistency")
        
        # Encode individually
        individual_embeddings = [
            self.default_encoder.encode(text) for text in self.test_batch
        ]
        
        # Encode as batch
        batch_embeddings = self.default_encoder.encode_batch(self.test_batch)
        
        # Check dimensions match
        self.assertEqual(batch_embeddings.shape, (len(self.test_batch), 128))
        
        # Check individual embeddings match batch results
        for i, individual in enumerate(individual_embeddings):
            np.testing.assert_array_equal(individual, batch_embeddings[i])
    
    def test_deterministic_encoding(self):
        """Test that encoding is deterministic (same input gives same output)."""
        print("Testing deterministic encoding")
        
        # Encode the same text twice
        embedding1 = self.default_encoder.encode(self.test_text)
        embedding2 = self.default_encoder.encode(self.test_text)
        
        # Check they're identical
        np.testing.assert_array_equal(embedding1, embedding2)
        
        # Encode batch twice
        batch1 = self.default_encoder.encode_batch(self.test_batch)
        batch2 = self.default_encoder.encode_batch(self.test_batch)
        
        # Check they're identical
        np.testing.assert_array_equal(batch1, batch2)
    
    def test_different_texts(self):
        """Test that different texts produce different embeddings."""
        print("Testing different texts produce different embeddings")
        
        text1 = "This is the first text."
        text2 = "This is the second text."
        text3 = "This is completely different."
        
        # Encode different texts
        embedding1 = self.default_encoder.encode(text1)
        embedding2 = self.default_encoder.encode(text2)
        embedding3 = self.default_encoder.encode(text3)
        
        # Check they're different
        self.assertFalse(np.array_equal(embedding1, embedding2))
        self.assertFalse(np.array_equal(embedding1, embedding3))
        self.assertFalse(np.array_equal(embedding2, embedding3))
        
        # But similar texts should be closer than very different ones
        similarity1_2 = np.dot(embedding1, embedding2)  # Similar texts
        similarity1_3 = np.dot(embedding1, embedding3)  # More different
        
        # First and second should be more similar than first and third
        self.assertGreater(similarity1_2, similarity1_3)
    
    def test_empty_input(self):
        """Test handling of empty text input."""
        print("Testing empty input handling")
        
        # Encode empty string
        empty_embedding = self.default_encoder.encode("")
        
        # Should be zeros
        expected = np.zeros(128)
        np.testing.assert_array_equal(empty_embedding, expected)
        
        # Batch with empty string
        mixed_batch = ["Normal text", "", "More normal text"]
        mixed_embeddings = self.default_encoder.encode_batch(mixed_batch)
        
        # Check second embedding is zeros
        np.testing.assert_array_equal(mixed_embeddings[1], expected)
    
    def test_very_short_text(self):
        """Test encoding very short text."""
        print("Testing very short text encoding")
        
        # Single character
        char_embedding = self.default_encoder.encode("a")
        self.assertEqual(char_embedding.shape, (128,))
        self.assertAlmostEqual(np.linalg.norm(char_embedding), 1.0, places=6)
        
        # Two characters
        two_char_embedding = self.default_encoder.encode("ab")
        self.assertEqual(two_char_embedding.shape, (128,))
        
        # They should be different
        self.assertFalse(np.array_equal(char_embedding, two_char_embedding))


# If SentenceTransformer is available, test it too
try:
    from vector_db.encoders import SentenceTransformerEncoder
    
    class TestSentenceTransformerEncoder(unittest.TestCase):
        """Test the SentenceTransformerEncoder class functionality."""
        
        @classmethod
        def setUpClass(cls):
            """Set up the encoder once for all tests."""
            try:
                cls.encoder = SentenceTransformerEncoder(model_name="all-MiniLM-L6-v2")
                cls.dimension = cls.encoder.model.get_sentence_embedding_dimension()
                cls.skip_tests = False
                print("SentenceTransformerEncoder available for testing")
            except Exception as e:
                print(f"SentenceTransformerEncoder not available: {e}")
                cls.skip_tests = True
        
        def setUp(self):
            """Set up test data."""
            if self.skip_tests:
                self.skipTest("SentenceTransformerEncoder not available")
            
            self.test_text = "This is a test sentence for encoding."
            self.test_batch = [
                "First test sentence.",
                "Second test sentence, a bit longer.",
                "Third and final test sentence with some additional text."
            ]
        
        def test_encoder_dimensions(self):
            """Test that encoder produces vectors with the correct dimensions."""
            print("Testing SentenceTransformer encoder dimensions")
            
            # Check encoder dimension
            embedding = self.encoder.encode(self.test_text)
            self.assertEqual(embedding.shape, (self.dimension,))
            
            # Check batch dimensions
            batch_embeddings = self.encoder.encode_batch(self.test_batch)
            self.assertEqual(batch_embeddings.shape, (len(self.test_batch), self.dimension))
        
        def test_semantic_similarity(self):
            """Test that semantically similar texts have similar embeddings."""
            print("Testing semantic similarity")
            
            # Similar texts
            text1 = "The cat sits on the mat."
            text2 = "A feline is resting on a rug."
            
            # Different text
            text3 = "Python is a popular programming language."
            
            # Encode texts
            embedding1 = self.encoder.encode(text1)
            embedding2 = self.encoder.encode(text2)
            embedding3 = self.encoder.encode(text3)
            
            # Calculate similarities (dot product of normalized vectors)
            similarity1_2 = np.dot(embedding1, embedding2)
            similarity1_3 = np.dot(embedding1, embedding3)
            
            # Similar texts should have higher similarity
            self.assertGreater(similarity1_2, similarity1_3)
        
        def test_empty_input(self):
            """Test handling of empty text input."""
            print("Testing empty input handling for SentenceTransformer")
            
            # Encode empty string
            empty_embedding = self.encoder.encode("")
            
            # Should be zeros
            expected = np.zeros(self.dimension)
            np.testing.assert_array_equal(empty_embedding, expected)
            
            # Batch with empty string
            mixed_batch = ["Normal text", "", "More normal text"]
            mixed_embeddings = self.encoder.encode_batch(mixed_batch)
            
            # Check second embedding is zeros
            np.testing.assert_array_equal(mixed_embeddings[1], expected)

except ImportError:
    print("Skipping SentenceTransformerEncoder tests")


if __name__ == "__main__":
    unittest.main()
