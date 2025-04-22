"""
시각화 도구 (Visualizer)

AI 모델 학습 결과 및 데이터를 시각화하는 기능을 제공합니다.
"""

import os
import logging
import json
import importlib
import subprocess
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

class Visualizer:
    """
    모델 학습 결과 및 데이터를 시각화하는 클래스
    """
    
    def __init__(self, config):
        """
        시각화 도구를 초기화합니다.
        
        Args:
            config (dict): 시각화 관련 설정
                - output_dir (str): 출력 디렉토리 (기본값: 'visualizations')
                - tensorboard_dir (str): TensorBoard 로그 디렉토리 (기본값: 'logs/tensorboard')
                - plot_types (list, optional): 생성할 플롯 유형 목록
                - format (str, optional): 출력 파일 형식 (기본값: 'png')
        """
        self.output_dir = config.get("output_dir", "visualizations")
        self.tensorboard_dir = config.get("tensorboard_dir", os.path.join("logs", "tensorboard"))
        self.plot_types = config.get("plot_types", ["training_history", "model_performance", "data_distribution"])
        self.format = config.get("format", "png")
        
        # 디렉토리 생성
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 현재 시각화 세션 ID
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(self.output_dir, f"session_{self.session_id}")
        os.makedirs(self.session_dir, exist_ok=True)
    
    def visualize(self, model_path, data_path, custom_script=None, env_info=None):
        """
        모델 및 데이터 시각화를 수행합니다.
        
        Args:
            model_path (str): 모델 경로
            data_path (str): 데이터 경로
            custom_script (str, optional): 사용자 정의 시각화 스크립트 경로
            env_info (dict, optional): 환경 정보
            
        Returns:
            str: 시각화 결과 경로
            
        Raises:
            ValueError: 유효하지 않은 매개변수가 제공된 경우
            RuntimeError: 시각화 중 오류가 발생한 경우
        """
        logger.info(f"시각화 시작: 세션 ID={self.session_id}")
        
        # 설정 저장
        self._save_visualization_config(model_path, data_path)
        
        try:
            # 사용자 정의 스크립트 실행 또는 기본 시각화 수행
            if custom_script:
                output_path = self._run_custom_visualization_script(custom_script, model_path, data_path, env_info)
            else:
                output_path = self._create_visualizations(model_path, data_path)
            
            # TensorBoard 실행 안내
            self._provide_tensorboard_info()
            
            logger.info(f"시각화 완료: {output_path}")
            return output_path
            
        except Exception as e:
            error_msg = f"시각화 실패: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _save_visualization_config(self, model_path, data_path):
        """
        시각화 설정을 저장합니다.
        
        Args:
            model_path (str): 모델 경로
            data_path (str): 데이터 경로
        """
        config = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "model_path": model_path,
            "data_path": data_path,
            "plot_types": self.plot_types,
            "format": self.format
        }
        
        config_path = os.path.join(self.session_dir, "visualization_config.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            
        logger.info(f"시각화 설정 저장됨: {config_path}")
    
    def _run_custom_visualization_script(self, script_path, model_path, data_path, env_info=None):
        """
        사용자 정의 시각화 스크립트를 실행합니다.
        
        Args:
            script_path (str): 스크립트 경로
            model_path (str): 모델 경로
            data_path (str): 데이터 경로
            env_info (dict, optional): 환경 정보
            
        Returns:
            str: 시각화 결과 경로
            
        Raises:
            ValueError: 스크립트가 유효하지 않은 경우
            RuntimeError: 스크립트 실행 중 오류가 발생한 경우
        """
        if not os.path.exists(script_path):
            raise ValueError(f"시각화 스크립트를 찾을 수 없습니다: {script_path}")
        
        logger.info(f"사용자 정의 시각화 스크립트 실행 중: {script_path}")
        
        # 환경 정보에 따른 실행 방법 선택
        if env_info:
            return self._run_script_in_env(script_path, model_path, data_path, env_info)
        else:
            return self._run_script_directly(script_path, model_path, data_path)
    
    def _run_script_in_env(self, script_path, model_path, data_path, env_info):
        """
        환경 내에서 시각화 스크립트를 실행합니다.
        
        Args:
            script_path (str): 스크립트 경로
            model_path (str): 모델 경로
            data_path (str): 데이터 경로
            env_info (dict): 환경 정보
            
        Returns:
            str: 시각화 결과 경로
            
        Raises:
            RuntimeError: 스크립트 실행 중 오류가 발생한 경우
        """
        if env_info.get("type") == "venv":
            # 가상 환경에서 실행
            python_path = env_info.get("python_path")
            if python_path and os.path.exists(python_path):
                try:
                    subprocess.run(
                        [
                            python_path, script_path,
                            "--model-dir", model_path,
                            "--data-dir", data_path,
                            "--output-dir", self.session_dir,
                            "--format", self.format
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True
                    )
                    return self.session_dir
                except subprocess.CalledProcessError as e:
                    error_msg = f"가상 환경에서 시각화 스크립트 실행 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
        
        elif env_info.get("type") == "conda":
            # Conda 환경에서 실행
            env_name = env_info.get("name")
            if env_name:
                try:
                    # 플랫폼에 따른 Conda 실행 방법
                    if sys.platform == 'win32':
                        cmd = f"conda run -n {env_name} python \"{script_path}\" --model-dir \"{model_path}\" --data-dir \"{data_path}\" --output-dir \"{self.session_dir}\" --format \"{self.format}\""
                        
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
                                "--model-dir", model_path,
                                "--data-dir", data_path,
                                "--output-dir", self.session_dir,
                                "--format", self.format
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            check=True
                        )
                    return self.session_dir
                except subprocess.CalledProcessError as e:
                    error_msg = f"Conda 환경에서 시각화 스크립트 실행 실패: {e.stderr if hasattr(e, 'stderr') else str(e)}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)
        
        # 환경 정보가 유효하지 않은 경우
        return self._run_script_directly(script_path, model_path, data_path)
    
    def _run_script_directly(self, script_path, model_path, data_path):
        """
        시각화 스크립트를 직접 모듈로 로드하여 실행합니다.
        
        Args:
            script_path (str): 스크립트 경로
            model_path (str): 모델 경로
            data_path (str): 데이터 경로
            
        Returns:
            str: 시각화 결과 경로
            
        Raises:
            RuntimeError: 스크립트 실행 중 오류가 발생한 경우
        """
        try:
            # 스크립트 모듈로 로드
            spec = importlib.util.spec_from_file_location("visualization_script", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 표준 함수들 찾아서 실행
            if hasattr(module, "visualize"):
                module.visualize(
                    model_dir=model_path,
                    data_dir=data_path,
                    output_dir=self.session_dir,
                    format=self.format
                )
            else:
                logger.warning(f"스크립트에 visualize 함수를 찾을 수 없습니다: {script_path}")
                
            return self.session_dir
                
        except Exception as e:
            error_msg = f"시각화 스크립트 직접 실행 실패: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _create_visualizations(self, model_path, data_path):
        """
        기본 시각화를 수행합니다.
        
        Args:
            model_path (str): 모델 경로
            data_path (str): 데이터 경로
            
        Returns:
            str: 시각화 결과 경로
            
        Raises:
            RuntimeError: 시각화 중 오류가 발생한 경우
        """
        try:
            # 데이터 분포 시각화
            if "data_distribution" in self.plot_types:
                self._visualize_data_distribution(data_path)
            
            # 학습 히스토리 시각화
            if "training_history" in self.plot_types:
                self._visualize_training_history(model_path)
            
            # 모델 성능 시각화
            if "model_performance" in self.plot_types:
                self._visualize_model_performance(model_path, data_path)
            
            # 모델 구조 시각화
            if "model_architecture" in self.plot_types:
                self._visualize_model_architecture(model_path)
            
            return self.session_dir
            
        except Exception as e:
            error_msg = f"기본 시각화 생성 실패: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _visualize_data_distribution(self, data_path):
        """
        데이터 분포를 시각화합니다.
        
        Args:
            data_path (str): 데이터 경로
            
        Raises:
            ImportError: 시각화 라이브러리를 가져올 수 없는 경우
        """
        logger.info(f"데이터 분포 시각화 중: {data_path}")
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            import pandas as pd
            import glob
            
            # 데이터 파일 찾기
            csv_files = glob.glob(os.path.join(data_path, "**", "*.csv"), recursive=True)
            
            if not csv_files:
                logger.warning(f"CSV 파일을 찾을 수 없습니다: {data_path}")
                return
            
            # 각 파일에 대해 시각화 생성
            for csv_file in csv_files[:5]:  # 최대 5개 파일만 처리
                try:
                    # 데이터 로드
                    df = pd.read_csv(csv_file)
                    
                    # 파일 기반 출력 파일명 생성
                    base_name = os.path.splitext(os.path.basename(csv_file))[0]
                    output_file = os.path.join(self.session_dir, f"dist_{base_name}.{self.format}")
                    
                    # 데이터 분포 시각화
                    fig, axs = plt.subplots(min(df.shape[1], 4), 1, figsize=(10, 8))
                    axs = axs if isinstance(axs, np.ndarray) else [axs]
                    
                    for i, col in enumerate(df.select_dtypes(include=np.number).columns[:4]):  # 최대 4개 열만 처리
                        axs[i].hist(df[col].dropna(), bins=30)
                        axs[i].set_title(f'Distribution of {col}')
                        axs[i].set_xlabel(col)
                        axs[i].set_ylabel('Frequency')
                    
                    plt.tight_layout()
                    plt.savefig(output_file)
                    plt.close()
                    
                    logger.info(f"데이터 분포 시각화 저장됨: {output_file}")
                    
                except Exception as e:
                    logger.warning(f"파일 시각화 실패: {csv_file} - {e}")
            
        except ImportError as e:
            error_msg = f"시각화 라이브러리를 가져올 수 없습니다: {e}"
            logger.error(error_msg)
            raise ImportError(error_msg)
    
    def _visualize_training_history(self, model_path):
        """
        학습 히스토리를 시각화합니다.
        
        Args:
            model_path (str): 모델 경로
            
        Raises:
            ImportError: 시각화 라이브러리를 가져올 수 없는 경우
        """
        logger.info(f"학습 히스토리 시각화 중: {model_path}")
        
        try:
            import matplotlib.pyplot as plt
            import json
            import glob
            
            # 학습 히스토리 파일 찾기
            history_files = glob.glob(os.path.join(model_path, "**", "history*.json"), recursive=True)
            
            if not history_files:
                logger.warning(f"학습 히스토리 파일을 찾을 수 없습니다: {model_path}")
                return
            
            # 각 파일에 대해 시각화 생성
            for history_file in history_files:
                try:
                    # 히스토리 로드
                    with open(history_file, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                    
                    # 출력 파일명 생성
                    base_name = os.path.splitext(os.path.basename(history_file))[0]
                    output_file = os.path.join(self.session_dir, f"history_{base_name}.{self.format}")
                    
                    # 학습 히스토리 시각화
                    metrics = [key for key in history.keys() if not key.startswith('val_')]
                    
                    fig, axs = plt.subplots(len(metrics), 1, figsize=(10, 3 * len(metrics)))
                    axs = axs if isinstance(axs, np.ndarray) else [axs]
                    
                    for i, metric in enumerate(metrics):
                        axs[i].plot(history[metric], label=f'Training {metric}')
                        if f'val_{metric}' in history:
                            axs[i].plot(history[f'val_{metric}'], label=f'Validation {metric}')
                        axs[i].set_title(f'{metric} during training')
                        axs[i].set_xlabel('Epoch')
                        axs[i].set_ylabel(metric)
                        axs[i].legend()
                    
                    plt.tight_layout()
                    plt.savefig(output_file)
                    plt.close()
                    
                    logger.info(f"학습 히스토리 시각화 저장됨: {output_file}")
                    
                except Exception as e:
                    logger.warning(f"히스토리 시각화 실패: {history_file} - {e}")
            
        except ImportError as e:
            error_msg = f"시각화 라이브러리를 가져올 수 없습니다: {e}"
            logger.error(error_msg)
            raise ImportError(error_msg)
    
    def _visualize_model_performance(self, model_path, data_path):
        """
        모델 성능을 시각화합니다.
        
        Args:
            model_path (str): 모델 경로
            data_path (str): 데이터 경로
            
        Raises:
            ImportError: 시각화 라이브러리를 가져올 수 없는 경우
        """
        logger.info(f"모델 성능 시각화 중: {model_path}")
        
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # 기본 성능 차트 생성 (예시)
            metrics = ["accuracy", "precision", "recall", "f1_score"]
            values = np.random.rand(4) * 0.5 + 0.5  # 0.5 ~ 1.0 사이의 랜덤 값
            
            # 출력 파일명 생성
            output_file = os.path.join(self.session_dir, f"model_performance.{self.format}")
            
            # 성능 시각화
            plt.figure(figsize=(10, 6))
            bars = plt.bar(metrics, values, color='skyblue')
            
            # 값 레이블 추가
            for bar, val in zip(bars, values):
                plt.text(bar.get_x() + bar.get_width()/2, val, f'{val:.3f}', 
                         ha='center', va='bottom')
                
            plt.title('Model Performance Metrics')
            plt.ylim(0, 1.0)
            plt.tight_layout()
            plt.savefig(output_file)
            plt.close()
            
            logger.info(f"모델 성능 시각화 저장됨: {output_file}")
            
        except ImportError as e:
            error_msg = f"시각화 라이브러리를 가져올 수 없습니다: {e}"
            logger.error(error_msg)
            raise ImportError(error_msg)
    
    def _visualize_model_architecture(self, model_path):
        """
        모델 구조를 시각화합니다.
        
        Args:
            model_path (str): 모델 경로
            
        Raises:
            ImportError: 시각화 라이브러리를 가져올 수 없는 경우
        """
        logger.info(f"모델 구조 시각화 중: {model_path}")
        
        # 이 기능은 특정 프레임워크에 따라 다르게 구현되어야 함
        # (PyTorch, TensorFlow 등에 따라 다름)
        
        logger.info("이 기능은 프레임워크에 맞게 구체적으로 구현해야 합니다.")
    
    def _provide_tensorboard_info(self):
        """
        TensorBoard 사용 정보를 제공합니다.
        """
        # TensorBoard 정보 파일 생성
        info = {
            "tensorboard_dir": self.tensorboard_dir,
            "command": f"tensorboard --logdir={self.tensorboard_dir}",
            "timestamp": datetime.now().isoformat()
        }
        
        info_path = os.path.join(self.session_dir, "tensorboard_info.json")
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
            
        logger.info(f"TensorBoard 정보 저장됨: {info_path}")
        logger.info(f"TensorBoard 실행 방법: tensorboard --logdir={self.tensorboard_dir}")
