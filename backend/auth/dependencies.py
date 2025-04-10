"""
인증 의존성 모듈

사용자 인증을 위한 의존성 주입 및 헬퍼 함수를 제공합니다.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta

from backend.database.connection import get_db
from backend.database.models import User
from backend.config import settings
from .models import TokenData

# 비밀번호 해싱을 위한 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 토큰 설정
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# 비밀번호 해싱 함수
def get_password_hash(password: str) -> str:
    """
    비밀번호를 해싱합니다.
    
    Args:
        password: 해싱할 비밀번호
        
    Returns:
        해싱된 비밀번호
    """
    return pwd_context.hash(password)

# 비밀번호 검증 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호와 해시를 검증합니다.
    
    Args:
        plain_password: 검증할 비밀번호
        hashed_password: 저장된 해시
        
    Returns:
        검증 결과 (True/False)
    """
    return pwd_context.verify(plain_password, hashed_password)

# 액세스 토큰 생성 함수
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰을 생성합니다.
    
    Args:
        data: 토큰에 인코딩할 데이터
        expires_delta: 토큰 만료 기간 (기본값: 1일)
        
    Returns:
        JWT 액세스 토큰
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=1)
    to_encode.update({"exp": expire})
    # 비밀 키 가져오기
    secret_key = settings.security.secret_key
    if not secret_key:
        # 기본 키 사용 (프로덕션 환경에서는 사용하지 말 것)
        secret_key = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.security.jwt_algorithm)
    return encoded_jwt

# 현재 사용자 가져오기
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    현재 인증된 사용자를 가져옵니다.
    
    Args:
        token: JWT 액세스 토큰
        db: 데이터베이스 세션
        
    Returns:
        인증된 사용자
        
    Raises:
        HTTPException: 인증 실패 시
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 비밀 키 가져오기
        secret_key = settings.security.secret_key
        if not secret_key:
            # 기본 키 사용 (프로덕션 환경에서는 사용하지 말 것)
            secret_key = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        payload = jwt.decode(token, secret_key, algorithms=[settings.security.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    
    # 마지막 로그인 시간 업데이트
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

# 현재 활성 사용자 가져오기
async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    현재 활성 상태인 인증된 사용자를 가져옵니다.
    
    Args:
        current_user: 현재 인증된 사용자
        
    Returns:
        활성 상태인 인증된 사용자
        
    Raises:
        HTTPException: 사용자가 비활성 상태인 경우
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# 관리자 사용자 확인
async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    현재 사용자가 관리자인지 확인합니다.
    
    Args:
        current_user: 현재 활성 상태인 인증된 사용자
        
    Returns:
        관리자 사용자
        
    Raises:
        HTTPException: 사용자가 관리자가 아닌 경우
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# 인증 선택적 의존성
async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    선택적으로 현재 인증된 사용자를 가져옵니다.
    토큰이 없거나 유효하지 않은 경우 None을 반환합니다.
    
    Args:
        token: JWT 액세스 토큰 (선택 사항)
        db: 데이터베이스 세션
        
    Returns:
        인증된 사용자 또는 None
    """
    if not token:
        return None
    
    try:
        # 비밀 키 가져오기
        secret_key = settings.security.secret_key
        if not secret_key:
            # 기본 키 사용 (프로덕션 환경에서는 사용하지 말 것)
            secret_key = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        payload = jwt.decode(token, secret_key, algorithms=[settings.security.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            return None
        
        user = db.query(User).filter(User.username == username).first()
        return user
    except JWTError:
        return None
