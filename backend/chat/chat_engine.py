"""
ChatEngine handles the conversation management and response generation.
It interfaces with the loaded models to generate responses and manages conversation history.
"""

import os
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Union, Any

# HuggingFace 라이브러리 추가
try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logging.warning("Transformers library not available. Please install: pip install transformers")

# DO NOT CHANGE CODE: Core chat engine functionality
# TEMP: Current implementation works but will be refactored later

class ChatEngine:
    def __init__(self, model_manager=None, storage_manager=None, code_listener=None):
        """
        Initialize the ChatEngine with necessary components.
        
        Args:
            model_manager: ModelManager instance for accessing loaded models
            storage_manager: StorageManager instance for persisting conversations
            code_listener: CodeListener instance for processing code in responses
        """
        self.model_manager = model_manager
        self.storage_manager = storage_manager
        self.code_listener = code_listener
        self.active_conversations = {}
        self.default_system_prompt = """You are a helpful AI assistant running in the LLM Forge application. You are powered by a local LLM model and can respond to various questions and tasks. Answer the user's questions accurately, helpfully, and provide thoughtful responses.

If you're asked to generate code, please provide well-commented, high-quality code that follows best practices.
For programming queries, you may include examples and explanations along with the code.

For technical topics, provide clear explanations suitable for the user's level of understanding.
You should be honest about your capabilities and limitations as a locally-running language model."""
    
    def create_conversation(self, conversation_id: str = None, model_id: str = None, 
                           system_prompt: str = None) -> Dict:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Optional ID for the conversation (generates UUID if not provided)
            model_id: ID of the model to use for the conversation
            system_prompt: Optional system prompt to use (uses default if not provided)
            
        Returns:
            Dictionary with conversation information
        """
        # Generate a conversation ID if not provided
        conversation_id = conversation_id or str(uuid.uuid4())
        
        # Use default system prompt if not provided
        system_prompt = system_prompt or self.default_system_prompt
        
        # Create conversation object
        conversation = {
            "id": conversation_id,
            "model_id": model_id,
            "created_at": time.time(),
            "updated_at": time.time(),
            "messages": [
                {"role": "system", "content": system_prompt, "timestamp": time.time()}
            ],
            "metadata": {
                "code_listener_results": []
            }
        }
        
        # Store in active conversations
        self.active_conversations[conversation_id] = conversation
        
        # Persist conversation if storage manager is available
        if self.storage_manager:
            self.storage_manager.save_conversation(conversation)
        
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: ID of the conversation to get
            
        Returns:
            Conversation object or None if not found
        """
        # Try to get from active conversations
        if conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]
        
        # Try to load from storage if not in active conversations
        if self.storage_manager:
            conversation = self.storage_manager.load_conversation(conversation_id)
            if conversation:
                self.active_conversations[conversation_id] = conversation
                return conversation
        
        return None
    
    def get_all_conversations(self) -> List[Dict]:
        """
        Get a list of all conversations.
        
        Returns:
            List of conversation objects
        """
        # Get list of conversations from storage
        conversations = []
        if self.storage_manager:
            conversations = self.storage_manager.list_conversations()
        
        # Add any active conversations that might not be in storage yet
        for conv_id, conv in self.active_conversations.items():
            # Check if this conversation is already in the list
            if not any(c["id"] == conv_id for c in conversations):
                conversations.append(conv)
        
        # Sort by updated_at timestamp (newest first)
        conversations.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        
        return conversations
    
    def add_message(self, conversation_id: str, role: str, content: str) -> Dict:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation to add message to
            role: Role of the message sender (user, assistant, system)
            content: Content of the message
            
        Returns:
            The added message object
        """
        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation with ID {conversation_id} not found")
        
        # Create message object
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        
        # Add message to conversation
        conversation["messages"].append(message)
        conversation["updated_at"] = time.time()
        
        # Persist conversation if storage manager is available
        if self.storage_manager:
            self.storage_manager.save_conversation(conversation)
        
        return message
    
    def generate_response(self, conversation_id: str, process_code: bool = True) -> Dict:
        """
        Generate a response for the last user message in a conversation.
        
        Args:
            conversation_id: ID of the conversation to generate response for
            process_code: Whether to process code blocks in the response
            
        Returns:
            The generated response message
        """
        # 모델 ID 변수를 미리 선언하여 finally 블록에서 접근 가능하도록 함
        model_id = None
        
        try:
            # 대화 가져오기
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation with ID {conversation_id} not found")
            
            # 대화에서 모델 ID 가져오기
            model_id = conversation.get("model_id")
            if not model_id:
                raise ValueError(f"No model ID specified for conversation {conversation_id}")
            
            # 로드된 모델 가져오기
            model = None
            model_instance = None
            model_type = None
            tokenizer = None
            
            # 모델 관리자가 있는 경우
            if self.model_manager:
                # 로그 추가 - 모델 관리자 상태 확인
                logging.info(f"Model manager info: available_models={list(self.model_manager.available_models.keys())}")
                logging.info(f"Model manager info: loaded_models={list(self.model_manager.loaded_models.keys())}")
                
                # If model_id is not specified or not available, default to Qwen
                if not model_id or model_id not in self.model_manager.available_models:
                    default_model = "Qwen/Qwen2.5-3B"
                    logging.info(f"Model ID {model_id} not available, defaulting to {default_model}")
                    model_id = default_model
                    # Update the conversation model ID
                    conversation["model_id"] = model_id
                    # Save the updated conversation
                    if self.storage_manager:
                        self.storage_manager.save_conversation(conversation)
                
                # 먼저 모델이 loaded_models에 있는지 확인 - 없으면 로드 시도
                if model_id not in self.model_manager.loaded_models:
                    logging.info(f"Model {model_id} not in loaded_models, trying to load it")
                    load_success = self.model_manager.load_model(model_id)
                    logging.info(f"Model load attempt result: {load_success}")
                else:
                    logging.info(f"Model {model_id} found in loaded_models")
                
                # 모델 객체 가져오기
                model_data = self.model_manager.loaded_models.get(model_id, {})
                model_instance = model_data.get("model_object")
                model_type = model_data.get("model_type")
                tokenizer = model_data.get("tokenizer")
                
                # Enhanced debugging logs
                logging.info(f"Retrieved model: type={model_type}, instance_type={type(model_instance)}")
                logging.info(f"Is mock model: {model_instance == 'mock_model_object'}")
                
                # Check if the model is a properly initialized HuggingFace pipeline
                if hasattr(model_instance, 'pipeline_class'):
                    logging.info(f"Pipeline class: {model_instance.pipeline_class}")
                    logging.info(f"Model info: {model_instance.model}")
                    logging.info(f"Device: {model_instance.device}")
                
                # 모델 상태를 running으로 업데이트
                if model_id in self.model_manager.loaded_models:
                    self.model_manager.loaded_models[model_id]["status"] = "running"
                    self.model_manager.loaded_models[model_id]["last_activity"] = time.time()
                    
                    # 가능한 경우 모델 정보도 업데이트
                    if model_id in self.model_manager.available_models:
                        model_info = self.model_manager.available_models[model_id]
                        # is_loaded를 true로 설정되어 있는지 확인
                        model_info["is_loaded"] = True
                        if "runtime" not in model_info:
                            model_info["runtime"] = {}
                        model_info["runtime"]["status"] = "running"
                        model_info["runtime"]["last_activity"] = time.time()
            
            # 지난 메시지를 기반으로 대화 형식의 입력을 만든다
            messages = conversation.get("messages", [])
            # 시스템 메시지 포함하여 모든 메시지를 준비
            formatted_messages = []
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                formatted_messages.append({"role": role, "content": content})
            
            # 모델에 따른 응답 생성
            response_content = ""
            
            # 디버깅 로그 추가
            logging.info(f"Generating response with model_id: {model_id}, model_instance: {model_instance}, model_type: {model_type}")
            
            # Log the model instance to debug
            logging.info(f"Model instance type: {type(model_instance)}")
            
            # 실제 모델을 사용하여 응답 생성
            if model_instance:
                try:
                    if model_type == "gpt4all":  # GPT4All 모델 사용
                        # 마지막 사용자 메시지 찾기
                        last_user_msg = ""
                        for msg in reversed(messages):
                            if msg["role"] == "user":
                                last_user_msg = msg["content"]
                                break
                                
                        # 시스템 메시지 찾기
                        system_msg = ""
                        for msg in messages:
                            if msg["role"] == "system":
                                system_msg = msg["content"]
                                break
                                
                        # GPT4All의 경우 문맥 텍스트를 직접 구성
                        context = f"""System: {system_msg}

