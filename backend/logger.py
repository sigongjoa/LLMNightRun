"""
LLMNightRun 로깅 모듈

애플리케이션 전체에서 일관된 로깅을 위한 설정과 인터페이스를 제공합니다.
"""

import logging
import os
import sys
from pathlib import Path

from backend.config import config


# 로그 디렉토리 생성
log_dir = config.base_dir / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "llmnightrun.log"

# 로깅 포맷 설정
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.DEBUG if config.debug else logging.INFO

# 루트 로거 설정
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file),
    ],
)

# 외부 라이브러리 로깅 레벨 조정
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("selenium").setLevel(logging.WARNING)
logging.getLogger("docker").setLevel(logging.WARNING)

# 애플리케이션 로거 생성
logger = logging.getLogger("llmnightrun")


class ColorFormatter(logging.Formatter):
    """색상이 적용된 로그 포맷터"""
    
    COLORS = {
        "DEBUG": "\033[36m",    # 청록색
        "INFO": "\033[32m",     # 녹색
        "WARNING": "\033[33m",  # 노란색
        "ERROR": "\033[31m",    # 빨간색
        "CRITICAL": "\033[41m", # 빨간 배경
        "RESET": "\033[0m",     # 리셋
    }
    
    def format(self, record):
        """로그 레코드 포맷팅"""
        if record.levelname in self.COLORS and sys.stdout.isatty():
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            )
            record.msg = f"{self.COLORS[record.levelname.strip()]}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)


# 터미널 출력에 색상 추가
for handler in logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setFormatter(ColorFormatter(LOG_FORMAT))


def get_logger(name):
    """모듈별 로거 생성
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        
    Returns:
        logging.Logger: 설정된 로거 인스턴스
    """
    module_logger = logging.getLogger(f"llmnightrun.{name}")
    return module_logger