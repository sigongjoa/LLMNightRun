"""
GitHub AI 설정 관리자 모듈

AI 설정을 위한 통합 인터페이스를 제공합니다.
"""

import os
import json
import shutil
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime

from core.logging import get_logger
from core.events import publish, subscribe
from core.config import get_config

from .analyzer import analyze_repository, get_ai_config_status
from .config_generator import generate_ai_config, apply_ai_config
from .environment import setup_environment, check_environment

logger = get_logger("github_ai_setup.manager")

class GitHubAIManager:
    """GitHub AI 설정 관리자 클래스"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        GitHub AI 설정 관리자 초기화
        
        Args:
            data_dir: 데이터 저장 디렉토리 (기본값: 설정에서 가져옴)
        """
        config = get_config()
        
        # 데이터 디렉토리 설정
        self.data_dir = data_dir or os.path.join(
            config.get("core", "data_dir", "data"),
            "github_ai"
        )
        
        # 하위 디렉토리 설정
        self.repos_dir = os.path.join(self.data_dir, "repositories")
        self.configs_dir = os.path.join(self.data_dir, "configs")
        self.reports_dir = os.path.join(self.data_dir, "reports")
        
        # 디렉토리 생성
        for directory in [self.data_dir, self.repos_dir, self.configs_dir, self.reports_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # 이벤트 구독
        subscribe("github_ai.analysis.complete", self._on_analysis_complete)
        subscribe("github_ai.config.applied", self._on_config_applied)
        
        logger.info("GitHub AI 설정 관리자 초기화됨")
    
    def analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        저장소 분석
        
        Args:
            repo_path: 저장소 경로
        
        Returns:
            분석 결과 딕셔너리
        """
        # 저장소 복사본 생성
        repo_name = os.path.basename(repo_path)
        target_dir = os.path.join(self.repos_dir, f"{repo_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        if not os.path.exists(repo_path):
            logger.error(f"저장소를 찾을 수 없음: {repo_path}")
            return {"error": "Repository not found"}
        
        try:
            # 저장소 분석
            analysis = analyze_repository(repo_path)
            
            # 분석 결과 저장
            report_path = os.path.join(self.reports_dir, f"{repo_name}_analysis.json")
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            logger.info(f"저장소 분석 보고서 저장됨: {report_path}")
            analysis["report_path"] = report_path
            
            return analysis
        
        except Exception as e:
            logger.error(f"저장소 분석 중 오류 발생: {str(e)}")
            return {"error": str(e)}
    
    def generate_config(self, repo_path: str, framework: str, model_type: str, 
                       parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        AI 구성 생성
        
        Args:
            repo_path: 저장소 경로
            framework: AI 프레임워크 이름
            model_type: 모델 타입 (예: "classification", "generation", "embedding")
            parameters: 모델 파라미터 (기본값: 자동 생성)
        
        Returns:
            생성된 구성 딕셔너리
        """
        try:
            # 구성 생성
            config = generate_ai_config(repo_path, framework, model_type, parameters)
            
            # 구성 저장
            repo_name = os.path.basename(repo_path)
            config_path = os.path.join(self.configs_dir, f"{repo_name}_config.json")
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"AI 구성 저장됨: {config_path}")
            
            return config
        
        except Exception as e:
            logger.error(f"AI 구성 생성 중 오류 발생: {str(e)}")
            return {"error": str(e)}
    
    def apply_config(self, repo_path: str, config: Dict[str, Any], 
                    file_format: str = "json") -> Dict[str, Any]:
        """
        AI 구성 적용
        
        Args:
            repo_path: 저장소 경로
            config: AI 구성 딕셔너리
            file_format: 파일 형식 ("json" 또는 "yaml")
        
        Returns:
            적용 결과 딕셔너리
        """
        try:
            # 구성 적용
            config_path = apply_ai_config(repo_path, config, file_format)
            
            if not config_path:
                return {"success": False, "error": "구성 적용 실패"}
            
            # 환경 설정
            env_result = setup_environment(repo_path, config.get("environment", {}))
            
            return {
                "success": True,
                "config_path": config_path,
                "environment_setup": env_result
            }
        
        except Exception as e:
            logger.error(f"AI 구성 적용 중 오류 발생: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def clone_repository(self, git_url: str) -> str:
        """
        Git 저장소 복제
        
        Args:
            git_url: Git 저장소 URL
        
        Returns:
            복제된 저장소 경로
        """
        repo_name = os.path.basename(git_url)
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        
        target_dir = os.path.join(self.repos_dir, repo_name)
        
        try:
            # 이미 존재하는 경우 제거
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            # Git 명령 실행
            subprocess.check_call(
                ["git", "clone", git_url, target_dir],
                stderr=subprocess.STDOUT
            )
            
            logger.info(f"저장소 복제됨: {git_url} -> {target_dir}")
            
            return target_dir
        
        except subprocess.CalledProcessError as e:
            logger.error(f"Git 복제 실패: {str(e)}")
            return ""
        
        except Exception as e:
            logger.error(f"저장소 복제 중 오류 발생: {str(e)}")
            return ""
    
    def setup_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        저장소 AI 설정 원스톱 셋업
        
        Args:
            repo_path: 저장소 경로
        
        Returns:
            설정 결과 딕셔너리
        """
        # 결과 딕셔너리
        result = {
            "success": False,
            "steps": {
                "analysis": False,
                "config_generation": False,
                "config_applied": False,
                "environment_setup": False
            },
            "repository": os.path.basename(repo_path),
            "repository_path": repo_path
        }
        
        try:
            # 1. 저장소 분석
            analysis = self.analyze_repository(repo_path)
            
            if "error" in analysis:
                result["error"] = analysis["error"]
                return result
            
            result["steps"]["analysis"] = True
            result["analysis"] = {
                "ai_score": analysis["ai_score"],
                "has_ai_components": analysis["has_ai_components"]
            }
            
            # 2. 프레임워크 감지
            framework = None
            for pkg in analysis["ai_packages"]:
                if pkg in ["tensorflow", "torch", "pytorch", "huggingface", "langchain", "openai"]:
                    framework = pkg
                    break
            
            if not framework:
                if analysis["ai_score"] > 30:
                    framework = "pytorch"  # 기본값
                else:
                    result["error"] = "AI 프레임워크를 감지할 수 없음"
                    return result
            
            # 3. 모델 타입 추론
            model_type = "classification"  # 기본값
            if any("embedding" in f for f in analysis.get("model_files", [])):
                model_type = "embedding"
            elif any("generator" in f for f in analysis.get("model_files", [])):
                model_type = "generation"
            
            # 4. 구성 생성
            config = self.generate_config(repo_path, framework, model_type)
            
            if "error" in config:
                result["error"] = config["error"]
                return result
            
            result["steps"]["config_generation"] = True
            
            # 5. 구성 적용
            apply_result = self.apply_config(repo_path, config)
            
            if not apply_result.get("success", False):
                result["error"] = apply_result.get("error", "구성 적용 실패")
                return result
            
            result["steps"]["config_applied"] = True
            result["config_path"] = apply_result["config_path"]
            
            # 6. 환경 설정
            result["steps"]["environment_setup"] = apply_result.get("environment_setup", {}).get("success", False)
            result["files_created"] = apply_result.get("environment_setup", {}).get("files_created", [])
            
            # 성공!
            result["success"] = True
            
            # 이벤트 발행
            publish("github_ai.setup.complete", repo_path=repo_path, success=True)
            
            return result
        
        except Exception as e:
            logger.error(f"저장소 AI 설정 중 오류 발생: {str(e)}")
            result["error"] = str(e)
            
            # 이벤트 발행
            publish("github_ai.setup.complete", repo_path=repo_path, success=False, error=str(e))
            
            return result
    
    def list_repositories(self) -> List[Dict[str, Any]]:
        """
        관리된 저장소 목록 가져오기
        
        Returns:
            저장소 정보 목록
        """
        repositories = []
        
        try:
            # 저장소 디렉토리 검색
            for repo_dir in os.listdir(self.repos_dir):
                path = os.path.join(self.repos_dir, repo_dir)
                
                if not os.path.isdir(path):
                    continue
                
                # 기본 정보
                repo_info = {
                    "name": repo_dir,
                    "path": path,
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(path)).isoformat(),
                    "has_config": False,
                    "has_environment": False
                }
                
                # 구성 파일 확인
                if os.path.exists(os.path.join(path, "ai-config.json")) or \
                   os.path.exists(os.path.join(path, "ai-config.yaml")):
                    repo_info["has_config"] = True
                
                # 환경 파일 확인
                if os.path.exists(os.path.join(path, "requirements.txt")) or \
                   os.path.exists(os.path.join(path, "environment.yml")) or \
                   os.path.exists(os.path.join(path, "Dockerfile")):
                    repo_info["has_environment"] = True
                
                repositories.append(repo_info)
        
        except Exception as e:
            logger.error(f"저장소 목록 가져오기 실패: {str(e)}")
        
        # 수정 시간 기준 정렬
        repositories.sort(key=lambda x: x["last_modified"], reverse=True)
        
        return repositories
    
    def _on_analysis_complete(self, repo_path=None, score=None):
        """분석 완료 이벤트 핸들러"""
        if repo_path and score is not None:
            logger.info(f"저장소 분석 완료: {repo_path}, 점수: {score}")
    
    def _on_config_applied(self, repo_path=None, config_path=None):
        """구성 적용 완료 이벤트 핸들러"""
        if repo_path and config_path:
            logger.info(f"AI 구성 적용됨: {repo_path}, 구성 파일: {config_path}")
