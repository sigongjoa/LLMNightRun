"""
Embedding models for vector representation of text.
"""
import os
import logging
from typing import List, Optional, Dict, Any, Union
from abc import ABC, abstractmethod

import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""
    
    @abstractmethod
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Convert text to vector embeddings.
        
        Args:
            texts: Single text or list of texts to embed
            
        Returns:
            Numpy array of embeddings
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of embeddings produced by this model."""
        pass
    
    def batch_embed(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Embed texts in batches to avoid memory issues.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process in each batch
            
        Returns:
            Numpy array of embeddings
        """
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.embed(batch)
            results.append(batch_embeddings)
            
        return np.vstack(results) if results else np.array([])


class SentenceTransformerEmbeddings(EmbeddingModel):
    """Embedding model using Sentence Transformers."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize with specified model name.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        logger.info(f"Initialized SentenceTransformer with model: {model_name}")
        
    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Convert text to vector embeddings.
        
        Args:
            texts: Single text or list of texts to embed
            
        Returns:
            Numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
            
        # Generate embeddings
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return zero embeddings as fallback
            return np.zeros((len(texts), self.dimension))
    
    @property
    def dimension(self) -> int:
        """Return the dimension of embeddings produced by this model."""
        return self.model.get_sentence_embedding_dimension()


def get_embedding_model(model_name: Optional[str] = None) -> EmbeddingModel:
    """Factory function to get an embedding model.
    
    Args:
        model_name: Optional name of embedding model to use
        
    Returns:
        EmbeddingModel instance
    """
    # Default to SentenceTransformer if none specified
    if not model_name:
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
    # Create appropriate embedding model based on name
    if model_name.startswith("sentence-transformers/"):
        return SentenceTransformerEmbeddings(model_name)
    else:
        # Default fallback
        return SentenceTransformerEmbeddings(model_name)
