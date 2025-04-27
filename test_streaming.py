"""
Test the streaming response generation using the StreamingResponseHandler.
This script will load the model and generate responses with visible streaming.
"""

import time
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def print_chunk(text, flush=True):
    """Print text and flush to display streaming output"""
    sys.stdout.write(text)
    if flush:
        sys.stdout.flush()

def test_streaming_generation():
    print("Testing streaming response generation with Qwen model...")
    print("=" * 60)
    
    # Check for GPU support
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # Set up loading spinner
    loading_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    loading_idx = 0
    
    # Load tokenizer
    print("Loading tokenizer... ", end="")
    sys.stdout.flush()
    tokenizer = AutoTokenizer.from_pretrained(
        "Qwen/Qwen2.5-3B", 
        trust_remote_code=True,
        padding_side="right"
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print("Done")
    
    # Load model with loading animation
    print("Loading model... ", end="")
    sys.stdout.flush()
    start_time = time.time()
    loading_timer = 0
    
    try:
        # Start loading animation in a separate thread
        import threading
        loading_active = True
        
        def loading_animation():
            nonlocal loading_idx
            while loading_active:
                sys.stdout.write(f"\rLoading model... {loading_chars[loading_idx]} ")
                sys.stdout.flush()
                loading_idx = (loading_idx + 1) % len(loading_chars)
                time.sleep(0.1)
        
        # Start animation thread
        animation_thread = threading.Thread(target=loading_animation)
        animation_thread.daemon = True
        animation_thread.start()
        
        # Load the model with correct parameters
        model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-3B",
            device_map="auto",
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )
        
        # Set up generation configuration for longer context if needed
        if hasattr(model, 'generation_config'):
            model.generation_config.max_length = 4096
        
        # Stop animation
        loading_active = False
        animation_thread.join(timeout=0.5)
        
        # Clear the loading line
        sys.stdout.write("\r" + " " * 50 + "\r")
        load_time = time.time() - start_time
        print(f"Model loaded in {load_time:.2f} seconds")
        
        # Import the streaming handler
        sys.path.append("D:\\LLM_Forge_gui")
        from backend.chat.streaming_handler import StreamingResponseHandler
        
        # Test with a simple question
        test_questions = [
            "What is the capital of France?",
            "Explain quantum computing in simple terms.",
            "Write a short poem about artificial intelligence."
        ]
        
        for i, question in enumerate(test_questions):
            print("\n" + "=" * 60)
            print(f"Test Question {i+1}: {question}")
            print("=" * 60)
            
            # Set up the prompt
            system_message = "You are a helpful AI assistant. Answer the user's questions accurately and helpfully."
            prompt = f"System: {system_message}\n\nUser: {question}\n\nAssistant:"
            
            # Set up streaming callback
            print("\nAssistant: ", end="")
            sys.stdout.flush()
            
            def streaming_print(text):
                print_chunk(text)
                # Add artificial delay to slow down output for better visualization
                time.sleep(0.01)
            
            # Generate response with streaming
            start_time = time.time()
            response = StreamingResponseHandler.generate_streaming_response(
                model,
                tokenizer,
                prompt,
                callback=streaming_print,
                max_new_tokens=300,  # Limit tokens for testing
                temperature=0.7
            )
            generation_time = time.time() - start_time
            
            print(f"\n\nGeneration completed in {generation_time:.2f} seconds")
            
    except Exception as e:
        # Stop animation if running
        if 'loading_active' in locals():
            loading_active = False
        
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_streaming_generation()
    if success:
        print("\nStreaming test completed successfully!")
    else:
        print("\nStreaming test failed.")
