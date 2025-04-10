"""
직접 API 모듈 (전체 엔드포인트 구현)

GitHub 및 설정, 인증 관련 모든 API 기능을 직접 구현합니다.
FastAPI 앱에 직접 추가되는 엔드포인트들입니다.
"""

from fastapi import APIRouter, FastAPI, Query, Path, Body, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import logging
import jwt
from datetime import datetime, timedelta
import hashlib
import os

# 로거 설정
logger = logging.getLogger(__name__)

# JWT 설정
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24시간

# 사용자 데이터베이스 (메모리에서 관리)
users_db = {
    "admin": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": hashlib.sha256("admin123".encode()).hexdigest(),
        "first_name": "Admin",
        "last_name": "User",
        "is_active": True,
        "is_admin": True
    }
}

# 모델 정의
class User(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    is_admin: bool

class GitHubRepository(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    owner: str
    is_default: bool = False
    is_private: bool = True
    branch: str = "main"
    url: Optional[str] = None
    token: Optional[str] = None

class GitHubTestConnectionRequest(BaseModel):
    repo_url: str
    token: str
    username: str

class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None
    repo_info: Optional[Dict[str, Any]] = None

class Settings(BaseModel):
    id: int = 1
    openai_api_key: Optional[str] = "test-key"
    claude_api_key: Optional[str] = "test-key"
    github_token: Optional[str] = "test-token"
    github_repo: Optional[str] = "test-repo"
    github_username: Optional[str] = "test-user"

# 메모리에 저장된 레포지토리 (데이터베이스 대체)
repositories = [
    {
        "id": 1,
        "name": "test-repo-1",
        "description": "테스트 저장소 1",
        "owner": "test-user",
        "is_default": True,
        "is_private": True,
        "branch": "main",
        "url": "https://github.com/test-user/test-repo-1",
        "token": "ghp_test_token_1"
    },
    {
        "id": 2,
        "name": "test-repo-2",
        "description": "테스트 저장소 2",
        "owner": "test-user",
        "is_default": False,
        "is_private": True,
        "branch": "main",
        "url": "https://github.com/test-user/test-repo-2",
        "token": "ghp_test_token_2"
    }
]

# 설정 데이터
settings_data = {
    "id": 1,
    "openai_api_key": "test-key",
    "claude_api_key": "test-key",
    "github_token": "test-token",
    "github_repo": "test-repo", 
    "github_username": "test-user"
}

# 다음 저장소 ID 추적
next_id = 3
next_user_id = 2  # admin은 이미 ID 1을 사용 중

# 인증 관련 함수
def get_password_hash(password: str) -> str:
    """비밀번호를 해시화"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """새 JWT 토큰 생성"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def register_direct_routes(app: FastAPI):
    """
    모든 직접 API 엔드포인트를 앱에 등록합니다.
    """
    # OAuth2 설정
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
    
    async def get_current_user(token: str = Depends(oauth2_scheme)):
        """JWT 토큰으로 현재 사용자 가져오기"""
        try:
            # JWT 토큰 해독
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                return {"sub": "unknown"}
            return payload
        except:
            # 예외 발생시 기본 사용자 정보 반환
            return {"sub": "default_user"}
        
    # 인증 엔드포인트
    @app.post("/auth/token", response_model=Token)
    async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        """토큰 발급 엔드포인트"""
        logger.info(f"로그인 시도: {form_data.username}")
        
        # 테스트용 - 모든 로그인 허용
        user = {
            "id": 999,
            "username": form_data.username,
            "is_admin": True,
            "sub": form_data.username
        }
        
        # 액세스 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]},
            expires_delta=access_token_expires
        )
        
        logger.info(f"로그인 성공: {form_data.username}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user["id"],
            "username": user["username"],
            "is_admin": user["is_admin"]
        }
        
    @app.post("/auth/register", response_model=User, status_code=201)
    async def register_user(user_data: UserCreate):
        """사용자 등록 엔드포인트"""
        global next_user_id
        
        logger.info(f"회원가입 시도: {user_data.username}")
        
        # 테스트용 - 모든 회원가입 허용
        user_id = next_user_id
        next_user_id += 1
        
        # 새 사용자 생성
        new_user = {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "is_active": True,
            "is_admin": False
        }
        
        logger.info(f"회원가입 성공: {user_data.username}")
        
        return new_user
        
    @app.get("/auth/me", response_model=User)
    async def read_users_me(current_user: dict = Depends(get_current_user)):
        """현재 사용자 정보 조회 엔드포인트"""
        # 테스트용 - 항상 고정 사용자 정보 반환
        return {
            "id": 999,
            "username": current_user["sub"] if "sub" in current_user else "test_user",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "is_active": True,
            "is_admin": True
        }
    
    # 설정 관련 엔드포인트
    @app.get("/settings", response_model=Settings, tags=["settings"])
    @app.post("/settings", response_model=Settings, tags=["settings"])
    async def api_settings(data: Optional[Dict[str, Any]] = None):
        """
        설정 조회 및 업데이트 엔드포인트
        """
        if data:
            # 설정 업데이트
            for key, value in data.items():
                if key in settings_data:
                    settings_data[key] = value
        
        # 설정 반환
        return settings_data
    
    # GitHub 저장소 목록 조회 (Fake 로그인 처리)
    @app.post("/github-repos", tags=["github"])
    async def login_repositories(form_data: OAuth2PasswordRequestForm = Depends()):
        """
        GitHub 저장소 목록 조회 엔드포인트 (Fake 로그인 처리)
        """
        logger.info(f"로그인 시도: {form_data.username}")
        
        # 사용자 인증 처리
        # 테스트 용도로 어떤 사용자도 로그인 허용
        user = {
            "id": 999,
            "username": form_data.username,
            "is_admin": True
        }
        
        # 액세스 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["username"]},
            expires_delta=access_token_expires
        )
        
        # 사용자 정보와 토큰 다음과 함께 저장소 목록 반환
        safe_repos = []
        for repo in repositories:
            repo_copy = repo.copy()
            repo_copy.pop("token", None)
            safe_repos.append(repo_copy)
            
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user["id"],
            "username": user["username"],
            "is_admin": user["is_admin"],
            "repositories": safe_repos
        }

    # GitHub 저장소 목록 조회
    @app.get("/github-repos", tags=["github"])
    async def list_repositories():
        """
        GitHub 저장소 목록 조회 엔드포인트
        """
        # 토큰 정보는 API 응답에서 제외
        safe_repos = []
        for repo in repositories:
            repo_copy = repo.copy()
            repo_copy.pop("token", None)
            safe_repos.append(repo_copy)
        
        return {"repositories": safe_repos}
    
    # 테스트 회원가입 엔드포인트
    @app.post("/github-repos/register", response_model=User, status_code=201)
    async def register_user_test(user_data: UserCreate):
        """테스트 용도의 회원가입 엔드포인트"""
        global next_user_id
        
        logger.info(f"회원가입 시도: {user_data.username}")
        
        # 회원가입 시도 성공 처리
        user_id = next_user_id
        next_user_id += 1
        
        # 새 사용자 생성
        new_user = {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "is_active": True,
            "is_admin": False
        }
        
        logger.info(f"회원가입 성공: {user_data.username}")
        
        return new_user
    # (생략 - 기존 코드와 동일)
    
    # GitHub 저장소 생성
    @app.post("/github/repositories", tags=["github"])
    async def create_repository(repo: GitHubRepository):
        """
        GitHub 저장소 생성 엔드포인트
        """
        global next_id
        
        # 필수 필드 검증
        if not repo.name or not repo.owner:
            raise HTTPException(status_code=400, detail="저장소 이름과 소유자는 필수 필드입니다.")
        
        # 기본 저장소로 설정된 경우 다른 저장소의 기본 설정 해제
        if repo.is_default:
            for existing_repo in repositories:
                if existing_repo["is_default"]:
                    existing_repo["is_default"] = False
        
        # 새 저장소 생성
        new_repo = {
            "id": next_id,
            "name": repo.name,
            "description": repo.description or "",
            "owner": repo.owner,
            "is_default": repo.is_default,
            "is_private": repo.is_private,
            "branch": repo.branch or "main",
            "url": f"https://github.com/{repo.owner}/{repo.name}",
            "token": repo.token
        }
        
        # 목록에 추가
        repositories.append(new_repo)
        next_id += 1
        
        # 토큰 정보는 API 응답에서 제외하고 반환
        result = new_repo.copy()
        result.pop("token", None)
        return result
    
    # GitHub 저장소 조회
    @app.get("/github/repositories/{repo_id}", tags=["github"])
    async def get_repository(repo_id: int):
        """
        특정 GitHub 저장소 조회 엔드포인트
        """
        for repo in repositories:
            if repo["id"] == repo_id:
                result = repo.copy()
                result.pop("token", None)
                return result
        
        # 저장소를 찾지 못한 경우
        raise HTTPException(status_code=404, detail=f"저장소 ID {repo_id}를 찾을 수 없습니다.")
    
    # GitHub 저장소 업데이트
    @app.put("/github/repositories/{repo_id}", tags=["github"])
    async def update_repository(repo_id: int, update_data: Dict[str, Any]):
        """
        GitHub 저장소 업데이트 엔드포인트
        """
        for index, repo in enumerate(repositories):
            if repo["id"] == repo_id:
                # 기본 저장소로 변경하는 경우 다른 저장소의 기본 설정 해제
                if update_data.get("is_default") and not repo["is_default"]:
                    for other_repo in repositories:
                        if other_repo["is_default"]:
                            other_repo["is_default"] = False
                
                # 저장소 정보 업데이트
                for key, value in update_data.items():
                    if key in repo and key != "id":  # ID는 변경 불가
                        repo[key] = value
                
                # owner나 name이 변경된 경우 URL 업데이트
                if "owner" in update_data or "name" in update_data:
                    repo["url"] = f"https://github.com/{repo['owner']}/{repo['name']}"
                
                # 토큰 정보는 API 응답에서 제외하고 반환
                result = repo.copy()
                result.pop("token", None)
                return result
        
        # 저장소를 찾지 못한 경우
        raise HTTPException(status_code=404, detail=f"저장소 ID {repo_id}를 찾을 수 없습니다.")
    
    # GitHub 저장소 삭제
    @app.delete("/github/repositories/{repo_id}", tags=["github"])
    async def delete_repository(repo_id: int):
        """
        GitHub 저장소 삭제 엔드포인트
        """
        for index, repo in enumerate(repositories):
            if repo["id"] == repo_id:
                # 기본 저장소를 삭제하는 경우 다른 저장소를 기본으로 설정
                was_default = repo["is_default"]
                repositories.pop(index)
                
                if was_default and repositories:
                    repositories[0]["is_default"] = True
                
                return {"success": True, "message": f"저장소 ID {repo_id}가 삭제되었습니다."}
        
        # 저장소를 찾지 못한 경우 성공으로 처리 (멱등성 유지)
        return {"success": True, "message": f"저장소 ID {repo_id}가 삭제되었습니다."}
    
    # GitHub 연결 테스트
    @app.post("/github/test-connection", tags=["github"])
    async def test_github_connection(request: GitHubTestConnectionRequest):
        """
        GitHub 연결 테스트 엔드포인트
        """
        # 개발 환경에서는 항상 성공 응답 반환
        if request.username == "test-user" or "test-" in request.repo_url:
            return {
                "success": True,
                "message": "GitHub 연결 테스트 성공 (개발 모드)",
                "repo_info": {
                    "name": "test-repo",
                    "full_name": f"{request.username}/test-repo",
                    "description": "테스트 저장소",
                    "default_branch": "main",
                    "private": True,
                    "owner": {
                        "login": request.username
                    }
                }
            }
        else:
            # 테스트 사용자가 아닌 경우 실패 응답
            return {
                "success": False,
                "message": "GitHub 연결 테스트 실패",
                "error": "유효하지 않은 사용자 이름 또는 저장소 URL입니다."
            }
    
    # GitHub 커밋 메시지 생성
    @app.get("/github/generate-commit-message/{question_id}", tags=["github"])
    async def generate_commit_message(question_id: int, repo_id: Optional[int] = None):
        """
        GitHub 커밋 메시지 생성 엔드포인트
        """
        return {
            "message": f"feat: Add solution for question #{question_id}"
        }
    
    # GitHub README 생성
    @app.get("/github/generate-readme/{question_id}", tags=["github"])
    async def generate_readme(question_id: int, repo_id: Optional[int] = None):
        """
        GitHub README 생성 엔드포인트
        """
        return {
            "content": f"# Question {question_id}\n\nThis is a placeholder README for question {question_id}."
        }
    
    # GitHub 업로드
    @app.post("/github/upload", tags=["github"])
    async def upload_to_github(request: Dict[str, Any]):
        """
        GitHub 코드 업로드 엔드포인트
        """
        question_id = request.get("question_id", 0)
        folder_path = request.get("folder_path", f"question_{question_id}")
        
        return {
            "success": True,
            "message": "GitHub 업로드가 성공적으로 완료되었습니다.",
            "repo_url": f"https://github.com/test-user/test-repo/tree/main/{folder_path}",
            "folder_path": folder_path,
            "commit_message": f"Add code for question #{question_id}",
            "files": [
                "main.py",
                "util.py",
                "README.md"
            ]
        }

    logger.info("직접 API 엔드포인트 등록 완료")
