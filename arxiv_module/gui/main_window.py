"""
arXiv Module GUI - 메인 윈도우 구현
"""

import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QStatusBar, QMessageBox,
    QSpinBox, QComboBox, QCheckBox, QLineEdit, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QSettings
from PyQt5.QtGui import QFont, QIcon

# 부모 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GUI 하위 모듈 import
from gui.search_panel import SearchPanel
from gui.results_panel import ResultsPanel
from gui.library_panel import LibraryPanel  # 추가
from gui.settings_panel import SettingsPanel  # 추가

class ArxivMainWindow(QMainWindow):
    """arXiv 모듈 메인 윈도우 클래스"""
    
    def __init__(self):
        """ArxivMainWindow 초기화"""
        super().__init__()
        
        # 설정 초기화
        self.settings = QSettings("LLMNightRun", "arXivAnalyzer")
        
        # 윈도우 설정
        self.setWindowTitle("arXiv CS/AI Paper Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        
        # 중앙 위젯 및 레이아웃 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 탭 위젯 설정
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # 상태 표시줄 설정
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # 탭 초기화
        self.init_tabs()
        
        # 설정 적용
        self.apply_settings()
        
        logger.info("ArxivMainWindow initialized")
        
    def init_tabs(self):
        """탭 위젯 초기화"""
        # 검색 탭
        self.search_tab = QWidget()
        self.search_layout = QVBoxLayout(self.search_tab)
        self.search_panel = SearchPanel(parent=self)
        self.search_layout.addWidget(self.search_panel)
        self.tabs.addTab(self.search_tab, "Search Papers")
        
        # 결과 탭
        self.results_tab = QWidget()
        self.results_layout = QVBoxLayout(self.results_tab)
        self.results_panel = ResultsPanel(parent=self)
        self.results_layout.addWidget(self.results_panel)
        self.tabs.addTab(self.results_tab, "Results")
        
        # 저장된 논문 관리 탭 (새로 추가)
        self.library_tab = QWidget()
        self.library_layout = QVBoxLayout(self.library_tab)
        self.library_panel = LibraryPanel(parent=self)
        self.library_layout.addWidget(self.library_panel)
        self.tabs.addTab(self.library_tab, "My Library")
        
        # 설정 탭 (새로 추가)
        self.settings_tab = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_tab)
        self.settings_panel = SettingsPanel(parent=self)
        self.settings_layout.addWidget(self.settings_panel)
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # 탭 변경 이벤트 연결
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
    def on_tab_changed(self, index):
        """탭 변경 이벤트 처리"""
        tab_name = self.tabs.tabText(index)
        logger.info(f"Switched to tab: {tab_name}")
        
        # 결과 탭으로 변경 시 결과 업데이트
        if tab_name == "Results" and hasattr(self, 'results_panel'):
            # self.results_panel.update_results()
            pass
        
        # 라이브러리 탭으로 변경 시 라이브러리 새로고침
        elif tab_name == "My Library" and hasattr(self, 'library_panel'):
            # 라이브러리 자동 새로고침 기능은 주석 처리 (필요 시 해제)
            # self.library_panel.load_library()
            pass
    
    def apply_settings(self):
        """설정 적용"""
        # 글꼴 크기 설정
        ui_font_size = self.settings.value("ui_font_size", 9, type=int)
        content_font_size = self.settings.value("content_font_size", 10, type=int)
        
        # UI 글꼴 설정
        app = QApplication.instance()
        if app:
            font = app.font()
            font.setPointSize(ui_font_size)
            app.setFont(font)
        
        # 테마 설정 (미구현)
        theme = self.settings.value("theme", "system")
        # TODO: 테마 설정 구현
        
        logger.info(f"Applied settings: UI font size={ui_font_size}, Content font size={content_font_size}, Theme={theme}")
    
    def display_error(self, title, message):
        """에러 메시지 표시"""
        QMessageBox.critical(self, title, message)
        
    def display_info(self, title, message):
        """정보 메시지 표시"""
        QMessageBox.information(self, title, message)
        
    def update_status(self, message):
        """상태 표시줄 업데이트"""
        self.status_bar.showMessage(message)
        
    def on_search_complete(self, results):
        """검색 완료 이벤트 처리"""
        # 결과 패널에 검색 결과 전달
        if hasattr(self, 'results_panel'):
            self.results_panel.set_results(results)
            
        # 결과 탭으로 전환
        self.tabs.setCurrentIndex(1)  # Results 탭
        
        # 상태 업데이트
        num_results = len(results) if results else 0
        self.update_status(f"Search complete: {num_results} papers found")

    def closeEvent(self, event):
        """애플리케이션 종료 이벤트 처리"""
        # 설정 변경 사항이 있는지 확인
        if hasattr(self, 'settings_panel') and self.settings_panel.has_unsaved_changes():
            reply = QMessageBox.question(
                self, 
                "Unsaved Settings", 
                "You have unsaved settings changes. Do you want to save them before quitting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, 
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.settings_panel.save_settings()
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        # 종료 확인
        reply = QMessageBox.question(
            self, 
            "Confirm Exit", 
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# 애플리케이션 실행 함수
def run_app():
    app = QApplication(sys.argv)
    window = ArxivMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
