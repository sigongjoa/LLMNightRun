"""
arXiv Module GUI - 검색 패널 구현
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QCheckBox, QGroupBox, QGridLayout, 
    QSpinBox, QDateEdit, QProgressBar, QMessageBox, QFrame,
    QListWidget, QListWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor

# 부모 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# arXiv 모듈 import
from crawler import ArxivCrawler, CS_CATEGORIES

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SearchWorker(QThread):
    """arXiv 검색 작업 스레드"""
    search_complete = pyqtSignal(list)
    search_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(self, 
                query, 
                categories, 
                date_from, 
                date_to, 
                max_results,
                download_papers=False):
        """
        SearchWorker 초기화
        
        Args:
            query (str): 검색 쿼리
            categories (List[str]): 카테고리 목록
            date_from (datetime): 시작 날짜
            date_to (datetime): 종료 날짜
            max_results (int): 최대 결과 수
            download_papers (bool): 논문 다운로드 여부
        """
        super().__init__()
        self.query = query
        self.categories = categories
        self.date_from = date_from
        self.date_to = date_to
        self.max_results = max_results
        self.download_papers = download_papers
        
    def run(self):
        """검색 작업 실행"""
        try:
            # 검색 진행 상태 업데이트
            self.progress_update.emit("Initializing arXiv crawler...")
            
            # 다운로드 디렉토리 설정
            download_dir = os.path.join(parent_dir, "papers")
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
                
            # arXiv 크롤러 초기화
            crawler = ArxivCrawler(download_dir=download_dir)
            
            # 검색 진행 상태 업데이트
            self.progress_update.emit(f"Searching arXiv for '{self.query}'...")
            
            # 검색 실행
            papers = crawler.search(
                query=self.query,
                categories=self.categories,
                date_from=self.date_from,
                date_to=self.date_to,
                max_results=self.max_results
            )
            
            # 논문 다운로드 (옵션)
            if self.download_papers and papers:
                self.progress_update.emit(f"Downloading {len(papers)} papers...")
                
                # 각 논문 다운로드
                for i, paper in enumerate(papers):
                    paper_id = paper['entry_id']
                    self.progress_update.emit(f"Downloading paper {i+1}/{len(papers)}: {paper['title']}")
                    
                    # 다운로드 실행
                    file_path = crawler.download_paper(paper_id)
                    
                    # 다운로드 결과 저장
                    if file_path:
                        paper['file_path'] = file_path
                    
            # 검색 결과 반환
            self.search_complete.emit(papers)
            
        except Exception as e:
            logger.error(f"Error in search worker: {e}")
            self.search_error.emit(str(e))

class DownloadWorker(QThread):
    """arXiv 논문 다운로드 작업 스레드"""
    download_complete = pyqtSignal(dict)
    download_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(self, paper_data):
        """
        DownloadWorker 초기화
        
        Args:
            paper_data (dict): 다운로드할 논문 데이터
        """
        super().__init__()
        self.paper_data = paper_data
        
    def run(self):
        """다운로드 작업 실행"""
        try:
            # 필요한 정보 추출
            paper_id = self.paper_data.get('entry_id', '')
            title = self.paper_data.get('title', '')
            
            if not paper_id:
                self.download_error.emit("Invalid paper ID")
                return
                
            # 다운로드 디렉토리 설정
            download_dir = os.path.join(parent_dir, "papers")
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
                
            # 진행 상태 업데이트
            self.progress_update.emit(f"Downloading paper: {title}")
            
            # arXiv 크롤러 초기화
            crawler = ArxivCrawler(download_dir=download_dir)
            
            # 논문 다운로드
            file_path = crawler.download_paper(paper_id)
            
            if file_path:
                # 다운로드 성공
                self.paper_data['file_path'] = file_path
                self.progress_update.emit(f"Download complete: {title}")
                self.download_complete.emit(self.paper_data)
            else:
                # 다운로드 실패
                self.download_error.emit(f"Failed to download paper: {title}")
                
        except Exception as e:
            logger.error(f"Error in download worker: {e}")
            self.download_error.emit(str(e))

class SearchPanel(QWidget):
    """arXiv 검색 패널 클래스"""
    
    def __init__(self, parent=None):
        """
        SearchPanel 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__()
        self.parent = parent
        self.search_results = []
        self.selected_papers = []  # 선택된 논문 목록
        self.init_ui()
        logger.info("SearchPanel initialized")
        
    def init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        
        # 제목 레이블
        title_label = QLabel("Search arXiv CS/AI Papers")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # 검색 옵션 그룹박스
        search_options_group = QGroupBox("Search Options")
        search_options_layout = QGridLayout()
        search_options_group.setLayout(search_options_layout)
        
        # 검색어 입력
        search_options_layout.addWidget(QLabel("Search Query:"), 0, 0)
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter keywords (e.g., 'transformer learning')")
        search_options_layout.addWidget(self.query_input, 0, 1, 1, 3)
        
        # 카테고리 선택
        search_options_layout.addWidget(QLabel("Categories:"), 1, 0)
        self.category_combo = QComboBox()
        self.category_combo.addItem("All CS/AI Categories", CS_CATEGORIES)
        self.category_combo.addItem("Artificial Intelligence (cs.AI)", ["cs.AI"])
        self.category_combo.addItem("Machine Learning (cs.LG)", ["cs.LG"])
        self.category_combo.addItem("Computer Vision (cs.CV)", ["cs.CV"])
        self.category_combo.addItem("Computation and Language (cs.CL)", ["cs.CL"])
        self.category_combo.addItem("Neural and Evolutionary Computing (cs.NE)", ["cs.NE"])
        self.category_combo.addItem("Information Retrieval (cs.IR)", ["cs.IR"])
        self.category_combo.addItem("Human-Computer Interaction (cs.HC)", ["cs.HC"])
        search_options_layout.addWidget(self.category_combo, 1, 1)
        
        # 최대 결과 수
        search_options_layout.addWidget(QLabel("Max Results:"), 1, 2)
        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(10, 1000)
        self.max_results_spin.setValue(50)
        self.max_results_spin.setSingleStep(10)
        search_options_layout.addWidget(self.max_results_spin, 1, 3)
        
        # 날짜 범위
        search_options_layout.addWidget(QLabel("Date From:"), 2, 0)
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        # 기본값: 7일 전
        default_from = QDate.currentDate().addDays(-7)
        self.date_from.setDate(default_from)
        search_options_layout.addWidget(self.date_from, 2, 1)
        
        search_options_layout.addWidget(QLabel("Date To:"), 2, 2)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        search_options_layout.addWidget(self.date_to, 2, 3)
        
        # 다운로드 옵션
        search_options_layout.addWidget(QLabel("Download Options:"), 3, 0)
        self.download_checkbox = QCheckBox("Auto-download all papers (PDF)")
        self.download_checkbox.setChecked(False)  # 기본값을 False로 변경
        search_options_layout.addWidget(self.download_checkbox, 3, 1, 1, 3)
        
        main_layout.addWidget(search_options_group)
        
        # 검색 버튼
        button_layout = QHBoxLayout()
        self.search_button = QPushButton("Search Papers")
        self.search_button.setMinimumHeight(40)
        self.search_button.setFont(QFont("Arial", 12))
        self.search_button.clicked.connect(self.start_search)
        button_layout.addWidget(self.search_button)
        
        # 초기화 버튼
        self.reset_button = QPushButton("Reset")
        self.reset_button.setMinimumHeight(40)
        self.reset_button.clicked.connect(self.reset_form)
        button_layout.addWidget(self.reset_button)
        
        main_layout.addLayout(button_layout)
        
        # 검색 결과 그룹박스 (새로 추가)
        self.results_group = QGroupBox("Search Results")
        self.results_group.setVisible(False)  # 처음에는 숨김
        results_layout = QVBoxLayout()
        self.results_group.setLayout(results_layout)
        
        # 결과 개수 레이블
        self.results_count_label = QLabel("No results yet")
        results_layout.addWidget(self.results_count_label)
        
        # 검색 결과 목록
        self.results_list = QListWidget()
        self.results_list.setAlternatingRowColors(True)
        self.results_list.setSelectionMode(QAbstractItemView.MultiSelection)  # 다중 선택 가능
        self.results_list.setMinimumHeight(200)
        results_layout.addWidget(self.results_list)
        
        # 선택 및 다운로드 버튼
        action_buttons_layout = QHBoxLayout()
        
        self.download_selected_button = QPushButton("Download Selected")
        self.download_selected_button.clicked.connect(self.download_selected_papers)
        self.download_selected_button.setEnabled(False)
        action_buttons_layout.addWidget(self.download_selected_button)
        
        self.view_selected_button = QPushButton("View/Analyze Selected")
        self.view_selected_button.clicked.connect(self.view_selected_papers)
        self.view_selected_button.setEnabled(False)
        action_buttons_layout.addWidget(self.view_selected_button)
        
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all_papers)
        action_buttons_layout.addWidget(self.select_all_button)
        
        results_layout.addLayout(action_buttons_layout)
        
        main_layout.addWidget(self.results_group)
        
        # 진행 상태 표시
        progress_group = QGroupBox("Search Progress")
        progress_layout = QVBoxLayout()
        progress_group.setLayout(progress_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        main_layout.addWidget(progress_group)
        
        # 여백 추가
        main_layout.addStretch()
        
        # 결과 선택 이벤트 연결
        self.results_list.itemSelectionChanged.connect(self.on_selection_changed)
    
    def start_search(self):
        """검색 시작"""
        # 검색어 확인
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter a search query")
            return
        
        # 날짜 범위 확인
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()
        if date_from > date_to:
            QMessageBox.warning(self, "Warning", "Invalid date range")
            return
        
        # 카테고리 및 옵션 가져오기
        selected_index = self.category_combo.currentIndex()
        categories = self.category_combo.itemData(selected_index)
        max_results = self.max_results_spin.value()
        download_papers = self.download_checkbox.isChecked()
        
        # UI 업데이트
        self.search_button.setEnabled(False)
        self.progress_bar.setRange(0, 0)  # 불확정 진행 상태
        self.status_label.setText(f"Searching for '{query}'...")
        
        if self.parent:
            self.parent.update_status(f"Searching arXiv for '{query}'...")
        
        # 검색 워커 스레드 생성 및 시작
        self.search_worker = SearchWorker(
            query=query,
            categories=categories,
            date_from=datetime.combine(date_from, datetime.min.time()),
            date_to=datetime.combine(date_to, datetime.min.time()),
            max_results=max_results,
            download_papers=download_papers
        )
        
        # 시그널 연결
        self.search_worker.search_complete.connect(self.on_search_complete)
        self.search_worker.search_error.connect(self.on_search_error)
        self.search_worker.progress_update.connect(self.update_progress)
        
        # 검색 시작
        self.search_worker.start()
    
    def on_search_complete(self, results):
        """검색 완료 이벤트 처리"""
        # UI 업데이트
        self.search_button.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        # 결과 저장
        self.search_results = results
        
        # 결과 목록 업데이트
        self.update_results_list()
        
        # 결과 그룹 표시
        self.results_group.setVisible(True)
        
        # 선택 버튼 업데이트
        self.select_all_button.setEnabled(len(results) > 0)
        
        num_results = len(results) if results else 0
        self.status_label.setText(f"Search complete: {num_results} papers found")
        
        if self.parent:
            self.parent.update_status(f"Search complete: {num_results} papers found")
    
    def update_results_list(self):
        """결과 목록 업데이트"""
        self.results_list.clear()
        self.selected_papers = []  # 선택 초기화
        
        if not self.search_results:
            self.results_count_label.setText("No results found")
            return
            
        self.results_count_label.setText(f"Found {len(self.search_results)} papers")
        
        for paper in self.search_results:
            item = QListWidgetItem()
            
            # 제목 및 저자 정보
            title = paper.get('title', 'Untitled')
            authors = paper.get('authors', [])
            author_text = ", ".join(authors[:3])
            if len(authors) > 3:
                author_text += f" et al."
                
            # 날짜 정보
            date_str = ""
            if 'published' in paper:
                try:
                    pub_date = paper['published']
                    if isinstance(pub_date, str):
                        date_str = pub_date.split('T')[0]  # ISO 형식 날짜 추출
                    else:
                        date_str = pub_date.strftime("%Y-%m-%d")
                except:
                    pass
            
            # 아이템 텍스트 설정
            item.setText(f"{title}\n{author_text} ({date_str})")
            item.setData(Qt.UserRole, paper)  # 논문 데이터 저장
            
            # 다운로드 여부에 따른 시각적 표시
            if 'file_path' in paper and os.path.exists(paper['file_path']):
                item.setBackground(QColor(230, 255, 230))  # 연한 녹색 (다운로드 완료)
                
            self.results_list.addItem(item)
    
    def on_selection_changed(self):
        """논문 선택 변경 이벤트 처리"""
        selected_items = self.results_list.selectedItems()
        self.selected_papers = [item.data(Qt.UserRole) for item in selected_items]
        
        # 버튼 활성화/비활성화
        has_selection = len(selected_items) > 0
        self.download_selected_button.setEnabled(has_selection)
        self.view_selected_button.setEnabled(has_selection)
        
        # 상태 표시 업데이트
        if has_selection:
            self.status_label.setText(f"Selected {len(selected_items)} papers")
            if self.parent:
                self.parent.update_status(f"Selected {len(selected_items)} papers")
    
    def select_all_papers(self):
        """모든 논문 선택"""
        self.results_list.selectAll()
    
    def download_selected_papers(self):
        """선택된 논문 다운로드"""
        if not self.selected_papers:
            return
            
        # 다운로드 디렉토리 확인
        download_dir = os.path.join(parent_dir, "papers")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
            
        # 다운로드 확인 메시지
        reply = QMessageBox.question(
            self, 
            "Download Papers", 
            f"Download {len(self.selected_papers)} selected papers?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.No:
            return
            
        # 다운로드 진행
        self.progress_bar.setRange(0, len(self.selected_papers))
        self.progress_bar.setValue(0)
        
        # 첫 번째 논문 다운로드 시작
        self.current_download_index = 0
        self.start_next_download()
    
    def start_next_download(self):
        """다음 논문 다운로드 시작"""
        if self.current_download_index >= len(self.selected_papers):
            # 모든 다운로드 완료
            self.status_label.setText(f"All {len(self.selected_papers)} papers downloaded")
            if self.parent:
                self.parent.update_status(f"All {len(self.selected_papers)} papers downloaded")
            return
            
        # 현재 논문 가져오기
        paper = self.selected_papers[self.current_download_index]
        
        # 이미 다운로드된 경우 건너뛰기
        if 'file_path' in paper and os.path.exists(paper['file_path']):
            self.progress_bar.setValue(self.current_download_index + 1)
            self.current_download_index += 1
            self.start_next_download()
            return
            
        # 다운로드 워커 생성 및 시작
        self.download_worker = DownloadWorker(paper)
        
        # 시그널 연결
        self.download_worker.download_complete.connect(self.on_download_complete)
        self.download_worker.download_error.connect(self.on_download_error)
        self.download_worker.progress_update.connect(self.update_progress)
        
        # 다운로드 시작
        self.download_worker.start()
    
    def on_download_complete(self, paper_data):
        """다운로드 완료 이벤트 처리"""
        # 결과 목록 업데이트
        for i in range(self.results_list.count()):
            item = self.results_list.item(i)
            item_data = item.data(Qt.UserRole)
            if item_data.get('entry_id') == paper_data.get('entry_id'):
                item.setData(Qt.UserRole, paper_data)  # 업데이트된 데이터 저장
                item.setBackground(QColor(230, 255, 230))  # 연한 녹색 (다운로드 완료)
                break
        
        # 검색 결과 업데이트
        for i, paper in enumerate(self.search_results):
            if paper.get('entry_id') == paper_data.get('entry_id'):
                self.search_results[i] = paper_data
                break
                
        # 선택된 논문 업데이트
        for i, paper in enumerate(self.selected_papers):
            if paper.get('entry_id') == paper_data.get('entry_id'):
                self.selected_papers[i] = paper_data
                break
        
        # 진행 상태 업데이트
        self.progress_bar.setValue(self.current_download_index + 1)
        
        # 다음 다운로드 진행
        self.current_download_index += 1
        self.start_next_download()
    
    def on_download_error(self, error_message):
        """다운로드 오류 이벤트 처리"""
        # 오류 메시지 표시
        QMessageBox.warning(
            self, 
            "Download Error", 
            f"Error downloading paper: {error_message}\n\nContinuing with next paper..."
        )
        
        # 진행 상태 업데이트
        self.progress_bar.setValue(self.current_download_index + 1)
        
        # 다음 다운로드 진행
        self.current_download_index += 1
        self.start_next_download()
    
    def view_selected_papers(self):
        """선택된 논문 보기"""
        if not self.selected_papers:
            return
            
        # 부모 윈도우에 결과 전달
        if self.parent:
            self.parent.on_search_complete(self.selected_papers)
    
    def on_search_error(self, error_message):
        """검색 오류 이벤트 처리"""
        # UI 업데이트
        self.search_button.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText(f"Error: {error_message}")
        
        # 오류 메시지 표시
        QMessageBox.critical(self, "Search Error", f"An error occurred during search:\n{error_message}")
        
        if self.parent:
            self.parent.update_status(f"Search error: {error_message}")
    
    def update_progress(self, message):
        """진행 상태 업데이트"""
        self.status_label.setText(message)
        if self.parent:
            self.parent.update_status(message)
    
    def reset_form(self):
        """폼 초기화"""
        self.query_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.max_results_spin.setValue(50)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_to.setDate(QDate.currentDate())
        self.download_checkbox.setChecked(False)
        
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")
        
        # 결과 목록 숨기기
        self.results_group.setVisible(False)
        self.results_list.clear()
        self.search_results = []
        self.selected_papers = []
        
        if self.parent:
            self.parent.update_status("Form reset")

# 테스트용
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    search_panel = SearchPanel()
    search_panel.show()
    sys.exit(app.exec_())
