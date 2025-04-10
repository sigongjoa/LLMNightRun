"""
인증 관련 모델 정의 모듈

인증 관련 Pydantic 모델을 정의합니다.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import re

class TokenData(BaseModel):
    """토큰 데이터 모델"""
    username: Optional[str] = None

class Token(BaseModel):
    """토큰 응답 모델"""
    access_token: str
    token_type: str
    user_id: int
    username: str
    is_admin: bool

class UserCreate(BaseModel):
    """사용자 생성 요청 모델"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    
    @validator('username')
    def username_alphanumeric(cls, v):
        """사용자명 검증: 알파벳, 숫자, 특수문자(-_.)만 포함 가능"""
        if not re.match(r'^[a-zA-Z0-9\-_.]+$', v):
            raise ValueError('Username must contain only letters, numbers, and characters -_.')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        """비밀번호 강도 검증: 대문자, 소문자, 숫자, 특수문자 중 3가지 이상 포함"""
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(not c.isalnum() for c in v)
        
        categories = [has_upper, has_lower, has_digit, has_special]
        if sum(categories) < 3:
            raise ValueError('Password must include at least 3 of: uppercase letters, lowercase letters, numbers, and special characters')
        return v

class UserLogin(BaseModel):
    """사용자 로그인 요청 모델"""
    username: str
    password: str

class UserUpdate(BaseModel):
    """사용자 정보 업데이트 요청 모델"""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    profile_image: Optional[str] = None
    
    @validator('password')
    def password_strength(cls, v):
        """비밀번호 강도 검증: 대문자, 소문자, 숫자, 특수문자 중 3가지 이상 포함"""
        if v is None:
            return v
            
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(not c.isalnum() for c in v)
        
        categories = [has_upper, has_lower, has_digit, has_special]
        if sum(categories) < 3:
            raise ValueError('Password must include at least 3 of: uppercase letters, lowercase letters, numbers, and special characters')
        return v

class UserResponse(BaseModel):
    """사용자 응답 모델"""
    id: int
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    is_admin: bool
    profile_image: Optional[str]
    created_at: str
    last_login: Optional[str]
    
    class Config:
        from_attributes = True

class UserSettingsResponse(BaseModel):
    """사용자 설정 응답 모델"""
    id: int
    user_id: int
    openai_api_key: Optional[str]
    claude_api_key: Optional[str]
    github_token: Optional[str]
    default_github_repo: Optional[str]
    default_github_username: Optional[str]
    theme: str
    language: str
    notification_enabled: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

class UserSettingsUpdate(BaseModel):
    """사용자 설정 업데이트 요청 모델"""
    openai_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    github_token: Optional[str] = None
    default_github_repo: Optional[str] = None
    default_github_username: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    notification_enabled: Optional[bool] = None
