"""
로깅 시스템

애플리케이션 전반에서 일관된 로깅을 제공하는 모듈입니다.
"""

import os
import logging
import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import get_config

# 로그 레벨 매핑
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# 로그 포맷
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logger(name: str, log_file: Optional[str] = None, level: Optional[str] = None) -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
        log_file: 로그 파일 경로 (기본값: None, 로그 디렉토리에 자동 생성)
        level: 로그 레벨 (기본값: None, 설정에서 가져옴)
    
    Returns:
        설정된 로거
    """
    config = get_config()
    
    # 로그 레벨 설정
    if level is None:
        level = config.get("core", "log_level", "INFO")
    
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    # 로그 디렉토리 설정
    log_dir = config.get("core", "log_dir")
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일 설정
    if log_file is None:
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        log_file = os.path.join(log_dir, f"{name}_{date_str}.log")
    
    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 이미 핸들러가 설정된 경우 중복 방지
    if not logger.handlers:
        # 파일 핸들러
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    모듈에 대한 로거 가져오기
    
    Args:
        name: 모듈 이름 또는 로거 이름
    
    Returns:
        설정된 로거
    """
    return setup_logger(name)