User: {last_user_msg}

Assistant: """
                        
                        # 응답 생성
                        response_content = model_instance.generate(context, max_tokens=1024)
                    
                    elif model_type == "llama.cpp":  # llama.cpp (llama-cpp-python) 사용
                        # llama.cpp는 코드 블록을 잘 처리하는 마커 구문 사용
                        prompt = ""  # 초기화
                        
                        # 대화 구성
                        for msg in messages:
                            role = msg["role"]
                            content = msg["content"]
                            
                            if role == "system":
                                prompt += f"<|system|>\n{content}\n"
                            elif role == "user":
                                prompt += f"<|user|>\n{content}\n"
                            elif role == "assistant":
                                prompt += f"<|assistant|>\n{content}\n"
                        
                        # 어시스턴트의 다음 응답 시작 하기
                        prompt += "<|assistant|>\n"
                        
                        # 응답 생성
                        response = model_instance.create_completion(
                            prompt,
                            max_tokens=1024,
                            temperature=0.7,
                            top_p=0.95,
                            stop=["<|user|>", "<|system|>"]
                        )
                        response_content = response["choices"][0]["text"]
                    
                    elif model_type == "transformers":  # HuggingFace 파이프라인 사용
                        logging.info("Using HuggingFace pipeline for response generation")
                        
                        # 대화 형식으로 포맷팅
                        chat_messages = []
                        for msg in messages:
                            role = msg.get("role")
                            content = msg.get("content")
                            if role == "user" or role == "assistant":  # 시스템 메시지 무시
                                chat_messages.append({"role": role, "content": content})
                        
                        logging.info(f"Sending messages to model: {chat_messages}")
                        
                        # 파이프라인으로 응답 생성
                        try:
                            # Import our simplified chat handler
                            from backend.chat.simple_chat_handler import SimpleChatHandler
                            
                            # Get the last user message
                            last_user_msg = ""
                            for msg in reversed(messages):
                                if msg["role"] == "user":
                                    last_user_msg = msg["content"]
                                    break
                            
                            # Get system message
                            system_msg = ""
                            for msg in messages:
                                if msg["role"] == "system":
                                    system_msg = msg["content"]
                                    break
                            
                            # Import our streaming handler
                            from backend.chat.streaming_handler import StreamingResponseHandler
                            
                            # Use the ChatML format that works better with instruction models
                            prompt = f"""<|im_start|>system
{system_msg}
<|im_end|>

