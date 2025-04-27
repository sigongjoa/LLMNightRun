"""
SimpleLLMClient - A minimal, reliable implementation for using Qwen2.5-3B model.
This is designed to work both with and without GPU, with proper attention mask handling.
"""

import time
import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer

class SimpleLLMClient:
    def __init__(self):
        """Initialize the LLM client"""
        # Configure logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Check for GPU support
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Device: {self.device}")
        
        # Track loaded status
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
    
    def load_model(self):
        """Load the Qwen2.5-3B model and tokenizer with proper settings"""
        if self.is_loaded:
            logging.info("Model already loaded")
            return True
            
        try:
            start_time = time.time()
            logging.info("Loading Qwen2.5-3B model...")
            
            # Load tokenizer with proper settings
            self.tokenizer = AutoTokenizer.from_pretrained(
                "Qwen/Qwen2.5-3B", 
                trust_remote_code=True,
                padding_side="right"
            )
            