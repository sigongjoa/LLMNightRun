"""
arXiv Module GUI - 설정 패널 구현

프로그램 설정을 관리하는 패널
"""

import sys
import os
import json
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QGridLayout, QLineEdit, QCheckBox, QSpinBox,
    QComboBox, QFileDialog, QMessageBox, QTabWidget,
    QRadioButton, QButtonGroup, QFrame
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont

# 부모 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SettingsPanel(QWidget):
    """arXiv 설정 패널 클래스"""
    
    def __init__(self, parent=None):
        """
        SettingsPanel 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__()
        self.parent = parent
        self.settings = QSettings("LLMNightRun", "arXivAnalyzer")
        self.init_ui()
        logger.info("SettingsPanel initialized")
        
    def init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        
        # 제목 레이블
        title_label = QLabel("Settings")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 설정 탭
        settings_tabs = QTabWidget()
        
        # 일반 설정 탭
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # 다운로드 디렉토리 설정
        download_group = QGroupBox("Download Settings")
        download_layout = QGridLayout()
        download_group.setLayout(download_layout)
        
        download_layout.addWidget(QLabel("Download Directory:"), 0, 0)
        self.download_dir_input = QLineEdit()
        self.download_dir_input.setText(self.get_setting("download_dir", os.path.join(parent_dir, "papers")))
        download_layout.addWidget(self.download_dir_input, 0, 1)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_download_dir)
        download_layout.addWidget(browse_button, 0, 2)
        
        download_layout.addWidget(QLabel("Auto-download Papers:"), 1, 0)
        self.auto_download_checkbox = QCheckBox("Download papers automatically when searching")
        self.auto_download_checkbox.setChecked(self.get_setting("auto_download", False))
        download_layout.addWidget(self.auto_download_checkbox, 1, 1, 1, 2)
        
        general_layout.addWidget(download_group)
        
        # 검색 설정
        search_group = QGroupBox("Search Settings")
        search_layout = QGridLayout()
        search_group.setLayout(search_layout)
        
        search_layout.addWidget(QLabel("Default Max Results:"), 0, 0)
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(10, 1000)
        self.max_results_spin.setValue(self.get_setting("default_max_results", 50))
        self.max_results_spin.setSingleStep(10)
        search_layout.addWidget(self.max_results_spin, 0, 1)
        
        search_layout.addWidget(QLabel("Default Category:"), 1, 0)
        self.category_combo = QComboBox()
        self.category_combo.addItem("All CS/AI Categories", "all")
        self.category_combo.addItem("Artificial Intelligence (cs.AI)", "cs.AI")
        self.category_combo.addItem("Machine Learning (cs.LG)", "cs.LG")
        self.category_combo.addItem("Computer Vision (cs.CV)", "cs.CV")
        self.category_combo.addItem("Computation and Language (cs.CL)", "cs.CL")
        self.category_combo.addItem("Neural Computing (cs.NE)", "cs.NE")
        
        # 기본 카테고리 설정
        default_category = self.get_setting("default_category", "all")
        index = 0
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == default_category:
                index = i
                break
        self.category_combo.setCurrentIndex(index)
        
        search_layout.addWidget(self.category_combo, 1, 1)
        
        search_layout.addWidget(QLabel("Default Date Range:"), 2, 0)
        self.date_range_combo = QComboBox()
        self.date_range_combo.addItem("Last 7 days", 7)
        self.date_range_combo.addItem("Last 14 days", 14)
        self.date_range_combo.addItem("Last 30 days", 30)
        self.date_range_combo.addItem("Last 90 days", 90)
        self.date_range_combo.addItem("Last 365 days", 365)
        
        # 기본 날짜 범위 설정
        default_date_range = self.get_setting("default_date_range", 7)
        index = 0
        for i in range(self.date_range_combo.count()):
            if self.date_range_combo.itemData(i) == default_date_range:
                index = i
                break
        self.date_range_combo.setCurrentIndex(index)
        
        search_layout.addWidget(self.date_range_combo, 2, 1)
        
        general_layout.addWidget(search_group)
        
        # API 설정 탭
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)
        
        # LLM API 설정
        llm_group = QGroupBox("LLM API Settings")
        llm_layout = QGridLayout()
        llm_group.setLayout(llm_layout)
        
        llm_layout.addWidget(QLabel("LLM API URL:"), 0, 0)
        self.llm_api_url = QLineEdit()
        self.llm_api_url.setText(self.get_setting("llm_api_url", "http://localhost:8000/api/local-llm/chat"))
        llm_layout.addWidget(self.llm_api_url, 0, 1)
        
        llm_layout.addWidget(QLabel("Use LLM for Summaries:"), 1, 0)
        self.use_llm_checkbox = QCheckBox("Generate LLM-based summaries when processing papers")
        self.use_llm_checkbox.setChecked(self.get_setting("use_llm", True))
        llm_layout.addWidget(self.use_llm_checkbox, 1, 1)
        
        llm_layout.addWidget(QLabel("API Timeout (seconds):"), 2, 0)
        self.api_timeout_spin = QSpinBox()
        self.api_timeout_spin.setRange(5, 300)
        self.api_timeout_spin.setValue(self.get_setting("api_timeout", 30))
        self.api_timeout_spin.setSingleStep(5)
        llm_layout.addWidget(self.api_timeout_spin, 2, 1)
        
        test_api_button = QPushButton("Test Connection")
        test_api_button.clicked.connect(self.test_llm_connection)
        llm_layout.addWidget(test_api_button, 3, 0, 1, 2)
        
        api_layout.addWidget(llm_group)
        
        # Vector DB 설정
        vectordb_group = QGroupBox("Vector Database Settings")
        vectordb_layout = QGridLayout()
        vectordb_group.setLayout(vectordb_layout)
        
        vectordb_layout.addWidget(QLabel("Vector DB Path:"), 0, 0)
        self.vectordb_path = QLineEdit()
        self.vectordb_path.setText(self.get_setting("vectordb_path", os.path.join(parent_dir, "vector_db_data")))
        vectordb_layout.addWidget(self.vectordb_path, 0, 1)
        
        browse_db_button = QPushButton("Browse...")
        browse_db_button.clicked.connect(self.browse_vectordb_path)
        vectordb_layout.addWidget(browse_db_button, 0, 2)
        
        vectordb_layout.addWidget(QLabel("Collection Name:"), 1, 0)
        self.collection_name = QLineEdit()
        self.collection_name.setText(self.get_setting("collection_name", "arxiv_papers"))
        vectordb_layout.addWidget(self.collection_name, 1, 1, 1, 2)
        
        api_layout.addWidget(vectordb_group)
        
        # 인터페이스 설정 탭
        ui_tab = QWidget()
        ui_layout = QVBoxLayout(ui_tab)
        
        # 테마 설정
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QVBoxLayout()
        theme_group.setLayout(theme_layout)
        
        theme_button_group = QButtonGroup(self)
        
        self.light_theme_radio = QRadioButton("Light Theme")
        theme_button_group.addButton(self.light_theme_radio)
        theme_layout.addWidget(self.light_theme_radio)
        
        self.dark_theme_radio = QRadioButton("Dark Theme")
        theme_button_group.addButton(self.dark_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        
        self.system_theme_radio = QRadioButton("Use System Theme")
        theme_button_group.addButton(self.system_theme_radio)
        theme_layout.addWidget(self.system_theme_radio)
        
        # 기본 테마 설정
        theme = self.get_setting("theme", "system")
        if theme == "light":
            self.light_theme_radio.setChecked(True)
        elif theme == "dark":
            self.dark_theme_radio.setChecked(True)
        else:
            self.system_theme_radio.setChecked(True)
        
        ui_layout.addWidget(theme_group)
        
        # 글꼴 크기 설정
        font_group = QGroupBox("Font Settings")
        font_layout = QGridLayout()
        font_group.setLayout(font_layout)
        
        font_layout.addWidget(QLabel("UI Font Size:"), 0, 0)
        self.ui_font_size = QSpinBox()
        self.ui_font_size.setRange(8, 18)
        self.ui_font_size.setValue(self.get_setting("ui_font_size", 9))
        self.ui_font_size.setSingleStep(1)
        font_layout.addWidget(self.ui_font_size, 0, 1)
        
        font_layout.addWidget(QLabel("Content Font Size:"), 1, 0)
        self.content_font_size = QSpinBox()
        self.content_font_size.setRange(8, 18)
        self.content_font_size.setValue(self.get_setting("content_font_size", 10))
        self.content_font_size.setSingleStep(1)
        font_layout.addWidget(self.content_font_size, 1, 1)
        
        ui_layout.addWidget(font_group)
        
        # 탭 추가
        settings_tabs.addTab(general_tab, "General")
        settings_tabs.addTab(api_tab, "API Settings")
        settings_tabs.addTab(ui_tab, "Interface")
        
        main_layout.addWidget(settings_tabs)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_changes)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # 상태 메시지
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # 여백
        main_layout.addStretch()
    
    def get_setting(self, key, default_value):
        """설정 값 가져오기"""
        return self.settings.value(key, default_value)
    
    def browse_download_dir(self):
        """다운로드 디렉토리 선택"""
        current_dir = self.download_dir_input.text()
        if not os.path.exists(current_dir):
            current_dir = parent_dir
            
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Download Directory",
            current_dir,
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.download_dir_input.setText(directory)
    
    def browse_vectordb_path(self):
        """Vector DB 경로 선택"""
        current_dir = self.vectordb_path.text()
        if not os.path.exists(current_dir):
            current_dir = parent_dir
            
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Vector DB Directory",
            current_dir,
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.vectordb_path.setText(directory)
    
    def test_llm_connection(self):
        """LLM API 연결 테스트"""
        import requests
        
        url = self.llm_api_url.text().strip()
        if not url:
            self.status_label.setText("Error: API URL is empty")
            return
            
        try:
            # 간단한 요청 보내기
            payload = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello"}
                ]
            }
            
            timeout = self.api_timeout_spin.value()
            response = requests.post(url, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                self.status_label.setText("LLM API connection successful!")
            else:
                self.status_label.setText(f"Error: API returned status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.status_label.setText("Error: Could not connect to API server")
        except requests.exceptions.Timeout:
            self.status_label.setText(f"Error: API request timed out (>{timeout}s)")
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def save_settings(self):
        """설정 저장"""
        try:
            # 다운로드 설정
            download_dir = self.download_dir_input.text()
            if not os.path.exists(download_dir):
                os.makedirs(download_dir, exist_ok=True)
                
            self.settings.setValue("download_dir", download_dir)
            self.settings.setValue("auto_download", self.auto_download_checkbox.isChecked())
            
            # 검색 설정
            self.settings.setValue("default_max_results", self.max_results_spin.value())
            self.settings.setValue("default_category", self.category_combo.currentData())
            self.settings.setValue("default_date_range", self.date_range_combo.currentData())
            
            # API 설정
            self.settings.setValue("llm_api_url", self.llm_api_url.text())
            self.settings.setValue("use_llm", self.use_llm_checkbox.isChecked())
            self.settings.setValue("api_timeout", self.api_timeout_spin.value())
            
            # Vector DB 설정
            self.settings.setValue("vectordb_path", self.vectordb_path.text())
            self.settings.setValue("collection_name", self.collection_name.text())
            
            # 테마 설정
            if self.light_theme_radio.isChecked():
                self.settings.setValue("theme", "light")
            elif self.dark_theme_radio.isChecked():
                self.settings.setValue("theme", "dark")
            else:
                self.settings.setValue("theme", "system")
            
            # 글꼴 설정
            self.settings.setValue("ui_font_size", self.ui_font_size.value())
            self.settings.setValue("content_font_size", self.content_font_size.value())
            
            self.settings.sync()
            
            self.status_label.setText("Settings saved successfully!")
            
            # 변경사항 적용 알림
            QMessageBox.information(
                self,
                "Settings Saved",
                "Settings have been saved. Some changes may require restarting the application to take effect."
            )
            
            # 부모 윈도우에 설정 변경 알림
            if self.parent and hasattr(self.parent, "apply_settings"):
                self.parent.apply_settings()
                
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            self.status_label.setText(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while saving settings:\n{e}")
    
    def reset_to_defaults(self):
        """기본값으로 초기화"""
        # 확인 메시지
        reply = QMessageBox.question(
            self, 
            "Reset Settings", 
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        try:
            # 다운로드 설정
            self.download_dir_input.setText(os.path.join(parent_dir, "papers"))
            self.auto_download_checkbox.setChecked(False)
            
            # 검색 설정
            self.max_results_spin.setValue(50)
            self.category_combo.setCurrentIndex(0)  # All categories
            self.date_range_combo.setCurrentIndex(0)  # Last 7 days
            
            # API 설정
            self.llm_api_url.setText("http://localhost:8000/api/local-llm/chat")
            self.use_llm_checkbox.setChecked(True)
            self.api_timeout_spin.setValue(30)
            
            # Vector DB 설정
            self.vectordb_path.setText(os.path.join(parent_dir, "vector_db_data"))
            self.collection_name.setText("arxiv_papers")
            
            # 테마 설정
            self.system_theme_radio.setChecked(True)
            
            # 글꼴 설정
            self.ui_font_size.setValue(9)
            self.content_font_size.setValue(10)
            
            self.status_label.setText("All settings reset to defaults")
            
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            self.status_label.setText(f"Error resetting settings: {e}")
    
    def cancel_changes(self):
        """변경사항 취소"""
        # 확인 메시지
        if self.has_unsaved_changes():
            reply = QMessageBox.question(
                self, 
                "Cancel Changes", 
                "You have unsaved changes. Are you sure you want to discard them?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # 설정 다시 불러오기
        self.reload_settings()
        self.status_label.setText("Changes discarded")
    
    def has_unsaved_changes(self):
        """변경사항 확인"""
        # 기존 설정과 현재 UI 상태 비교
        if self.download_dir_input.text() != self.get_setting("download_dir", os.path.join(parent_dir, "papers")):
            return True
        if self.auto_download_checkbox.isChecked() != self.get_setting("auto_download", False):
            return True
        if self.max_results_spin.value() != self.get_setting("default_max_results", 50):
            return True
        if self.category_combo.currentData() != self.get_setting("default_category", "all"):
            return True
        if self.date_range_combo.currentData() != self.get_setting("default_date_range", 7):
            return True
        if self.llm_api_url.text() != self.get_setting("llm_api_url", "http://localhost:8000/api/local-llm/chat"):
            return True
        if self.use_llm_checkbox.isChecked() != self.get_setting("use_llm", True):
            return True
        if self.api_timeout_spin.value() != self.get_setting("api_timeout", 30):
            return True
        if self.vectordb_path.text() != self.get_setting("vectordb_path", os.path.join(parent_dir, "vector_db_data")):
            return True
        if self.collection_name.text() != self.get_setting("collection_name", "arxiv_papers"):
            return True
        
        # 테마 설정 확인
        current_theme = "system"
        if self.light_theme_radio.isChecked():
            current_theme = "light"
        elif self.dark_theme_radio.isChecked():
            current_theme = "dark"
            
        if current_theme != self.get_setting("theme", "system"):
            return True
            
        # 글꼴 설정 확인
        if self.ui_font_size.value() != self.get_setting("ui_font_size", 9):
            return True
        if self.content_font_size.value() != self.get_setting("content_font_size", 10):
            return True
            
        return False
    
    def reload_settings(self):
        """설정 다시 불러오기"""
        # 다운로드 설정
        self.download_dir_input.setText(self.get_setting("download_dir", os.path.join(parent_dir, "papers")))
        self.auto_download_checkbox.setChecked(self.get_setting("auto_download", False))
        
        # 검색 설정
        self.max_results_spin.setValue(self.get_setting("default_max_results", 50))
        
        # 카테고리 콤보박스
        default_category = self.get_setting("default_category", "all")
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == default_category:
                self.category_combo.setCurrentIndex(i)
                break
        
        # 날짜 범위 콤보박스
        default_date_range = self.get_setting("default_date_range", 7)
        for i in range(self.date_range_combo.count()):
            if self.date_range_combo.itemData(i) == default_date_range:
                self.date_range_combo.setCurrentIndex(i)
                break
        
        # API 설정
        self.llm_api_url.setText(self.get_setting("llm_api_url", "http://localhost:8000/api/local-llm/chat"))
        self.use_llm_checkbox.setChecked(self.get_setting("use_llm", True))
        self.api_timeout_spin.setValue(self.get_setting("api_timeout", 30))
        
        # Vector DB 설정
        self.vectordb_path.setText(self.get_setting("vectordb_path", os.path.join(parent_dir, "vector_db_data")))
        self.collection_name.setText(self.get_setting("collection_name", "arxiv_papers"))
        
        # 테마 설정
        theme = self.get_setting("theme", "system")
        if theme == "light":
            self.light_theme_radio.setChecked(True)
        elif theme == "dark":
            self.dark_theme_radio.setChecked(True)
        else:
            self.system_theme_radio.setChecked(True)
        
        # 글꼴 설정
        self.ui_font_size.setValue(self.get_setting("ui_font_size", 9))
        self.content_font_size.setValue(self.get_setting("content_font_size", 10))

# 테스트용
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    settings_panel = SettingsPanel()
    settings_panel.show()
    sys.exit(app.exec_())
