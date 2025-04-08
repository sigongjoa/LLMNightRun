"""
API router for memory management.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any

from ...memory.memory_manager import get_memory_manager
from ...memory.memory_types import (
    Memory, MemoryType, MemorySearch, MemoryResponse, 
    MemoryBatch, ExperimentMemory
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/memory",
    tags=["memory"],
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    },
)

# Health check endpoint
@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Check the health of the memory system.
    
    Returns:
        Status message
    """
    try:
        memory_manager = get_memory_manager()
        count = memory_manager.count_memories()
        return {"status": "healthy", "memory_count": str(count)}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Memory system health check failed: {str(e)}")


@router.post("/add", response_model=Dict[str, str])
async def add_memory(memory: Memory, background_tasks: BackgroundTasks):
    """Add a new memory to the store.
    
    Args:
        memory: Memory object to add
        background_tasks: FastAPI background tasks
        
    Returns:
        Dictionary with memory ID
    """
    try:
        memory_manager = get_memory_manager()
        memory_id = memory_manager.add_memory(memory)
        
        # Refresh in-memory cache in the background
        background_tasks.add_task(lambda: None)  # Dummy task to keep the manager active
        
        return {"id": memory_id}
    except Exception as e:
        logger.error(f"Error adding memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add memory: {str(e)}")


@router.post("/batch", response_model=Dict[str, List[str]])
async def add_memories_batch(batch: MemoryBatch, background_tasks: BackgroundTasks):
    """Add multiple memories in batch.
    
    Args:
        batch: Batch of memories to add
        background_tasks: FastAPI background tasks
        
    Returns:
        Dictionary with memory IDs
    """
    try:
        memory_manager = get_memory_manager()
        memory_ids = memory_manager.add_memories(batch.memories)
        
        # Refresh in-memory cache in the background
        background_tasks.add_task(lambda: None)  # Dummy task to keep the manager active
        
        return {"ids": memory_ids}
    except Exception as e:
        logger.error(f"Error adding memories in batch: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add memories: {str(e)}")


@router.post("/search", response_model=List[MemoryResponse])
async def search_memories(search: MemorySearch):
    """Search for memories.
    
    Args:
        search: Search parameters
        
    Returns:
        List of matching memories
    """
    try:
        memory_manager = get_memory_manager()
        memories = memory_manager.search_memories(search)
        return memories
    except Exception as e:
        logger.error(f"Error searching memories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search memories: {str(e)}")


