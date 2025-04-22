"""
모델 트레이너 (Model Trainer)

AI 모델 학습 및 관리 기능을 제공합니다.
"""

import os
import logging
import json
import importlib
import subprocess
import sys
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

class ModelTrainer:
    """
    AI 모델을 학습하는 클래스
    """
    
    def __init__(self, config):
        """
        모델 트레이너를 초기화합니다.
        
        Args:
            config (dict): 학습 관련 설정
                - model_dir (str): 모델 저장 디렉토리 (기본값: 'models')
                - tensorboard_dir (str): TensorBoard 로그 디렉토리 (기본값: 'logs/tensorboard')
                - checkpoint_dir (str): 체크포인트 디렉토리 (기본값: 'models/checkpoints')
                - model_type (str, optional): 모델 유형
                - hyperparameters (dict, optional): 하이퍼파라미터
                - epochs (int, optional): 학습 에폭 수
                - batch_size (int, optional): 배치 크기
        """
        self.model_dir = config.get("model_dir", "models")
        self.tensorboard_dir = config.get("tensorboard_dir", os.path.join("logs", "tensorboard"))
        self.checkpoint_dir = config.get("checkpoint_dir", os.path.join("models", "checkpoints"))
        self.model_type = config.get("model_type")
        self.hyperparameters = config.get("hyperparameters", {})
        self.epochs = config.get("epochs", 10)
        self.batch_size = config.get("batch_size", 32)
        
        # 디렉토리 생성
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.tensorboard_dir, exist_ok=True)
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        # 현재 학습 세션 ID
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(self.model_dir, f"session_{self.session_id}")
        os.makedirs(self.session_dir, exist_ok=True)
    
    def train(self, data_path, custom_script=None, env_info=None):
        """
        모델 학습을 수행합니다.
        
        Args:
            data_path (str): 전처리된 데이터 경로
            custom_script (str, optional): 사용자 정의 학습 스크립트 경로
            env_info (dict, optional): 환경 정보
            
        Returns:
            str: 학습된 모델 경로
            
        Raises:
            ValueError: 유효하지 않은 매개변수가 제공된 경우
            RuntimeError: 학습 중 오류가 발생한 경우
        """
        logger.info(f"모델 학습 시작: 세션 ID={self.session_id}")
        
        # 설정 저장
        self._save_training_config(data_path)
        
        try:
            # 사용자 정의 스크립트 실행 또는 기본 학습 수행
            if custom_script:
                model_path = self._run_custom_training_script(custom_script, data_path, env_info)
            else:
                model_path = self._train_model(data_path, env_info)
            
            logger.info(f"모델 학습 완료: {model_path}")
            return model_path
            
        except Exception as e:
            error_msg = f"모델 학습 실패: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _save_training_config(self, data_path):
        """
        학습 설정을 저장합니다.
        
        Args:
            data_path (str): 데이터 경로
        """
        config = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "model_type": self.model_type,
            "hyperparameters": self.hyperparameters,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "data_path": data_path,
            "tensorboard_dir": os.path.join(self.tensorboard_dir, self.session_id)
        }
        
        config_path = os.path.join(self.session_dir, "training_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        logger.info(f"학습 설정 저장됨: {config_path}")
    
    def _run_custom_training_script(self, script_path, data_path, env_info=None):
        """
        사용자 정의 학습 스크립트를 실행합니다.
        
        Args:
            script_path (str): 스크립트 경로
            data_path (str): 데이터 경로
            env_info (dict, optional): 환경 정보
            
        Returns:
            str: 학습된 모델 경로
            
        Raises:
            ValueError: 스크립트가 유효하지 않은 경우
            RuntimeError: 스크립트 실행 중 오류가 발생한 경우
        """
        if not os.path.exists(script_path):
            raise ValueError(f"학습 스크립트를 찾을 수 없습니다: {script_path}")
        
        logger.info(f"사용자 정의 학습 스크립트 실행 중: {script_path}")
        
        # 환경 정보에 따른 실행 방법 선택
        if env_info:
            return self._run_script_in_env(script_path, data_path, env_info)
        else:
            return self._run_script_directly(script_path, data_path)
    
    def _run_script_in_env(self, script_path, data_path, env_info):
        """
        환경 내에서 학습 스크립트를 실행합니다.
        
        Args:
            script_path (str): 스크립트 경로
            data_path (str): 데이터 경로
            env_info (dict): 환경 정보
            
        Returns:
            str: 학습된 모델 경로
            
        Raises:
            RuntimeError: 스크립트 실행 중 오류가 발생한 경우
        """
        model_path = os.path.join(self.session_dir, "model")
        
        if env_info.get("type") == "venv":
            # 가상 환경에서 실행
            python_path = env_info.get("python_path")
            if python_path and os.path.exists(python_path):
                try:
                    subprocess.run(
                        [
                            python_path, script_path,
                            "--data-dir", data_path,
                            "--model-dir", model_path,
                            "--tensorboard-dir", os.path.join(self.tensorboard_dir, self.session_id),
                            "--epochs", str(self.epochs),
                            "--batch-size", str(self.batch_size),
                            "--hyperparams", json.dumps(self.hyperparameters)
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True
                    )
                    return model_path
                except subprocess.CalledProcessError as e:
                    error_msg = f"가상 환경에서 학습 스크립트 실행 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
        
        elif env_info.get("type") == "conda":
            # Conda 환경에서 실행
            env_name = env_info.get("name")
            if env_name:
                try:
                    # 플랫폼에 따른 Conda 실행 방법
                    if sys.platform == 'win32':
                        hyperparams_str = json.dumps(self.hyperparameters).replace('"', '\\"')
                        cmd = f"conda run -n {env_name} python \"{script_path}\" --data-dir \"{data_path}\" --model-dir \"{model_path}\" --tensorboard-dir \"{os.path.join(self.tensorboard_dir, self.session_id)}\" --epochs {self.epochs} --batch-size {self.batch_size} --hyperparams \"{hyperparams_str}\""
                        
                        subprocess.run(
                            cmd,
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True
                        )
                    else:
                        subprocess.run(
                            [
                                "conda", "run", "-n", env_name,
                                "python", script_path,
                                "--data-dir", data_path,
                                "--model-dir", model_path,
                                "--tensorboard-dir", os.path.join(self.tensorboard_dir, self.session_id),
                                "--epochs", str(self.epochs),
                                "--batch-size", str(self.batch_size),
                                "--hyperparams", json.dumps(self.hyperparameters)
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True
                        )
                    return model_path
                except subprocess.CalledProcessError as e:
                    error_msg = f"Conda 환경에서 학습 스크립트 실행 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
        
        # 환경 정보가 유효하지 않은 경우
        return self._run_script_directly(script_path, data_path)
    
    def _run_script_directly(self, script_path, data_path):
        """
        학습 스크립트를 직접 모듈로 로드하여 실행합니다.
        
        Args:
            script_path (str): 스크립트 경로
            data_path (str): 데이터 경로
            
        Returns:
            str: 학습된 모델 경로
            
        Raises:
            RuntimeError: 스크립트 실행 중 오류가 발생한 경우
        """
        model_path = os.path.join(self.session_dir, "model")
        os.makedirs(model_path, exist_ok=True)
        
        try:
            # 스크립트 모듈로 로드
            spec = importlib.util.spec_from_file_location("training_script", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 표준 함수들 찾아서 실행
            if hasattr(module, "train"):
                module.train(
                    data_dir=data_path,
                    model_dir=model_path,
                    tensorboard_dir=os.path.join(self.tensorboard_dir, self.session_id),
                    epochs=self.epochs,
                    batch_size=self.batch_size,
                    hyperparameters=self.hyperparameters
                )
            else:
                logger.warning(f"스크립트에 train 함수를 찾을 수 없습니다: {script_path}")
                
            return model_path
                
        except Exception as e:
            error_msg = f"학습 스크립트 직접 실행 실패: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _train_model(self, data_path, env_info=None):
        """
        기본 학습 로직을 수행합니다.
        
        Args:
            data_path (str): 데이터 경로
            env_info (dict, optional): 환경 정보
            
        Returns:
            str: 학습된 모델 경로
            
        Raises:
            ValueError: 모델 유형이 지정되지 않은 경우
            RuntimeError: 학습 중 오류가 발생한 경우
        """
        if not self.model_type:
            raise ValueError("모델 유형이 지정되지 않았습니다.")
        
        model_path = os.path.join(self.session_dir, "model")
        os.makedirs(model_path, exist_ok=True)
        
        # 기본 모델 유형에 따른 학습 수행
        try:
            if self.model_type.lower() == "pytorch":
                self._train_pytorch_model(data_path, model_path)
            elif self.model_type.lower() == "tensorflow":
                self._train_tensorflow_model(data_path, model_path)
            elif self.model_type.lower() == "scikit-learn":
                self._train_sklearn_model(data_path, model_path)
            else:
                raise ValueError(f"지원되지 않는 모델 유형: {self.model_type}")
                
            return model_path
            
        except Exception as e:
            error_msg = f"모델 학습 중 오류 발생: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _train_pytorch_model(self, data_path, model_path):
        """
        PyTorch 모델 학습을 수행합니다. (예시 구현)
        
        Args:
            data_path (str): 데이터 경로
            model_path (str): 모델 저장 경로
            
        Raises:
            ImportError: PyTorch를 가져올 수 없는 경우
        """
        logger.info("PyTorch 모델 학습 시작")
        
        try:
            import torch
            from torch.utils.tensorboard import SummaryWriter
            
            # TensorBoard 설정
            writer = SummaryWriter(os.path.join(self.tensorboard_dir, self.session_id))
            
            # 모델 학습 로직 (실제 구현 필요)
            # 이 부분은 예시 코드이며, 실제 프로젝트에 맞게 구현해야 합니다.
            
            # 학습 완료 후 TensorBoard 종료
            writer.close()
            
            # 모델 저장
            dummy_model = {"state": "trained", "type": "pytorch"}
            torch.save(dummy_model, os.path.join(model_path, "model.pt"))
            
            logger.info(f"PyTorch 모델 저장 완료: {model_path}")
            
        except ImportError as e:
            error_msg = f"PyTorch 모듈을 가져올 수 없습니다: {e}"
            logger.error(error_msg)
            raise ImportError(error_msg)
    
    def _train_tensorflow_model(self, data_path, model_path):
        """
        TensorFlow 모델 학습을 수행합니다. (예시 구현)
        
        Args:
            data_path (str): 데이터 경로
            model_path (str): 모델 저장 경로
            
        Raises:
            ImportError: TensorFlow를 가져올 수 없는 경우
        """
        logger.info("TensorFlow 모델 학습 시작")
        
        try:
            import tensorflow as tf
            
            # TensorBoard 설정
            tensorboard_callback = tf.keras.callbacks.TensorBoard(
                log_dir=os.path.join(self.tensorboard_dir, self.session_id),
                histogram_freq=1
            )
            
            # 모델 학습 로직 (실제 구현 필요)
            # 이 부분은 예시 코드이며, 실제 프로젝트에 맞게 구현해야 합니다.
            
            # 모델 저장
            dummy_model = tf.keras.Sequential()
            dummy_model.save(os.path.join(model_path, "model.h5"))
            
            logger.info(f"TensorFlow 모델 저장 완료: {model_path}")
            
        except ImportError as e:
            error_msg = f"TensorFlow 모듈을 가져올 수 없습니다: {e}"
            logger.error(error_msg)
            raise ImportError(error_msg)
    
    def _train_sklearn_model(self, data_path, model_path):
        """
        scikit-learn 모델 학습을 수행합니다. (예시 구현)
        
        Args:
            data_path (str): 데이터 경로
            model_path (str): 모델 저장 경로
            
        Raises:
            ImportError: scikit-learn을 가져올 수 없는 경우
        """
        logger.info("scikit-learn 모델 학습 시작")
        
        try:
            import joblib
            import numpy as np
            from sklearn.linear_model import LogisticRegression
            
            # 모델 학습 로직 (실제 구현 필요)
            # 이 부분은 예시 코드이며, 실제 프로젝트에 맞게 구현해야 합니다.
            
            # 더미 데이터 및 모델
            X = np.random.random((100, 5))
            y = np.random.randint(0, 2, 100)
            model = LogisticRegression()
            model.fit(X, y)
            
            # 모델 저장
            joblib.dump(model, os.path.join(model_path, "model.joblib"))
            
            logger.info(f"scikit-learn 모델 저장 완료: {model_path}")
            
        except ImportError as e:
            error_msg = f"scikit-learn 모듈을 가져올 수 없습니다: {e}"
            logger.error(error_msg)
            raise ImportError(error_msg)
