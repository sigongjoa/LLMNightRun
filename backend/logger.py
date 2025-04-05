"""
LLMNightRun 로깅 모듈

애플리케이션 전체에서 일관된 로깅을 위한 설정과 인터페이스를 제공합니다.
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime
import logging.handlers

from .config import settings


def setup_logging(log_level=None):
    """
    애플리케이션 로깅을 설정합니다.
    
    Args:
        log_level: 로그 레벨 (None인 경우 config 설정 사용)
        
    Returns:
        logger: 설정된 루트 로거
    """
    # 로그 레벨 설정
    if log_level is None:
        log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # 로그 디렉토리 생성
    log_dir = settings.base_dir / "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 로그 파일 경로
    log_file = log_dir / f"llmnightrun_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # 로깅 포맷 설정
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 핸들러 초기화 (중복 방지)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter(log_format))
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (일별 로그 파일)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when="midnight",
        backupCount=30,  # 최대 30일분 보관
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    # 외부 라이브러리 로깅 레벨 조정
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    # 애플리케이션 로거 생성
    app_logger = logging.getLogger("llmnightrun")
    app_logger.setLevel(log_level)
    
    app_logger.info("로깅 시스템 초기화 완료")
    return app_logger


class ColorFormatter(logging.Formatter):
    """색상이 적용된 로그 포맷터"""
    
    COLORS = {
        "DEBUG": "\033[36m",     # 청록색
        "INFO": "\033[32m",      # 녹색
        "WARNING": "\033[33m",   # 노란색
        "ERROR": "\033[31m",     # 빨간색
        "CRITICAL": "\033[41m",  # 빨간 배경
        "RESET": "\033[0m",      # 리셋
    }
    
    def format(self, record):
        """로그 레코드 포맷팅"""
        if record.levelname in self.COLORS and sys.stdout.isatty():
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            )
            record.msg = f"{self.COLORS[record.levelname.strip()]}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)


def get_logger(name):
    """모듈별 로거 생성
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        
    Returns:
        logging.Logger: 설정된 로거 인스턴스
    """
    module_logger = logging.getLogger(f"llmnightrun.{name}")
    return module_logger