@router.get("/get/{memory_id}", response_model=MemoryResponse)
async def get_memory(memory_id: str):
    """Get memory by ID.
    
    Args:
        memory_id: ID of memory to retrieve
        
    Returns:
        Memory if found
    """
    try:
        memory_manager = get_memory_manager()
        memory = memory_manager.get_memory(memory_id)
        
        if not memory:
            raise HTTPException(status_code=404, detail="Memory not found")
            
        return memory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving memory {memory_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve memory: {str(e)}")


@router.delete("/delete/{memory_id}", response_model=Dict[str, bool])
async def delete_memory(memory_id: str, background_tasks: BackgroundTasks):
    """Delete memory by ID.
    
    Args:
        memory_id: ID of memory to delete
        background_tasks: FastAPI background tasks
        
    Returns:
        Success status
    """
    try:
        memory_manager = get_memory_manager()
        success = memory_manager.delete_memory(memory_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Memory with ID {memory_id} not found or could not be deleted")
        
        # Refresh in-memory cache in the background
        background_tasks.add_task(lambda: None)  # Dummy task to keep the manager active
        
        return {"success": success}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting memory {memory_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete memory: {str(e)}")


@router.post("/clear", response_model=Dict[str, bool])
async def clear_memories(memory_type: Optional[MemoryType] = None, background_tasks: BackgroundTasks = None):
    """Clear all memories of specified type, or all if type is None.
    
    Args:
        memory_type: Type of memories to clear, or all if None
        background_tasks: FastAPI background tasks
        
    Returns:
        Success status
    """
    try:
        memory_manager = get_memory_manager()
        success = memory_manager.clear_memories(memory_type)
        
        # Refresh in-memory cache in the background
        if background_tasks:
            background_tasks.add_task(lambda: None)  # Dummy task to keep the manager active
        
        return {"success": success}
    except Exception as e:
        logger.error(f"Error clearing memories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear memories: {str(e)}")


@router.get("/working", response_model=List[Memory])
async def get_working_memory():
    """Get current working memory.
    
    Returns:
        List of memories in working memory
    """
    try:
        memory_manager = get_memory_manager()
        memories = memory_manager.get_working_memory()
        
        return memories
    except Exception as e:
        logger.error(f"Error retrieving working memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve working memory: {str(e)}")


@router.post("/working/limit", response_model=Dict[str, int])
async def set_working_memory_limit(limit: int):
    """Set the working memory limit.
    
    Args:
        limit: New working memory limit
        
    Returns:
        New limit
    """
    try:
        if limit < 1:
            raise HTTPException(status_code=400, detail="Limit must be at least 1")
            
        memory_manager = get_memory_manager()
        memory_manager.set_working_memory_limit(limit)
        
        return {"limit": limit}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting working memory limit: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set working memory limit: {str(e)}")


@router.post("/context", response_model=Dict[str, str])
async def get_memory_context(query: str, top_k: int = 5):
    """Get memory context for a query.
    
    Args:
        query: Query to get context for
        top_k: Number of memories to include
        
    Returns:
        Memory context
    """
    try:
        memory_manager = get_memory_manager()
        context = memory_manager.get_memory_context(query, top_k)
        
        return {"context": context}
    except Exception as e:
        logger.error(f"Error getting memory context: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory context: {str(e)}")


@router.post("/attach-context", response_model=Dict[str, str])
async def attach_context_to_prompt(prompt: str, query: str = "", top_k: int = 5):
    """Attach memory context to a prompt.
    
    Args:
        prompt: Original prompt
        query: Query to get context for, or use prompt if empty
        top_k: Number of memories to include
        
    Returns:
        Prompt with memory context
    """
    try:
        memory_manager = get_memory_manager()
        enhanced_prompt = memory_manager.attach_context_to_prompt(prompt, query, top_k)
        
        return {"prompt": enhanced_prompt}
    except Exception as e:
        logger.error(f"Error attaching context to prompt: {str(e)}")
        # Return original prompt as fallback
        return {"prompt": prompt}


@router.get("/count", response_model=Dict[str, int])
async def count_memories():
    """Get the total number of memories.
    
    Returns:
        Number of memories
    """
    try:
        memory_manager = get_memory_manager()
        count = memory_manager.count_memories()
        return {"count": count}
    except Exception as e:
        logger.error(f"Error counting memories: {str(e)}")
        # Return 0 count as fallback
        return {"count": 0}


@router.post("/experiment", response_model=Dict[str, str])
async def store_experiment_memory(experiment_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Store memory about an experiment.
    
    Args:
        experiment_data: Data about the experiment
        background_tasks: FastAPI background tasks
        
    Returns:
        ID of the created memory
    """
    try:
        memory_manager = get_memory_manager()
        memory_id = memory_manager.store_experiment_memory(experiment_data)
        
        # Refresh in-memory cache in the background
        background_tasks.add_task(lambda: None)  # Dummy task to keep the manager active
        
        return {"id": memory_id}
    except Exception as e:
        logger.error(f"Error storing experiment memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store experiment memory: {str(e)}")


@router.post("/related", response_model=List[MemoryResponse])
async def retrieve_related_memories(
    prompt: str, 
    top_k: int = 5,
    memory_types: Optional[List[MemoryType]] = Query(None)
):
    """Retrieve memories related to a prompt.
    
    Args:
        prompt: Prompt to find related memories for
        top_k: Number of memories to return
        memory_types: Types of memories to include
        
    Returns:
        List of related memories
    """
    try:
        memory_manager = get_memory_manager()
        memories = memory_manager.retrieve_related_memories(prompt, top_k, memory_types)
        
        return memories
    except Exception as e:
        logger.error(f"Error retrieving related memories: {str(e)}")
        # Return empty list as fallback
        return []
