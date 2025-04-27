"""
Helper module for handling chat prompts with different model types.
This module provides functions to format prompts correctly for different LLM models.
"""

def format_prompt_for_qwen(system_message, user_message):
    """
    Format a prompt specifically for Qwen models.
    
    Args:
        system_message: The system instructions
        user_message: The user's query
        
    Returns:
        A formatted prompt string
    """
    # Qwen models work better with a simpler format
    prompt = f"""System: {system_message}

User: {user_message}