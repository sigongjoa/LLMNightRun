"""
데이터베이스 마이그레이션 실행 스크립트
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# 프로젝트 루트 디렉토리
project_root = os.path.dirname(os.path.abspath(__file__))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """마이그레이션 실행 메인 함수"""
    try:
        # logs 디렉토리 생성 (없는 경우)
        logs_dir = os.path.join(project_root, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        logger.info("데이터베이스 마이그레이션 시작")
        
        # 마이그레이션 스크립트 실행
        migration_script = os.path.join(project_root, 'backend', 'database', 'migrations', 'migrate.py')
        
        if not os.path.exists(migration_script):
            logger.error(f"마이그레이션 스크립트를 찾을 수 없습니다: {migration_script}")
            sys.exit(1)
        
        # Python 환경에서 마이그레이션 스크립트 실행
        result = subprocess.run(
            [sys.executable, migration_script, '--action', 'upgrade'],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        # 결과 확인
        if result.returncode == 0:
            logger.info("마이그레이션 성공!")
            logger.info(result.stdout)
        else:
            logger.error("마이그레이션 실패!")
            logger.error(f"오류: {result.stderr}")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"마이그레이션 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
