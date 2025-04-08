"""
Memory service implementation for LLMNightRun.
"""
import logging
from typing import List, Dict, Any, Optional

from ...memory.memory_manager import get_memory_manager
from ...memory.memory_types import Memory, MemorySearch, MemoryResponse

logger = logging.getLogger(__name__)

class MemoryService:
    """Service class for memory operations."""
    
    def __init__(self):
        """Initialize memory service."""
        self.memory_manager = get_memory_manager()
        logger.info("Memory service initialized")
    
    def add_memory(self, memory: Memory) -> str:
        """Add a memory.
        
        Args:
            memory: Memory to add
            
        Returns:
            ID of the added memory
        """
        return self.memory_manager.add_memory(memory)
    
    def add_memories_batch(self, memories: List[Memory]) -> List[str]:
        """Add multiple memories in batch.
        
        Args:
            memories: List of memories to add
            
        Returns:
            List of IDs for the added memories
        """
        return self.memory_manager.add_memories(memories)
    
    def search_memories(self, search: MemorySearch) -> List[MemoryResponse]:
        """Search for memories by query.
        
        Args:
            search: Search parameters
            
        Returns:
            List of matching memories
        """
        return self.memory_manager.search_memories(search)
    
    def get_memory(self, memory_id: str) -> Optional[MemoryResponse]:
        """Get memory by ID.
        
        Args:
            memory_id: ID of memory to retrieve
            
        Returns:
            Memory if found, None otherwise
        """
        return self.memory_manager.get_memory(memory_id)
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete memory by ID.
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if memory was deleted, False otherwise
        """
        return self.memory_manager.delete_memory(memory_id)
    
    def clear_memories(self, memory_type: Optional[str] = None) -> bool:
        """Clear all memories of specified type, or all if type is None.
        
        Args:
            memory_type: Type of memories to clear, or all if None
            
        Returns:
            True if memories were cleared
        """
        return self.memory_manager.clear_memories(memory_type)
    
    def get_working_memory(self) -> List[Memory]:
        """Get current working memory.
        
        Returns:
            List of memories in working memory
        """
        return self.memory_manager.get_working_memory()
    
    def set_working_memory_limit(self, limit: int) -> None:
        """Set the working memory limit.
        
        Args:
            limit: New working memory limit
        """
        self.memory_manager.set_working_memory_limit(limit)
    
    def get_memory_context(self, query: str, top_k: int = 5) -> str:
        """Get memory context for a query.
        
        Args:
            query: Query to get context for
            top_k: Number of memories to include
            
        Returns:
            String of memory context
        """
        return self.memory_manager.get_memory_context(query, top_k)
    
    def attach_context_to_prompt(self, prompt: str, query: str = "", top_k: int = 5) -> str:
        """Attach memory context to a prompt.
        
        Args:
            prompt: Original prompt
            query: Query to get context for, or use prompt if empty
            top_k: Number of memories to include
            
        Returns:
            Prompt with memory context
        """
        return self.memory_manager.attach_context_to_prompt(prompt, query, top_k)
    
    def count_memories(self) -> int:
        """Get the total number of memories.
        
        Returns:
            Number of memories
        """
        return self.memory_manager.count_memories()
    
    def store_experiment_memory(self, experiment_data: Dict[str, Any]) -> str:
        """Store memory about an experiment.
        
        Args:
            experiment_data: Data about the experiment
            
        Returns:
            ID of the created memory
        """
        return self.memory_manager.store_experiment_memory(experiment_data)
    
    def retrieve_related_memories(self, prompt: str, top_k: int = 5,
                                  memory_types: Optional[List[str]] = None) -> List[MemoryResponse]:
        """Retrieve memories related to a prompt.
        
        Args:
            prompt: Prompt to find related memories for
            top_k: Number of memories to return
            memory_types: Types of memories to include
            
        Returns:
            List of related memories
        """
        return self.memory_manager.retrieve_related_memories(prompt, top_k, memory_types)


# Singleton instance
_memory_service = None

def get_memory_service() -> MemoryService:
    """Get the singleton memory service instance.
    
    Returns:
        MemoryService instance
    """
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service