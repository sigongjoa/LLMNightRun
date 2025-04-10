"""
인증 라우터 모듈

사용자 인증 및 관리를 위한 API 엔드포인트를 제공합니다.
"""

import logging
from typing import List, Optional
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database.connection import get_db
from backend.database.models import User, UserSettings, UserActivity
from backend.config import settings
from .dependencies import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_active_user, get_current_admin_user
)
from .models import (
    UserCreate, UserLogin, UserUpdate, UserResponse, Token,
    UserSettingsUpdate, UserSettingsResponse
)

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 설정
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Unauthorized"}},
)

# 액세스 토큰 발급
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    사용자 인증 및 JWT 토큰 발급
    
    - **username**: 사용자명
    - **password**: 비밀번호
    """
    # 사용자 조회
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 비활성 사용자 검사
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 액세스 토큰 생성
    access_token_expires = timedelta(minutes=settings.security.jwt_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # 로그인 활동 기록
    activity = UserActivity(
        user_id=user.id,
        activity_type="login",
        description="사용자 로그인"
    )
    db.add(activity)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "is_admin": user.is_admin
    }

# 사용자 등록
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    새 사용자 등록
    
    - **username**: 사용자명 (필수)
    - **email**: 이메일 (필수)
    - **password**: 비밀번호 (필수)
    - **first_name**: 이름 (선택)
    - **last_name**: 성 (선택)
    """
    # 사용자명 중복 검사
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 이메일 중복 검사
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 새 사용자 생성
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=True,
        is_admin=False  # 기본값은 일반 사용자
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # 사용자 설정 생성
        user_settings = UserSettings(
            user_id=new_user.id,
            theme="light",
            language="ko",
            notification_enabled=True
        )
        db.add(user_settings)
        
        # 사용자 등록 활동 기록
        activity = UserActivity(
            user_id=new_user.id,
            activity_type="register",
            description="사용자 계정 생성"
        )
        db.add(activity)
        db.commit()
        
        return new_user
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"사용자 등록 중 DB 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database error occurred during registration"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 등록 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )

# 현재 사용자 정보 조회
@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """현재 인증된 사용자 정보 조회"""
    return current_user

# 사용자 정보 업데이트
@router.put("/me", response_model=UserResponse)
async def update_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    현재 사용자 정보 업데이트
    
    - **email**: 이메일 (선택)
    - **first_name**: 이름 (선택)
    - **last_name**: 성 (선택)
    - **password**: 비밀번호 (선택)
    - **profile_image**: 프로필 이미지 URL (선택)
    """
    # 이메일 중복 검사
    if user_data.email and user_data.email != current_user.email:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_data.email
    
    # 비밀번호 업데이트
    if user_data.password:
        current_user.hashed_password = get_password_hash(user_data.password)
    
    # 이름과 성 업데이트
    if user_data.first_name is not None:
        current_user.first_name = user_data.first_name
    if user_data.last_name is not None:
        current_user.last_name = user_data.last_name
    
    # 프로필 이미지 업데이트
    if user_data.profile_image is not None:
        current_user.profile_image = user_data.profile_image
    
    try:
        db.add(current_user)
        
        # 사용자 정보 업데이트 활동 기록
        activity = UserActivity(
            user_id=current_user.id,
            activity_type="profile_update",
            description="사용자 프로필 정보 업데이트"
        )
        db.add(activity)
        
        db.commit()
        db.refresh(current_user)
        return current_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 정보 업데이트 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating user information"
        )

# 사용자 설정 조회
@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """현재 사용자의 설정 정보 조회"""
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        # 설정이 없는 경우 기본 설정 생성
        settings = UserSettings(
            user_id=current_user.id,
            theme="light",
            language="ko",
            notification_enabled=True
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return settings

# 사용자 설정 업데이트
@router.put("/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    사용자 설정 업데이트
    
    - **openai_api_key**: OpenAI API 키 (선택)
    - **claude_api_key**: Claude API 키 (선택)
    - **github_token**: GitHub 토큰 (선택)
    - **default_github_repo**: 기본 GitHub 저장소 (선택)
    - **default_github_username**: 기본 GitHub 사용자명 (선택)
    - **theme**: UI 테마 (선택)
    - **language**: 언어 (선택)
    - **notification_enabled**: 알림 활성화 여부 (선택)
    """
    settings = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not settings:
        # 설정이 없는 경우 새로 생성
        settings = UserSettings(
            user_id=current_user.id,
            theme="light",
            language="ko",
            notification_enabled=True
        )
    
    # 설정 업데이트
    if settings_data.openai_api_key is not None:
        settings.openai_api_key = settings_data.openai_api_key
    if settings_data.claude_api_key is not None:
        settings.claude_api_key = settings_data.claude_api_key
    if settings_data.github_token is not None:
        settings.github_token = settings_data.github_token
    if settings_data.default_github_repo is not None:
        settings.default_github_repo = settings_data.default_github_repo
    if settings_data.default_github_username is not None:
        settings.default_github_username = settings_data.default_github_username
    if settings_data.theme is not None:
        settings.theme = settings_data.theme
    if settings_data.language is not None:
        settings.language = settings_data.language
    if settings_data.notification_enabled is not None:
        settings.notification_enabled = settings_data.notification_enabled
    
    try:
        db.add(settings)
        
        # 설정 업데이트 활동 기록
        activity = UserActivity(
            user_id=current_user.id,
            activity_type="settings_update",
            description="사용자 설정 업데이트"
        )
        db.add(activity)
        
        db.commit()
        db.refresh(settings)
        return settings
        
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 설정 업데이트 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating user settings"
        )

