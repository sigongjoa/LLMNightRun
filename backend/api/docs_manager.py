"""
문서 관리 API 모듈

이 모듈은 LLMNightRun 프로젝트의 문서 자동화 및 GitHub 연동 API를 제공합니다.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Path, Query, Body
from pydantic import BaseModel

import os
import sys
import logging
from datetime import datetime

# 문서 생성 모듈 임포트
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from docs_generator.workflow import DocumentationWorkflow
from docs_generator.git_handler import GitHandler

# 로깅 설정
logger = logging.getLogger(__name__)

# 라우터 설정
router = APIRouter(
    prefix="/docs-manager",
    tags=["docs-manager"],
    responses={404: {"description": "Not found"}},
)

# 모델 정의
class DocumentGenerateRequest(BaseModel):
    doc_types: List[str]
    force_update: bool = False
    push_to_github: bool = False

class GitHubConfigRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    auth_token: Optional[str] = None
    auto_push: bool = False

class DocumentInfo(BaseModel):
    doc_type: str
    path: str
    last_updated: Optional[str] = None
    exists: bool

# API 엔드포인트 구현
@router.get("/list")
async def list_documents() -> Dict[str, Any]:
    """
    사용 가능한 문서 목록과 상태 조회
    """
    try:
        # 문서 디렉토리
        docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../docs'))
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        
        # 문서 유형 정의
        doc_types = [
            "README", "API", "MODELS", "DATABASE", 
            "ARCHITECTURE", "TESTING", "CHANGELOG", "CONFIGURATION"
        ]
        
        # 결과 구성
        docs_info = []
        
        for doc_type in doc_types:
            # 문서 파일 경로 결정
            if doc_type == "README":
                path = os.path.join(repo_root, "README.md")
            else:
                path = os.path.join(docs_dir, f"{doc_type.upper()}.md")
            
            # 파일 존재 및 마지막 수정 시간 확인
            exists = os.path.exists(path)
            last_updated = None
            
            if exists:
                last_updated = datetime.fromtimestamp(
                    os.path.getmtime(path)
                ).strftime("%Y-%m-%d %H:%M:%S")
            
            # 문서 정보 추가
            docs_info.append(
                DocumentInfo(
                    doc_type=doc_type,
                    path=os.path.relpath(path, repo_root),
                    last_updated=last_updated,
                    exists=exists
                )
            )
        
        return {
            "status": "success",
            "documents": [doc.dict() for doc in docs_info]
        }
        
    except Exception as e:
        logger.error(f"문서 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/generate")
async def generate_documents(
    background_tasks: BackgroundTasks,
    request: DocumentGenerateRequest
) -> Dict[str, Any]:
    """
    선택한 문서 생성 또는 업데이트
    """
    try:
        # repo_path 설정
        repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        
        # 백그라운드 작업으로 문서 생성 실행
        background_tasks.add_task(
            _generate_documents_task,
            repo_path=repo_path,
            doc_types=request.doc_types,
            force_update=request.force_update,
            push_to_github=request.push_to_github
        )
        
        return {
            "status": "success",
            "message": "문서 생성 작업이 시작되었습니다.",
            "doc_types": request.doc_types
        }
        
    except Exception as e:
        logger.error(f"문서 생성 요청 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 생성 요청 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/content/{doc_type}")
async def get_document_content(
    doc_type: str = Path(..., description="문서 유형")
) -> Dict[str, Any]:
    """
    특정 문서의 내용 조회
    """
    try:
        # repo_path 설정
        repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        
        # 문서 파일 경로 결정
        if doc_type.upper() == "README":
            path = os.path.join(repo_path, "README.md")
        else:
            path = os.path.join(repo_path, "docs", f"{doc_type.upper()}.md")
        
        # 파일 존재 확인
        if not os.path.exists(path):
            return {
                "status": "error",
                "message": f"{doc_type} 문서가 존재하지 않습니다."
            }
        
        # 파일 내용 읽기
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "status": "success",
            "doc_type": doc_type,
            "content": content,
            "path": os.path.relpath(path, repo_path),
            "last_updated": datetime.fromtimestamp(
                os.path.getmtime(path)
            ).strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        logger.error(f"문서 내용 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"문서 내용 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/github/config")
async def set_github_config(config: GitHubConfigRequest) -> Dict[str, Any]:
    """
    GitHub 연동 설정 저장
    """
    try:
        # 설정 디렉토리
        config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../config'))
        os.makedirs(config_dir, exist_ok=True)
        
        # 설정 파일 경로
        config_path = os.path.join(config_dir, "github_config.json")
        
        # 설정 저장 (비밀번호는 암호화 고려)
        import json
        with open(config_path, 'w', encoding='utf-8') as f:
            # auth_token은 실제 운영 환경에서는 안전하게 저장해야 함
            json.dump({
                "repo_url": config.repo_url,
                "branch": config.branch,
                "auth_token": config.auth_token,
                "auto_push": config.auto_push,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
        
        return {
            "status": "success",
            "message": "GitHub 설정이 저장되었습니다."
        }
        
    except Exception as e:
        logger.error(f"GitHub 설정 저장 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub 설정 저장 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/github/config")
async def get_github_config() -> Dict[str, Any]:
    """
    GitHub 연동 설정 조회
    """
    try:
        # 설정 파일 경로
        config_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../../../config/github_config.json')
        )
        
        # 설정 파일 존재 확인
        if not os.path.exists(config_path):
            return {
                "status": "warning",
                "message": "GitHub 설정이 존재하지 않습니다.",
                "config": None
            }
        
        # 설정 읽기
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
            # 보안을 위해 auth_token 마스킹
            if "auth_token" in config and config["auth_token"]:
                config["auth_token"] = "********"
        
        return {
            "status": "success",
            "config": config
        }
        
    except Exception as e:
        logger.error(f"GitHub 설정 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub 설정 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/github/status")
async def get_github_status() -> Dict[str, Any]:
    """
    GitHub 리포지토리 상태 조회
    """
    try:
        # repo_path 설정
        repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
        
        # Git 핸들러 초기화
        git = GitHandler(repo_path)
        
        # 상태 정보 수집
        current_branch = git.get_branch_name()
        staged_files = git.get_staged_files()
        uncommitted_changes = git.get_uncommitted_changes()
        
        return {
            "status": "success",
            "git_status": {
                "current_branch": current_branch,
                "staged_files": staged_files,
                "uncommitted_changes": uncommitted_changes,
                "has_changes": len(staged_files) > 0 or len(uncommitted_changes) > 0
            }
        }
        
    except Exception as e:
        logger.error(f"GitHub 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"GitHub 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )

# 백그라운드 작업 함수
async def _generate_documents_task(
    repo_path: str,
    doc_types: List[str],
    force_update: bool = False,
    push_to_github: bool = False
):
    """
    백그라운드 문서 생성 작업
    """
    try:
        logger.info(f"문서 생성 작업 시작: {doc_types}")
        
        # 워크플로우 초기화
        workflow = DocumentationWorkflow(
            repo_path=repo_path,
            push_changes=push_to_github
        )
        
        # 모든 문서 강제 업데이트 여부
        if "ALL" in doc_types:
            force_all = True
            logger.info("모든 문서 강제 업데이트 모드")
        else:
            force_all = False
            # TODO: 특정 문서만 업데이트하는 로직 구현
            logger.info(f"선택 문서 업데이트 모드: {doc_types}")
        
        # 워크플로우 실행
        success = workflow.run(force_all=force_all)
        
        if success:
            logger.info("문서 생성 작업이 성공적으로 완료되었습니다.")
        else:
            logger.error("문서 생성 작업이 실패했습니다.")
            
    except Exception as e:
        logger.error(f"문서 생성 작업 실패: {str(e)}")
