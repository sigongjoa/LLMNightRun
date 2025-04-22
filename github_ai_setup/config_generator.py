"""
AI 구성 파일 생성 모듈

GitHub 저장소에 대한 AI 구성 파일을 생성하고 적용하는 기능을 제공합니다.
"""

import os
import json
import yaml
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path

from core.logging import get_logger
from core.events import publish
from core.config import get_config

from .analyzer import analyze_repository, get_ai_config_status

logger = get_logger("github_ai_setup.config_generator")

# 지원되는 프레임워크
SUPPORTED_FRAMEWORKS = [
    "tensorflow", "pytorch", "sklearn", "huggingface", 
    "langchain", "openai", "spacy", "nltk"
]

def generate_ai_config(repo_path: str, framework: str, model_type: str, 
                     parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    AI 구성 파일 생성
    
    Args:
        repo_path: 저장소 경로
        framework: AI 프레임워크 이름
        model_type: 모델 타입 (예: "classification", "generation", "embedding")
        parameters: 모델 파라미터 (기본값: 자동 생성)
    
    Returns:
        생성된 구성 딕셔너리
    """
    logger.info(f"AI 구성 생성 중: {repo_path}, 프레임워크: {framework}, 모델 타입: {model_type}")
    
    # 저장소 분석
    analysis = analyze_repository(repo_path)
    
    # 프레임워크 확인
    if framework not in SUPPORTED_FRAMEWORKS:
        logger.warning(f"지원되지 않는 프레임워크: {framework}")
        framework = _detect_framework(analysis) or "pytorch"
    
    # 구성 템플릿 가져오기
    template = _get_config_template(framework, model_type)
    
    # 파라미터 생성 또는 결합
    if parameters:
        template["parameters"].update(parameters)
    
    # 환경 설정 생성
    template["environment"] = _generate_environment_config(repo_path, framework)
    
    # 구성 생성
    config = {
        "name": os.path.basename(repo_path),
        "framework": framework,
        "model_type": model_type,
        "version": "1.0.0",
        "description": f"{framework} {model_type} model configuration",
        "environment": template["environment"],
        "model": template["model"],
        "parameters": template["parameters"],
        "training": template["training"],
        "evaluation": template["evaluation"],
        "deployment": template["deployment"]
    }
    
    # 이벤트 발행
    publish("github_ai.config.generated", repo_path=repo_path, framework=framework)
    
    return config

def apply_ai_config(repo_path: str, config: Dict[str, Any], file_format: str = "json") -> str:
    """
    생성된 AI 구성을 저장소에 적용
    
    Args:
        repo_path: 저장소 경로
        config: AI 구성 딕셔너리
        file_format: 파일 형식 ("json" 또는 "yaml")
    
    Returns:
        저장된 구성 파일 경로
    """
    # 파일 이름 생성
    filename = "ai-config." + file_format.lower()
    config_path = os.path.join(repo_path, filename)
    
    # 구성 저장
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            if file_format.lower() == "json":
                json.dump(config, f, indent=2, ensure_ascii=False)
            else:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"AI 구성 파일 저장됨: {config_path}")
        
        # 이벤트 발행
        publish("github_ai.config.applied", repo_path=repo_path, config_path=config_path)
        
        return config_path
    
    except Exception as e:
        logger.error(f"AI 구성 저장 실패: {str(e)}")
        return ""

def _detect_framework(analysis: Dict[str, Any]) -> Optional[str]:
    """분석 결과에서 사용된 프레임워크 감지"""
    for pkg in analysis["ai_packages"]:
        for framework in SUPPORTED_FRAMEWORKS:
            if framework in pkg.lower():
                return framework
    
    return None

def _get_config_template(framework: str, model_type: str) -> Dict[str, Any]:
    """프레임워크 및 모델 타입에 따른 구성 템플릿 제공"""
    # 기본 템플릿
    template = {
        "model": {
            "name": f"{framework}_{model_type}_model",
            "architecture": "default",
            "input_shape": None,
            "output_shape": None
        },
        "parameters": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 10,
            "optimizer": "adam"
        },
        "training": {
            "data": {
                "train_path": "data/train",
                "val_path": "data/validation",
                "format": "csv"
            },
            "callbacks": [],
            "metrics": ["accuracy"]
        },
        "evaluation": {
            "data": "data/test",
            "metrics": ["accuracy", "f1_score"]
        },
        "deployment": {
            "method": "rest_api",
            "format": "native",
            "requirements": []
        }
    }
    
    # 프레임워크별 템플릿 사용자 정의
    if framework == "tensorflow":
        template["model"]["architecture"] = "sequential"
        template["parameters"]["optimizer"] = "adam"
        template["deployment"]["format"] = "saved_model"
    
    elif framework == "pytorch":
        template["model"]["architecture"] = "nn.Module"
        template["parameters"]["optimizer"] = "SGD"
        template["deployment"]["format"] = "torchscript"
    
    elif framework == "huggingface":
        template["model"]["architecture"] = "transformers"
        template["model"]["base_model"] = "bert-base-uncased" if "bert" in model_type else "t5-small"
        template["parameters"]["optimizer"] = "AdamW"
        template["parameters"]["weight_decay"] = 0.01
    
    elif framework == "langchain":
        template["model"]["architecture"] = "chain"
        template["model"]["components"] = ["llm", "embeddings", "vectorstore"]
        template["parameters"] = {
            "temperature": 0.7,
            "max_tokens": 500
        }
    
    elif framework == "openai":
        template["model"]["architecture"] = "openai"
        template["model"]["base_model"] = "gpt-4"
        template["parameters"] = {
            "temperature": 0.7,
            "max_tokens": 500,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
    
    # 모델 타입별 사용자 정의
    if model_type == "classification":
        template["model"]["output_activation"] = "softmax"
        template["evaluation"]["metrics"].append("confusion_matrix")
    
    elif model_type == "regression":
        template["model"]["output_activation"] = "linear"
        template["evaluation"]["metrics"] = ["mse", "mae", "r2"]
    
    elif model_type == "generation":
        template["parameters"]["temperature"] = 0.7
        template["parameters"]["max_length"] = 100
        template["evaluation"]["metrics"] = ["perplexity", "bleu"]
    
    elif model_type == "embedding":
        template["model"]["output_shape"] = [None, 768]
        template["evaluation"]["metrics"] = ["cosine_similarity"]
    
    return template

def _generate_environment_config(repo_path: str, framework: str) -> Dict[str, Any]:
    """프레임워크에 따른 환경 설정 생성"""
    # 기본 환경 설정
    env_config = {
        "python_version": "3.8",
        "cuda_version": "11.8",
        "packages": [
            f"{framework}",
            "numpy",
            "pandas"
        ],
        "system_dependencies": []
    }
    
    # 프레임워크별 패키지 추가
    if framework == "tensorflow":
        env_config["packages"].extend(["tensorflow>=2.10.0", "tensorboard"])
    
    elif framework == "pytorch":
        env_config["packages"].extend(["torch>=2.0.0", "torchvision", "torchaudio"])
    
    elif framework == "huggingface":
        env_config["packages"].extend(["transformers>=4.25.0", "datasets", "evaluate"])
    
    elif framework == "langchain":
        env_config["packages"].extend(["langchain>=0.0.200", "openai", "faiss-cpu"])
    
    elif framework == "sklearn":
        env_config["packages"].extend(["scikit-learn>=1.0.0", "matplotlib", "joblib"])
    
    # Dockerfile 생성 플래그
    env_config["generate_dockerfile"] = True
    
    # requirements.txt 생성 플래그
    env_config["generate_requirements"] = True
    
    return env_config
