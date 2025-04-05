"""
Git 변경사항 감지 및 처리 모듈

이 모듈은 Git 저장소의 변경사항을 감지하고 분석하는 기능을 제공합니다.
"""

import os
import subprocess
from typing import Dict, List, Set, Tuple, Optional
import logging

# 로깅 설정
logger = logging.getLogger(__name__)


class GitHandler:
    """Git 저장소 상호작용을 관리하는 클래스"""

    def __init__(self, repo_path: str = "."):
        """
        Git 핸들러 초기화
        
        Args:
            repo_path: Git 저장소 경로 (기본값: 현재 디렉토리)
        """
        self.repo_path = os.path.abspath(repo_path)
        if not self._is_git_repo():
            raise ValueError(f"{self.repo_path}는 유효한 Git 저장소가 아닙니다.")

    def _is_git_repo(self) -> bool:
        """현재 디렉토리가 Git 저장소인지 확인"""
        try:
            subprocess.check_output(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=self.repo_path,
                stderr=subprocess.PIPE
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def _run_git_command(self, command: List[str]) -> str:
        """
        Git 명령 실행
        
        Args:
            command: 실행할 Git 명령 인자 리스트
            
        Returns:
            명령 실행 결과 문자열
            
        Raises:
            RuntimeError: Git 명령 실행 실패 시
        """
        try:
            result = subprocess.check_output(
                ["git"] + command,
                cwd=self.repo_path,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            return result.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git 명령 실행 실패: {e.stderr}")
            raise RuntimeError(f"Git 명령 실행 실패: {e.stderr}")

    def get_staged_files(self) -> List[str]:
        """
        스테이징된 파일 목록 조회
        
        Returns:
            스테이징된 파일 경로 목록
        """
        result = self._run_git_command(["diff", "--name-only", "--cached"])
        return result.splitlines() if result else []

    def get_last_commit_files(self) -> List[str]:
        """
        마지막 커밋에서 변경된 파일 목록 조회
        
        Returns:
            변경된 파일 경로 목록
        """
        result = self._run_git_command(["diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"])
        return result.splitlines() if result else []

    def get_uncommitted_changes(self) -> List[str]:
        """
        커밋되지 않은 변경사항이 있는 파일 목록 조회
        
        Returns:
            변경된 파일 경로 목록
        """
        result = self._run_git_command(["diff", "--name-only"])
        return result.splitlines() if result else []

    def get_file_diff(self, file_path: str, staged: bool = False) -> str:
        """
        파일의 diff 내용 조회
        
        Args:
            file_path: 파일 경로
            staged: 스테이징된 변경사항 여부
            
        Returns:
            diff 내용 문자열
        """
        if staged:
            return self._run_git_command(["diff", "--cached", file_path])
        else:
            return self._run_git_command(["diff", file_path])

    def classify_changes(self, files: List[str]) -> Dict[str, List[str]]:
        """
        변경된 파일을 유형별로 분류
        
        Args:
            files: 변경된 파일 목록
            
        Returns:
            파일 유형별 목록을 담은 딕셔너리
        """
        classified = {
            "python": [],
            "router": [],
            "model": [],
            "database": [],
            "test": [],
            "config": [],
            "docs": [],
            "other": []
        }
        
        for file in files:
            # 확장자로 기본 분류
            _, ext = os.path.splitext(file)
            
            if ext.lower() == ".py":
                # Python 파일 세부 분류
                if "/tests/" in file or file.startswith("tests/") or file.endswith("_test.py"):
                    classified["test"].append(file)
                elif "/routes/" in file or "/api/" in file or "router" in file.lower():
                    classified["router"].append(file)
                elif "/models/" in file or "model" in file.lower():
                    classified["model"].append(file)
                elif "/database/" in file or "db" in file.lower():
                    classified["database"].append(file)
                else:
                    classified["python"].append(file)
            elif ext.lower() in [".md", ".rst"]:
                classified["docs"].append(file)
            elif file.endswith(".env") or ext.lower() in [".yml", ".yaml", ".json", ".toml", ".ini"]:
                classified["config"].append(file)
            else:
                classified["other"].append(file)
        
        return classified

    def generate_commit_message(self, files: List[str]) -> str:
        """
        변경된 파일 목록을 기반으로 커밋 메시지 생성
        
        Args:
            files: 변경된 파일 목록
            
        Returns:
            생성된 커밋 메시지
        """
        classified = self.classify_changes(files)
        
        # 변경 유형별로 그룹화
        message_parts = []
        
        if classified["router"]:
            if len(classified["router"]) == 1:
                message_parts.append(f"Update API in {os.path.basename(classified['router'][0])}")
            else:
                message_parts.append(f"Update {len(classified['router'])} API routes")
                
        if classified["model"]:
            if len(classified["model"]) == 1:
                message_parts.append(f"Update model in {os.path.basename(classified['model'][0])}")
            else:
                message_parts.append(f"Update {len(classified['model'])} models")
                
        if classified["database"]:
            message_parts.append("Update database models")
            
        if classified["test"]:
            message_parts.append(f"Update {len(classified['test'])} tests")
            
        if classified["config"]:
            message_parts.append("Update configuration")
            
        if classified["docs"]:
            message_parts.append("Update documentation")
        
        # 나머지 Python 파일
        remaining_py = len(classified["python"])
        if remaining_py > 0:
            message_parts.append(f"Update {remaining_py} Python files")
            
        # 기타 파일
        if classified["other"]:
            message_parts.append(f"Update {len(classified['other'])} other files")
            
        # 최종 메시지 조합
        if message_parts:
            return "; ".join(message_parts)
        else:
            return "Update repository content"

    def stage_files(self, files: List[str]) -> bool:
        """
        파일 스테이징
        
        Args:
            files: 스테이징할 파일 경로 목록
            
        Returns:
            성공 여부
        """
        try:
            for file in files:
                self._run_git_command(["add", file])
            return True
        except Exception as e:
            logger.error(f"파일 스테이징 실패: {str(e)}")
            return False

    def commit_changes(self, message: str, files: Optional[List[str]] = None) -> bool:
        """
        변경사항 커밋
        
        Args:
            message: 커밋 메시지
            files: 커밋할 파일 목록 (None인 경우 스테이징된 모든 파일)
            
        Returns:
            성공 여부
        """
        try:
            if files:
                self.stage_files(files)
                
            self._run_git_command(["commit", "-m", message])
            return True
        except Exception as e:
            logger.error(f"변경사항 커밋 실패: {str(e)}")
            return False

    def push_changes(self, remote: str = "origin", branch: str = "main") -> bool:
        """
        변경사항 원격 저장소에 푸시
        
        Args:
            remote: 원격 저장소 이름
            branch: 브랜치 이름
            
        Returns:
            성공 여부
        """
        try:
            self._run_git_command(["push", remote, branch])
            return True
        except Exception as e:
            logger.error(f"변경사항 푸시 실패: {str(e)}")
            return False

    def get_file_content(self, file_path: str, revision: str = "HEAD") -> str:
        """
        특정 리비전의 파일 내용 조회
        
        Args:
            file_path: 파일 경로
            revision: Git 리비전 (기본값: HEAD)
            
        Returns:
            파일 내용 문자열
        """
        try:
            return self._run_git_command(["show", f"{revision}:{file_path}"])
        except Exception:
            # 파일이 새로 추가된 경우
            if os.path.exists(os.path.join(self.repo_path, file_path)):
                with open(os.path.join(self.repo_path, file_path), 'r', encoding='utf-8') as f:
                    return f.read()
            return ""

    def get_branch_name(self) -> str:
        """
        현재 브랜치 이름 조회
        
        Returns:
            현재 브랜치 이름
        """
        return self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])