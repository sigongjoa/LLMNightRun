"""
LLMNightRun 로깅 모듈

애플리케이션 전체에서 일관된 로깅을 위한 설정과 인터페이스를 제공합니다.
구조화된 로깅과 컨텍스트 관리를 지원하며, 개발 및 프로덕션 환경에 적합한 설정을 제공합니다.
"""

import logging
import os
import sys
import json
import traceback
from pathlib import Path
from datetime import datetime
import logging.handlers
from typing import Dict, Any, Optional, Union
from contextvars import ContextVar

from backend.config import settings

# 로그 컨텍스트를 저장하는 context var
log_context: ContextVar[Dict[str, Any]] = ContextVar('log_context', default={})


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
    json_log_file = log_dir / f"llmnightrun_json_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # 로깅 포맷 설정
    log_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s - %(context)s"
    simple_format = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    formatter = CustomFormatter(log_format)
    simple_formatter = logging.Formatter(simple_format)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 핸들러 초기화 (중복 방지)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 콘솔 핸들러 추가
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter(simple_format))
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # 파일 핸들러 추가 (일별 로그 파일)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when="midnight",
        backupCount=30,  # 최대 30일분 보관
        encoding="utf-8"
    )
    file_handler.setFormatter(simple_formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    # JSON 파일 핸들러 추가 (구조화된 로깅)
    json_file_handler = logging.handlers.TimedRotatingFileHandler(
        json_log_file,
        when="midnight",
        backupCount=30,
        encoding="utf-8"
    )
    json_file_handler.setFormatter(JsonFormatter())
    json_file_handler.setLevel(log_level)
    root_logger.addHandler(json_file_handler)
    
    # 외부 라이브러리 로깅 레벨 조정
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    # 애플리케이션 로거 생성
    app_logger = logging.getLogger("llmnightrun")
    app_logger.setLevel(log_level)
    
    # 모듈별 로그 레벨 설정
    module_log_levels = {
        "llmnightrun.api": logging.DEBUG if settings.debug else logging.INFO,
        "llmnightrun.agent": logging.DEBUG,
        "llmnightrun.llm": logging.DEBUG,
        "llmnightrun.database": logging.INFO,
    }
    
    for module, level in module_log_levels.items():
        logging.getLogger(module).setLevel(level)
    
    app_logger.info("로깅 시스템 초기화 완료", extra={"component": "logger", "action": "setup"})
    return app_logger


class CustomFormatter(logging.Formatter):
    """커스텀 로그 포맷터"""
    
    def format(self, record):
        """로그 레코드 포맷팅"""
        # 로그 컨텍스트 추가
        record.context = ""
        if hasattr(record, 'context_data') and record.context_data:
            record.context = json.dumps(record.context_data, ensure_ascii=False)
        elif log_context.get({}):
            record.context = json.dumps(log_context.get(), ensure_ascii=False)
        
        # 예외 정보 추가
        if record.exc_info:
            record.exc_text = self.formatException(record.exc_info)
        
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON 형식의 로그 포맷터"""
    
    def format(self, record):
        """로그 레코드를 JSON 형식으로 포맷팅"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 컨텍스트 데이터 추가
        context_data = getattr(record, 'context_data', None) or log_context.get({})
        if context_data:
            log_data.update(context_data)
        
        # extra 필드 추가
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text",
                          "filename", "funcName", "id", "levelname", "levelno",
                          "lineno", "module", "msecs", "message", "msg", "name",
                          "pathname", "process", "processName", "relativeCreated",
                          "stack_info", "thread", "threadName", "context_data"]:
                log_data[key] = value
        
        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data, ensure_ascii=False)


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
            # 색상 적용
            levelname = record.levelname
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            record.msg = f"{self.COLORS[levelname]}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)


def get_logger(name: str):
    """
    모듈별 로거 생성
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        
    Returns:
        logging.Logger: 설정된 로거 인스턴스
    """
    if name.startswith("backend."):
        # backend.module.submodule -> llmnightrun.module.submodule
        name = "llmnightrun" + name[7:]
    else:
        name = f"llmnightrun.{name}"
    
    return logging.getLogger(name)


def set_context(**kwargs):
    """
    현재 스레드의 로그 컨텍스트 설정
    
    Args:
        **kwargs: 컨텍스트에 추가할 키-값 쌍
    """
    current = log_context.get({}).copy()
    current.update(kwargs)
    log_context.set(current)


def clear_context():
    """현재 스레드의 로그 컨텍스트 초기화"""
    log_context.set({})


class LogContext:
    """로그 컨텍스트를 관리하는 컨텍스트 매니저"""
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.previous = {}
    
    def __enter__(self):
        self.previous = log_context.get({}).copy()
        current = self.previous.copy()
        current.update(self.kwargs)
        log_context.set(current)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        log_context.set(self.previous)


def log_execution_time(logger=None, level=logging.INFO, operation_name=None):
    """
    함수 실행 시간을 로깅하는 데코레이터
    
    Args:
        logger: 사용할 로거 (None인 경우 함수 모듈의 로거 사용)
        level: 로그 레벨
        operation_name: 작업 이름 (None인 경우 함수 이름 사용)
        
    Returns:
        decorator: 함수 실행 시간을 로깅하는 데코레이터
    """
    import time
    import functools
    
    def decorator(func):
        nonlocal logger
        
        if logger is None:
            logger = get_logger(func.__module__)
            
        func_name = operation_name or func.__name__
            
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.log(
                level,
                f"{func_name} 실행 완료 (소요 시간: {execution_time:.3f}초)",
                extra={
                    "context_data": {
                        "operation": func_name,
                        "execution_time": execution_time
                    }
                }
            )
            
            return result
        
        return wrapper
    
    return decorator
