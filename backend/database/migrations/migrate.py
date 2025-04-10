"""
데이터베이스 마이그레이션 실행 스크립트

이 스크립트는 정의된 마이그레이션을 순서대로 실행하거나 롤백합니다.
"""

import argparse
import logging
import importlib
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = str(Path(__file__).parent.parent.parent.parent)
sys.path.append(project_root)

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(project_root, 'logs', 'migration.log'))
    ]
)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 문자열
from backend.config import settings
DB_CONN_STRING = settings.database.url

def run_migration(migration_module, action='upgrade'):
    """
    지정된 마이그레이션 모듈의 업그레이드 또는 다운그레이드 함수 실행

    Args:
        migration_module: 마이그레이션 모듈
        action: 'upgrade' 또는 'downgrade'
    """
    try:
        if action == 'upgrade':
            migration_module.upgrade(DB_CONN_STRING)
        else:
            migration_module.downgrade(DB_CONN_STRING)
    except Exception as e:
        logger.error(f"마이그레이션 실행 오류: {str(e)}")
        raise

def get_migration_modules():
    """
    마이그레이션 모듈 목록을 가져옴

    Returns:
        마이그레이션 모듈과 이름의 튜플 리스트, 마이그레이션 번호 순서로 정렬됨
    """
    migrations_dir = Path(__file__).parent
    migration_files = [f for f in migrations_dir.glob('migration_*.py') if f.is_file()]
    
    migration_modules = []
    for file in migration_files:
        module_name = file.stem
        # 모듈 이름에서 마이그레이션 번호 추출 (예: 'migration_001_...' -> 1)
        try:
            migration_num = int(module_name.split('_')[1])
        except (IndexError, ValueError):
            logger.warning(f"잘못된 마이그레이션 파일 이름: {file.name}")
            continue
        
        try:
            module = importlib.import_module(f'backend.database.migrations.{module_name}')
            migration_modules.append((migration_num, module_name, module))
        except ImportError as e:
            logger.error(f"마이그레이션 모듈 로드 오류: {str(e)}")
    
    # 마이그레이션 번호 순서로 정렬
    migration_modules.sort(key=lambda x: x[0])
    return migration_modules

def main():
    """
    마이그레이션 실행 메인 함수
    """
    parser = argparse.ArgumentParser(description='데이터베이스 마이그레이션 실행 도구')
    parser.add_argument('--action', choices=['upgrade', 'downgrade'], default='upgrade', 
                        help='마이그레이션 동작: upgrade (기본) 또는 downgrade')
    parser.add_argument('--migration', type=str, 
                        help='실행할 특정 마이그레이션 (예: migration_001_add_user_system). 지정하지 않으면 모든 마이그레이션 실행')
    parser.add_argument('--list', action='store_true', 
                        help='사용 가능한 마이그레이션 목록 표시')

    args = parser.parse_args()
    
    try:
        migration_modules = get_migration_modules()
        
        if args.list:
            logger.info("=== 사용 가능한 마이그레이션 목록 ===")
            for num, name, _ in migration_modules:
                logger.info(f"{num:03d}: {name}")
            return
        
        if args.migration:
            # 특정 마이그레이션만 실행
            for num, name, module in migration_modules:
                if name == args.migration:
                    logger.info(f"마이그레이션 {name} {args.action} 실행 중...")
                    run_migration(module, args.action)
                    logger.info(f"마이그레이션 {name} {args.action} 완료")
                    break
            else:
                logger.error(f"지정된 마이그레이션을 찾을 수 없음: {args.migration}")
        else:
            # 모든 마이그레이션 실행
            if args.action == 'upgrade':
                logger.info("모든 마이그레이션 업그레이드 실행 중...")
                for num, name, module in migration_modules:
                    logger.info(f"마이그레이션 {name} 업그레이드 실행 중...")
                    run_migration(module, 'upgrade')
                    logger.info(f"마이그레이션 {name} 업그레이드 완료")
            else:
                logger.info("모든 마이그레이션 다운그레이드 실행 중 (역순)...")
                for num, name, module in reversed(migration_modules):
                    logger.info(f"마이그레이션 {name} 다운그레이드 실행 중...")
                    run_migration(module, 'downgrade')
                    logger.info(f"마이그레이션 {name} 다운그레이드 완료")
                    
            logger.info(f"모든 마이그레이션 {args.action} 완료")
    
    except Exception as e:
        logger.error(f"마이그레이션 실행 중 오류 발생: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
