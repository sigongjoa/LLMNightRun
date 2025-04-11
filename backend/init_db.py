"""\n데이터베이스 초기화 및 테스트 사용자 생성 스크립트\n\n초기 설정 및 테스트 데이터 생성을 위한 스크립트입니다.\n"""\n\nimport logging\nimport sys\nfrom pathlib import Path\nfrom sqlalchemy.orm import Session\nfrom sqlalchemy.exc import IntegrityError\n\n# 상위 디렉토리를 Python 경로에 추가\nsys.path.append(str(Path(__file__).parent.parent))\n\n# 백엔드 패키지 임포트\nfrom backend.database.connection import get_db, create_tables\nfrom backend.database.models import User, UserSettings, Project\nfrom backend.auth.dependencies import get_password_hash

# 로거 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 기본 관리자 계정 정보
DEFAULT_ADMIN = {
    "username": "admin",
    "email": "admin@example.com",
    "password": "admin123",
    "first_name": "관리자",
    "last_name": "계정",
    "is_admin": True
}

# 기본 테스트 계정 정보
DEFAULT_USER = {
    "username": "user",
    "email": "user@example.com",
    "password": "user123",
    "first_name": "테스트",
    "last_name": "사용자",
    "is_admin": False
}

def create_user(db: Session, user_data: dict) -> User:
    """사용자 생성 함수"""
    # 이미 존재하는 사용자인지 확인
    existing_user = db.query(User).filter(User.username == user_data["username"]).first()
    if existing_user:
        logger.info(f"사용자 {user_data['username']}이(가) 이미 존재합니다.")
        return existing_user

    # 새 사용자 생성
    hashed_password = get_password_hash(user_data["password"])
    new_user = User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=hashed_password,
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        is_active=True,
        is_admin=user_data.get("is_admin", False)
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"사용자 {new_user.username} 생성 완료")
        
        # 사용자 설정 생성
        user_settings = UserSettings(
            user_id=new_user.id,
            theme="light",
            language="ko",
            notification_enabled=True
        )
        db.add(user_settings)
        db.commit()
        
        return new_user
    except IntegrityError as e:
        db.rollback()
        logger.error(f"사용자 생성 중 오류 발생: {str(e)}")
        raise

def create_default_project(db: Session, user: User) -> Project:
    """기본 프로젝트 생성 함수"""
    # 이미 존재하는 프로젝트인지 확인
    existing_project = db.query(Project).filter(
        Project.name == "기본 프로젝트", 
        Project.owner_id == user.id
    ).first()
    
    if existing_project:
        logger.info(f"사용자 {user.username}의 기본 프로젝트가 이미 존재합니다.")
        return existing_project

    # 새 프로젝트 생성
    new_project = Project(
        name="기본 프로젝트",
        description="사용자의 기본 프로젝트입니다.",
        tags=["기본", "시작"],
        is_active=True,
        is_public=False,
        owner_id=user.id
    )
    
    try:
        db.add(new_project)
        db.commit()
        db.refresh(new_project)
        logger.info(f"사용자 {user.username}의 기본 프로젝트 생성 완료")
        return new_project
    except IntegrityError as e:
        db.rollback()
        logger.error(f"프로젝트 생성 중 오류 발생: {str(e)}")
        raise

def init_database():
    """데이터베이스 초기화 및 기본 데이터 생성"""
    logger.info("데이터베이스 초기화 및 기본 데이터 생성 시작")
    
    # 데이터베이스 테이블 생성 (없는 경우)
    create_tables()
    logger.info("데이터베이스 테이블 생성 완료")
    
    # 데이터베이스 세션 시작
    db = next(get_db())
    
    try:
        # 관리자 계정 생성
        admin_user = create_user(db, DEFAULT_ADMIN)
        create_default_project(db, admin_user)
        
        # 테스트 사용자 계정 생성
        test_user = create_user(db, DEFAULT_USER)
        create_default_project(db, test_user)
        
        logger.info("기본 사용자 및 프로젝트 생성 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
