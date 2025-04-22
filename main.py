#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
LLM Night Run

Tkinter 기반 LLM, 벡터 검색, 대화 관리 통합 애플리케이션
"""

import os
import sys
import tkinter as tk
import argparse
import logging
from pathlib import Path

# 필요한 디렉토리 확인 및 생성
def ensure_directories():
    """필요한 디렉토리 확인 및 생성"""
    # 기본 디렉토리
    directories = [
        "config",       # 설정 파일
        "logs",         # 로그 파일
        "data",         # 데이터 파일
        "data/vector_db",  # 벡터 DB 파일
        "data/conversations",  # 대화 파일
        "plugins"       # 플러그인 파일
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Directory checked: {directory}")

# 로깅 설정
def setup_logging(log_level=logging.INFO):
    """로깅 설정"""
    # 로그 디렉토리 확인
    os.makedirs("logs", exist_ok=True)
    
    # 로그 파일 경로
    log_file = os.path.join("logs", "llm_night_run.log")
    
    # 로깅 설정
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # 로거 가져오기
    logger = logging.getLogger("main")
    
    logger.info("Logging initialized")
    return logger

# 인수 파싱
def parse_arguments():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description="LLM Night Run")
    
    # 설정 파일 경로
    parser.add_argument(
        "--config", 
        type=str, 
        default="config/config.yaml",
        help="설정 파일 경로"
    )
    
    # 로그 레벨
    parser.add_argument(
        "--log-level", 
        type=str, 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="로그 레벨"
    )
    
    return parser.parse_args()

# 메인 함수
def main():
    """메인 함수"""
    # 인수 파싱
    args = parse_arguments()
    
    # 로그 레벨 설정
    log_level = getattr(logging, args.log_level)
    
    # 디렉토리 확인
    ensure_directories()
    
    # 로깅 설정
    logger = setup_logging(log_level)
    
    try:
        # Python 경로에 현재 디렉토리 추가
        import sys
        sys.path.insert(0, os.path.abspath('.'))
        
        # 코어 모듈 임포트
        from core.config import get_config
        
        # 설정 로드
        config = get_config(args.config)
        
        # TK 초기화
        root = tk.Tk()
        
        # GUI 앱 생성
        from gui import LLMNightRunApp
        app = LLMNightRunApp(root)
        
        # 앱 실행
        logger.info("Starting application")
        
        # 앱 초기화 후 모듈 탭으로 전환
        app.main_notebook.select(1) # 모듈 탭을 선택 (인덱스 1)
        
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        
        # 간단한 오류 메시지
        if 'root' in locals() and root:
            import tkinter.messagebox as messagebox
            messagebox.showerror("오류", f"애플리케이션 오류: {str(e)}")
        else:
            print(f"Error: {str(e)}", file=sys.stderr)
        
        sys.exit(1)

# 스크립트 실행
if __name__ == "__main__":
    main()
