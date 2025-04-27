"""
VectorStore manages document embeddings and provides vector-based similarity search.
"""

import os
import json
import logging
import time
import pickle
import numpy as np
from typing import Dict, List, Optional, Union, Any

# DO NOT CHANGE CODE: Core vector store functionality
# TEMP: Current implementation works but will be refactored later

class VectorStore:
    def __init__(self, vector_dir: str = None):
        """
        Initialize the VectorStore with the directory to store vector indices.
        
        Args:
            vector_dir: Directory to store vector indices
        """
        self.vector_dir = vector_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "vectors")
        
        # Ensure vector directory exists
        os.makedirs(self.vector_dir, exist_ok=True)
        
        # Dictionary to cache loaded indices
        self.indices = {}
        
        # Mock embeddings for demonstration (in a real implementation, this would use a proper embedding model)
        self.mock_embedding_dim = 384
    
    def _get_index_path(self, collection_id: str) -> str:
        """
        Get the path to the index file for a collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            Path to the index file
        """
        return os.path.join(self.vector_dir, f"{collection_id}_index.pkl")
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get the embedding vector for a text.
        
        Args:
            text: Text to get embedding for
            
        Returns:
            Embedding vector as numpy array
        """
        # 실제 임베딩 모델 사용 시도
        try:
            # 문서 컨텐츠가 너무 긴 경우를 대비한 처리
            # 임베딩 해야 할 텍스트가 너무 긴 경우, 일부만 사용
            max_text_length = 8192  # 최대 길이 제한
            if len(text) > max_text_length:
                # 긴 텍스트를 잘라서 처리
                # 앞부분 1/3, 중앙 1/3, 뒤부분 1/3으로 나누어서 샘플링
                part_length = max_text_length // 3
                prefix = text[:part_length]
                middle = text[len(text)//2 - part_length//2:len(text)//2 + part_length//2]
                suffix = text[-part_length:]
                text = prefix + middle + suffix
            
            # sentence-transformers를 사용하여 실제 임베딩 생성
            try:
                from sentence_transformers import SentenceTransformer
                
                # 모델이 로드되지 않았다면 초기화
                if not hasattr(self, 'embedding_model'):
                    # 경량화된 임베딩 모델 사용
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    # 기존 mock_embedding_dim 정보 업데이트
                    self.mock_embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
                    logging.info(f"Loaded sentence-transformers embedding model with dimension {self.mock_embedding_dim}")
                
                # 텍스트 임베딩 생성
                embedding = self.embedding_model.encode(text, convert_to_numpy=True)
                
                # 정규화
                embedding = embedding / np.linalg.norm(embedding)
                
                return embedding
            except ImportError:
                logging.warning("sentence-transformers not installed. Falling back to mock embeddings.")
                # 실패하면 목업 임베딩으로 돌아감
        except Exception as e:
            logging.error(f"Error generating embedding: {e}. Using mock embedding.")
        
        # 실패 시 mock embedding 사용
        # 일관성을 위해 동일한 텍스트에 대해 동일한 임베딩을 생성하는 로직 유지
        seed = sum(ord(c) for c in text[:1000])  # 성능을 위해 처음 1000자만 사용
        np.random.seed(seed)
        
        # 목업 임베딩 생성
        embedding = np.random.randn(self.mock_embedding_dim)
        
        # 정규화
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding
    
    def index_documents(self, collection_id: str, documents: List[Dict]) -> bool:
        """
        Index documents for a collection.
        
        Args:
            collection_id: ID of the collection
            documents: List of documents to index
            
        Returns:
            True if indexing was successful, False otherwise
        """
        try:
            # Create index dictionary
            index = {
                "embeddings": {},
                "updated_at": time.time()
            }
            
            # Generate embeddings for each document
            for document in documents:
                document_id = document.get("id")
                
                # Skip documents without ID or content
                if not document_id or "content" not in document:
                    continue
                
                # Get embedding for document content
                content = document.get("content", "")
                if content:
                    embedding = self._get_embedding(content)
                    index["embeddings"][document_id] = embedding
            
            # Save index to disk
            index_path = self._get_index_path(collection_id)
            with open(index_path, 'wb') as f:
                pickle.dump(index, f)
            
            # Update cache
            self.indices[collection_id] = index
            
            return True
        except Exception as e:
            logging.error(f"Error indexing documents for collection {collection_id}: {e}")
            return False
    
    def _load_index(self, collection_id: str) -> Optional[Dict]:
        """
        Load the index for a collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            Index dictionary or None if not found
        """
        # Check if index is already loaded
        if collection_id in self.indices:
            return self.indices[collection_id]
        
        # Load index from disk
        index_path = self._get_index_path(collection_id)
        if not os.path.exists(index_path):
            return None
        
        try:
            with open(index_path, 'rb') as f:
                index = pickle.load(f)
            
            # Cache index
            self.indices[collection_id] = index
            
            return index
        except Exception as e:
            logging.error(f"Error loading index for collection {collection_id}: {e}")
            return None
    
    def search(self, collection_id: str, query: str, limit: int = 5) -> List[str]:
        """
        Search for documents in a collection by similarity to a query.
        
        Args:
            collection_id: ID of the collection to search in
            query: Query text to search for
            limit: Maximum number of results to return
            
        Returns:
            List of document IDs sorted by relevance
        """
        try:
            # Load index
            index = self._load_index(collection_id)
            if not index or "embeddings" not in index:
                return []
            
            # Get embedding for query
            query_embedding = self._get_embedding(query)
            
            # Calculate similarity scores
            similarities = {}
            for doc_id, embedding in index["embeddings"].items():
                # Calculate cosine similarity
                similarity = np.dot(query_embedding, embedding)
                similarities[doc_id] = similarity
            
            # Sort by similarity (descending)
            sorted_docs = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
            
            # Return top results
            return [doc_id for doc_id, _ in sorted_docs[:limit]]
        except Exception as e:
            logging.error(f"Error searching in collection {collection_id}: {e}")
            return []
    
    def delete_index(self, collection_id: str) -> bool:
        """
        Delete the index for a collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Remove from cache
            if collection_id in self.indices:
                del self.indices[collection_id]
            
            # Delete index file
            index_path = self._get_index_path(collection_id)
            if os.path.exists(index_path):
                os.remove(index_path)
            
            return True
        except Exception as e:
            logging.error(f"Error deleting index for collection {collection_id}: {e}")
            return False
    
    def get_embedding_for_text(self, text: str) -> List[float]:
        """
        Get the embedding vector for a text.
        
        Args:
            text: Text to get embedding for
            
        Returns:
            Embedding vector as list of floats
        """
        embedding = self._get_embedding(text)
        return embedding.tolist()
    
    def add_document_to_index(self, collection_id: str, document_id: str, text: str) -> bool:
        """
        Add a single document to an existing index.
        
        Args:
            collection_id: ID of the collection
            document_id: ID of the document
            text: Text content of the document
            
        Returns:
            True if addition was successful, False otherwise
        """
        try:
            # Load index
            index = self._load_index(collection_id)
            if not index:
                return False
            
            # Generate embedding
            embedding = self._get_embedding(text)
            
            # Add to index
            index["embeddings"][document_id] = embedding
            index["updated_at"] = time.time()
            
            # Save index
            index_path = self._get_index_path(collection_id)
            with open(index_path, 'wb') as f:
                pickle.dump(index, f)
            
            # Update cache
            self.indices[collection_id] = index
            
            return True
        except Exception as e:
            logging.error(f"Error adding document {document_id} to index for collection {collection_id}: {e}")
            return False
    
    def remove_document_from_index(self, collection_id: str, document_id: str) -> bool:
        """
        Remove a document from an existing index.
        
        Args:
            collection_id: ID of the collection
            document_id: ID of the document
            
        Returns:
            True if removal was successful, False otherwise
        """
        try:
            # Load index
            index = self._load_index(collection_id)
            if not index or "embeddings" not in index:
                return False
            
            # Remove from index
            if document_id in index["embeddings"]:
                del index["embeddings"][document_id]
                index["updated_at"] = time.time()
                
                # Save index
                index_path = self._get_index_path(collection_id)
                with open(index_path, 'wb') as f:
                    pickle.dump(index, f)
                
                # Update cache
                self.indices[collection_id] = index
            
            return True
        except Exception as e:
            logging.error(f"Error removing document {document_id} from index for collection {collection_id}: {e}")
            return False
