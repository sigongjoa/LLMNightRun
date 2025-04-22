"""
GitHub 저장소 AI 분석 모듈

저장소를 분석하여 AI/ML 관련 구성 요소와 가능성을 평가합니다.
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path

from core.logging import get_logger
from core.events import publish

logger = get_logger("github_ai_setup.analyzer")

# AI 관련 패키지 및 파일 패턴
AI_ML_PACKAGES = {
    "python": [
        "tensorflow", "torch", "pytorch", "sklearn", "scikit-learn", 
        "keras", "numpy", "pandas", "huggingface", "transformers",
        "nltk", "spacy", "gensim", "xgboost", "lightgbm", "catboost",
        "langchain", "openai", "llama-index", "faiss"
    ],
    "javascript": [
        "tensorflow", "tensorflow.js", "@tensorflow/tfjs", 
        "ml5", "brain.js", "ml-matrix", "synaptic",
        "natural", "compromise", "nlp.js", "openai"
    ],
    "r": [
        "caret", "mlr", "randomForest", "xgboost", "e1071", 
        "kernlab", "neuralnet", "nnet", "deepnet"
    ]
}

# AI 설정 파일 패턴
AI_CONFIG_FILES = [
    "model-config.json", "model_config.json", "model_config.yaml", "model-config.yaml",
    "ml-config.json", "ml_config.json", "ml_config.yaml", "ml-config.yaml",
    "ai-config.json", "ai_config.json", "ai_config.yaml", "ai-config.yaml",
    ".huggingface", "openai.json", "langchain.json"
]

def analyze_repository(repo_path: str) -> Dict[str, Any]:
    """
    저장소 분석: AI/ML 관련 구성 요소 검색
    
    Args:
        repo_path: 저장소 경로
    
    Returns:
        분석 결과 딕셔너리
    """
    logger.info(f"저장소 AI 분석 중: {repo_path}")
    
    # 결과 딕셔너리
    result = {
        "repo_path": repo_path,
        "has_ai_components": False,
        "ai_packages": [],
        "ai_config_files": [],
        "data_files": [],
        "model_files": [],
        "notebook_files": [],
        "environment_files": [],
        "ai_score": 0.0,
        "recommendations": []
    }
    
    # 패키지 의존성 추출
    requirements = _extract_dependencies(repo_path)
    
    # 저장소 파일 분석
    _analyze_repository_files(repo_path, result, requirements)
    
    # AI 점수 계산 (0-100)
    result["ai_score"] = _calculate_ai_score(result)
    
    # 권장 사항 생성
    result["recommendations"] = _generate_recommendations(result)
    
    # 최종 결과
    result["has_ai_components"] = result["ai_score"] > 10.0
    
    logger.info(f"저장소 AI 분석 완료: 점수 {result['ai_score']:.1f}/100")
    
    # 이벤트 발행
    publish("github_ai.analysis.complete", repo_path=repo_path, score=result["ai_score"])
    
    return result

def _extract_dependencies(repo_path: str) -> Dict[str, List[str]]:
    """의존성 파일에서 패키지 추출"""
    dependencies = {
        "python": [],
        "javascript": [],
        "r": []
    }
    
    # Python 의존성
    for req_file in ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py"]:
        req_path = os.path.join(repo_path, req_file)
        if os.path.exists(req_path):
            try:
                with open(req_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 간단한 패키지 추출 (정교한 파싱은 필요에 따라 개선)
                for pkg in AI_ML_PACKAGES["python"]:
                    if pkg in content.lower():
                        dependencies["python"].append(pkg)
            except Exception as e:
                logger.warning(f"의존성 파일 읽기 실패: {req_file} - {str(e)}")
    
    # JavaScript 의존성
    package_json = os.path.join(repo_path, "package.json")
    if os.path.exists(package_json):
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_deps = {}
            if "dependencies" in data:
                all_deps.update(data["dependencies"])
            if "devDependencies" in data:
                all_deps.update(data["devDependencies"])
            
            for pkg in AI_ML_PACKAGES["javascript"]:
                if pkg in all_deps:
                    dependencies["javascript"].append(pkg)
        except Exception as e:
            logger.warning(f"package.json 읽기 실패: {str(e)}")
    
    # R 의존성
    for r_file in ["DESCRIPTION"]:
        r_path = os.path.join(repo_path, r_file)
        if os.path.exists(r_path):
            try:
                with open(r_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pkg in AI_ML_PACKAGES["r"]:
                    if pkg in content:
                        dependencies["r"].append(pkg)
            except Exception as e:
                logger.warning(f"R 의존성 파일 읽기 실패: {r_file} - {str(e)}")
    
    # 중복 제거
    for key in dependencies:
        dependencies[key] = list(set(dependencies[key]))
    
    return dependencies

def _analyze_repository_files(repo_path: str, result: Dict[str, Any], requirements: Dict[str, List[str]]):
    """저장소 파일 분석"""
    # 파일 카운터
    file_counters = {
        "python": 0,
        "jupyter": 0,
        "data": 0,
        "model": 0,
        "config": 0
    }
    
    # 이미 찾은 AI 패키지
    result["ai_packages"] = []
    for lang, pkgs in requirements.items():
        result["ai_packages"].extend(pkgs)
    
    # 파일 목록 가져오기
    for root, dirs, files in os.walk(repo_path):
        # .git 디렉토리 건너뛰기
        if ".git" in dirs:
            dirs.remove(".git")
        
        # 가상 환경 디렉토리 건너뛰기
        venv_dirs = [d for d in dirs if d in ["venv", "env", "__pycache__", "node_modules"]]
        for d in venv_dirs:
            if d in dirs:
                dirs.remove(d)
        
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, repo_path)
            
            # 파일 확장자
            ext = os.path.splitext(file)[1].lower()
            
            # AI 설정 파일 확인
            if file in AI_CONFIG_FILES or any(pattern in file.lower() for pattern in ["model", "ai_", "ai-", "ml_", "ml-"]):
                result["ai_config_files"].append(relative_path)
                file_counters["config"] += 1
            
            # Jupyter 노트북
            if ext == ".ipynb":
                result["notebook_files"].append(relative_path)
                file_counters["jupyter"] += 1
                
                # 노트북 내용 분석
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        notebook = json.load(f)
                    
                    if "cells" in notebook:
                        for cell in notebook.get("cells", []):
                            source = "".join(cell.get("source", []))
                            for lang, pkgs in AI_ML_PACKAGES.items():
                                for pkg in pkgs:
                                    if f"import {pkg}" in source or f"from {pkg}" in source:
                                        if pkg not in result["ai_packages"]:
                                            result["ai_packages"].append(pkg)
                except Exception as e:
                    logger.debug(f"노트북 분석 실패: {relative_path} - {str(e)}")
            
            # 데이터 파일
            if ext in [".csv", ".json", ".parquet", ".h5", ".hdf5", ".tfrecord", ".txt", ".tsv"]:
                # 크기 확인 (1KB 이상)
                if os.path.getsize(file_path) > 1024:
                    result["data_files"].append(relative_path)
                    file_counters["data"] += 1
            
            # 모델 파일
            if ext in [".pt", ".pth", ".h5", ".pb", ".tflite", ".pkl", ".joblib", ".model", ".weights"]:
                result["model_files"].append(relative_path)
                file_counters["model"] += 1
            
            # 환경 파일
            if file in ["environment.yml", "environment.yaml", "docker-compose.yml", "Dockerfile"]:
                result["environment_files"].append(relative_path)
            
            # Python 파일 분석
            if ext == ".py":
                file_counters["python"] += 1
                
                # 파일 내용 검색
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pkg in AI_ML_PACKAGES["python"]:
                        if f"import {pkg}" in content or f"from {pkg}" in content:
                            if pkg not in result["ai_packages"]:
                                result["ai_packages"].append(pkg)
                except Exception as e:
                    logger.debug(f"Python 파일 분석 실패: {relative_path} - {str(e)}")
    
    # 파일 통계 추가
    result["file_stats"] = file_counters

def _calculate_ai_score(result: Dict[str, Any]) -> float:
    """AI 점수 계산 (0-100)"""
    score = 0.0
    
    # AI 패키지 기반 점수 (최대 40점)
    ai_pkg_count = len(result["ai_packages"])
    score += min(40, ai_pkg_count * 5)
    
    # 데이터 파일 점수 (최대 15점)
    data_file_count = len(result["data_files"])
    score += min(15, data_file_count * 1.5)
    
    # 모델 파일 점수 (최대 20점)
    model_file_count = len(result["model_files"])
    score += min(20, model_file_count * 5)
    
    # 노트북 파일 점수 (최대 15점)
    notebook_file_count = len(result["notebook_files"])
    score += min(15, notebook_file_count * 3)
    
    # 설정 파일 점수 (최대 10점)
    config_file_count = len(result["ai_config_files"])
    score += min(10, config_file_count * 5)
    
    return score

def _generate_recommendations(result: Dict[str, Any]) -> List[str]:
    """AI 저장소 권장 사항 생성"""
    recommendations = []
    
    # 점수 기반 권장 사항
    score = result["ai_score"]
    
    if score < 10:
        recommendations.append("이 저장소는 AI/ML 구성 요소가 거의 없습니다. AI 기능 추가를 고려해보세요.")
    elif score < 30:
        recommendations.append("이 저장소는 일부 AI/ML 구성 요소가 있지만, 완전한 AI 파이프라인이 아닙니다.")
    
    # 특정 구성 요소 기반 권장 사항
    if not result["model_files"] and score > 10:
        recommendations.append("모델 파일이 없습니다. 학습된 모델을 저장하는 방식을 고려해보세요.")
    
    if not result["ai_config_files"] and score > 20:
        recommendations.append("모델 구성 파일이 없습니다. 모델 파라미터 및 설정을 구성 파일로 관리하세요.")
    
    if not result["environment_files"] and score > 30:
        recommendations.append("환경 설정 파일이 없습니다. Docker 또는 conda 환경 파일을 추가하세요.")
    
    # 의존성 관련 권장 사항
    if not result["ai_packages"]:
        recommendations.append("AI/ML 라이브러리 의존성이 없습니다. 적절한 ML 프레임워크를 선택하세요.")
    
    return recommendations

def get_ai_config_status(repo_path: str) -> Dict[str, Any]:
    """
    AI 설정 상태 확인
    
    Args:
        repo_path: 저장소 경로
    
    Returns:
        AI 설정 상태 딕셔너리
    """
    # 설정 파일 확인
    config_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file in AI_CONFIG_FILES:
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                config_files.append(rel_path)
    
    # 설정 상태
    status = {
        "has_config": len(config_files) > 0,
        "config_files": config_files,
        "config_content": None,
        "is_valid": False,
        "missing_components": []
    }
    
    # 첫 번째 설정 파일의 내용 확인
    if config_files:
        try:
            config_path = os.path.join(repo_path, config_files[0])
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith(('.json')):
                    status["config_content"] = json.load(f)
                else:
                    import yaml
                    status["config_content"] = yaml.safe_load(f)
            
            # 필수 구성 요소 확인
            required_fields = ["model", "environment", "parameters"]
            missing = [field for field in required_fields 
                      if not status["config_content"] or field not in status["config_content"]]
            
            status["missing_components"] = missing
            status["is_valid"] = not missing
        
        except Exception as e:
            logger.warning(f"AI 설정 파일 읽기 실패: {str(e)}")
            status["missing_components"] = ["invalid_format"]
    else:
        status["missing_components"] = ["no_config_file"]
    
    return status
