from fastapi import FastAPI, Depends, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
import uvicorn
from datetime import datetime, timedelta

# 간단한 FastAPI 앱 생성
app = FastAPI(title="Simple Auth Server")

# 모든 오리진에서의 CORS 요청 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# JWT 설정
SECRET_KEY = "my_super_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24시간

# 데이터 모델
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class User(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    profile_image: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    is_admin: bool

# 토큰 생성 함수
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 1. 로그인 엔드포인트
@app.post("/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(f"로그인 시도: {form_data.username}, {form_data.password}")
    
    # 예시 계정: admin/admin123
    if form_data.username == "admin" and form_data.password != "admin123":
        return {
            "access_token": "invalid_token",
            "token_type": "bearer",
            "user_id": 0,
            "username": form_data.username,
            "is_admin": False,
            "detail": "비밀번호가 일치하지 않습니다."
        }
    
    # 모든 로그인 시도를 성공으로 처리
    user_id = 1
    
    # 토큰 생성
    token_data = {"sub": form_data.username}
    access_token = create_access_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user_id,
        "username": form_data.username,
        "is_admin": True
    }

# 2. 회원가입 엔드포인트
@app.post("/auth/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    # 모든 회원가입 시도를 성공으로 처리
    return {
        "id": 1,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": True,
        "is_admin": False,
        "profile_image": None
    }

# 3. 사용자 정보 엔드포인트
@app.get("/auth/me", response_model=User)
async def get_user_info():
    # 고정된 사용자 정보 반환
    return {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "is_admin": True,
        "profile_image": None
    }

# 서버 실행
if __name__ == "__main__":
    print("=" * 50)
    print("간단한 인증 서버를 시작합니다...")
    print("URL: http://localhost:8000")
    print("문서: http://localhost:8000/docs")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
