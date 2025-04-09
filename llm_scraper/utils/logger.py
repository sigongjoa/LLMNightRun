"""
Logging utilities for LLM Scraper.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

def setup_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name: Name of the logger, typically __name__
        log_level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
        
    logger.setLevel(log_level)
    
    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"llm_scraper_{current_date}.log"
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger
