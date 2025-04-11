from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import crud
import schemas
from database import get_db
from auth.dependencies import get_current_active_user

router = APIRouter(
    prefix="/github-repos",
    tags=["github-repositories"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.GitHubRepositoryResponse)
def create_github_repository(
    repository: schemas.GitHubRepositoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        # 사용자 객체 대신 user_id 전달
        db_repo = crud.create_github_repository(
            db=db, 
            repository=repository, 
            user_id=current_user.id
        )
        
        # 응답 객체 생성
        response = schemas.GitHubRepositoryResponse(
            id=db_repo.id,
            name=db_repo.name,
            url=db_repo.url,
            description=db_repo.description,
            is_private=db_repo.is_private,
            owner_id=current_user.id,
            owner_name=current_user.username
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"저장소 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/", response_model=List[schemas.GitHubRepositoryResponse])
def read_github_repositories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    try:
        repositories = crud.get_user_github_repositories(db, user_id=current_user.id, skip=skip, limit=limit)
        
        # 각 repository에 대해 owner_name 설정
        responses = []
        for repo in repositories:
            responses.append(schemas.GitHubRepositoryResponse(
                id=repo.id,
                name=repo.name,
                url=repo.url,
                description=repo.description,
                is_private=repo.is_private,
                owner_id=current_user.id,
                owner_name=current_user.username
            ))
        return responses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"저장소 목록을 불러오는 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{repo_id}", response_model=schemas.GitHubRepositoryResponse)
def read_github_repository(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_repo = crud.get_github_repository(db, repo_id=repo_id)
    if db_repo is None:
        raise HTTPException(status_code=404, detail="저장소를 찾을 수 없습니다")
    if db_repo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 저장소에 접근할 권한이 없습니다")
    
    # 응답 객체 생성
    response = schemas.GitHubRepositoryResponse(
        id=db_repo.id,
        name=db_repo.name,
        url=db_repo.url,
        description=db_repo.description,
        is_private=db_repo.is_private,
        owner_id=current_user.id,
        owner_name=current_user.username
    )
    return response


@router.put("/{repo_id}", response_model=schemas.GitHubRepositoryResponse)
def update_github_repository(
    repo_id: int,
    repository: schemas.GitHubRepositoryCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_repo = crud.get_github_repository(db, repo_id=repo_id)
    if db_repo is None:
        raise HTTPException(status_code=404, detail="저장소를 찾을 수 없습니다")
    if db_repo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 저장소를 수정할 권한이 없습니다")
    
    updated_repo = crud.update_github_repository(db=db, repo_id=repo_id, repository=repository)
    
    # 응답 객체 생성
    response = schemas.GitHubRepositoryResponse(
        id=updated_repo.id,
        name=updated_repo.name,
        url=updated_repo.url,
        description=updated_repo.description,
        is_private=updated_repo.is_private,
        owner_id=current_user.id,
        owner_name=current_user.username
    )
    return response


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_github_repository(
    repo_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    db_repo = crud.get_github_repository(db, repo_id=repo_id)
    if db_repo is None:
        raise HTTPException(status_code=404, detail="저장소를 찾을 수 없습니다")
    if db_repo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 저장소를 삭제할 권한이 없습니다")
    
    crud.delete_github_repository(db=db, repo_id=repo_id)
    return {"detail": "저장소가 성공적으로 삭제되었습니다"}

# 추가 엔드포인트 - LLM 상태
@router.get("/api/local-llm/status", tags=["local-llm"])
def local_llm_status():
    """로컬 LLM 상태를 확인하는 직접 엔드포인트"""
    return {
        "enabled": True,
        "connected": False,
        "base_url": "http://127.0.0.1:1234",
        "error": "LM Studio에 연결할 수 없습니다. LM Studio가 실행 중인지 확인해주세요."
    }
