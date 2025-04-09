"""
모델 설치 시스템 컨트롤러

이 모듈은 GitHub 모델 자동 설치 시스템의 핵심 컨트롤러로, 전체 설치 과정을 관리합니다.
"""

import os
import json
import logging
import time
import subprocess
import traceback
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from .github_analyzer import GitHubAnalyzer
from .environment_manager import EnvironmentManager
from .model_directory import ModelDirectoryManager
from .launcher_generator import LauncherGenerator
from .lm_studio_connector import LMStudioConnector
from .mcp_connector import MCPConnector


logger = logging.getLogger(__name__)


class ModelInstallerController:
    """GitHub 모델 자동 설치 시스템의 주요 컨트롤러"""
    
    def __init__(self, models_base_dir: str = "models", lm_studio_url: str = "http://localhost:1234/v1"):
        """
        초기화 함수
        
        Args:
            models_base_dir: 모델이 저장될 기본 디렉토리 (기본값: "models")
            lm_studio_url: LM Studio API URL (기본값: "http://localhost:1234/v1")
        """
        self.models_base_dir = models_base_dir
        
        # 디렉토리 관리자 초기화
        self.dir_manager = ModelDirectoryManager(models_base_dir)
        
        # LM Studio 연결자 초기화
        self.lm_studio = LMStudioConnector(lm_studio_url)
        
        # MCP 연결자 초기화
        self.mcp_connector = MCPConnector()
        
        # 로깅 설정
        self.setup_logging()
    
    def setup_logging(self):
        """로깅 설정"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"model_installer_{int(time.time())}.log")
        
        # 파일 핸들러
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷 설정
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 루트 로거에 핸들러 추가
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        logger.info("Logging setup complete")
    
    def install_model(self, repo_url: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        GitHub 저장소에서 모델 설치
        
        Args:
            repo_url: GitHub 저장소 URL
            model_name: 모델 이름 (기본값: None - 저장소 이름에서 추출)
            
        Returns:
            Dict[str, Any]: 설치 결과 정보
        """
        start_time = time.time()
        logger.info(f"Starting installation of model from {repo_url}")
        
        result = {
            "status": "failed",
            "repo_url": repo_url,
            "model_name": model_name,
            "timestamp": int(start_time),
            "steps": []
        }
        
        try:
            # 1. GitHub 저장소 분석
            analyzer = GitHubAnalyzer(repo_url)
            result["steps"].append({"name": "repo_analysis", "status": "started"})
            
            repo_analysis = analyzer.analyze()
            if "error" in repo_analysis:
                result["steps"][-1]["status"] = "failed"
                result["steps"][-1]["error"] = repo_analysis["error"]
                result["error"] = f"Repository analysis failed: {repo_analysis['error']}"
                return result
            
            result["steps"][-1]["status"] = "completed"
            
            # 모델 이름이 제공되지 않은 경우 저장소 이름 사용
            if not model_name:
                model_name = repo_analysis.get("repo_name", "unknown_model")
            
            result["model_name"] = model_name
            
            # 2. LM Studio로 설치 방법 생성
            result["steps"].append({"name": "installation_analysis", "status": "started"})
            
            install_info = self.lm_studio.analyze_repository(repo_analysis)
            if "error" in install_info:
                result["steps"][-1]["status"] = "failed"
                result["steps"][-1]["error"] = install_info["error"]
                result["error"] = f"Installation analysis failed: {install_info['error']}"
                return result
            
            repo_analysis["install_info"] = install_info
            result["steps"][-1]["status"] = "completed"
            
            # 3. 모델 디렉토리 생성
            result["steps"].append({"name": "directory_creation", "status": "started"})
            
            model_dir = self.dir_manager.create_model_directory(model_name)
            if not model_dir:
                result["steps"][-1]["status"] = "failed"
                result["steps"][-1]["error"] = "Failed to create model directory"
                result["error"] = "Failed to create model directory"
                return result
            
            result["model_dir"] = model_dir
            result["steps"][-1]["status"] = "completed"
            
            # 4. 모델 메타데이터 저장
            result["steps"].append({"name": "metadata_creation", "status": "started"})
            
            metadata = {
                "name": model_name,
                "repo_url": repo_url,
                "repo_analysis": repo_analysis,
                "install_info": install_info,
                "created_at": int(time.time())
            }
            
            if not self.dir_manager.save_model_metadata(model_dir, metadata):
                result["steps"][-1]["status"] = "failed"
                result["steps"][-1]["error"] = "Failed to save model metadata"
                result["error"] = "Failed to save model metadata"
                return result
            
            result["steps"][-1]["status"] = "completed"
            
            # 5. 설정 파일 복사
            result["steps"].append({"name": "config_files_copy", "status": "started"})
            
            copied_configs = self.dir_manager.copy_configuration_files(
                analyzer.clone_path, model_dir
            )
            
            result["steps"][-1]["status"] = "completed"
            result["steps"][-1]["copied_configs"] = copied_configs
            
            # 6. 실행 스크립트 복사
            result["steps"].append({"name": "launch_scripts_copy", "status": "started"})
            
            launch_scripts = repo_analysis.get("launch_scripts", [])
            copied_scripts = self.dir_manager.copy_launch_scripts(
                analyzer.clone_path, model_dir, launch_scripts
            )
            
            result["steps"][-1]["status"] = "completed"
            result["steps"][-1]["copied_scripts"] = copied_scripts
            
            # 7. 가상 환경 설정
            result["steps"].append({"name": "environment_setup", "status": "started"})
            
            env_manager = EnvironmentManager(model_name, model_dir)
            
            # 의존성 패키지 목록
            dependencies = install_info.get("dependencies", [])
            
            # 요구사항 파일 경로
            requirements_file = None
            if "requirements.txt" in repo_analysis.get("requirements", {}):
                requirements_file = os.path.join(analyzer.clone_path, "requirements.txt")
            
            if not env_manager.setup_environment(requirements_file, dependencies):
                result["steps"][-1]["status"] = "failed"
                result["steps"][-1]["error"] = "Failed to set up environment"
                result["error"] = "Failed to set up environment"
                return result
            
            result["steps"][-1]["status"] = "completed"
            
            # 8. 설치 스크립트 생성 및 실행
            result["steps"].append({"name": "setup_script_generation", "status": "started"})
            
            script_info = self.lm_studio.generate_setup_script(repo_analysis, model_dir)
            if "error" in script_info:
                result["steps"][-1]["status"] = "failed"
                result["steps"][-1]["error"] = script_info["error"]
                result["error"] = f"Setup script generation failed: {script_info['error']}"
                return result
            
            setup_script_path = os.path.join(model_dir, "scripts", script_info["filename"])
            with open(setup_script_path, 'w') as f:
                f.write(script_info["script"])
            
            result["steps"][-1]["status"] = "completed"
            result["steps"][-1]["setup_script"] = setup_script_path
            
            # 9. 런처 스크립트 생성
            result["steps"].append({"name": "launcher_generation", "status": "started"})
            
            launcher = LauncherGenerator(model_dir, model_name)
            
            # 각 실행 스크립트에 대한 런처 생성
            generated_launchers = []
            for script in copied_scripts:
                bat_path, sh_path = launcher.generate_run_script(
                    os.path.join("scripts", script)
                )
                generated_launchers.append({
                    "script": script,
                    "bat_path": bat_path,
                    "sh_path": sh_path
                })
            
            # 통합 런처 생성
            universal_bat, universal_sh = launcher.generate_universal_launcher(copied_scripts)
            
            result["steps"][-1]["status"] = "completed"
            result["steps"][-1]["launchers"] = generated_launchers
            result["steps"][-1]["universal_launcher"] = {
                "bat_path": universal_bat,
                "sh_path": universal_sh
            }
            
            # 10. README 생성
            result["steps"].append({"name": "readme_generation", "status": "started"})
            
            readme_path = launcher.generate_readme(repo_analysis, launch_scripts)
            
            result["steps"][-1]["status"] = "completed"
            result["steps"][-1]["readme_path"] = readme_path
            
            # 설치 완료
            elapsed_time = time.time() - start_time
            result["status"] = "success"
            result["elapsed_time"] = elapsed_time
            
            logger.info(f"Model installation completed successfully in {elapsed_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during model installation: {str(e)}")
            logger.error(traceback.format_exc())
            
            # 마지막 단계가 있으면 실패로 표시
            if result["steps"]:
                result["steps"][-1]["status"] = "failed"
                result["steps"][-1]["error"] = str(e)
            
            result["status"] = "failed"
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()
            
            return result
    
    def list_installed_models(self) -> List[Dict[str, Any]]:
        """
        설치된 모델 목록 조회
        
        Returns:
            List[Dict[str, Any]]: 설치된 모델 정보 목록
        """
        return self.dir_manager.list_model_directories()
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        모델 정보 조회
        
        Args:
            model_name: 모델 이름
            
        Returns:
            Optional[Dict[str, Any]]: 모델 정보 (없는 경우 None)
        """
        model_dir = self.dir_manager.get_model_directory(model_name)
        if not model_dir:
            return None
        
        metadata_path = os.path.join(model_dir, "config", "metadata.json")
        if not os.path.exists(metadata_path):
            return {
                "name": model_name,
                "path": model_dir,
                "error": "Metadata file not found"
            }
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            return {
                "name": model_name,
                "path": model_dir,
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Error reading model metadata: {str(e)}")
            return {
                "name": model_name,
                "path": model_dir,
                "error": f"Error reading metadata: {str(e)}"
            }
    
    def run_model(self, model_name: str, script_name: Optional[str] = None) -> Dict[str, Any]:
        """
        모델 실행
        
        Args:
            model_name: 모델 이름
            script_name: 실행할 스크립트 이름 (기본값: None - 통합 런처 사용)
            
        Returns:
            Dict[str, Any]: 실행 결과 정보
        """
        model_dir = self.dir_manager.get_model_directory(model_name)
        if not model_dir:
            return {"status": "failed", "error": f"Model '{model_name}' not found"}
        
        scripts_dir = os.path.join(model_dir, "scripts")
        
        result = {
            "status": "failed",
            "model_name": model_name,
            "model_dir": model_dir,
            "timestamp": int(time.time())
        }
        
        try:
            # 실행할 스크립트 결정
            if script_name:
                if os.name == 'nt':  # Windows
                    script_path = os.path.join(scripts_dir, f"run_{script_name}.bat")
                else:  # Unix
                    script_path = os.path.join(scripts_dir, f"run_{script_name}.sh")
                
                if not os.path.exists(script_path):
                    return {"status": "failed", "error": f"Script '{script_name}' not found"}
                
                result["script_path"] = script_path
                result["script_name"] = script_name
                
            else:  # 통합 런처 사용
                if os.name == 'nt':  # Windows
                    script_path = os.path.join(scripts_dir, "launcher.bat")
                else:  # Unix
                    script_path = os.path.join(scripts_dir, "launcher.sh")
                
                if not os.path.exists(script_path):
                    return {"status": "failed", "error": "Launcher script not found"}
                
                result["script_path"] = script_path
                result["script_name"] = "launcher"
            
            # 스크립트 실행
            logger.info(f"Running model {model_name} with script {script_path}")
            
            if os.name == 'nt':  # Windows
                process = subprocess.Popen(
                    script_path,
                    cwd=model_dir,
                    shell=True
                )
            else:  # Unix
                process = subprocess.Popen(
                    ["bash", script_path],
                    cwd=model_dir
                )
            
            result["status"] = "success"
            result["process_id"] = process.pid
            result["message"] = f"Model {model_name} started with script {script_path}"
            
            return result
                
        except Exception as e:
            logger.error(f"Error running model {model_name}: {str(e)}")
            result["status"] = "failed"
            result["error"] = str(e)
            return result
    
    def analyze_error(self, error_log: str) -> Dict[str, Any]:
        """
        에러 로그 분석
        
        Args:
            error_log: 에러 로그
            
        Returns:
            Dict[str, Any]: 분석 결과 및 해결 방안
        """
        return self.lm_studio.analyze_error_log(error_log)
    
    def push_to_mcp(self, model_name: str) -> Dict[str, Any]:
        """
        설치된 모델을 MCP 서버에 푸시
        
        Args:
            model_name: 모델 이름
            
        Returns:
            Dict[str, Any]: 푸시 결과 정보
        """
        model_info = self.get_model_info(model_name)
        if not model_info:
            return {"status": "failed", "error": f"Model '{model_name}' not found"}
        
        if "error" in model_info:
            return {"status": "failed", "error": model_info["error"]}
        
        model_dir = model_info["path"]
        metadata = model_info.get("metadata", {})
        
        logger.info(f"Pushing model {model_name} to MCP server")
        
        result = self.mcp_connector.upload_model(model_dir, metadata)
        
        return result
    
    def get_mcp_model_status(self, model_name: str) -> Dict[str, Any]:
        """
        MCP 서버에 업로드된 모델 상태 조회
        
        Args:
            model_name: 모델 이름
            
        Returns:
            Dict[str, Any]: 모델 상태 정보
        """
        return self.mcp_connector.get_model_status(model_name)
    
    def update_mcp_model(self, model_name: str) -> Dict[str, Any]:
        """
        MCP 서버에 업로드된 모델 업데이트
        
        Args:
            model_name: 모델 이름
            
        Returns:
            Dict[str, Any]: 업데이트 결과 정보
        """
        model_info = self.get_model_info(model_name)
        if not model_info:
            return {"status": "failed", "error": f"Model '{model_name}' not found"}
        
        if "error" in model_info:
            return {"status": "failed", "error": model_info["error"]}
        
        model_dir = model_info["path"]
        metadata = model_info.get("metadata", {})
        
        logger.info(f"Updating model {model_name} on MCP server")
        
        result = self.mcp_connector.update_model(model_name, model_dir, metadata)
        
        return result
