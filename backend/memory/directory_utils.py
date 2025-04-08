"""
디렉토리 유틸리티 모듈

벡터 DB 저장을 위한 디렉토리 관리 기능을 제공합니다.
"""
import os
import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

def ensure_directory(directory_path: str) -> str:
    """
    디렉토리가 존재하는지 확인하고, 없으면 생성합니다.
    
    Args:
        directory_path: 확인할 디렉토리 경로
        
    Returns:
        생성된 또는 확인된 디렉토리 경로
    """
    path = Path(directory_path)
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"디렉토리 확인/생성 완료: {directory_path}")
        return directory_path
    except Exception as e:
        fallback_path = get_fallback_directory()
        logger.error(f"디렉토리 생성 실패 ({directory_path}): {str(e)}. 대체 경로 사용: {fallback_path}")
        return fallback_path

def get_data_directory() -> str:
    """
    애플리케이션 데이터 디렉토리 경로를 반환합니다.
    
    Returns:
        데이터 디렉토리 경로
    """
    # 기본 애플리케이션 디렉토리
    app_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = app_dir / "data"
    
    # 디렉토리 생성 시도
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        return str(data_dir)
    except Exception as e:
        # 실패 시 대체 경로 사용
        logger.error(f"기본 데이터 디렉토리 생성 실패: {str(e)}")
        return get_fallback_directory()

def get_vector_store_directory(store_type: str = "faiss") -> str:
    """
    벡터 스토어 디렉토리 경로를 반환합니다.
    
    Args:
        store_type: 벡터 스토어 유형 ('faiss' 등)
        
    Returns:
        벡터 스토어 디렉토리 경로
    """
    data_dir = get_data_directory()
    store_dir = os.path.join(data_dir, f"{store_type}_store")
    return ensure_directory(store_dir)

def get_fallback_directory() -> str:
    """
    기본 데이터 디렉토리 생성에 실패한 경우 사용할 대체 디렉토리를 반환합니다.
    
    Returns:
        대체 디렉토리 경로
    """
    # 시스템 임시 디렉토리 하위에 애플리케이션 폴더 생성
    import tempfile
    temp_dir = os.path.join(tempfile.gettempdir(), "llmnightrun_data")
    os.makedirs(temp_dir, exist_ok=True)
    logger.warning(f"대체 데이터 디렉토리 사용: {temp_dir}")
    return temp_dir

def cleanup_directory(directory_path: str, max_age_days: Optional[int] = None) -> None:
    """
    디렉토리 내 파일을 정리합니다. max_age_days가 설정된 경우 오래된 파일을 제거합니다.
    
    Args:
        directory_path: 정리할 디렉토리 경로
        max_age_days: 유지할 파일의 최대 기간(일). None인 경우 모든 파일 유지
    """
    if max_age_days is None:
        return
        
    if not os.path.exists(directory_path):
        return
        
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            
            # 디렉토리는 건너뜀
            if os.path.isdir(item_path):
                continue
                
            # 파일 생성 시간 확인
            file_creation_time = os.path.getctime(item_path)
            
            # 지정된 기간보다 오래된 파일 삭제
            if current_time - file_creation_time > max_age_seconds:
                os.remove(item_path)
                logger.info(f"오래된 파일 삭제: {item_path}")
    except Exception as e:
        logger.error(f"디렉토리 정리 실패: {str(e)}")
