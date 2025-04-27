"""
이 파일을 실행하여 model_manager.py 파일의 함수를 수정합니다.
"""
import os

def patch_model_manager():
    model_manager_path = "D:/LLM_Forge_gui/backend/models/model_manager.py"
    
    with open(model_manager_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # load_model 함수 찾기
    load_model_start = content.find("    def load_model(self, model_id: str) -> bool:")
    if load_model_start == -1:
        print("load_model 함수를 찾을 수 없습니다.")
        return
    
    # load_model 함수의 끝 찾기
    next_def = content.find("    def ", load_model_start + 10)
    if next_def == -1:
        print("load_model 함수의 끝을 찾을 수 없습니다.")
        return
    
    # 기존 load_model 함수
    old_load_model = content[load_model_start:next_def]
    
    # 새로운 load_model 함수
    new_load_model = """    def load_model(self, model_id: str) -> bool:
        """
        Load a model into memory.
        
        Args:
            model_id: ID of the model to load
            
        Returns:
            True if loading was successful, False otherwise
        """
        with self._load_lock:
            try:
                model_info = self.available_models.get(model_id)
                if not model_info:
                    logging.error(f"Model {model_id} not found in available models")
                    return False
                
                # If model is already loaded, just return success
                if model_id in self.loaded_models and self.loaded_models[model_id].get("model_object") != "mock_model_object":
                    # Update status to indicate it's loaded and active
                    self.loaded_models[model_id]["status"] = "loaded"
                    self.loaded_models[model_id]["last_activity"] = time.time()
                    logging.info(f"Model {model_id} is already loaded")
                    
                    # Make sure the is_loaded flag is set
                    if not model_info.get("is_loaded", False):
                        model_info["is_loaded"] = True
                        if "runtime" not in model_info:
                            model_info["runtime"] = {}
                        model_info["runtime"]["status"] = "loaded"
                        model_info["runtime"]["last_activity"] = time.time()
                        self._save_models_info()
                    
                    return True
                
                # In a real implementation, load the actual model
                logging.info(f"Loading model {model_id}")
                
                try:
                    # HuggingFace에서 직접 Qwen 모델 로드
                    if HAS_LLM_LIBS:
                        logging.info("Attempting to load Qwen2.5-3B model directly from HuggingFace")
                        try:
                            from transformers import pipeline
                            model_object = pipeline("text-generation", model="Qwen/Qwen2.5-3B")
                            model_type = "transformers"
                            logging.info("Successfully loaded Qwen2.5-3B model")
                        except Exception as e:
                            import traceback
                            logging.error(f"Failed to load Qwen model: {e}")
                            logging.error(f"Traceback: {traceback.format_exc()}")
                            model_object = "mock_model_object"
                    else:
                        logging.error("Transformers library not available. Using mock model.")
                        model_object = "mock_model_object"
                except Exception as e:
                    logging.error(f"Error loading model {model_id}: {e}")
                    model_object = "mock_model_object"  # Fallback to mock model
                
                # Store the loaded model with additional info
                self.loaded_models[model_id] = {
                    "model_object": model_object,
                    "tokenizer": None,
                    "model_type": "transformers",
                    "info": model_info,
                    "status": "loaded",
                    "last_activity": time.time()
                }
                
                # Update model information - set the current model as loaded
                model_info["is_loaded"] = True
                model_info["model_type"] = "transformers"
                if "runtime" not in model_info:
                    model_info["runtime"] = {}
                model_info["runtime"]["status"] = "loaded"
                model_info["runtime"]["last_activity"] = time.time()
                
                # Save updated model information
                self._save_models_info()
                
                return model_object != "mock_model_object"  # Return True if actual model loaded
            except Exception as e:
                logging.error(f"Error loading model {model_id}: {e}")
                return False
"""
    
    # 새로운 load_model 함수로 교체
    new_content = content.replace(old_load_model, new_load_model)
    
    # 수정된 내용 저장
    with open(model_manager_path, "w", encoding="utf-8") as file:
        file.write(new_content)
    
    print("model_manager.py 파일을 성공적으로 패치했습니다.")
    
    # chat_engine.py 파일도 수정하기
    chat_engine_path = "D:/LLM_Forge_gui/backend/chat/chat_engine.py"
    
    with open(chat_engine_path, "r", encoding="utf-8") as file:
        chat_content = file.read()
    
    # 추가할 transformers import
    if "from transformers import pipeline" not in chat_content:
        import_idx = chat_content.find("from typing import Dict, List, Optional, Union, Any")
        if import_idx != -1:
            new_imports = "from typing import Dict, List, Optional, Union, Any\n\n# HuggingFace 라이브러리 추가\ntry:\n    from transformers import pipeline\n    HAS_TRANSFORMERS = True\nexcept ImportError:\n    HAS_TRANSFORMERS = False\n    logging.warning(\"Transformers library not available. Please install: pip install transformers\")\n"
            chat_content = chat_content.replace("from typing import Dict, List, Optional, Union, Any", new_imports)
    
    # transformers 모델 타입 핸들링 부분 찾기
    transformers_start = chat_content.find("                    elif model_type == \"transformers\":")
    if transformers_start == -1:
        print("transformers 모델 타입 처리 부분을 찾을 수 없습니다.")
        return
    
    # transformers 모델 타입 핸들링 부분의 끝 찾기
    next_elif = chat_content.find("                    else:", transformers_start)
    if next_elif == -1:
        print("transformers 모델 타입 처리 부분의 끝을 찾을 수 없습니다.")
        return
    
    # 기존 transformers 모델 타입 핸들링
    old_transformers_handling = chat_content[transformers_start:next_elif]
    
    # 새로운 transformers 모델 타입 핸들링
    new_transformers_handling = """                    elif model_type == "transformers":  # HuggingFace 파이프라인 사용
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
                            generated_response = model_instance(chat_messages)
                            response_content = generated_response[0]["generated_text"]
                            
                            # 마지막 사용자 메시지 찾기
                            last_user_content = ""
                            for msg in reversed(chat_messages):
                                if msg["role"] == "user":
                                    last_user_content = msg["content"]
                                    break
                            
                            # 사용자 메시지 이후의 콘텐츠만 추출
                            if last_user_content and last_user_content in response_content:
                                response_parts = response_content.split(last_user_content)
                                if len(response_parts) > 1:
                                    response_content = response_parts[1].strip()
                                    
                                    # assistant: 등의 마커 제거
                                    if response_content.startswith("assistant"):
                                        response_content = response_content.replace("assistant", "", 1).lstrip(":\\n ")
                                    elif response_content.startswith("Assistant"):
                                        response_content = response_content.replace("Assistant", "", 1).lstrip(":\\n ")
                            
                            # 응답이 비어있다면 전체 반환
                            if not response_content.strip():
                                response_content = generated_response[0]["generated_text"]
                                
                            logging.info(f"Model response generated. Length: {len(response_content)} characters")
                        except Exception as e:
                            logging.error(f"Error calling model pipeline: {e}")
                            response_content = self._generate_mock_response(conversation)"""
    
    # 새로운 transformers 모델 타입 핸들링으로 교체
    chat_content = chat_content.replace(old_transformers_handling, new_transformers_handling)
    
    # 수정된 내용 저장
    with open(chat_engine_path, "w", encoding="utf-8") as file:
        file.write(chat_content)
    
    print("chat_engine.py 파일을 성공적으로 패치했습니다.")

if __name__ == "__main__":
    patch_model_manager()
