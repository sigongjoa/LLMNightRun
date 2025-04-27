"""
Improved test script to verify if the model can load properly.
This script fixes the attention mask and token ID issues.
"""

import time
import torch
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def test_model_loading():
    """Test loading the model with proper attention mask settings"""
    try:
        # Check if CUDA is available
        cuda_available = torch.cuda.is_available()
        device = "cuda" if cuda_available else "cpu"
        logging.info(f"CUDA available: {cuda_available}, using device: {device}")
        
        if cuda_available:
            # Log GPU information
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # Convert to GB
            logging.info(f"GPU: {gpu_name}, Memory: {gpu_memory:.2f} GB")
        
        start_time = time.time()
        logging.info("Loading Qwen2.5-3B model and tokenizer with fixed settings...")
        
        # Import necessary components
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Load tokenizer with proper settings
        tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen2.5-3B", 
            trust_remote_code=True,
            padding_side="right"  # Set explicit padding side
        )
        
        # Set proper pad token ID to avoid warnings
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with appropriate settings
        model_load_start = time.time()
        model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-3B",
            device_map="auto" if device == "cuda" else None,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        model_load_time = time.time() - model_load_start
        
        logging.info(f"Model loaded in {model_load_time:.2f} seconds")
        
        # Test generation
        logging.info("Testing response generation with fixed attention mask...")
        
        test_prompt = "System: You are a helpful assistant. Answer briefly.\n\nUser: What is the capital of France?\n\nAssistant:"
        
        generation_start = time.time()
        
        # Tokenize with explicit attention mask
        inputs = tokenizer(
            test_prompt, 
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(device)
        
        # Make sure attention mask is properly set
        if 'attention_mask' not in inputs:
            inputs['attention_mask'] = torch.ones_like(inputs['input_ids'])
        
        # Generate with less tokens for quicker testing
        outputs = model.generate(
            inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_new_tokens=50,
            pad_token_id=tokenizer.pad_token_id,
            temperature=0.7,
            top_p=0.95,
            do_sample=True
        )
        
        # Decode the response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        generation_time = time.time() - generation_start
        
        logging.info(f"Response generated in {generation_time:.2f} seconds")
        logging.info(f"Response: {response}")
        
        # Log total execution time
        total_time = time.time() - start_time
        logging.info(f"Total execution time: {total_time:.2f} seconds")
        
        return {
            "success": True,
            "device": device,
            "model_load_time": model_load_time,
            "generation_time": generation_time,
            "total_time": total_time,
            "response": response
        }
    
    except Exception as e:
        logging.error(f"Error testing model: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "device": device if 'device' in locals() else "unknown"
        }

if __name__ == "__main__":
    # Set environment variables 
    os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Avoid warnings
    
    result = test_model_loading()
    
    if result["success"]:
        print("\n" + "=" * 50)
        print(f"Test completed successfully on {result['device']}!")
        print(f"Model loading time: {result['model_load_time']:.2f} seconds")
        print(f"Response generation time: {result['generation_time']:.2f} seconds")
        print(f"Total execution time: {result['total_time']:.2f} seconds")
        print("\nResponse: " + result["response"])
        print("=" * 50 + "\n")
    else:
        print("\n" + "=" * 50)
        print(f"Test failed on {result['device']}!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print("=" * 50 + "\n")
