"""
Memory manager for storing and retrieving memories using vector database.
"""
import os
import json
import logging
import time
import threading
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

from .embeddings import EmbeddingModel, get_embedding_model
from .vector_store import VectorStore, get_vector_store
from .directory_utils import get_vector_store_directory
from .memory_types import (
    Memory, MemoryType, MemorySearch, MemoryResponse,
    ConversationMemory, ExperimentMemory, CodeMemory
)

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages vector storage and retrieval of memories."""
    
    def __init__(self, 
                 vector_store: Optional[VectorStore] = None,
                 embedding_model: Optional[EmbeddingModel] = None,
                 working_memory_limit: int = 10,
                 max_memory_days: Optional[int] = 90):
        """Initialize memory manager.
        
        Args:
            vector_store: Vector store for long-term memory
            embedding_model: Model for generating embeddings
            working_memory_limit: Maximum number of items in working memory
            max_memory_days: Maximum age of memories in days, None for no limit
        """
        # Initialize embedding model if not provided
        self.embedding_model = embedding_model or get_embedding_model()
        
        # Initialize vector store if not provided
        if not vector_store:
            vector_store_path = get_vector_store_directory()
            self.vector_store = get_vector_store(
                embedding_model=self.embedding_model,
                vector_store_path=vector_store_path,
                max_memory_days=max_memory_days
            )
        else:
            self.vector_store = vector_store
        
        self.working_memory_limit = working_memory_limit
        self.working_memory = []  # List of most recent memories
        self._lock = threading.RLock()  # Thread lock for thread safety
        
        logger.info("Memory manager initialized")
        
    def add_memory(self, memory: Union[Memory, Dict[str, Any]]) -> str:
        """Add memory to both working and long-term memory.
        
        Args:
            memory: Memory object or dict to add
            
        Returns:
            ID of the added memory
        """
        try:
            with self._lock:
                if isinstance(memory, dict):
                    # Convert dict to Memory object based on type
                    memory_type = memory.get('type', MemoryType.NOTE)
                    if memory_type == MemoryType.EXPERIMENT:
                        memory = ExperimentMemory(**memory)
                    elif memory_type == MemoryType.CONVERSATION:
                        memory = ConversationMemory(**memory)
                    elif memory_type == MemoryType.CODE:
                        memory = CodeMemory(**memory)
                    else:
                        memory = Memory(**memory)
                
                # Update working memory
                self.working_memory.append(memory)
                if len(self.working_memory) > self.working_memory_limit:
                    self.working_memory.pop(0)  # Remove oldest memory
                    
                # Add to vector store
                text = memory.content
                metadata = {
                    "type": memory.type,
                    "timestamp": memory.timestamp or int(time.time()),
                    **memory.metadata,
                    **memory.dict(exclude={'id', 'content', 'metadata', 'timestamp'})
                }
                
                # Remove None values from metadata
                metadata = {k: v for k, v in metadata.items() if v is not None}
                
                # Add to vector store
                ids = self.vector_store.add([text], metadatas=[metadata])
                memory_id = ids[0] if ids else None
                
                logger.info(f"Added memory {memory_id} of type {memory.type}")
                return memory_id
        except Exception as e:
            logger.error(f"Error adding memory: {str(e)}")
            # Generate a temporary ID for failure case
            return f"temp_{int(time.time())}"
    
    def add_memories(self, memories: List[Union[Memory, Dict[str, Any]]]) -> List[str]:
        """Add multiple memories in batch.
        
        Args:
            memories: List of Memory objects or dicts to add
            
        Returns:
            List of IDs for the added memories
        """
        if not memories:
            return []
            
        processed_memories = []
        texts = []
        metadatas = []
        
        for memory in memories:
            if isinstance(memory, dict):
                # Convert dict to Memory object based on type
                memory_type = memory.get('type', MemoryType.NOTE)
                if memory_type == MemoryType.EXPERIMENT:
                    memory = ExperimentMemory(**memory)
                elif memory_type == MemoryType.CONVERSATION:
                    memory = ConversationMemory(**memory)
                elif memory_type == MemoryType.CODE:
                    memory = CodeMemory(**memory)
                else:
                    memory = Memory(**memory)
            
            processed_memories.append(memory)
            texts.append(memory.content)
            
            # Create metadata
            metadata = {
                "type": memory.type,
                "timestamp": memory.timestamp or int(time.time()),
                **memory.metadata,
                **memory.dict(exclude={'id', 'content', 'metadata', 'timestamp'})
            }
            
            # Remove None values from metadata
            metadata = {k: v for k, v in metadata.items() if v is not None}
            metadatas.append(metadata)
        
        # Update working memory (keep most recent ones)
        self.working_memory.extend(processed_memories)
        self.working_memory = self.working_memory[-self.working_memory_limit:]
        
        # Add to vector store
        ids = self.vector_store.add(texts, metadatas=metadatas)
        
        logger.info(f"Added {len(ids)} memories in batch")
        return ids
    
    def search_memories(self, search: Union[MemorySearch, Dict[str, Any]]) -> List[MemoryResponse]:
        """Search for memories by query.
        
        Args:
            search: Search parameters
            
        Returns:
            List of matching memories
        """
        try:
            if isinstance(search, dict):
                search = MemorySearch(**search)
                
            # Build filter metadata
            filter_metadata = {}
            
            if search.memory_types:
                filter_metadata["type"] = [mt for mt in search.memory_types]
                
            if search.date_from or search.date_to:
                timestamp_filter = {}
                if search.date_from:
                    timestamp_filter["gte"] = int(search.date_from.timestamp())
                if search.date_to:
                    timestamp_filter["lte"] = int(search.date_to.timestamp())
                filter_metadata["timestamp"] = timestamp_filter
                
            if search.tags:
                filter_metadata["tags"] = search.tags
                
            # Search vector store
            results = self.vector_store.search(
                query=search.query,
                top_k=search.top_k,
                filter_metadata=filter_metadata
            )
            
            # Convert to MemoryResponse objects
            responses = []
            for result in results:
                metadata = result.get("metadata", {})
                
                response = MemoryResponse(
                    id=result.get("id", ""),
                    content=result.get("text", ""),
                    type=metadata.get("type", MemoryType.NOTE),
                    timestamp=metadata.get("timestamp", 0),
                    metadata={k: v for k, v in metadata.items() 
                              if k not in {"type", "timestamp"}},
                    score=result.get("score")
                )
                responses.append(response)
                
            return responses
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []
    
    def get_memory(self, memory_id: str) -> Optional[MemoryResponse]:
        """Get memory by ID.
        
        Args:
            memory_id: ID of memory to retrieve
            
        Returns:
            Memory if found, None otherwise
        """
        results = self.vector_store.get([memory_id])
        if not results:
            return None
            
        result = results[0]
        metadata = result.get("metadata", {})
        
        return MemoryResponse(
            id=result.get("id", ""),
            content=result.get("text", ""),
            type=metadata.get("type", MemoryType.NOTE),
            timestamp=metadata.get("timestamp", 0),
            metadata={k: v for k, v in metadata.items() 
                      if k not in {"type", "timestamp"}}
        )
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete memory by ID.
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if memory was deleted, False otherwise
        """
        # Also remove from working memory if present
        self.working_memory = [m for m in self.working_memory if m.id != memory_id]
        
        # Delete from vector store
        self.vector_store.delete([memory_id])
        logger.info(f"Deleted memory {memory_id}")
        return True
    
    def clear_memories(self, memory_type: Optional[MemoryType] = None) -> bool:
        """Clear all memories of specified type, or all if type is None.
        
        Args:
            memory_type: Type of memories to clear, or all if None
            
        Returns:
            True if memories were cleared
        """
        # Clear working memory
        if memory_type:
            self.working_memory = [m for m in self.working_memory if m.type != memory_type]
        else:
            self.working_memory = []
            
        # TODO: Implement selective clearing of vector store by type
        # For now, we can only clear all memories
        if not memory_type:
            self.vector_store.clear()
            logger.info("Cleared all memories")
            return True
            
        logger.warning("Selective clearing by memory type not fully implemented")
        return False
    
    def get_working_memory(self) -> List[Memory]:
        """Get current working memory.
        
        Returns:
            List of memories in working memory
        """
        return self.working_memory
    
    def set_working_memory_limit(self, limit: int) -> None:
        """Set the working memory limit.
        
        Args:
            limit: New working memory limit
        """
        self.working_memory_limit = limit
        # Trim working memory if needed
        if len(self.working_memory) > limit:
            self.working_memory = self.working_memory[-limit:]
            
    def get_memory_context(self, query: str, top_k: int = 5) -> str:
        """Get memory context for a query.
        
        Args:
            query: Query to get context for
            top_k: Number of memories to include
            
        Returns:
            String of memory context
        """
        search = MemorySearch(query=query, top_k=top_k)
        memories = self.search_memories(search)
        
        if not memories:
            return ""
            
        context_parts = []
        for i, memory in enumerate(memories):
            context_parts.append(f"Memory {i+1}: {memory.content}")
            
        return "\n\n".join(context_parts)
    
    def attach_context_to_prompt(self, prompt: str, query: str = "", top_k: int = 5) -> str:
        """Attach memory context to a prompt.
        
        Args:
            prompt: Original prompt
            query: Query to get context for, or use prompt if empty
            top_k: Number of memories to include
            
        Returns:
            Prompt with memory context
        """
        # Use the prompt as the query if none provided
        if not query:
            query = prompt
            
        # Get memory context
        context = self.get_memory_context(query, top_k)
        
        if not context:
            return prompt
            
        # Attach context
        return f"""
I'll provide you with some relevant memories that might help with this query:

{context}

Now, please respond to the following prompt:

{prompt}
""".strip()
    
    def count_memories(self) -> int:
        """Get the total number of memories.
        
        Returns:
            Number of memories
        """
        return self.vector_store.count()
        
    def store_experiment_memory(self, experiment_data: Dict[str, Any]) -> str:
        """Store memory about an experiment.
        
        Args:
            experiment_data: Data about the experiment
            
        Returns:
            ID of the created memory
        """
        # Create a summary of the experiment
        experiment_id = experiment_data.get("experiment_id", f"exp_{int(time.time())}")
        model_name = experiment_data.get("model_name", "unknown")
        prompt = experiment_data.get("prompt", "")
        response = experiment_data.get("response", "")
        metrics = experiment_data.get("metrics", {})
        
        # Create a summary
        metric_str = ", ".join([f"{k}: {v}" for k, v in metrics.items()])
        summary = f"Experiment {experiment_id} with {model_name}: {metric_str}"
        
        # Additional metadata
        metadata = experiment_data.get("metadata", {})
        if not metadata.get("tags"):
            metadata["tags"] = []
        if model_name and model_name not in metadata["tags"]:
            metadata["tags"].append(model_name)
        
        # Create memory
        memory = ExperimentMemory(
            content=summary,
            experiment_id=experiment_id,
            model_name=model_name,
            prompt=prompt,
            response=response,
            metrics=metrics,
            metadata=metadata
        )
        
        return self.add_memory(memory)
        
    def retrieve_related_memories(self, prompt: str, top_k: int = 5, 
                                 memory_types: Optional[List[MemoryType]] = None) -> List[MemoryResponse]:
        """Retrieve memories related to a prompt.
        
        Args:
            prompt: Prompt to find related memories for
            top_k: Number of memories to return
            memory_types: Types of memories to include
            
        Returns:
            List of related memories
        """
        search = MemorySearch(
            query=prompt,
            top_k=top_k,
            memory_types=memory_types
        )
        
        return self.search_memories(search)


# Singleton instance
_memory_manager = None
_memory_manager_lock = threading.Lock()

def get_memory_manager(reset: bool = False) -> MemoryManager:
    """Get or create the singleton memory manager instance.
    
    Args:
        reset: Whether to reset the instance
        
    Returns:
        MemoryManager instance
    """
    global _memory_manager
    
    with _memory_manager_lock:
        if _memory_manager is None or reset:
            try:
                # Set up vector store path
                vector_store_path = get_vector_store_directory()
                
                # Initialize embedding model and vector store
                embedding_model = get_embedding_model()
                vector_store = get_vector_store(
                    "faiss", 
                    embedding_model, 
                    vector_store_path,
                    use_ivf_index=True,
                    max_memory_days=90
                )
                
                # Create memory manager
                _memory_manager = MemoryManager(vector_store, embedding_model)
                
            except Exception as e:
                logger.error(f"Error initializing memory manager: {str(e)}")
                # Create a fallback minimal memory manager if initialization fails
                _memory_manager = MemoryManager()
        
        return _memory_manager
