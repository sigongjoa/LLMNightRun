"""
Quick test script for the Qwen2.5-3B model to test response generation.
This script uses a modified version of the SimpleChatHandler for a quick test.
"""

import time
import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class QuickResponseGenerator:
    def __init__(self, use_gpu=True):
        """Initialize the response generator"""
        # Check if CUDA is available and user wants to use GPU
        self.cuda_available = torch.cuda.is_available() and use_gpu
        self.device = "cuda" if self.cuda_available else "cpu"
        logging.info(f"CUDA available: {self.cuda_available}, using device: {self.device}")
        
        # Log GPU info if using CUDA
        if self.cuda_available:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # Convert to GB
            logging.info(f"GPU: {gpu_name}, Memory: {gpu_memory:.2f} GB")
        
        # Load the model and tokenizer
        self._load_model()
    
    def _load_model(self):
        """Load the Qwen model and tokenizer"""
        start_time = time.time()
        logging.info("Loading Qwen2.5-3B model and tokenizer...")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-3B", trust_remote_code=True)
        
        # Load model with appropriate settings for the device
        self.model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-3B",
            device_map="auto" if self.device == "cuda" else None,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        elapsed = time.time() - start_time
        logging.info(f"Model loaded in {elapsed:.2f} seconds")
    
    def generate_response(self, system_message, user_message):
        """Generate a response to the user's message"""
        try:
            # Format the prompt
            prompt = f"System: {system_message}\n\nUser: {user_message}\n\nAssistant:"
            logging.info(f"Generating response for prompt with length: {len(prompt)}")
            
            # Measure generation time
            start_time = time.time()
            
            # Tokenize input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
            
            # Generate
            outputs = self.model.generate(
                inputs["input_ids"],
                max_new_tokens=512,
                temperature=0.7,
                top_p=0.95,
                do_sample=True
            )
            
            # Decode the response
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the assistant's response
            if "Assistant:" in full_response:
                response = full_response.split("Assistant:")[-1].strip()
            else:
                # Fallback extraction method
                parts = full_response.split(user_message)
                if len(parts) > 1:
                    response = parts[1].strip()
                    # Remove any "System:" or "User:" text that might have been generated
                    if "System:" in response:
                        response = response.split("System:")[0].strip()
                    if "User:" in response:
                        response = response.split("User:")[0].strip()
                else:
                    response = full_response
            
            elapsed = time.time() - start_time
            logging.info(f"Response generated in {elapsed:.2f} seconds")
            
            return {
                "success": True,
                "response": response,
                "generation_time": elapsed,
                "full_response": full_response
            }
            
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e)
            }

def run_test(use_gpu=True):
    """Run a quick test of the model"""
    print("=" * 50)
    print(f"TESTING QWEN MODEL ON {'GPU' if use_gpu else 'CPU'}")
    print("=" * 50)
    
    try:
        # Create the response generator
        generator = QuickResponseGenerator(use_gpu=use_gpu)
        
        # Test with a simple question
        system_message = "You are a helpful AI assistant. Answer the user's questions accurately and helpfully."
        user_message = "Do you know the current US president?"
        
        print(f"\nSystem: {system_message}")
        print(f"User: {user_message}")
        
        # Generate response
        result = generator.generate_response(system_message, user_message)
        
        if result["success"]:
            print("\nAssistant: " + result["response"])
            print(f"\nGeneration time: {result['generation_time']:.2f} seconds")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
        
        # Test with another question
        user_message = "What is the capital of France?"
        
        print(f"\nUser: {user_message}")
        
        # Generate response
        result = generator.generate_response(system_message, user_message)
        
        if result["success"]:
            print("\nAssistant: " + result["response"])
            print(f"\nGeneration time: {result['generation_time']:.2f} seconds")
        else:
            print(f"\nError: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 50)
        print("Test completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Qwen2.5-3B model")
    parser.add_argument('--use-cpu', action='store_true', help='Force using CPU even if GPU is available')
    args = parser.parse_args()
    
    # Run the test
    run_test(use_gpu=not args.use_cpu)
