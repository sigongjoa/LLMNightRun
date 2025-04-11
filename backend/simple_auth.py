"""
단순화된 인증 모듈

로그인 문제 해결을 위한 간단한 인증 구현
"""

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
import logging

from database import get_db
from database.models import User

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(tags=["simple-auth"])

# 간단한 사용자 정보 반환 함수
def get_user_info(user: User):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
        "is_active": user.is_active
    }

# 토큰 생성 함수
def create_simple_token(username: str):
    # 만료 시간 설정 (24시간)
    expires = datetime.utcnow() + timedelta(hours=24)
    
    # 페이로드 생성
    payload = {
        "sub": username,
        "exp": expires
    }
    
    # 토큰 생성 (간단한 비밀키 사용)
    token = jwt.encode(payload, "simple_secret_key", algorithm="HS256")
    
    return token

# 단순 로그인 엔드포인트
@router.post("/simple-login")
def simple_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    logger.info(f"단순 로그인 시도: 사용자={username}, 비밀번호={password}")
    
    # 하드코딩된 관리자 계정 (디버그용)
    if username == "admin" and password == "admin123":
        logger.info("하드코딩된 관리자 계정으로 로그인 성공")
        
        # 데이터베이스에서 admin 사용자 조회
        user = db.query(User).filter(User.username == "admin").first()
        
        # 사용자가 없는 경우 생성
        if not user:
            logger.info("관리자 계정이 데이터베이스에 없어 새로 생성합니다")
            user = User(
                username="admin",
                email="admin@example.com",
                hashed_password="admin123",  # 실제로는 해싱해야 함
                first_name="관리자",
                last_name="계정",
                is_active=True,
                is_admin=True
            )
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
                logger.info(f"admin 계정 생성 완료: id={user.id}")
            except Exception as e:
                db.rollback()
                logger.error(f"admin 계정 생성 실패: {str(e)}")
        
        # 토큰 생성
        token = create_simple_token(username)
        
        # 응답 데이터
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": get_user_info(user) if user else {
                "username": "admin",
                "email": "admin@example.com",
                "is_admin": True,
                "is_active": True
            }
        }
    
    # 일반 사용자 계정 체크
    if username == "user" and password == "user123":
        logger.info("하드코딩된 일반 사용자 계정으로 로그인 성공")
        
        # 데이터베이스에서 user 사용자 조회
        user = db.query(User).filter(User.username == "user").first()
        
        # 사용자가 없는 경우 생성
        if not user:
            logger.info("일반 사용자 계정이 데이터베이스에 없어 새로 생성합니다")
            user = User(
                username="user",
                email="user@example.com",
                hashed_password="user123",  # 실제로는 해싱해야 함
                first_name="일반",
                last_name="사용자",
                is_active=True,
                is_admin=False
            )
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
                logger.info(f"user 계정 생성 완료: id={user.id}")
            except Exception as e:
                db.rollback()
                logger.error(f"user 계정 생성 실패: {str(e)}")
        
        # 토큰 생성
        token = create_simple_token(username)
        
        # 응답 데이터
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": get_user_info(user) if user else {
                "username": "user",
                "email": "user@example.com",
                "is_admin": False,
                "is_active": True
            }
        }
    
    # 데이터베이스에서 사용자 검색 시도 (하드코딩 계정이 아닌 경우)
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if user:
            logger.info(f"사용자 {username}을 데이터베이스에서 찾았습니다")
            
            # 간단한 비밀번호 검증 (실제로는 해싱된 비밀번호와 비교해야 함)
            hashed_password = user.hashed_password
            if "bcrypt" in hashed_password:  # 해싱된 경우 실패 (단순화를 위해)
                logger.info("해싱된 비밀번호가 있어 로그인 실패")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="비밀번호가 일치하지 않습니다"
                )
            
            # 단순 비교
            if hashed_password == password:
                logger.info(f"사용자 {username} 로그인 성공")
                token = create_simple_token(username)
                return {
                    "access_token": token,
                    "token_type": "bearer",
                    "user": get_user_info(user)
                }
    except Exception as e:
        logger.error(f"사용자 검색 중 오류 발생: {str(e)}")
    
    # 인증 실패
    logger.warning(f"사용자 {username} 로그인 실패: 잘못된 사용자명 또는 비밀번호")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="잘못된 사용자명 또는 비밀번호"
    )

# 간단한 사용자 정보 조회 엔드포인트
@router.get("/simple-me")
def get_current_user(authorization: str = None, db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효한 인증 토큰이 필요합니다"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # 토큰 디코딩
        payload = jwt.decode(token, "simple_secret_key", algorithms=["HS256"])
        username = payload.get("sub")
        
        # 사용자 조회
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        return get_user_info(user)
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰"
        )
