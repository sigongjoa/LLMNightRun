"""
문서 관리 API 모듈

이 모듈은 LLMNightRun 프로젝트의 문서 자동화 및 GitHub 연동 API를 제공합니다.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body
from fastapi.param_functions import Path as FastAPIPath
from pydantic import BaseModel, Field

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path as PathLib

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

# 경로 유틸리티 함수
def get_project_paths() -> Dict[str, str]:
    """프로젝트 경로 정보 반환"""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    docs_dir = os.path.join(repo_root, "docs")
    config_dir = os.path.join(repo_root, "config")
    
    # 필요한 디렉토리 생성
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(config_dir, exist_ok=True)
    
    return {
        "repo_root": repo_root,
        "docs_dir": docs_dir,
        "config_dir": config_dir,
        "github_config": os.path.join(config_dir, "github_config.json")
    }

def get_document_path(doc_type: str) -> str:
    """문서 유형에 따른 파일 경로 반환"""
    paths = get_project_paths()
    
    if doc_type.upper() == "README":
        return os.path.join(paths["repo_root"], "README.md")
    else:
        return os.path.join(paths["docs_dir"], f"{doc_type.upper()}.md")

# 문서 유형 목록
DOC_TYPES = [
    "README", "API", "MODELS", "DATABASE", 
    "ARCHITECTURE", "TESTING", "CHANGELOG", "CONFIGURATION"
]

# API 엔드포인트 구현
@router.get("/list")
async def list_documents() -> Dict[str, Any]:
    """
    사용 가능한 문서 목록과 상태 조회
    """
    try:
        paths = get_project_paths()
        docs_info = []
        
        for doc_type in DOC_TYPES:
            path = get_document_path(doc_type)
            exists = os.path.exists(path)
            last_updated = None
            
            if exists:
                last_updated = datetime.fromtimestamp(
                    os.path.getmtime(path)
                ).strftime("%Y-%m-%d %H:%M:%S")
            
            docs_info.append(
                DocumentInfo(
                    doc_type=doc_type,
                    path=os.path.relpath(path, paths["repo_root"]),
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
        paths = get_project_paths()
        
        # 백그라운드 작업으로 문서 생성 실행
        background_tasks.add_task(
            _generate_documents_task,
            repo_path=paths["repo_root"],
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
    doc_type: str = FastAPIPath(..., description="문서 유형")
) -> Dict[str, Any]:
    """
    특정 문서의 내용 조회
    """
    try:
        paths = get_project_paths()
        path = get_document_path(doc_type)
        
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
            "path": os.path.relpath(path, paths["repo_root"]),
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
        paths = get_project_paths()
        
        # 설정 저장
        with open(paths["github_config"], 'w', encoding='utf-8') as f:
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
        paths = get_project_paths()
        
        # 설정 파일 존재 확인
        if not os.path.exists(paths["github_config"]):
            return {
                "status": "warning",
                "message": "GitHub 설정이 존재하지 않습니다.",
                "config": None
            }
        
        # 설정 읽기
        with open(paths["github_config"], 'r', encoding='utf-8') as f:
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
        paths = get_project_paths()
        
        # Git 저장소 확인
        try:
            # Git 핸들러 초기화
            git = GitHandler(paths["repo_root"])
            
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
        except ValueError as e:
            # Git 저장소가 초기화되지 않은 경우
            return {
                "status": "warning",
                "message": "Git 저장소가 초기화되지 않았습니다.",
                "git_status": {
                    "current_branch": None,
                    "staged_files": [],
                    "uncommitted_changes": [],
                    "has_changes": False,
                    "initialized": False
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