# 관리자용 엔드포인트 - 모든 사용자 목록 조회
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    모든 사용자 목록 조회 (관리자 전용)
    
    - **skip**: 건너뛸 결과 수 (페이지네이션)
    - **limit**: 가져올 결과 수 (페이지네이션)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# 관리자용 엔드포인트 - 특정 사용자 정보 조회
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int = Path(..., description="사용자 ID"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    특정 사용자 정보 조회 (관리자 전용)
    
    - **user_id**: 조회할 사용자 ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# 관리자용 엔드포인트 - 사용자 활성/비활성화
@router.put("/users/{user_id}/active", response_model=UserResponse)
async def update_user_active_status(
    user_id: int = Path(..., description="사용자 ID"),
    is_active: bool = Body(..., embed=True),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    사용자 활성/비활성화 (관리자 전용)
    
    - **user_id**: 업데이트할 사용자 ID
    - **is_active**: 활성 상태 (true/false)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 자기 자신을 비활성화할 수 없음
    if user.id == current_user.id and not is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.is_active = is_active
    
    try:
        db.add(user)
        
        # 사용자 상태 변경 활동 기록
        activity = UserActivity(
            user_id=current_user.id,
            activity_type="user_status_change",
            description=f"사용자 #{user_id}의 상태를 {'활성화' if is_active else '비활성화'}로 변경"
        )
        db.add(activity)
        
        db.commit()
        db.refresh(user)
        return user
        
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 상태 업데이트 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating user status"
        )

# 관리자용 엔드포인트 - 사용자 관리자 권한 설정
@router.put("/users/{user_id}/admin", response_model=UserResponse)
async def update_user_admin_status(
    user_id: int = Path(..., description="사용자 ID"),
    is_admin: bool = Body(..., embed=True),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    사용자 관리자 권한 설정 (관리자 전용)
    
    - **user_id**: 업데이트할 사용자 ID
    - **is_admin**: 관리자 상태 (true/false)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 자기 자신의 관리자 권한을 제거할 수 없음
    if user.id == current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin privileges from your own account"
        )
    
    user.is_admin = is_admin
    
    try:
        db.add(user)
        
        # 사용자 권한 변경 활동 기록
        activity = UserActivity(
            user_id=current_user.id,
            activity_type="user_admin_change",
            description=f"사용자 #{user_id}의 관리자 권한을 {'부여' if is_admin else '제거'}"
        )
        db.add(activity)
        
        db.commit()
        db.refresh(user)
        return user
        
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 관리자 권한 업데이트 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating user admin status"
        )

# 비밀번호 변경
@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    current_password: str = Body(..., embed=True),
    new_password: str = Body(..., embed=True),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    비밀번호 변경
    
    - **current_password**: 현재 비밀번호
    - **new_password**: 새 비밀번호
    """
    # 현재 비밀번호 확인
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # 새 비밀번호 해싱 및 업데이트
    hashed_password = get_password_hash(new_password)
    current_user.hashed_password = hashed_password
    
    try:
        db.add(current_user)
        
        # 비밀번호 변경 활동 기록
        activity = UserActivity(
            user_id=current_user.id,
            activity_type="password_change",
            description="사용자 비밀번호 변경"
        )
        db.add(activity)
        
        db.commit()
        return {"message": "Password updated successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"비밀번호 변경 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while changing password"
        )
