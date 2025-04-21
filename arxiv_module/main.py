"""
arXiv CS/AI 논문 크롤링 및 분석 애플리케이션

arXiv API를 사용해 CS/AI 카테고리의 논문을 검색하고 분석하는 GUI 애플리케이션
"""

import sys
import os
import logging
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox

# NLTK 설정 스크립트 import
from nltk_setup import setup_nltk_data

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("arxiv_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def show_error_message(title, message):
    """오류 메시지 표시"""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.exec_()

def check_dependencies():
    """
    필요한 디렉토리 및 의존성 확인
    """
    # 필요한 디렉토리 생성
    papers_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "papers")
    os.makedirs(papers_dir, exist_ok=True)
    
    # 기타 의존성 확인
    try:
        import arxiv
        logger.info("arxiv 라이브러리 확인 완료")
    except ImportError:
        error_msg = "arxiv 라이브러리가 설치되지 않았습니다. 'pip install arxiv' 명령어로 설치해주세요."
        logger.error(error_msg)
        show_error_message("의존성 오류", error_msg)
        return False
        
    try:
        from PyQt5.QtWidgets import QMainWindow
        logger.info("PyQt5 라이브러리 확인 완료")
    except ImportError:
        error_msg = "PyQt5 라이브러리가 설치되지 않았습니다. 'pip install PyQt5' 명령어로 설치해주세요."
        logger.error(error_msg)
        show_error_message("의존성 오류", error_msg)
        return False
        
    try:
        import nltk
        logger.info("nltk 라이브러리 확인 완료")
        
        # NLTK 데이터 설정
        try:
            logger.info("NLTK 데이터 설정 시작...")
            setup_nltk_data()
            logger.info("NLTK 데이터 설정 완료")
        except Exception as e:
            logger.warning(f"NLTK 데이터 설정 중 오류: {e}")
            # 오류가 발생해도 계속 진행
            
    except ImportError:
        error_msg = "nltk 라이브러리가 설치되지 않았습니다. 'pip install nltk' 명령어로 설치해주세요."
        logger.error(error_msg)
        show_error_message("의존성 오류", error_msg)
        return False
        
    logger.info("모든 의존성 확인 완료")
    return True

def main():
    """
    메인 애플리케이션 실행
    """
    try:
        # NLTK 설정 실행 - 어떠한 경우라도 먼저 실행
        try:
            logger.info("NLTK 데이터 관리 도구 설정 시작...")
            setup_nltk_data()
            logger.info("NLTK 데이터 관리 도구 설정 완료")
        except Exception as e:
            logger.warning(f"NLTK 설정 오류: {e} - 계속 진행")
            
        # Qt 애플리케이션 생성
        app = QApplication(sys.argv)
        app.setApplicationName("arXiv CS/AI Paper Analyzer")
        
        # 의존성 확인
        if not check_dependencies():
            return
            
        # 이 부분에서 필요한 모듈을 임포트합니다
        # 의존성 확인 후에 임포트하여 불필요한 오류 메시지 방지
        try:
            from gui.main_window import ArxivMainWindow
            
            # 메인 윈도우 생성 및 표시
            window = ArxivMainWindow()
            window.show()
            
            logger.info("애플리케이션 시작됨")
            
            # 애플리케이션 실행
            sys.exit(app.exec_())
            
        except ImportError as e:
            error_msg = f"필요한 모듈을 임포트할 수 없습니다: {e}"
            logger.error(error_msg)
            show_error_message("모듈 임포트 오류", error_msg)
            return
        
    except Exception as e:
        error_msg = f"애플리케이션 시작 중 오류 발생: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        show_error_message("애플리케이션 오류", f"애플리케이션 시작 중 오류가 발생했습니다:\n{e}")

if __name__ == "__main__":
    main()
