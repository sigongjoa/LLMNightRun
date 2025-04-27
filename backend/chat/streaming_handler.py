"""
StreamingHandler provides functionality for streaming responses from LLM models.
This allows text to appear incrementally rather than waiting for the full response.
"""

import logging
import time
import torch
from typing import List, Callable, Dict, Any, Optional, Generator

class StreamingResponseHandler:
    """Handler for generating streaming responses from language models"""
    
    @staticmethod
    def generate_streaming_response(
        model, 
        tokenizer, 
        prompt: str,
        callback: Callable[[str], None] = None,
        max_new_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.95,
        stopping_criteria: Optional[List] = None
    ) -> str:
        """
        Generate a response with streaming output using the huggingface streaming API.
        
        Args:
            model: The loaded language model
            tokenizer: The tokenizer for the model
            prompt: The input prompt
            callback: Function to call with each new token (for UI updates)
            max_new_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p sampling parameter
            stopping_criteria: Optional stopping criteria for generation
            
        Returns:
            The complete generated response
        """
        try:
            logging.info(f"Starting streaming generation for prompt of length {len(prompt)}")
            start_time = time.time()
            
            # Tokenize the prompt with proper handling of longer context
            input_ids = tokenizer(
                prompt, 
                return_tensors="pt",
                truncation=True,
                max_length=4096  # Support longer context
            ).input_ids
            
            # Move to the same device as the model
            if hasattr(model, "device"):
                input_ids = input_ids.to(model.device)
            
            # Set up any stopping criteria if provided
            if stopping_criteria is None:
                from transformers import StoppingCriteria, StoppingCriteriaList
                
                # Define a stopping criteria class
                class KeywordsStoppingCriteria(StoppingCriteria):
                    def __init__(self, tokens_ids, tokenizer):
                        self.tokens_ids = tokens_ids
                        self.tokenizer = tokenizer
                    
                    def __call__(self, input_ids, scores, **kwargs):
                        # Check if any stopping sequences are in the generated text
                        generated_text = tokenizer.decode(input_ids[0])
                        for stop_text in ["<|im_start|>", "<|im_end|>", "<|im_start|>user", "<|im_start|>system"]:
                            if stop_text in generated_text[-20:]:  # Check only in recent text for efficiency
                                return True
                        return False
                
                stopping_criteria = StoppingCriteriaList([
                    KeywordsStoppingCriteria([], tokenizer)
                ])
            
            # Prepare generation parameters with support for longer responses
            generation_config = {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "do_sample": True,
                "stopping_criteria": stopping_criteria,
                "pad_token_id": tokenizer.pad_token_id or tokenizer.eos_token_id,
                # Additional parameters for better handling of longer context
                "repetition_penalty": 1.1,  # Discourage repetition
                "no_repeat_ngram_size": 5,  # Avoid repeating the same phrases
                "early_stopping": True      # Stop when the model would naturally stop
            }
            
            # Track the tokens for incremental output
            full_response = ""
            response_buffer = ""
            
            # Start streaming generation
            streamer_kwargs = {}
            
            # Create a streamer if supported
            try:
                from transformers import TextStreamer
                
                class CustomTextStreamer(TextStreamer):
                    """Custom streamer that calls a callback with each new token"""
                    
                    def on_finalized_text(self, text: str, stream_end: bool = False):
                        """Called when new text is ready"""
                        nonlocal full_response, response_buffer
                        
                        # Update the full response
                        full_response += text
                        response_buffer += text
                        
                        # Call the callback if provided
                        if callback is not None:
                            callback(text)
                
                # Set up streamer
                streamer = CustomTextStreamer(
                    tokenizer, 
                    skip_prompt=True,  # Skip the input prompt in the output
                    skip_special_tokens=True
                )
                generation_config["streamer"] = streamer
                
            except (ImportError, AttributeError) as e:
                logging.warning(f"Streaming not fully supported: {e}. Falling back to manual streaming.")
                # Fallback to manual streaming is handled below
            
            # Generate with streaming
            logging.info("Starting token generation with streaming...")
            
            # If streamer is configured, use it
            if "streamer" in generation_config:
                with torch.no_grad():
                    model.generate(
                        input_ids, 
                        **generation_config
                    )
            else:
                # Manual streaming implementation as fallback
                logging.info("Using manual streaming implementation")
                
                # Generate tokens one by one
                all_ids = input_ids.clone()
                for _ in range(max_new_tokens):
                    with torch.no_grad():
                        outputs = model(all_ids)
                        next_token_logits = outputs.logits[:, -1, :]
                        
                        # Apply temperature and top-p sampling
                        if temperature > 0:
                            next_token_logits = next_token_logits / temperature
                        
                        # Apply top-p sampling
                        if top_p < 1.0:
                            sorted_logits, sorted_indices = torch.sort(next_token_logits, descending=True)
                            cumulative_probs = torch.cumsum(torch.softmax(sorted_logits, dim=-1), dim=-1)
                            
                            # Remove tokens with cumulative probability above the threshold
                            sorted_indices_to_remove = cumulative_probs > top_p
                            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
                            sorted_indices_to_remove[..., 0] = 0
                            
                            # Scatter sorted indices back
                            indices_to_remove = sorted_indices_to_remove.scatter(
                                dim=1, 
                                index=sorted_indices, 
                                src=sorted_indices_to_remove
                            )
                            next_token_logits[indices_to_remove] = -float("inf")
                        
                        # Sample from the distribution
                        probs = torch.softmax(next_token_logits, dim=-1)
                        next_token = torch.multinomial(probs, num_samples=1)
                        
                        # Append to the sequence
                        all_ids = torch.cat([all_ids, next_token], dim=-1)
                        
                        # Get the token text
                        next_token_text = tokenizer.decode(next_token[0], skip_special_tokens=True)
                        
                        # Update responses
                        full_response += next_token_text
                        response_buffer += next_token_text
                        
                        # Call the callback if provided and buffer is not empty
                        if callback is not None and response_buffer:
                            callback(response_buffer)
                            response_buffer = ""
                        
                        # Check stopping criteria
                        if tokenizer.eos_token_id is not None and next_token[0, 0].item() == tokenizer.eos_token_id:
                            break
                            
                        # Custom stopping criteria check
                        if "System:" in full_response or "User:" in full_response:
                            break
            
            # Calculate generation time
            generation_time = time.time() - start_time
            logging.info(f"Streaming generation completed in {generation_time:.2f} seconds")
            
            # Extract the assistant's response from the full output
            if "<|im_start|>assistant" in full_response:
                # Extract just the assistant's part
                parts = full_response.split("<|im_start|>assistant")
                if len(parts) > 1:
                    assistant_part = parts[1].strip()
                    # Handle potential end marker
                    if "<|im_end|>" in assistant_part:
                        final_response = assistant_part.split("<|im_end|>")[0].strip()
                    else:
                        final_response = assistant_part.strip()
                else:
                    final_response = full_response
            else:
                # Fallback extraction methods
                if "assistant" in full_response.lower():
                    parts = full_response.lower().split("assistant")
                    if len(parts) > 1:
                        final_response = parts[1].strip()
                    else:
                        final_response = full_response
                else:
                    final_response = full_response
            
            return final_response
            
        except Exception as e:
            logging.error(f"Error in streaming generation: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
            # If callback exists, send an error message
            if callback:
                error_msg = "I'm sorry, an error occurred during response generation."
                callback(error_msg)
            
            return "Error during response generation. Please try again."
