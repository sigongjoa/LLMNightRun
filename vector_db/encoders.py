"""
Encoders for converting text to vector embeddings.
"""

import os
import numpy as np
from typing import List, Optional, Dict, Any, Union
from abc import ABC, abstractmethod

# 디버그용 로그 출력 설정
DEBUG = True

class Encoder(ABC):
    """
    Abstract base class for text encoders.
    """
    @abstractmethod
    def encode(self, text: str) -> np.ndarray:
        """
        Encode text into a vector representation.
        
        Args:
            text: The text to encode
            
        Returns:
            Vector embedding as numpy array
        """
        pass
    
    @abstractmethod
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Encode multiple texts into vector representations.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            Array of vector embeddings
        """
        pass


class DefaultEncoder(Encoder):
    """
    Default encoder that uses a simple character-level approach.
    This is a placeholder for when no proper embedding model is available.
    In production, this should be replaced with a proper embedding model.
    """
    def __init__(self, dimension: int = 768):
        """
        Initialize the default encoder.
        
        Args:
            dimension: Dimension of the output vectors
        """
        self.dimension = dimension
        if DEBUG:
            print(f"Initialized DefaultEncoder with dimension {dimension}")
    
    def encode(self, text: str) -> np.ndarray:
        """
        Encode text using a deterministic hashing approach.
        
        Args:
            text: The text to encode
            
        Returns:
            Vector embedding
        """
        if not text:
            if DEBUG:
                print("Warning: Encoding empty text")
            # Return zero vector for empty text
            return np.zeros(self.dimension)
        
        # Use a simple hash-based approach to generate a vector
        # This is NOT a proper embedding model, just a placeholder
        hash_values = []
        
        # Use character n-grams for a more stable representation
        for i in range(len(text) - 2):
            ngram = text[i:i+3]
            # Simple hash
            hash_val = hash(ngram) % 10000
            hash_values.append(hash_val)
        
        # Ensure we have some values
        if not hash_values:
            hash_values = [hash(text) % 10000]
        
        # Create a seed from the text
        seed = hash(text) % 2**32
        np.random.seed(seed)
        
        # Generate a random vector with the seed
        vector = np.random.randn(self.dimension)
        
        # Normalize the vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        if DEBUG:
            print(f"Encoded text of length {len(text)} -> vector shape {vector.shape}")
            
        return vector
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Encode multiple texts into vector representations.
        
        Args:
            texts: List of texts to encode
            
        Returns:
            Array of vector embeddings
        """
        return np.array([self.encode(text) for text in texts])


try:
    # Try to import SentenceTransformer for better embeddings
    from sentence_transformers import SentenceTransformer
    
    class SentenceTransformerEncoder(Encoder):
        """
        Encoder using SentenceTransformer models for high-quality embeddings.
        """
        def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
            """
            Initialize the SentenceTransformer encoder.
            
            Args:
                model_name: Name of the model to use
            """
            self.model_name = model_name
            self.model = SentenceTransformer(model_name)
            
            if DEBUG:
                print(f"Initialized SentenceTransformerEncoder using model: {model_name}")
        
        def encode(self, text: str) -> np.ndarray:
            """Encode a single text."""
            if not text:
                # Return zero vector for empty text
                return np.zeros(self.model.get_sentence_embedding_dimension())
            
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            if DEBUG:
                print(f"Encoded text with SentenceTransformer -> vector shape {embedding.shape}")
                
            return embedding
        
        def encode_batch(self, texts: List[str]) -> np.ndarray:
            """Encode multiple texts efficiently."""
            # Filter out empty texts
            non_empty_indices = [i for i, text in enumerate(texts) if text]
            non_empty_texts = [texts[i] for i in non_empty_indices]
            
            if not non_empty_texts:
                # All texts are empty
                return np.zeros((len(texts), self.model.get_sentence_embedding_dimension()))
            
            # Encode non-empty texts
            embeddings = self.model.encode(non_empty_texts, convert_to_numpy=True)
            
            # Create result array with zeros for empty texts
            result = np.zeros((len(texts), self.model.get_sentence_embedding_dimension()))
            
            # Fill in embeddings for non-empty texts
            for i, embedding in zip(non_empty_indices, embeddings):
                result[i] = embedding
                
            return result

except ImportError:
    if DEBUG:
        print("SentenceTransformer not available, using DefaultEncoder only")
