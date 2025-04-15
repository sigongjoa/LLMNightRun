"""
AI 환경 설정 적용기

생성된 AI 환경 설정을 GitHub 저장소에 적용합니다.
"""

import os
import logging
import tempfile
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path
import base64
import json

# 로깅 설정
logger = logging.getLogger("github_ai_setup.applier")


class AISetupApplier:
    """
    AI 환경 설정 적용 클래스
    
    생성된 설정 파일을 실제 저장소에 적용합니다.
    """
    
    def __init__(self, repo_data: Dict[str, Any], setup_result: Dict[str, Any]):
        """
        적용기 초기화
        
        Args:
            repo_data: 저장소 정보
            setup_result: 생성된 설정 정보
        """
        self.repo_data = repo_data
        self.setup_result = setup_result
        self.repo_url = repo_data.get("url", "")
        self.repo_path = repo_data.get("path")
        self.branch = repo_data.get("branch", "main")
        self.access_token = repo_data.get("access_token")
        
        # 저장소 ID 설정
        if "repo_id" in setup_result:
            self.repo_id = setup_result["repo_id"]
        else:
            # URL에서 소유자/저장소 추출
            parts = self.repo_url.strip('/').split('/')
            if 'github.com' in parts and len(parts) >= 5:
                self.repo_id = f"{parts[-2]}/{parts[-1]}"
            else:
                self.repo_id = "unknown/unknown"
        
        logger.info(f"AI 환경 설정 적용기 초기화: {self.repo_id}")
    
    async def apply(self, create_pr: bool = True, pr_title: str = None, pr_body: str = None) -> Dict[str, Any]:
        """
        설정 적용 실행
        
        Args:
            create_pr: 풀 리퀘스트 생성 여부
            pr_title: 풀 리퀘스트 제목
            pr_body: 풀 리퀘스트 본문
            
        Returns:
            적용 결과
        """
        try:
            logger.info(f"AI 환경 설정 적용 시작: {self.repo_id}")
            
            # 적용할 파일 목록 수집
            files_to_apply = self._collect_files_to_apply()
            
            # 로컬 저장소가 제공된 경우
            if self.repo_path and os.path.exists(self.repo_path):
                # 로컬 저장소에 직접 적용
                applied_files = await self._apply_to_local_repo(files_to_apply)
                pr_url = None
            else:
                # GitHub API를 통해 적용 (임시 클론 후 PR 생성)
                applied_files, pr_url = await self._apply_via_github_api(
                    files_to_apply, create_pr, pr_title, pr_body
                )
            
            # 결과 반환
            result = {
                "repo_id": self.repo_id,
                "status": "completed",
                "applied_files": applied_files,
            }
            
            if pr_url:
                result["pull_request_url"] = pr_url
            
            logger.info(f"AI 환경 설정 적용 완료: {self.repo_id}, 파일 수: {len(applied_files)}")
            return result
            
        except Exception as e:
            logger.error(f"AI 환경 설정 적용 오류: {str(e)}")
            return {
                "repo_id": self.repo_id,
                "status": "failed",
                "error": str(e),
                "applied_files": []
            }
    
    def _collect_files_to_apply(self) -> List[Dict[str, Any]]:
        """
        적용할 파일 목록 수집
        
        Returns:
            적용할 파일 목록
        """
        files = []
        
        # 구성 파일
        if "config_files" in self.setup_result:
            files.extend(self.setup_result["config_files"])
        
        # 설치 스크립트
        if "setup_scripts" in self.setup_result:
            files.extend(self.setup_result["setup_scripts"])
        
        # 워크플로우
        if "workflows" in self.setup_result:
            files.extend(self.setup_result["workflows"])
        
        # 문서
        if "documentation" in self.setup_result and isinstance(self.setup_result["documentation"], dict):
            files.append(self.setup_result["documentation"])
        
        return files
    
    async def _apply_to_local_repo(self, files_to_apply: List[Dict[str, Any]]) -> List[str]:
        """
        로컬 저장소에 파일 적용
        
        Args:
            files_to_apply: 적용할 파일 목록
            
        Returns:
            적용된 파일 경로 목록
        """
        applied_files = []
        repo_path = Path(self.repo_path)
        
        for file_info in files_to_apply:
            file_path = file_info.get("path", "")
            content = file_info.get("content", "")
            
            if not file_path or not content:
                continue
            
            # 파일 경로 및 디렉토리 생성
            full_path = repo_path / file_path
            os.makedirs(full_path.parent, exist_ok=True)
            
            # 특별한 확장자 처리 (.append, .update)
            if file_path.endswith(".append"):
                # 기존 파일에 내용 추가
                actual_path = file_path.replace(".append", "")
                full_path = repo_path / actual_path
                
                if full_path.exists():
                    # 기존 내용에 추가
                    with open(full_path, 'a', encoding='utf-8') as f:
                        f.write('\n\n')
                        f.write(content)
                else:
                    # 새 파일 생성
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                applied_files.append(actual_path)
            
            elif file_path.endswith(".update"):
                # 기존 파일 업데이트 (JSON 병합 등)
                actual_path = file_path.replace(".update", "")
                full_path = repo_path / actual_path
                
                if full_path.exists() and actual_path.endswith(".json"):
                    # JSON 파일 병합
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            original_data = json.load(f)
                        
                        update_data = json.loads(content)
                        merged_data = self._deep_merge(original_data, update_data)
                        
                        with open(full_path, 'w', encoding='utf-8') as f:
                            json.dump(merged_data, f, indent=2)
                    except json.JSONDecodeError:
                        # JSON 형식이 아니면 단순 덮어쓰기
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                else:
                    # 새 파일 생성
                    with open(full_path.parent / actual_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                applied_files.append(actual_path)
            
            else:
                # 일반 파일 저장
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                applied_files.append(file_path)
        
        return applied_files
    
    async def _apply_via_github_api(
        self, 
        files_to_apply: List[Dict[str, Any]], 
        create_pr: bool, 
        pr_title: str,
        pr_body: str
    ) -> tuple:
        """
        GitHub API를 통해 파일 적용
        
        Args:
            files_to_apply: 적용할 파일 목록
            create_pr: 풀 리퀘스트 생성 여부
            pr_title: 풀 리퀘스트 제목
            pr_body: 풀 리퀘스트 본문
            
        Returns:
            (적용된 파일 경로 목록, 풀 리퀘스트 URL)
        """
        # 실제 구현에서는 GitHub API 호출
        # 여기서는 성공 응답 시뮬레이션
        
        applied_files = [file_info.get("path", "").replace(".append", "").replace(".update", "") 
                         for file_info in files_to_apply]
        
        pr_url = "https://github.com/example/repo/pull/123" if create_pr else None
        
        return applied_files, pr_url
    
    def _deep_merge(self, source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
        """
        두 딕셔너리의 깊은 병합
        
        Args:
            source: 소스 딕셔너리
            destination: 대상 딕셔너리
            
        Returns:
            병합된 딕셔너리
        """
        for key, value in destination.items():
            if key in source and isinstance(source[key], dict) and isinstance(value, dict):
                source[key] = self._deep_merge(source[key], value)
            else:
                source[key] = value
        return source


async def apply_ai_setup(
    repo_data: Dict[str, Any], 
    setup_result: Dict[str, Any], 
    create_pr: bool = True, 
    pr_title: str = "AI 환경 설정 추가", 
    pr_body: str = None
) -> Dict[str, Any]:
    """
    AI 환경 설정 적용 함수
    
    Args:
        repo_data: 저장소 정보
        setup_result: 설정 정보
        create_pr: 풀 리퀘스트 생성 여부
        pr_title: 풀 리퀘스트 제목
        pr_body: 풀 리퀘스트 본문
        
    Returns:
        적용 결과
    """
    applier = AISetupApplier(repo_data, setup_result)
    result = await applier.apply(create_pr, pr_title, pr_body)
    
    return result
