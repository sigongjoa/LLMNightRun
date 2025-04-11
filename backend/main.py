from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from database import engine, Base, get_db
import models
import crud
import schemas
from auth.dependencies import get_current_active_user
from auth.router import router as auth_router
from github_repos import router as github_repos_router
from settings import router as settings_router

# 데이터베이스 테이블 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LLMNightRun API")

# 라우터 등록
app.include_router(auth_router)
app.include_router(github_repos_router)
app.include_router(settings_router)

# CORS 미들웨어 설정
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서버 상태 확인 엔드포인트
@app.get("/health-check")
def health_check():
    return {"status": "healthy", "message": "서버가 정상적으로 실행 중입니다."}

# 사용자 관련 엔드포인트
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    return crud.create_user(db=db, user=user)

@app.get("/users/me/", response_model=schemas.User)
def read_users_me(current_user = Depends(get_current_active_user)):
    return current_user

# 질문 관련 엔드포인트
@app.post("/questions/", response_model=schemas.Question)
def create_question(question: schemas.QuestionCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    return crud.create_question(db=db, question=question, user_id=current_user.id)

@app.get("/questions/", response_model=List[schemas.Question])
def read_questions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        # 빈 리스트 반환 (임시 해결책)
        return []
    except Exception as e:
        print(f"질문 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="질문 목록을 가져오는 중 오류가 발생했습니다.")

@app.get("/questions/{question_id}", response_model=schemas.Question)
def read_question(question_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    db_question = crud.get_question(db, question_id=question_id)
    if db_question is None or db_question.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다.")
    return db_question

# 응답 관련 엔드포인트
@app.post("/responses/", response_model=schemas.Response)
def create_response(response: schemas.ResponseCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    # 질문이 사용자의 것인지 확인
    question = crud.get_question(db, question_id=response.question_id)
    if question is None or question.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다.")
    return crud.create_response(db=db, response=response, user_id=current_user.id)

@app.get("/responses/", response_model=List[schemas.Response])
def read_responses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        # 빈 리스트 반환 (임시 해결책)
        return []
    except Exception as e:
        print(f"응답 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="응답 목록을 가져오는 중 오류가 발생했습니다.")

@app.get("/responses/{response_id}", response_model=schemas.Response)
def read_response(response_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    db_response = crud.get_response(db, response_id=response_id)
    if db_response is None or db_response.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="응답을 찾을 수 없습니다.")
    return db_response

# GitHub 저장소 관련 엔드포인트
@app.post("/github-repos/", response_model=schemas.GitHubRepositoryResponse)
def create_github_repository(repo: schemas.GitHubRepositoryCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        # 사용자 객체 대신 user_id 전달
        db_repo = crud.create_github_repository(db=db, repository=repo, user_id=current_user.id)
        
        # 응답 객체 생성
        response = schemas.GitHubRepositoryResponse(
            id=db_repo.id,
            name=db_repo.name,
            owner_id=current_user.id,
            owner_name=current_user.username,
            url=db_repo.url,
            description=db_repo.description,
            is_private=db_repo.is_private
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"저장소 생성 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/github-repos/", response_model=List[schemas.GitHubRepositoryResponse])
def read_github_repositories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    try:
        repositories = crud.get_user_github_repositories(db, user_id=current_user.id, skip=skip, limit=limit)
        
        # 각 repository에 대해 owner_name 설정
        responses = []
        for repo in repositories:
            responses.append(schemas.GitHubRepositoryResponse(
                id=repo.id,
                name=repo.name,
                owner_id=current_user.id,
                owner_name=current_user.username,
                url=repo.url,
                description=repo.description,
                is_private=repo.is_private
            ))
        return responses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"저장소 목록을 불러오는 중 오류가 발생했습니다: {str(e)}"
        )

@app.get("/github-repos/{repo_id}", response_model=schemas.GitHubRepositoryResponse)
def read_github_repository(repo_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    db_repo = crud.get_github_repository(db, repo_id=repo_id)
    if db_repo is None:
        raise HTTPException(status_code=404, detail="저장소를 찾을 수 없습니다")
    if db_repo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="이 저장소에 접근할 권한이 없습니다")
    
    # 응답 객체 생성
    response = schemas.GitHubRepositoryResponse(
        id=db_repo.id,
        name=db_repo.name,
        owner_id=current_user.id,
        owner_name=current_user.username,
        url=db_repo.url,
        description=db_repo.description,
        is_private=db_repo.is_private
    )
    return response

# 모델 설치 관련 엔드포인트 (예시)
@app.post("/model-installer/analyze")
def analyze_repository(data: dict):
    # 이 부분은 실제 구현이 필요합니다. 현재는 더미 데이터를 반환합니다.
    return {
        "model_type": {
            "primary": "PyTorch",
            "secondary": ["Neural Network", "Computer Vision"]
        },
        "launch_scripts": [
            "python train.py",
            "python inference.py"
        ],
        "requirements": {
            "requirements.txt": ["torch", "torchvision", "numpy"]
        }
    }

@app.post("/model-installer/setup")
def setup_environment(data: dict):
    # 이 부분은 실제 구현이 필요합니다. 현재는 성공 메시지를 반환합니다.
    return {
        "status": "success",
        "message": "환경 설정이 완료되었습니다."
    }

@app.post("/model-installer/install")
def install_model(data: dict):
    # 이 부분은 실제 구현이 필요합니다. 현재는 설치 ID를 반환합니다.
    return {
        "status": "started",
        "installation_id": "mock-install-123",
        "message": "모델 설치가 시작되었습니다."
    }

@app.get("/model-installer/status/{installation_id}")
def get_installation_status(installation_id: str):
    # 이 부분은 실제 구현이 필요합니다. 현재는 더미 상태 정보를 반환합니다.
    return {
        "status": "completed",
        "installation_id": installation_id,
        "logs": [
            "패키지 설치 중...",
            "모델 다운로드 중...",
            "설정 파일 생성 중...",
            "설치 완료!"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
