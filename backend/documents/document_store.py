"""
DocumentStore manages document collections and provides vector search functionality.
"""

import os
import json
import logging
import time
import uuid
import shutil
from typing import Dict, List, Optional, Union, Any

# DO NOT CHANGE CODE: Core document store functionality
# TEMP: Current implementation works but will be refactored later

class DocumentStore:
    def __init__(self, docs_dir: str = None, vector_store=None):
        """
        Initialize the DocumentStore with the documents directory and vector store.
        
        Args:
            docs_dir: Directory to store document collections
            vector_store: VectorStore instance for document embeddings
        """
        self.docs_dir = docs_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "documents")
        self.collections_info_path = os.path.join(self.docs_dir, "collections_info.json")
        self.vector_store = vector_store
        
        # Ensure documents directory exists
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # Load collections information if exists
        self._load_collections_info()
    
    def _load_collections_info(self):
        """Load collections information from collections_info.json file."""
        if os.path.exists(self.collections_info_path):
            try:
                with open(self.collections_info_path, 'r', encoding='utf-8') as f:
                    self.collections = json.load(f)
            except Exception as e:
                logging.error(f"Error loading collections info: {e}")
                self.collections = {}
        else:
            self.collections = {}
            self._save_collections_info()
    
    def _save_collections_info(self):
        """Save collections information to collections_info.json file."""
        try:
            with open(self.collections_info_path, 'w', encoding='utf-8') as f:
                json.dump(self.collections, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving collections info: {e}")
    
    def create_collection(self, name: str, description: str = "") -> Dict:
        """
        Create a new document collection.
        
        Args:
            name: Name of the collection
            description: Description of the collection
            
        Returns:
            Dictionary with collection information
        """
        # Generate a collection ID
        collection_id = str(uuid.uuid4())
        
        # Create collection object
        collection = {
            "id": collection_id,
            "name": name,
            "description": description,
            "created_at": time.time(),
            "updated_at": time.time(),
            "document_count": 0,
            "index_status": "empty"
        }
        
        # Create collection directory
        collection_dir = os.path.join(self.docs_dir, collection_id)
        os.makedirs(collection_dir, exist_ok=True)
        
        # Save collection information
        self.collections[collection_id] = collection
        self._save_collections_info()
        
        return collection
    
    def get_collection(self, collection_id: str) -> Optional[Dict]:
        """
        Get information about a collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            Dictionary with collection information or None if not found
        """
        return self.collections.get(collection_id)
    
    def list_collections(self) -> List[Dict]:
        """
        List all document collections.
        
        Returns:
            List of collection information dictionaries
        """
        return list(self.collections.values())
    
    def delete_collection(self, collection_id: str) -> bool:
        """
        Delete a document collection.
        
        Args:
            collection_id: ID of the collection to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Check if collection exists
            if collection_id not in self.collections:
                return False
            
            # Delete collection directory
            collection_dir = os.path.join(self.docs_dir, collection_id)
            if os.path.exists(collection_dir):
                shutil.rmtree(collection_dir)
            
            # Remove from collections dictionary
            del self.collections[collection_id]
            self._save_collections_info()
            
            # Delete vector index if vector store is available
            if self.vector_store:
                self.vector_store.delete_index(collection_id)
            
            return True
        except Exception as e:
            logging.error(f"Error deleting collection {collection_id}: {e}")
            return False
    
    def add_document(self, collection_id: str, document: Dict) -> Optional[str]:
        """
        Add a document to a collection.
        
        Args:
            collection_id: ID of the collection to add document to
            document: Document to add (must have content field)
            
        Returns:
            ID of the added document or None if failed
        """
        try:
            # Check if collection exists
            collection = self.get_collection(collection_id)
            if not collection:
                logging.error(f"Collection {collection_id} not found")
                return None
            
            # Generate document ID if not provided
            document_id = document.get("id", str(uuid.uuid4()))
            document["id"] = document_id
            
            # Add timestamp if not provided
            if "created_at" not in document:
                document["created_at"] = time.time()
            document["updated_at"] = time.time()
            
            # Save document
            collection_dir = os.path.join(self.docs_dir, collection_id)
            document_path = os.path.join(collection_dir, f"{document_id}.json")
            
            with open(document_path, 'w', encoding='utf-8') as f:
                json.dump(document, f, indent=2)
            
            # Update collection information
            collection["document_count"] = len(self.list_documents(collection_id))
            collection["updated_at"] = time.time()
            collection["index_status"] = "needs_indexing"
            self.collections[collection_id] = collection
            self._save_collections_info()
            
            return document_id
        except Exception as e:
            logging.error(f"Error adding document to collection {collection_id}: {e}")
            return None
    
    def get_document(self, collection_id: str, document_id: str) -> Optional[Dict]:
        """
        Get a document from a collection.
        
        Args:
            collection_id: ID of the collection
            document_id: ID of the document
            
        Returns:
            Document dictionary or None if not found
        """
        try:
            # Check if collection exists
            if collection_id not in self.collections:
                return None
            
            # Get document path
            collection_dir = os.path.join(self.docs_dir, collection_id)
            document_path = os.path.join(collection_dir, f"{document_id}.json")
            
            if not os.path.exists(document_path):
                return None
            
            # Load document
            with open(document_path, 'r', encoding='utf-8') as f:
                document = json.load(f)
            
            return document
        except Exception as e:
            logging.error(f"Error getting document {document_id} from collection {collection_id}: {e}")
            return None
    
    def list_documents(self, collection_id: str) -> List[Dict]:
        """
        List all documents in a collection.
        
        Args:
            collection_id: ID of the collection
            
        Returns:
            List of document dictionaries
        """
        documents = []
        
        try:
            # Check if collection exists
            if collection_id not in self.collections:
                return documents
            
            # Get collection directory
            collection_dir = os.path.join(self.docs_dir, collection_id)
            
            # Load each document
            for filename in os.listdir(collection_dir):
                if filename.endswith(".json"):
                    document_id = os.path.splitext(filename)[0]
                    document = self.get_document(collection_id, document_id)
                    if document:
                        documents.append(document)
        except Exception as e:
            logging.error(f"Error listing documents in collection {collection_id}: {e}")
        
        # Sort by updated_at timestamp (newest first)
        documents.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        
        return documents
    
    def update_document(self, collection_id: str, document_id: str, updates: Dict) -> bool:
        """
        Update a document in a collection.
        
        Args:
            collection_id: ID of the collection
            document_id: ID of the document to update
            updates: Dictionary with fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Get current document
            document = self.get_document(collection_id, document_id)
            if not document:
                return False
            
            # Update document fields
            for key, value in updates.items():
                document[key] = value
            
            # Update timestamp
            document["updated_at"] = time.time()
            
            # Save updated document
            collection_dir = os.path.join(self.docs_dir, collection_id)
            document_path = os.path.join(collection_dir, f"{document_id}.json")
            
            with open(document_path, 'w', encoding='utf-8') as f:
                json.dump(document, f, indent=2)
            
            # Update collection status
            collection = self.get_collection(collection_id)
            collection["updated_at"] = time.time()
            collection["index_status"] = "needs_indexing"
            self.collections[collection_id] = collection
            self._save_collections_info()
            
            return True
        except Exception as e:
            logging.error(f"Error updating document {document_id} in collection {collection_id}: {e}")
            return False
    
    def delete_document(self, collection_id: str, document_id: str) -> bool:
        """
        Delete a document from a collection.
        
        Args:
            collection_id: ID of the collection
            document_id: ID of the document to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Check if collection exists
            if collection_id not in self.collections:
                return False
            
            # Get document path
            collection_dir = os.path.join(self.docs_dir, collection_id)
            document_path = os.path.join(collection_dir, f"{document_id}.json")
            
            if not os.path.exists(document_path):
                return False
            
            # Delete document file
            os.remove(document_path)
            
            # Update collection information
            collection = self.get_collection(collection_id)
            collection["document_count"] = len(self.list_documents(collection_id))
            collection["updated_at"] = time.time()
            collection["index_status"] = "needs_indexing"
            self.collections[collection_id] = collection
            self._save_collections_info()
            
            return True
        except Exception as e:
            logging.error(f"Error deleting document {document_id} from collection {collection_id}: {e}")
            return False
    
    def index_collection(self, collection_id: str) -> bool:
        """
        Index a collection for vector search.
        
        Args:
            collection_id: ID of the collection to index
            
        Returns:
            True if indexing was successful, False otherwise
        """
        if not self.vector_store:
            logging.error("No vector store available for indexing")
            return False
        
        try:
            # Check if collection exists
            collection = self.get_collection(collection_id)
            if not collection:
                return False
            
            # Get all documents in the collection
            documents = self.list_documents(collection_id)
            
            # Update collection status
            collection["index_status"] = "indexing"
            self.collections[collection_id] = collection
            self._save_collections_info()
            
            # Index documents in vector store
            success = self.vector_store.index_documents(collection_id, documents)
            
            # Update collection status
            if success:
                collection["index_status"] = "indexed"
            else:
                collection["index_status"] = "index_failed"
            
            collection["updated_at"] = time.time()
            self.collections[collection_id] = collection
            self._save_collections_info()
            
            return success
        except Exception as e:
            logging.error(f"Error indexing collection {collection_id}: {e}")
            
            # Update collection status
            if collection_id in self.collections:
                collection = self.collections[collection_id]
                collection["index_status"] = "index_failed"
                collection["updated_at"] = time.time()
                self.collections[collection_id] = collection
                self._save_collections_info()
            
            return False
    
    def search_documents(self, collection_id: str, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for documents in a collection by vector similarity.
        
        Args:
            collection_id: ID of the collection to search in
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            List of document dictionaries sorted by relevance
        """
        if not self.vector_store:
            logging.error("No vector store available for search")
            return []
        
        try:
            # Check if collection exists and is indexed
            collection = self.get_collection(collection_id)
            if not collection:
                return []
            
            if collection.get("index_status") != "indexed":
                logging.warning(f"Collection {collection_id} is not indexed")
                return []
            
            # Search in vector store
            document_ids = self.vector_store.search(collection_id, query, limit)
            
            # Load documents
            documents = []
            for doc_id in document_ids:
                document = self.get_document(collection_id, doc_id)
                if document:
                    documents.append(document)
            
            return documents
        except Exception as e:
            logging.error(f"Error searching in collection {collection_id}: {e}")
            return []
    
    def import_documents_from_directory(self, collection_id: str, directory: str, 
                                      file_types: List[str] = None) -> int:
        """
        Import documents from a directory into a collection.
        
        Args:
            collection_id: ID of the collection to import into
            directory: Directory to import documents from
            file_types: List of file extensions to import (default: ['.txt', '.md', '.pdf'])
            
        Returns:
            Number of documents imported
        """
        if not file_types:
            file_types = ['.txt', '.md', '.pdf']
        
        try:
            # Check if collection exists
            collection = self.get_collection(collection_id)
            if not collection:
                return 0
            
            # Check if directory exists
            if not os.path.isdir(directory):
                return 0
            
            # Import files
            imported_count = 0
            
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check file extension
                    _, ext = os.path.splitext(file)
                    if ext.lower() not in file_types:
                        continue
                    
                    # 실제 파일 내용 추출 및 처리
                    content = ""
                    try:
                        if ext.lower() == '.txt' or ext.lower() == '.md':
                            # 텍스트 파일 또는 마크다운 파일 읽기
                            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                                content = f.read()
                        elif ext.lower() == '.pdf':
                            # PDF 파일 처리
                            try:
                                import fitz  # PyMuPDF
                                pdf_doc = fitz.open(file_path)
                                content = ""
                                for page_num in range(len(pdf_doc)):
                                    page = pdf_doc.load_page(page_num)
                                    content += page.get_text()
                                pdf_doc.close()
                            except ImportError:
                                logging.warning("PyMuPDF (fitz) not installed, using text placeholder for PDF content")
                                content = f"PDF content from {file} - PyMuPDF not installed for extraction"
                    except Exception as file_error:
                        logging.error(f"Error reading file {file_path}: {file_error}")
                        content = f"Error reading file content: {str(file_error)}"
                    
                    # 문서 객체 생성
                    document = {
                        "title": file,
                        "source_path": file_path,
                        "file_type": ext.lower()[1:],  # Remove the dot
                        "content": content,
                        "created_at": time.time(),
                        "updated_at": time.time()
                    }
                    
                    # 문서를 커렉션에 추가
                    if self.add_document(collection_id, document):
                        imported_count += 1
                        logging.info(f"Imported document: {file_path}")
            
            # 커렉션 상태 업데이트
            if imported_count > 0:
                collection["index_status"] = "needs_indexing"
                collection["updated_at"] = time.time()
                collection["document_count"] = len(self.list_documents(collection_id))
                self.collections[collection_id] = collection
                self._save_collections_info()
                
                logging.info(f"Successfully imported {imported_count} documents into collection {collection_id}")
            
            return imported_count
        except Exception as e:
            logging.error(f"Error importing documents into collection {collection_id}: {e}")
            return 0
