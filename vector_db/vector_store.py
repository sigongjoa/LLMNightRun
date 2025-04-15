"""
Vector Database implementation for document storage and retrieval.
"""

import os
import json
import uuid
import numpy as np
import pickle
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path

from .encoders import DefaultEncoder, Encoder

# 디버그용 로그 출력 설정
DEBUG = True

class Document:
    """
    Document class to store text and metadata.
    """
    def __init__(self, 
                 text: str, 
                 metadata: Optional[Dict[str, Any]] = None, 
                 id: Optional[str] = None):
        """
        Initialize a document object.
        
        Args:
            text: The document text
            metadata: Optional metadata dictionary
            id: Optional document ID (will be generated if not provided)
        """
        self.text = text
        self.metadata = metadata or {}
        self.id = id or str(uuid.uuid4())
        self.embedding = None
        self.created_at = datetime.now().isoformat()
        
        if DEBUG:
            print(f"Document created: ID={self.id}, Text length={len(self.text)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "metadata": self.metadata,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create document from dictionary."""
        doc = cls(
            text=data["text"],
            metadata=data["metadata"],
            id=data["id"]
        )
        doc.created_at = data.get("created_at", datetime.now().isoformat())
        return doc

    def __repr__(self) -> str:
        return f"Document(id={self.id}, text='{self.text[:30]}...', metadata={self.metadata})"


class VectorDB:
    """
    Vector database for storing and retrieving documents based on semantic similarity.
    """
    def __init__(self, 
                 encoder: Optional[Encoder] = None,
                 storage_dir: Optional[str] = None):
        """
        Initialize the vector database.
        
        Args:
            encoder: The encoder to use for converting text to vectors
            storage_dir: Directory to persist the database (if None, in-memory only)
        """
        self.encoder = encoder or DefaultEncoder()
        self.storage_dir = storage_dir
        
        # Initialize storage
        self.documents: Dict[str, Document] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        
        if DEBUG:
            print(f"VectorDB initialized with encoder: {self.encoder.__class__.__name__}")
            print(f"Storage directory: {self.storage_dir or 'In-memory only'}")
        
        # If storage directory is provided, ensure it exists
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
            
            # Try to load existing data
            self._load_if_exists()
    
    def add(self, document: Union[Document, str], metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a document to the database.
        
        Args:
            document: The document or text to add
            metadata: Metadata if document is a string
            
        Returns:
            Document ID
        """
        # Handle string input
        if isinstance(document, str):
            document = Document(text=document, metadata=metadata or {})
        
        # Encode the document
        document.embedding = self.encoder.encode(document.text)
        
        # Store the document and its embedding
        self.documents[document.id] = document
        self.embeddings[document.id] = document.embedding
        
        if DEBUG:
            print(f"Added document: ID={document.id}, Embedding shape={document.embedding.shape}")
        
        # Persist to disk if storage_dir is set
        if self.storage_dir:
            self._save()
        
        return document.id
    
    def add_batch(self, documents: List[Union[Document, str]], 
                 metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Add multiple documents in batch.
        
        Args:
            documents: List of documents or strings
            metadatas: List of metadata dictionaries (when documents are strings)
            
        Returns:
            List of document IDs
        """
        if metadatas is None:
            metadatas = [{} for _ in documents]
        
        doc_ids = []
        for i, doc in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            doc_id = self.add(doc, metadata)
            doc_ids.append(doc_id)
        
        return doc_ids
    
    def search(self, 
              query: str, 
              k: int = 5, 
              threshold: Optional[float] = None,
              filter_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[Document, float]]:
        """
        Search for similar documents.
        
        Args:
            query: The search query
            k: Number of results to return
            threshold: Similarity threshold (0-1), if None, return top k
            filter_metadata: Filter results by metadata
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.documents:
            if DEBUG:
                print("Search called on empty database")
            return []
        
        # Encode the query
        query_embedding = self.encoder.encode(query)
        
        # Calculate similarities
        similarities = []
        for doc_id, embedding in self.embeddings.items():
            # Apply metadata filter if provided
            if filter_metadata and not self._matches_filter(self.documents[doc_id], filter_metadata):
                continue
            
            similarity = self._calculate_similarity(query_embedding, embedding)
            similarities.append((doc_id, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Apply threshold if provided
        if threshold is not None:
            similarities = [(doc_id, score) for doc_id, score in similarities if score >= threshold]
        
        # Return top k results
        result = [(self.documents[doc_id], score) for doc_id, score in similarities[:k]]
        
        if DEBUG:
            print(f"Search for '{query[:30]}...' returned {len(result)} results")
            for doc, score in result[:3]:  # Print top 3 for debugging
                print(f"  - Score: {score:.4f}, Doc: {doc.text[:50]}...")
        
        return result
    
    def get(self, doc_id: str) -> Optional[Document]:
        """Retrieve a document by ID."""
        return self.documents.get(doc_id)
    
    def delete(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.embeddings[doc_id]
            
            if self.storage_dir:
                self._save()
                
            if DEBUG:
                print(f"Deleted document ID={doc_id}")
                
            return True
        return False
    
    def update(self, doc_id: str, 
              text: Optional[str] = None, 
              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update a document's text or metadata.
        
        Args:
            doc_id: Document ID
            text: New text (if None, keep existing)
            metadata: New metadata (if None, keep existing)
            
        Returns:
            Success flag
        """
        if doc_id not in self.documents:
            return False
        
        doc = self.documents[doc_id]
        
        # Update text if provided
        if text is not None:
            doc.text = text
            # Re-encode
            doc.embedding = self.encoder.encode(text)
            self.embeddings[doc_id] = doc.embedding
        
        # Update metadata if provided
        if metadata is not None:
            doc.metadata = metadata
        
        if self.storage_dir:
            self._save()
            
        if DEBUG:
            print(f"Updated document ID={doc_id}")
            
        return True
    
    def clear(self) -> None:
        """Clear all documents from the database."""
        self.documents.clear()
        self.embeddings.clear()
        
        if self.storage_dir:
            self._save()
            
        if DEBUG:
            print("Cleared all documents from database")
    
    def count(self) -> int:
        """Return the number of documents in the database."""
        return len(self.documents)
    
    def list_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """List documents with pagination."""
        return list(self.documents.values())[offset:offset+limit]
    
    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between vectors."""
        # Normalize the vectors
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2)
        
        # Calculate cosine similarity
        return float(np.dot(vec1_norm, vec2_norm))
    
    def _matches_filter(self, doc: Document, filter_dict: Dict[str, Any]) -> bool:
        """Check if document matches the metadata filter."""
        for key, value in filter_dict.items():
            if key not in doc.metadata or doc.metadata[key] != value:
                return False
        return True
    
    def _save(self) -> None:
        """Save the database to disk."""
        if not self.storage_dir:
            return
        
        # Save metadata and document text separately from embeddings
        docs_path = os.path.join(self.storage_dir, "documents.json")
        embeddings_path = os.path.join(self.storage_dir, "embeddings.pkl")
        
        # Save documents as JSON
        docs_data = {doc_id: doc.to_dict() for doc_id, doc in self.documents.items()}
        with open(docs_path, "w", encoding="utf-8") as f:
            json.dump(docs_data, f, ensure_ascii=False, indent=2)
        
        # Save embeddings with pickle (numpy arrays)
        with open(embeddings_path, "wb") as f:
            pickle.dump(self.embeddings, f)
            
        if DEBUG:
            print(f"Saved {len(self.documents)} documents to {self.storage_dir}")
    
    def _load_if_exists(self) -> None:
        """Load database if files exist."""
        docs_path = os.path.join(self.storage_dir, "documents.json")
        embeddings_path = os.path.join(self.storage_dir, "embeddings.pkl")
        
        # Check if both files exist
        if not (os.path.exists(docs_path) and os.path.exists(embeddings_path)):
            return
        
        try:
            # Load documents
            with open(docs_path, "r", encoding="utf-8") as f:
                docs_data = json.load(f)
                
            for doc_id, doc_dict in docs_data.items():
                self.documents[doc_id] = Document.from_dict(doc_dict)
            
            # Load embeddings
            with open(embeddings_path, "rb") as f:
                self.embeddings = pickle.load(f)
                
            if DEBUG:
                print(f"Loaded {len(self.documents)} documents from {self.storage_dir}")
                
        except Exception as e:
            if DEBUG:
                print(f"Error loading database: {str(e)}")