<|im_start|>user
{last_user_msg}
<|im_end|>

<|im_start|>assistant
"""
                            
                            # Get direct access to model and tokenizer
                            if hasattr(model_instance, 'model') and hasattr(model_instance, 'tokenizer'):
                                model = model_instance.model
                                tokenizer = model_instance.tokenizer
                                
                                # Define a callback for streaming updates
                                def streaming_callback(new_text):
                                    # Log the streaming updates
                                    logging.debug(f"Streaming update: {new_text}")
                                    # In a future update, this could send real-time updates to the UI
                                
                                # Use streaming response handler
                                response_content = StreamingResponseHandler.generate_streaming_response(
                                    model,
                                    tokenizer,
                                    prompt,
                                    callback=streaming_callback,
                                    max_new_tokens=2048,  # Increased token limit
                                    temperature=0.7,
                                    top_p=0.95
                                )
                            else:
                                # Fall back to the simplified handler if we can't access model/tokenizer directly
                                response_content = SimpleChatHandler.generate_response(
                                    model_instance, 
                                    system_msg, 
                                    last_user_msg
                                )
                            
                            logging.info(f"Response generated. Length: {len(response_content)} characters")
                        except Exception as e:
                            logging.error(f"Error calling model pipeline: {e}")
                            response_content = "I'm sorry, but there was an error generating a response. Please try again."
                    
                    else:  # 알 수 없는 모델 형식의 경우 오류 메시지 사용
                        logging.error(f"Unknown model type: {model_type}.")
                        response_content = "I'm sorry, but I don't recognize this model type. Please check your model configuration."
                except Exception as e:
                    logging.error(f"Error generating response with model: {e}")
                    # 오류 발생 시 오류 메시지로 대체
                    response_content = "I'm sorry, but there was an error while generating a response. Please try again or check the application logs."
            else:  # 모델이 없는 경우 
                logging.error(f"No valid model found. Model: {model_instance}")
                
                # Try to load the model again if it failed
                if self.model_manager and model_id:
                    logging.info(f"Attempting to reload model {model_id}")
                    # Force a reload of the model
                    if model_id in self.model_manager.loaded_models:
                        # Remove existing model instance
                        self.model_manager.loaded_models.pop(model_id, None)
                    
                    # Try loading again
                    try:
                        success = self.model_manager.load_model(model_id)
                        if success:
                            # Get the fresh model
                            model_data = self.model_manager.loaded_models.get(model_id, {})
                            model_instance = model_data.get("model_object")
                            if model_instance:
                                logging.info(f"Successfully reloaded model {model_id}")
                                
                                # Use the same code from above for generation
                                try:
                                    # Get the last user message
                                    last_user_msg = ""
                                    for msg in reversed(messages):
                                        if msg["role"] == "user":
                                            last_user_msg = msg["content"]
                                            break
                                    
                                    # Get system message
                                    system_msg = ""
                                    for msg in messages:
                                        if msg["role"] == "system":
                                            system_msg = msg["content"]
                                            break
                                    
                                    # Import our streaming handler
                                    from backend.chat.streaming_handler import StreamingResponseHandler
                                    
                                    # Use the ChatML format for consistency
                                    prompt = f"""<|im_start|>system
{system_msg}
<|im_end|>

