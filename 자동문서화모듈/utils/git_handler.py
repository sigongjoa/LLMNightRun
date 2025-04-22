"""
Git 연동 기능을 위한 유틸리티
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

class GitHandler:
    """Git 연동을 위한 클래스"""
    
    def __init__(self, repo_path: Optional[str] = None):
        """
        GitHandler 초기화
        
        Args:
            repo_path: Git 저장소 경로 (없으면 현재 디렉토리)
        """
        self.repo_path = repo_path if repo_path else os.getcwd()
        
    def is_git_repo(self) -> bool:
        """
        현재 디렉토리가 Git 저장소인지 확인
        
        Returns:
            Git 저장소 여부
        """
        try:
            result = self._run_git_command(['rev-parse', '--is-inside-work-tree'])
            return result.returncode == 0
        except Exception:
            return False
    
    def _run_git_command(self, args: list, cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """
        Git 명령 실행
        
        Args:
            args: Git 명령 인수 리스트
            cwd: 작업 디렉토리 (없으면 repo_path)
            
        Returns:
            명령 실행 결과
        """
        work_dir = cwd if cwd else self.repo_path
        return subprocess.run(['git'] + args, cwd=work_dir, 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              text=True, encoding='utf-8')
    
    def add_file(self, file_path: str) -> Tuple[bool, str]:
        """
        파일을 Git 스테이지에 추가
        
        Args:
            file_path: 추가할 파일 경로
            
        Returns:
            (성공 여부, 메시지) 튜플
        """
        if not self.is_git_repo():
            return False, "Git 저장소가 아닙니다."
            
        try:
            # 파일 경로가 저장소 내부인지 확인
            abs_file_path = os.path.abspath(file_path)
            abs_repo_path = os.path.abspath(self.repo_path)
            
            if not abs_file_path.startswith(abs_repo_path):
                return False, f"파일이 저장소 외부에 있습니다: {abs_file_path} (저장소: {abs_repo_path})"
            
            # 저장소 루트에 대한 상대 경로로 변환
            rel_path = os.path.relpath(abs_file_path, abs_repo_path)
            
            result = self._run_git_command(['add', rel_path])
            if result.returncode == 0:
                return True, f"파일 추가 성공: {rel_path}"
            else:
                return False, f"파일 추가 실패: {result.stderr}"
        except Exception as e:
            return False, f"파일 추가 중 오류 발생: {str(e)}"
    
    def commit(self, message: str) -> Tuple[bool, str]:
        """
        변경사항 커밋
        
        Args:
            message: 커밋 메시지
            
        Returns:
            (성공 여부, 메시지) 튜플
        """
        if not self.is_git_repo():
            return False, "Git 저장소가 아닙니다."
            
        try:
            result = self._run_git_command(['commit', '-m', message])
            if result.returncode == 0:
                return True, f"커밋 성공: {message}"
            else:
                return False, f"커밋 실패: {result.stderr}"
        except Exception as e:
            return False, f"커밋 중 오류 발생: {str(e)}"
    
    def get_status(self) -> Tuple[bool, str]:
        """
        저장소 상태 확인
        
        Returns:
            (성공 여부, 상태 메시지) 튜플
        """
        if not self.is_git_repo():
            return False, "Git 저장소가 아닙니다."
            
        try:
            result = self._run_git_command(['status', '--porcelain'])
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, f"상태 확인 실패: {result.stderr}"
        except Exception as e:
            return False, f"상태 확인 중 오류 발생: {str(e)}"
    
    def format_commit_message(self, commit_info: Dict[str, str]) -> str:
        """
        커밋 정보를 Conventional Commit 형식으로 변환
        
        Args:
            commit_info: 커밋 정보 딕셔너리 (type, scope, message)
            
        Returns:
            형식에 맞는 커밋 메시지
        """
        commit_type = commit_info.get("type", "docs")
        scope = commit_info.get("scope", None)
        message = commit_info.get("message", "Update documentation")
        
        if scope:
            return f"{commit_type}({scope}): {message}"
        else:
            return f"{commit_type}: {message}"
    
    def copy_to_repo(self, source_path: str, target_subdir: str = "docs") -> Tuple[bool, str, Optional[str]]:
        """
        파일을 Git 저장소 내부로 복사
        
        Args:
            source_path: 원본 파일 경로
            target_subdir: 대상 하위 디렉토리 (저장소 루트에 대한 상대 경로)
            
        Returns:
            (성공 여부, 메시지, 대상 파일 경로) 튜플
        """
        if not self.is_git_repo():
            return False, "Git 저장소가 아닙니다.", None
            
        try:
            # 원본 파일 경로 확인
            if not os.path.exists(source_path):
                return False, f"원본 파일이 존재하지 않습니다: {source_path}", None
                
            # 대상 디렉토리 생성
            target_dir = os.path.join(self.repo_path, target_subdir)
            os.makedirs(target_dir, exist_ok=True)
            
            # 파일 이름 추출
            file_name = os.path.basename(source_path)
            
            # 대상 파일 경로
            target_path = os.path.join(target_dir, file_name)
            
            # 파일 복사
            shutil.copy2(source_path, target_path)
            
            return True, f"파일 복사 성공: {source_path} -> {target_path}", target_path
        except Exception as e:
            return False, f"파일 복사 중 오류 발생: {str(e)}", None
    
    def push(self, remote: str = "origin", branch: str = "main") -> Tuple[bool, str]:
        """
        변경사항을 원격 저장소에 푸시
        
        Args:
            remote: 원격 저장소 이름 (기본값: origin)
            branch: 브랜치 이름 (기본값: main)
            
        Returns:
            (성공 여부, 메시지) 튜플
        """
        if not self.is_git_repo():
            return False, "Git 저장소가 아닙니다."
            
        try:
            result = self._run_git_command(['push', remote, branch])
            if result.returncode == 0:
                return True, f"푸시 성공: {remote}/{branch}"
            else:
                return False, f"푸시 실패: {result.stderr}"
        except Exception as e:
            return False, f"푸시 중 오류 발생: {str(e)}"
    
    def get_current_branch(self) -> Tuple[bool, str]:
        """
        현재 작업 중인 브랜치 이름 확인
        
        Returns:
            (성공 여부, 브랜치 이름 또는 오류 메시지) 튜플
        """
        if not self.is_git_repo():
            return False, "Git 저장소가 아닙니다."
            
        try:
            result = self._run_git_command(['branch', '--show-current'])
            if result.returncode == 0:
                branch = result.stdout.strip()
                return True, branch if branch else "main"
            else:
                return False, f"브랜치 확인 실패: {result.stderr}"
        except Exception as e:
            return False, f"브랜치 확인 중 오류 발생: {str(e)}"
    
    def get_remotes(self) -> Tuple[bool, List[str]]:
        """
        원격 저장소 목록 확인
        
        Returns:
            (성공 여부, 원격 저장소 목록 또는 오류 메시지) 튜플
        """
        if not self.is_git_repo():
            return False, "Git 저장소가 아닙니다."
            
        try:
            result = self._run_git_command(['remote'])
            if result.returncode == 0:
                remotes = [r.strip() for r in result.stdout.split('\n') if r.strip()]
                return True, remotes
            else:
                return False, [f"원격 저장소 확인 실패: {result.stderr}"]
        except Exception as e:
            return False, [f"원격 저장소 확인 중 오류 발생: {str(e)}"]
    
    def commit_document(self, file_path: str, commit_info: Dict[str, str], target_subdir: str = "docs") -> Tuple[bool, str]:
        """
        문서 파일 추가 및 커밋
        
        Args:
            file_path: 문서 파일 경로
            commit_info: 커밋 정보 딕셔너리 (type, scope, message)
            target_subdir: 저장소 내 대상 하위 디렉토리
            
        Returns:
            (성공 여부, 메시지) 튜플
        """
        # 파일 경로가 저장소 내부인지 확인
        abs_file_path = os.path.abspath(file_path)
        abs_repo_path = os.path.abspath(self.repo_path)
        
        repo_file_path = file_path
        
        # 파일이 저장소 외부에 있는 경우 저장소 내부로 복사
        if not abs_file_path.startswith(abs_repo_path):
            copy_success, copy_message, repo_file_path = self.copy_to_repo(file_path, target_subdir)
            if not copy_success:
                return copy_success, copy_message
        
        # 파일 추가
        add_success, add_message = self.add_file(repo_file_path)
        if not add_success:
            return add_success, add_message
            
        # 커밋 메시지 생성
        commit_message = self.format_commit_message(commit_info)
        
        # 커밋
        return self.commit(commit_message)
