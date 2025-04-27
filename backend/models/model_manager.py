"""
ModelManager is responsible for managing language models in the application.
It handles model downloading, loading, listing, and unloading.
"""

import os
import json
import logging
import threading
import time
import torch
import numpy as np
from typing import Dict, List, Optional, Union, Any

# LLM 라이브러리들 임포트 - transformers와 llama.cpp (llama-cpp-python) 사용
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    from llama_cpp import Llama  # llama-cpp-python 패키지
    from gpt4all import GPT4All  # GPT4All Python 바인딩
    HAS_LLM_LIBS = True
except ImportError:
    HAS_LLM_LIBS = False
    logging.warning("Some LLM libraries are not available. Please install them: pip install transformers llama-cpp-python gpt4all")

# DO NOT CHANGE CODE: Core model management functionality
# TEMP: Current implementation works but will be refactored later

class ModelManager:
    def __init__(self, models_dir: str = None, auto_install_default: bool = True):
        """
        Initialize the ModelManager with the directory to store models.
        
        Args:
            models_dir: Directory to store downloaded models
            auto_install_default: Whether to automatically install a default model
        """
        self.models_dir = models_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "models")
        self.models_info_path = os.path.join(self.models_dir, "models_info.json")
        self.loaded_models = {}  # key: model_id, value: model instance & metadata
        self.available_models = {}
        self._load_lock = threading.RLock()
        self._refresh_timer = None  # To maintain consistency between is_loaded flags and loaded_models
        
        # Ensure models directory exists
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Load model information if exists
        self._load_models_info()
        
        # Auto-install and load a default model if requested
        if auto_install_default:
            self._ensure_default_model()
            
        # Start the refresh timer to maintain consistency
        self._start_refresh_timer()
    
    def _load_models_info(self):
        """Load available models information from the models_info.json file."""
        if os.path.exists(self.models_info_path):
            try:
                with open(self.models_info_path, 'r', encoding='utf-8') as f:
                    self.available_models = json.load(f)
            except Exception as e:
                logging.error(f"Error loading models info: {e}")
                self.available_models = {}
        
        # If no models found or error occurred, initialize with default HuggingFace model (Qwen only)
        if not self.available_models:
            self.available_models = {
                "Qwen/Qwen2.5-3B": {
                    "id": "Qwen/Qwen2.5-3B",
                    "name": "Qwen2.5-3B",
                    "description": "Alibaba's Qwen2.5-3B model - small and efficient for general text generation.",
                    "size": "1.9GB",
                    "ram_required": "6GB",
                    "parameters": "3B",
                    "quant": "None",
                    "type": "huggingface",
                    "is_installed": True,
                    "is_loaded": False
                }
            }
            self._save_models_info()
    
    def _save_models_info(self):
        """Save model information to the models_info.json file."""
        try:
            with open(self.models_info_path, 'w', encoding='utf-8') as f:
                json.dump(self.available_models, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving models info: {e}")
    
    def _ensure_default_model(self):
        """Ensure that at least one model is installed and loaded."""
        # Check if any model is already installed
        installed_models = self.get_installed_models()
        if installed_models:
            # Load the first installed model if not already loaded
            model_id = installed_models[0].get("id")
            if model_id and not installed_models[0].get("is_loaded", False):
                self.load_model(model_id)
            return
        
        # Add only the Qwen model
        qwen_model_info = {
            "id": "Qwen/Qwen2.5-3B",
            "name": "Qwen2.5-3B",
            "description": "Alibaba's Qwen2.5-3B model - small and efficient for general text generation.",
            "size": "1.9GB",
            "ram_required": "6GB",
            "parameters": "3B",
            "quant": "None",
            "type": "huggingface",
            "is_installed": True,
            "is_loaded": False
        }
        
        # Add model to available_models
        logging.info("Adding default Qwen model")
        self.add_model_source(qwen_model_info)
        
        # Load the model
        logging.info("Loading default Qwen model")
        self.load_model("Qwen/Qwen2.5-3B")
    
    def _start_refresh_timer(self):
        """
        Start a timer to periodically check and fix inconsistencies between 
        available_models flags and loaded_models dictionary
        """
        if not self._refresh_timer:
            import threading
            self._refresh_timer = threading.Timer(5.0, self._check_model_consistency)
            self._refresh_timer.daemon = True  # Allow the program to exit even if the timer is running
            self._refresh_timer.start()
    
    def _check_model_consistency(self):
        """
        Check and fix inconsistencies between available_models flags and loaded_models dictionary
        This ensures that models marked as loaded are actually in the loaded_models dictionary
        """
        try:
            with self._load_lock:
                # Clean up loaded_models - remove any models not in available_models
                for model_id in list(self.loaded_models.keys()):
                    if model_id not in self.available_models:
                        logging.info(f"Removing {model_id} from loaded_models as it's no longer in available_models")
                        self.loaded_models.pop(model_id, None)
                
                # Find models marked as loaded but not in loaded_models
                for model_id, model_info in self.available_models.items():
                    if model_info.get("is_loaded", False) and model_id not in self.loaded_models:
                        # For Qwen model, try to actually load it
                        if model_id == "Qwen/Qwen2.5-3B":
                            logging.info(f"Qwen model marked as loaded but not in loaded_models. Attempting to load.")
                            try:
                                self.load_model(model_id)
                                continue
                            except Exception as e:
                                logging.error(f"Error loading Qwen model: {e}")
                        
                        # For other models or if loading failed, create a placeholder and update the flag
                        try:
                            logging.info(f"Attempting to load model {model_id} properly")
                            self.load_model(model_id)
                        except Exception as e:
                            logging.error(f"Error fixing model inconsistency for {model_id}: {e}")
                
                # Find models in loaded_models but marked as not loaded in available_models
                for model_id in list(self.loaded_models.keys()):
                    if model_id in self.available_models and not self.available_models[model_id].get("is_loaded", False):
                        # Update the flag to match reality
                        self.available_models[model_id]["is_loaded"] = True
                        if "runtime" not in self.available_models[model_id]:
                            self.available_models[model_id]["runtime"] = {}
                        self.available_models[model_id]["runtime"]["status"] = "loaded"
                        logging.info(f"Updated {model_id} status to loaded")
        except Exception as e:
            logging.error(f"Error in consistency check: {e}")
        finally:
            # Schedule the next check
            if self._refresh_timer:
                self._refresh_timer = threading.Timer(5.0, self._check_model_consistency)
                self._refresh_timer.daemon = True
                self._refresh_timer.start()
    
    def get_available_models(self) -> List[Dict]:
        """
        Get a list of all available models (both installed and not installed).
        
        Returns:
            List of model information dictionaries
        """
        return list(self.available_models.values())
    
    def get_installed_models(self) -> List[Dict]:
        """
        Get a list of installed models.
        
        Returns:
            List of installed model information dictionaries
        """
        return [model for model in self.available_models.values() if model.get("is_installed", False)]
    
    def get_model_info(self, model_id: str) -> Optional[Dict]:
        """
        Get information about a specific model.
        
        Args:
            model_id: ID of the model to get information for
            
        Returns:
            Dictionary with model information or None if model not found
        """
        return self.available_models.get(model_id)
    
    def download_model(self, model_id: str, progress_callback=None) -> bool:
        """
        Download a model to the models directory.
        
        Args:
            model_id: ID of the model to download
            progress_callback: Optional callback for download progress updates
            
        Returns:
            True if download was successful, False otherwise
        """
        try:
            model_info = self.available_models.get(model_id)
            if not model_info:
                logging.error(f"Model {model_id} not found in available models")
                return False
                
            # 실제 모델 다운로드 구현
            download_url = model_info.get('download_url')
            if not download_url:
                logging.error(f"No download URL for model {model_id}")
                return False
                
            # 모델 파일 경로 설정
            model_path = os.path.join(self.models_dir, f"{model_id}.bin")
            
            # 이미 다운로드된 모델인지 확인
            if os.path.exists(model_path):
                # 이미 존재하는 모델은 새로 다운로드하지 않고 성공으로 처리
                model_info["is_installed"] = True
                self._save_models_info()
                logging.info(f"Model {model_id} already exists at {model_path}")
                return True
            
            # 파이썬에서 모델 다운로드
            import requests
            from tqdm import tqdm
            import shutil
            
            # 로그 메시지 출력
            logging.info(f"Downloading model {model_id} from {download_url}")
            
            # 시작 시간 기록
            start_time = time.time()
            
            # 요청 보내기
            response = requests.get(download_url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 * 1024  # 1MB
            
            # 크기가 없는 경우 처리
            if total_size == 0:
                total_size = None  # tqdm에서는 None으로 처리
            
            # 무조건 상위 디렉토리 생성 확인
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            # 다운로드 진행 및 프로그레스 보여주기
            with open(model_path, 'wb') as f:
                # tqdm을 사용하여 진행률 표시
                with tqdm(total=total_size, unit='iB', unit_scale=True, unit_divisor=1024) as pbar:
                    for chunk in response.iter_content(chunk_size=block_size):
                        if chunk:  # 데이터가 있는 경우에만 처리
                            f.write(chunk)
                            pbar.update(len(chunk))
                            
                            # 콜백이 있는 경우 진행률 전달
                            if progress_callback and total_size:
                                progress_percentage = min(int((pbar.n / total_size) * 100), 100)
                                progress_callback(progress_percentage)
            
            # 다운로드 시간 계산
            download_time = time.time() - start_time
            logging.info(f"Model {model_id} downloaded successfully in {download_time:.1f} seconds")
            
            # 모델 정보 업데이트
            model_info["is_installed"] = True
            self.available_models[model_id] = model_info
            self._save_models_info()
            
            return True
        except Exception as e:
            logging.error(f"Error downloading model {model_id}: {e}")
            # 다운로드 실패 시 부분적으로 다운로드된 파일이 있을 수 있으므로 삭제
            model_path = os.path.join(self.models_dir, f"{model_id}.bin")
            if os.path.exists(model_path):
                try:
                    os.remove(model_path)
                    logging.info(f"Removed partial download file: {model_path}")
                except Exception as remove_error:
                    logging.error(f"Error removing partial download file: {remove_error}")
            return False
    
    def load_model(self, model_id: str) -> bool:
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
                if model_id in self.loaded_models:
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
                            
                            # Check if CUDA/GPU is available
                            cuda_available = torch.cuda.is_available()
                            device = "cuda" if cuda_available else "cpu"
                            logging.info(f"CUDA available: {cuda_available}, using device: {device}")
                            
                            # We now only use Qwen model with more explicit settings
                            logging.info(f"Loading Qwen model on device {device}")
                            
                            # Import necessary components for more control
                            from transformers import AutoModelForCausalLM, AutoTokenizer, TextGenerationPipeline
                            
                            # Load model components explicitly with proper settings
                            logging.info("Loading Qwen2.5-3B model and tokenizer separately for better control")
                            
                            # Load tokenizer with proper settings
                            tokenizer = AutoTokenizer.from_pretrained(
                                "Qwen/Qwen2.5-3B", 
                                trust_remote_code=True,
                                padding_side="right"
                            )
                            
                            # Set proper pad token to avoid warnings
                            if tokenizer.pad_token is None:
                                tokenizer.pad_token = tokenizer.eos_token
                            
                            # Load model with device_map="auto" for automatic placement
                            # Note: Extended context is handled by the model configuration
                            model = AutoModelForCausalLM.from_pretrained(
                                "Qwen/Qwen2.5-3B", 
                                device_map="auto",  # This handles device placement automatically
                                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                                trust_remote_code=True,
                                low_cpu_mem_usage=True
                            )
                            
                            # For Qwen models, we don't need to specify max_length directly
                            # as it's determined by the model's default configuration
                            
                            # Create a pipeline manually without specifying device
                            model_object = TextGenerationPipeline(
                                model=model,
                                tokenizer=tokenizer
                                # Don't specify device here as it's already set when loading the model
                            )
                            
                            # Store the tokenizer as well
                            self.tokenizer = tokenizer
                            model_type = "transformers"
                            logging.info(f"Successfully loaded model on {device}")
                        except Exception as e:  
                            import traceback
                            logging.error(f"Failed to load Qwen model: {e}")
                            logging.error(f"Traceback: {traceback.format_exc()}")
                            # Instead of using mock_model_object, raise the exception so we actually handle the error
                            raise
                    else:
                        logging.error("Transformers library not available.")
                        raise ImportError("Transformers library not available for model loading")
                except Exception as e:
                    logging.error(f"Error loading model {model_id}: {e}")
                    raise  # Re-raise the exception so we know there was a problem
                
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
                
                return True  # Model was successfully loaded
            except Exception as e:
                logging.error(f"Error loading model {model_id}: {e}")
                return False
    
    def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_id: ID of the model to unload
            
        Returns:
            True if unloading was successful, False otherwise
        """
        with self._load_lock:
            try:
                # If the model is not loaded, just return success
                if model_id not in self.loaded_models:
                    # Make sure the is_loaded flag is false for consistency
                    if model_id in self.available_models and self.available_models[model_id].get("is_loaded", False):
                        self.available_models[model_id]["is_loaded"] = False
                        if "runtime" in self.available_models[model_id]:
                            self.available_models[model_id]["runtime"]["status"] = "unloaded"
                        self._save_models_info()
                    
                    logging.info(f"Model {model_id} is not loaded")
                    return True
                
                # In a real implementation, this would properly clean up the model resources
                # For this demo, we'll just simulate unloading
                logging.info(f"Unloading model {model_id}")
                
                # Instead of removing from loaded_models, keep it but mark as unloaded
                # This preserves the model reference while still indicating it's not actively used
                self.loaded_models[model_id]["status"] = "unloaded"
                
                # Update model information to reflect the unloaded state
                if model_id in self.available_models:
                    model_info = self.available_models[model_id]
                    model_info["is_loaded"] = False
                    if "runtime" in model_info:
                        model_info["runtime"]["status"] = "unloaded"
                    self._save_models_info()
                
                return True
            except Exception as e:
                logging.error(f"Error unloading model {model_id}: {e}")
                return False
    
    def delete_model(self, model_id: str) -> bool:
        """
        Delete a model from disk.
        
        Args:
            model_id: ID of the model to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            with self._load_lock:  # Use the lock to ensure thread safety
                # Unload the model first if it's loaded
                if model_id in self.loaded_models:
                    # Instead of fully unloading, just mark it as unloaded
                    self.loaded_models[model_id]["status"] = "unloaded"
                
                model_path = os.path.join(self.models_dir, f"{model_id}.bin")
                
                # Delete the model file if it exists
                if os.path.exists(model_path):
                    os.remove(model_path)
                
                # Update model information
                if model_id in self.available_models:
                    model_info = self.available_models[model_id]
                    model_info["is_installed"] = False
                    model_info["is_loaded"] = False
                    if "runtime" in model_info:
                        model_info["runtime"]["status"] = "unloaded"
                    self._save_models_info()
                
                return True
        except Exception as e:
            logging.error(f"Error deleting model {model_id}: {e}")
            return False
    
    def add_model_source(self, model_info: Dict) -> bool:
        """
        Add a new model source to the available models.
        
        Args:
            model_info: Dictionary with model information
            
        Returns:
            True if addition was successful, False otherwise
        """
        try:
            model_id = model_info.get("id")
            if not model_id:
                logging.error("Model information must include an 'id' field")
                return False
            
            # Add or update model information
            self.available_models[model_id] = model_info
            self._save_models_info()
            
            return True
        except Exception as e:
            logging.error(f"Error adding model source: {e}")
            return False
    
    def get_loaded_model(self, model_id: str):
        """
        Get a loaded model object.
        
        Args:
            model_id: ID of the model to get
            
        Returns:
            The loaded model object or None if not loaded
        """
        return self.loaded_models.get(model_id, {}).get("model_object")