<|im_start|>user
{last_user_msg}
<|im_end|>

<|im_start|>assistant
"""
                                    
                                    # Get direct access to model and tokenizer if possible
                                    if hasattr(model_instance, 'model') and hasattr(model_instance, 'tokenizer'):
                                        model = model_instance.model
                                        tokenizer = model_instance.tokenizer
                                        
                                        # Use streaming response handler
                                        response_content = StreamingResponseHandler.generate_streaming_response(
                                            model,
                                            tokenizer,
                                            prompt,
                                            max_new_tokens=2048,  # Increased token limit
                                            temperature=0.7,
                                            top_p=0.95
                                        )
                                    else:
                                        # Fall back to the simplified handler
                                        from backend.chat.simple_chat_handler import SimpleChatHandler
                                        response_content = SimpleChatHandler.generate_response(
                                            model_instance,
                                            system_msg,
                                            last_user_msg
                                        )
                                    
                                    logging.info(f"Model response generated after reload. Length: {len(response_content)} characters")
                                    return self.add_message(conversation_id, "assistant", response_content)
                                except Exception as reload_error:
                                    logging.error(f"Error generating response after reload: {reload_error}")
                    except Exception as e:
                        logging.error(f"Failed to reload model: {e}")
                
                # If we get here, all attempts failed - return an error message
                logging.error("Could not generate a response with the LLM model")
                response_content = ("I'm sorry, but I'm currently unable to generate a response. There may be an issue "
                                   "with the language model. Please try again later or check the application logs "
                                   "for more information.")
            
            # 대화에 응답 추가
            response_message = self.add_message(conversation_id, "assistant", response_content)
            
            # 코드 블록 처리 (요청된 경우)
            if process_code and self.code_listener and response_content:
                code_results = self.code_listener.process_response(response_content)
                if code_results:
                    # 대화 메타데이터에 코드 리스너 결과 추가
                    if "code_listener_results" not in conversation["metadata"]:
                        conversation["metadata"]["code_listener_results"] = []
                    conversation["metadata"]["code_listener_results"].append(code_results)
                    
                    # 스토리지에 대화 저장
                    if self.storage_manager:
                        self.storage_manager.save_conversation(conversation)
            
            return response_message
            
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            raise
            
        finally:
            # 항상 완료 후 모델 상태를 loaded로 재설정 (그러나 모델을 언로드하지는 않음)
            if model_id and self.model_manager and model_id in self.model_manager.loaded_models:
                try:
                    # 상태만 업데이트하고 모델은 loaded_models에서 보존
                    self.model_manager.loaded_models[model_id]["status"] = "loaded"
                    
                    # 모델 정보도 loaded 상태를 반영하도록 업데이트
                    if model_id in self.model_manager.available_models:
                        model_info = self.model_manager.available_models[model_id]
                        # is_loaded가 true로 유지되도록 함
                        model_info["is_loaded"] = True
                        if "runtime" in model_info:
                            model_info["runtime"]["status"] = "loaded"
                except Exception as e:
                    logging.error(f"Error resetting model status in finally block: {e}")
    
    # The _generate_mock_response method has been removed as we now use real model responses only
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        # Remove from active conversations
        if conversation_id in self.active_conversations:
            del self.active_conversations[conversation_id]
        
        # Delete from storage if storage manager is available
        if self.storage_manager:
            return self.storage_manager.delete_conversation(conversation_id)
        
        return True
    
    def update_conversation_model(self, conversation_id: str, model_id: str) -> bool:
        """
        Update the model used for a conversation.
        
        Args:
            conversation_id: ID of the conversation to update
            model_id: New model ID to use
            
        Returns:
            True if update was successful, False otherwise
        """
        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        # Update model ID
        conversation["model_id"] = model_id
        conversation["updated_at"] = time.time()
        
        # Persist conversation if storage manager is available
        if self.storage_manager:
            self.storage_manager.save_conversation(conversation)
        
        return True
