"""
SimpleChatHandler provides a streamlined way to interact with LLM models.
This is a simplified version that handles basic prompt formatting and response generation.
"""

import logging

class SimpleChatHandler:
    @staticmethod
    def generate_response(model_instance, system_message, user_message):
        """
        Generate a response using a simpler approach that works better with Qwen models.
        
        Args:
            model_instance: The loaded language model instance
            system_message: System instructions
            user_message: User's question or input
            
        Returns:
            Generated response text
        """
        try:
            # Use a format that works better with instruction-tuned models like Qwen
            simple_prompt = f"""<|im_start|>system
{system_message}
<|im_end|>

<|im_start|>user
{user_message}
<|im_end|>

<|im_start|>assistant
"""
            
            logging.info(f"Sending simplified prompt to model. Length: {len(simple_prompt)}")
            
            # Tokenize with proper attention mask to avoid warnings
            if hasattr(model_instance, 'tokenizer'):
                tokenizer = model_instance.tokenizer
                
                # Tokenize with explicit attention mask
                inputs = tokenizer(
                    simple_prompt,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                )
                
                # Make sure pad token is set
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token
                
                # Generate with more conservative parameters using direct tokenizer
                response_ids = model_instance.model.generate(
                    inputs["input_ids"].to(model_instance.device),
                    attention_mask=inputs["attention_mask"].to(model_instance.device),
                    max_new_tokens=512,
                    pad_token_id=tokenizer.pad_token_id,
                    temperature=0.5,
                    top_p=0.92,
                    do_sample=True
                )
                
                # Decode the response
                full_response = tokenizer.decode(response_ids[0], skip_special_tokens=True)
            else:
                # Fall back to using the pipeline directly if tokenizer isn't accessible
                generation_config = {
                    "max_new_tokens": 512,  # Shorter to avoid timeouts
                    "temperature": 0.5,     # More deterministic
                    "top_p": 0.92,
                    "do_sample": True,
                    "num_return_sequences": 1
                }
                
                # Generate response
                generated_response = model_instance(
                    simple_prompt,
                    **generation_config
                )
                
                # Get the generated text
                full_response = generated_response[0]["generated_text"]
            
            # Extract just the assistant's part using the ChatML format
            if "<|im_start|>assistant" in full_response:
                # Extract just the assistant's part
                parts = full_response.split("<|im_start|>assistant")
                if len(parts) > 1:
                    assistant_part = parts[1].strip()
                    # Handle potential end marker
                    if "<|im_end|>" in assistant_part:
                        response = assistant_part.split("<|im_end|>")[0].strip()
                    else:
                        response = assistant_part.strip()
                else:
                    response = full_response
            elif "<|im_start|>" in full_response:
                # Try other ChatML markers
                parts = full_response.split("<|im_start|>")
                for part in parts:
                    if part.startswith("assistant"):
                        assistant_content = part.replace("assistant", "", 1).strip()
                        if "<|im_end|>" in assistant_content:
                            response = assistant_content.split("<|im_end|>")[0].strip()
                        else:
                            response = assistant_content
                        break
                else:
                    response = full_response.strip()
            else:
                # Fallback to simpler extraction if ChatML markers aren't found
                response = full_response.strip()
                
            # As a final fallback, if the response is very short (like "Sure"), expand it
            if len(response) < 10:
                longer_response = f"{response}. I'm here to help you with any questions or tasks you might have. What would you like to know or discuss?"
                response = longer_response
            
            # Clean up any system or user message that might have been generated
            if response.startswith("System:") or response.startswith("User:"):
                response = "I'm sorry, but I had trouble generating a proper response. Please try again with a different question."
            
            logging.info(f"Simplified model response generated. Length: {len(response)}")
            
            return response
            
        except Exception as e:
            logging.error(f"Error in simplified chat handler: {e}")
            return "I apologize, but there was an error generating a response. Please try again later."
