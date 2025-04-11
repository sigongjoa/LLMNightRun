"""\n프로젝트 초기 설정 스크립트\n\n이 스크립트는 LLMNightRun을 처음 시작할 때 필요한 설정을 자동으로 수행합니다.\n1. 데이터베이스 초기화\n2. 기본 사용자 계정 생성\n3. 테스트 프로젝트 생성\n"""\n\nimport os\nimport sys\nimport logging\nfrom pathlib import Path\n\n# 상위 디렉토리를 Python 경로에 추가 (현재 디렉토리가 backend일 경우)\nsys.path.append(str(Path(__file__).parent.parent))\n\n# 로깅 설정\nlogging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')\nlogger = logging.getLogger(__name__)

def setup_environment():
    """환경 설정"""
    logger.info("LLMNightRun 환경 설정 시작")
    
    # 현재 디렉토리 확인
    current_dir = Path(__file__).parent
    logger.info(f"현재 디렉토리: {current_dir}")
    
    # 환경 변수 설정
    os.environ.setdefault("BACKEND_ENV", "development")
    
    try:
        # 데이터베이스 초기화 스크립트 실행
        logger.info("데이터베이스 초기화 시작")
        from backend.init_db import init_database
        init_database()
        logger.info("데이터베이스 초기화 완료")
        
        # 기본 사용자 계정 정보 출력
        logger.info("\n" + "-"*50)
        logger.info("기본 계정 정보:")
        logger.info("1. 관리자 계정")
        logger.info("   - 아이디: admin")
        logger.info("   - 비밀번호: admin123")
        logger.info("2. 일반 사용자 계정")
        logger.info("   - 아이디: user")
        logger.info("   - 비밀번호: user123")
        logger.info("-"*50 + "\n")
        
        logger.info("설정이 완료되었습니다. 이제 서버를 시작하세요.")
        logger.info("서버 시작 명령어: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")
        
        return True
    except Exception as e:
        logger.error(f"설정 중 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    setup_environment()
