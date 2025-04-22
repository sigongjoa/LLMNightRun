"""
GitHub 핸들러 (GitHub Handler)

GitHub 레포지토리를 다운로드하고 관리하는 기능을 제공합니다.
"""

import os
import logging
import subprocess
import shutil
import re
from pathlib import Path

logger = logging.getLogger(__name__)

class GitHubHandler:
    """
    GitHub 레포지토리를 처리하는 클래스
    """
    
    def __init__(self, config):
        """
        GitHub 핸들러를 초기화합니다.
        
        Args:
            config (dict): GitHub 관련 설정
                - repo_dir (str): 레포지토리를 저장할 디렉토리 (기본값: 'data/repos')
                - auth_token (str, optional): GitHub 인증 토큰
        """
        self.repo_dir = config.get("repo_dir", os.path.join("data", "repos"))
        self.auth_token = config.get("auth_token", None)
        
        # 레포지토리 디렉토리가 없으면 생성
        os.makedirs(self.repo_dir, exist_ok=True)
    
    def clone_repository(self, repo_url):
        """
        GitHub 레포지토리를 클론합니다.
        
        Args:
            repo_url (str): GitHub 레포지토리 URL
            
        Returns:
            str: 클론된 레포지토리의 로컬 경로
            
        Raises:
            ValueError: 유효하지 않은 URL이 제공된 경우
            RuntimeError: 클론 과정에서 오류가 발생한 경우
        """
        # URL 유효성 검사
        if not self._is_valid_github_url(repo_url):
            raise ValueError(f"유효하지 않은 GitHub URL: {repo_url}")
        
        # 레포지토리 이름 추출
        repo_name = self._extract_repo_name(repo_url)
        local_path = os.path.join(self.repo_dir, repo_name)
        
        # 이미 존재하는 경우 삭제
        if os.path.exists(local_path):
            logger.info(f"기존 레포지토리 삭제 중: {local_path}")
            shutil.rmtree(local_path)
        
        # Git 클론 명령 실행
        try:
            logger.info(f"레포지토리 클론 중: {repo_url}")
            clone_url = self._prepare_clone_url(repo_url)
            
            result = subprocess.run(
                ["git", "clone", clone_url, local_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            logger.debug(f"Git 클론 출력: {result.stdout}")
            logger.info(f"레포지토리 클론 완료: {local_path}")
            
            return local_path
            
        except subprocess.CalledProcessError as e:
            error_msg = f"레포지토리 클론 실패: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _is_valid_github_url(self, url):
        """
        GitHub URL의 유효성을 검사합니다.
        
        Args:
            url (str): 검사할 URL
            
        Returns:
            bool: URL이 유효한 GitHub URL인 경우 True
        """
        # GitHub URL 패턴
        github_patterns = [
            r'^https?://github\.com/[\w.-]+/[\w.-]+(?:\.git)?$',
            r'^git@github\.com:[\w.-]+/[\w.-]+(?:\.git)?$'
        ]
        
        return any(re.match(pattern, url) for pattern in github_patterns)
    
    def _extract_repo_name(self, url):
        """
        GitHub URL에서 레포지토리 이름을 추출합니다.
        
        Args:
            url (str): GitHub URL
            
        Returns:
            str: 레포지토리 이름
        """
        # URL에서 레포지토리 이름 추출
        match = re.search(r'[\w.-]+/[\w.-]+(?:\.git)?$', url)
        if match:
            repo_path = match.group(0).replace('.git', '')
            return repo_path.replace('/', '_')
        
        # 기본값 반환
        return "github_repo_" + str(hash(url) % 10000)
    
    def _prepare_clone_url(self, url):
        """
        인증 토큰이 설정된 경우 URL을 준비합니다.
        
        Args:
            url (str): 원본 URL
            
        Returns:
            str: 인증 정보가 추가된 URL
        """
        if not self.auth_token:
            return url
        
        # HTTPS URL인 경우에만 토큰 추가
        if url.startswith('https://'):
            return url.replace('https://', f'https://{self.auth_token}@')
        
        return url
    
    def get_repo_info(self, repo_path):
        """
        레포지토리 정보를 가져옵니다.
        
        Args:
            repo_path (str): 레포지토리 로컬 경로
            
        Returns:
            dict: 레포지토리 정보 (커밋 해시, 브랜치, 태그 등)
            
        Raises:
            FileNotFoundError: 레포지토리 경로가 존재하지 않는 경우
            RuntimeError: Git 명령 실행 중 오류가 발생한 경우
        """
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"레포지토리 경로를 찾을 수 없습니다: {repo_path}")
        
        try:
            # 현재 브랜치 가져오기
            branch_proc = subprocess.run(
                ["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            current_branch = branch_proc.stdout.strip()
            
            # 현재 커밋 해시 가져오기
            commit_proc = subprocess.run(
                ["git", "-C", repo_path, "rev-parse", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            commit_hash = commit_proc.stdout.strip()
            
            # 최신 태그 가져오기
            tag_proc = subprocess.run(
                ["git", "-C", repo_path, "describe", "--tags", "--abbrev=0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            latest_tag = tag_proc.stdout.strip() if tag_proc.returncode == 0 else None
            
            return {
                "path": repo_path,
                "branch": current_branch,
                "commit": commit_hash,
                "tag": latest_tag
            }
            
        except subprocess.CalledProcessError as e:
            error_msg = f"레포지토리 정보 가져오기 실패: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def checkout_version(self, repo_path, version):
        """
        특정 버전(브랜치, 태그, 커밋 해시)으로 체크아웃합니다.
        
        Args:
            repo_path (str): 레포지토리 로컬 경로
            version (str): 체크아웃할 버전
            
        Raises:
            FileNotFoundError: 레포지토리 경로가 존재하지 않는 경우
            RuntimeError: 체크아웃 중 오류가 발생한 경우
        """
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"레포지토리 경로를 찾을 수 없습니다: {repo_path}")
        
        try:
            logger.info(f"버전 체크아웃 중: {version}")
            
            result = subprocess.run(
                ["git", "-C", repo_path, "checkout", version],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            logger.debug(f"Git 체크아웃 출력: {result.stdout}")
            logger.info(f"버전 체크아웃 완료: {version}")
            
        except subprocess.CalledProcessError as e:
            error_msg = f"버전 체크아웃 실패: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def analyze_repo_ai_content(self, repo_path):
        """
        레포지토리에서 AI 관련 파일을 분석합니다.
        
        Args:
            repo_path (str): 레포지토리 로컬 경로
            
        Returns:
            dict: AI 관련 파일 및 구조 정보
            
        Raises:
            FileNotFoundError: 레포지토리 경로가 존재하지 않는 경우
        """
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"레포지토리 경로를 찾을 수 없습니다: {repo_path}")
        
        # 결과 저장할 딕셔너리
        analysis = {
            "framework": None,
            "model_files": [],
            "config_files": [],
            "data_files": [],
            "requirements_file": None,
            "setup_script": None,
            "readme_file": None
        }
        
        # 주요 프레임워크 키워드
        frameworks = {
            "pytorch": ["torch", "pytorch"],
            "tensorflow": ["tensorflow", "tf"],
            "keras": ["keras"],
            "scikit-learn": ["sklearn", "scikit-learn"],
            "huggingface": ["transformers", "huggingface"],
            "jax": ["jax", "flax"]
        }
        
        # 파일 확장자 패턴
        patterns = {
            "model_files": [r'\.py$', r'model', r'train', r'net\.py$'],
            "config_files": [r'\.yaml$', r'\.yml$', r'\.json$', r'config', r'settings'],
            "data_files": [r'\.csv$', r'\.txt$', r'\.jsonl$', r'data', r'dataset']
        }
        
        # 레포지토리 순회
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                file_path = Path(os.path.join(root, file))
                rel_path = file_path.relative_to(repo_path)
                
                # README 파일 확인
                if file.lower() == "readme.md":
                    analysis["readme_file"] = str(rel_path)
                    
                    # README 내용에서 프레임워크 키워드 확인
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read().lower()
                            
                            for framework, keywords in frameworks.items():
                                if any(keyword in content for keyword in keywords):
                                    analysis["framework"] = framework
                                    break
                    except:
                        pass
                
                # 요구사항 파일 확인
                if file.lower() in ["requirements.txt", "environment.yml", "setup.py"]:
                    analysis["requirements_file"] = str(rel_path)
                    
                    # 요구사항 파일에서 프레임워크 키워드 확인
                    if analysis["framework"] is None:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read().lower()
                                
                                for framework, keywords in frameworks.items():
                                    if any(keyword in content for keyword in keywords):
                                        analysis["framework"] = framework
                                        break
                        except:
                            pass
                
                # 설정 스크립트 확인
                if file.lower() in ["setup.sh", "install.sh", "setup.bat", "install.bat"]:
                    analysis["setup_script"] = str(rel_path)
                
                # 파일 분류
                for category, file_patterns in patterns.items():
                    if any(re.search(pattern, str(rel_path), re.IGNORECASE) for pattern in file_patterns):
                        analysis[category].append(str(rel_path))
        
        logger.info(f"레포지토리 분석 완료: {repo_path}")
        logger.debug(f"분석 결과: {analysis}")
        return analysis
