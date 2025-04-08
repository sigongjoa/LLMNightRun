"""
Vector database interface for storing and retrieving embeddings.
"""
import os
import json
import pickle
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
import faiss

from .embeddings import EmbeddingModel, get_embedding_model

logger = logging.getLogger(__name__)

class VectorStore(ABC):
    """Abstract base class for vector storage backends."""
    
    @abstractmethod
    def add(self, texts: List[str], embeddings: Optional[np.ndarray] = None, 
            metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Add texts and their embeddings to the vector store.
        
        Args:
            texts: List of text to store
            embeddings: Optional pre-computed embeddings
            metadatas: Optional metadata for each text
            
        Returns:
            List of IDs for the added texts
        """
        pass
    
    @abstractmethod
    def search(self, query: str, embedding: Optional[np.ndarray] = None, 
              top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar texts in the vector store.
        
        Args:
            query: Query text
            embedding: Optional pre-computed query embedding
            top_k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of dictionaries containing id, text, metadata, and score
        """
        pass
    
    @abstractmethod
    def get(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Get texts and metadata by IDs.
        
        Args:
            ids: List of IDs to retrieve
            
        Returns:
            List of dictionaries containing id, text, and metadata
        """
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete texts by IDs.
        
        Args:
            ids: List of IDs to delete
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all data from the vector store."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Return the number of items in the vector store."""
        pass


class FAISSVectorStore(VectorStore):
    """Vector store using FAISS for efficient similarity search."""
    
    def __init__(self, embedding_model: Optional[EmbeddingModel] = None, 
                 index_path: Optional[str] = None):
        """Initialize FAISS vector store.
        
        Args:
            embedding_model: Model for generating embeddings
            index_path: Path to load existing index
        """
        # Initialize embedding model
        self.embedding_model = embedding_model or get_embedding_model()
        
        # We'll store metadata and texts in memory with IDs as keys
        self.texts = {}  # id -> text
        self.metadata = {}  # id -> metadata dict
        self.id_to_index = {}  # id -> index in FAISS
        self.index_to_id = {}  # index in FAISS -> id
        self.next_id = 0
        
        # Create or load FAISS index
        self.dimension = self.embedding_model.dimension
        if index_path and os.path.exists(index_path):
            self._load(index_path)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index_path = index_path
            
        logger.info(f"Initialized FAISS vector store with dimension: {self.dimension}")
    
    def _load(self, path: str) -> None:
        """Load FAISS index and metadata from disk.
        
        Args:
            path: Path to the index directory
        """
        index_file = os.path.join(path, "faiss.index")
        metadata_file = os.path.join(path, "metadata.pkl")
        
        if os.path.exists(index_file) and os.path.exists(metadata_file):
            try:
                # Load FAISS index
                self.index = faiss.read_index(index_file)
                
                # Load metadata
                with open(metadata_file, 'rb') as f:
                    data = pickle.load(f)
                    self.texts = data.get('texts', {})
                    self.metadata = data.get('metadata', {})
                    self.id_to_index = data.get('id_to_index', {})
                    self.index_to_id = data.get('index_to_id', {})
                    self.next_id = data.get('next_id', 0)
                
                logger.info(f"Loaded FAISS index from {path} with {self.count()} items")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {str(e)}")
                # Initialize a new index
                self.index = faiss.IndexFlatL2(self.dimension)
                self.texts = {}
                self.metadata = {}
                self.id_to_index = {}
                self.index_to_id = {}
                self.next_id = 0
        else:
            logger.warning(f"Index files not found at {path}, initializing new index")
            self.index = faiss.IndexFlatL2(self.dimension)
        
        self.index_path = path
    
    def _save(self) -> None:
        """Save FAISS index and metadata to disk."""
        if not self.index_path:
            return
            
        os.makedirs(self.index_path, exist_ok=True)
        index_file = os.path.join(self.index_path, "faiss.index")
        metadata_file = os.path.join(self.index_path, "metadata.pkl")
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, index_file)
            
            # Save metadata
            with open(metadata_file, 'wb') as f:
                pickle.dump({
                    'texts': self.texts,
                    'metadata': self.metadata,
                    'id_to_index': self.id_to_index,
                    'index_to_id': self.index_to_id,
                    'next_id': self.next_id
                }, f)
                
            logger.info(f"Saved FAISS index to {self.index_path}")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
            
    def add(self, texts: List[str], embeddings: Optional[np.ndarray] = None, 
            metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Add texts and their embeddings to the vector store.
        
        Args:
            texts: List of text to store
            embeddings: Optional pre-computed embeddings
            metadatas: Optional metadata for each text
            
        Returns:
            List of IDs for the added texts
        """
        # Generate embeddings if not provided
        if embeddings is None:
            embeddings = self.embedding_model.batch_embed(texts)
        
        # Ensure metadatas is a list of dicts
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # Add timestamp to metadata
        timestamp = int(time.time())
        for metadata in metadatas:
            metadata['timestamp'] = metadata.get('timestamp', timestamp)
        
        # Generate IDs
        ids = [f"mem_{self.next_id + i}" for i in range(len(texts))]
        
        # Add to FAISS index
        start_idx = self.index.ntotal
        self.index.add(embeddings.astype(np.float32))
        
        # Update mappings
        for i, (id_, text, metadata) in enumerate(zip(ids, texts, metadatas)):
            idx = start_idx + i
            self.texts[id_] = text
            self.metadata[id_] = metadata
            self.id_to_index[id_] = idx
            self.index_to_id[idx] = id_
        
        self.next_id += len(texts)
        
        # Save to disk
        self._save()
        
        return ids
    
    def search(self, query: str, embedding: Optional[np.ndarray] = None, 
              top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar texts in the vector store.
        
        Args:
            query: Query text
            embedding: Optional pre-computed query embedding
            top_k: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of dictionaries containing id, text, metadata, and score
        """
        if self.count() == 0:
            return []
            
        # Generate embedding if not provided
        if embedding is None:
            embedding = self.embedding_model.embed(query)
            
        if len(embedding.shape) == 1:
            embedding = embedding.reshape(1, -1)
            
        # Increase top_k if filtering to ensure we get enough results
        search_k = top_k
        if filter_metadata:
            search_k = min(top_k * 10, self.count())  # Get more results for filtering
            
        # Search in FAISS
        embedding = embedding.astype(np.float32)
        distances, indices = self.index.search(embedding, search_k)
        
        # Convert to results
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= self.index.ntotal:  # Invalid index
                continue
                
            id_ = self.index_to_id.get(idx)
            if not id_:
                continue
                
            text = self.texts.get(id_)
            metadata = self.metadata.get(id_, {})
            
            # Apply metadata filter
            if filter_metadata:
                if not self._matches_filter(metadata, filter_metadata):
                    continue
            
            # Convert distance to similarity score (higher is more similar)
            score = 1.0 / (1.0 + distance)
            
            results.append({
                'id': id_,
                'text': text,
                'metadata': metadata,
                'score': float(score)
            })
            
            if len(results) >= top_k:
                break
                
        return results
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_: Dict[str, Any]) -> bool:
        """Check if metadata matches the filter.
        
        Args:
            metadata: Metadata to check
            filter_: Filter to apply
            
        Returns:
            True if metadata matches filter
        """
        for key, value in filter_.items():
            if key not in metadata:
                return False
                
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            elif metadata[key] != value:
                return False
                
        return True
    
    def get(self, ids: List[str]) -> List[Dict[str, Any]]:
        """Get texts and metadata by IDs.
        
        Args:
            ids: List of IDs to retrieve
            
        Returns:
            List of dictionaries containing id, text, and metadata
        """
        results = []
        
        for id_ in ids:
            if id_ in self.texts:
                results.append({
                    'id': id_,
                    'text': self.texts[id_],
                    'metadata': self.metadata.get(id_, {})
                })
                
        return results
    
    def delete(self, ids: List[str]) -> None:
        """Delete texts by IDs.
        
        Args:
            ids: List of IDs to delete
        """
        # FAISS doesn't support direct deletion, so we need to rebuild the index
        to_delete_indices = set()
        for id_ in ids:
            if id_ in self.id_to_index:
                to_delete_indices.add(self.id_to_index[id_])
                del self.id_to_index[id_]
                self.texts.pop(id_, None)
                self.metadata.pop(id_, None)
        
        if not to_delete_indices:
            return  # Nothing to delete
            
        # Extract all vectors to keep
        all_vectors = []
        new_index_to_id = {}
        id_to_new_index = {}
        
        for i in range(self.index.ntotal):
            if i not in to_delete_indices:
                id_ = self.index_to_id.get(i)
                if id_:
                    # Get vector at this index
                    vector = np.zeros((1, self.dimension), dtype=np.float32)
                    faiss.extract_rows(self.index, i, 1, vector)
                    all_vectors.append(vector.reshape(-1))
                    
                    # Update mappings
                    new_idx = len(all_vectors) - 1
                    new_index_to_id[new_idx] = id_
                    id_to_new_index[id_] = new_idx
        
        # Create new index and add vectors
        new_index = faiss.IndexFlatL2(self.dimension)
        if all_vectors:
            vectors_array = np.vstack(all_vectors).astype(np.float32)
            new_index.add(vectors_array)
        
        # Update instance variables
        self.index = new_index
        self.index_to_id = new_index_to_id
        self.id_to_index = id_to_new_index
        
        # Save changes
        self._save()
    
    def clear(self) -> None:
        """Clear all data from the vector store."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.texts = {}
        self.metadata = {}
        self.id_to_index = {}
        self.index_to_id = {}
        self.next_id = 0
        self._save()
    
    def count(self) -> int:
        """Return the number of items in the vector store."""
        return self.index.ntotal


def get_vector_store(
    store_type: str = "faiss", 
    embedding_model: Optional[EmbeddingModel] = None,
    vector_store_path: Optional[str] = None,
    use_ivf_index: bool = True,
    max_memory_days: Optional[int] = 90
) -> VectorStore:
    """Factory function to get a vector store based on type.
    
    Args:
        store_type: Type of vector store ('faiss')
        embedding_model: Optional embedding model to use
        vector_store_path: Optional path to vector store files
        use_ivf_index: Whether to use IVF index for better performance
        max_memory_days: Maximum age of memories in days, None for no limit
        
    Returns:
        VectorStore instance
    """
    # Use default path if not provided
    if not vector_store_path:
        vector_store_path = get_vector_store_directory(store_type)
    
    # Create embedding model if not provided
    if not embedding_model:
        embedding_model = get_embedding_model()
    
    # Create vector store based on type
    if store_type.lower() == "faiss":
        return FAISSVectorStore(
            embedding_model=embedding_model, 
            index_path=vector_store_path,
            use_ivf_index=use_ivf_index,
            max_memory_days=max_memory_days
        )
    else:
        logger.warning(f"Unknown vector store type: {store_type}, falling back to FAISS")
        return FAISSVectorStore(
            embedding_model=embedding_model, 
            index_path=vector_store_path,
            use_ivf_index=use_ivf_index,
            max_memory_days=max_memory_days
        )
