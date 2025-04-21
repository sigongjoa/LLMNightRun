"""
arXiv Module GUI - 라이브러리 패널 구현

저장된 논문을 관리하고 표시하는 패널
"""

import sys
import os
import logging
from datetime import datetime
import webbrowser
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QSplitter, QTextEdit, 
    QGroupBox, QGridLayout, QMessageBox, QFrame, QProgressBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QAbstractItemView, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QSize
from PyQt5.QtGui import QFont, QColor, QIcon

# 부모 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 필요한 모듈 import
from vector_db_handler import ArxivVectorDBHandler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LibraryLoadWorker(QThread):
    """라이브러리 로딩 워커 스레드"""
    load_complete = pyqtSignal(list)
    load_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(self, db_handler, query="", limit=100):
        """
        LibraryLoadWorker 초기화
        
        Args:
            db_handler: 벡터 DB 핸들러
            query (str): 검색 쿼리
            limit (int): 결과 제한 수
        """
        super().__init__()
        self.db_handler = db_handler
        self.query = query
        self.limit = limit
        
    def run(self):
        """로딩 작업 실행"""
        try:
            # 진행 상태 업데이트
            self.progress_update.emit("Loading library...")
            
            # DB 핸들러 확인
            if not self.db_handler:
                raise ValueError("Vector database handler is not initialized")
                
            # 검색어가 있는 경우 검색, 없는 경우 전체 목록 가져오기
            if self.query:
                self.progress_update.emit(f"Searching for '{self.query}'...")
                try:
                    papers = self.db_handler.search_papers(self.query, limit=self.limit)
                    logger.info(f"Found {len(papers)} papers matching '{self.query}'")
                except Exception as search_err:
                    logger.error(f"Search operation failed: {search_err}")
                    raise ValueError(f"Search operation failed: {search_err}")
            else:
                self.progress_update.emit("Getting all papers...")
                try:
                    papers = self.db_handler.list_papers(limit=self.limit)
                    logger.info(f"Listed {len(papers)} papers from database")
                except Exception as list_err:
                    logger.error(f"List operation failed: {list_err}")
                    raise ValueError(f"List operation failed: {list_err}")
            
            # 결과 확인
            if papers is None:
                papers = []
                logger.warning("Received None result from database, using empty list instead")
            
            # 완료
            self.progress_update.emit(f"Loaded {len(papers)} papers")
            self.load_complete.emit(papers)
            
        except Exception as e:
            logger.error(f"Error loading library: {e}")
            self.load_error.emit(str(e))

class LibraryPanel(QWidget):
    """arXiv 라이브러리 패널 클래스"""
    
    def __init__(self, parent=None):
        """
        LibraryPanel 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__()
        self.parent = parent
        self.library_papers = []  # 라이브러리 논문 목록
        self.selected_paper = None  # 선택된 논문
        
        try:
            # VectorDB 핸들러 초기화
            self.db_handler = ArxivVectorDBHandler()
        except Exception as e:
            logger.error(f"Error initializing VectorDB handler: {e}")
            self.db_handler = None
        
        self.init_ui()
        logger.info("LibraryPanel initialized")
        
    def init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        
        # 제목 레이블
        title_label = QLabel("My Library")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 검색 영역
        search_layout = QHBoxLayout()
        
        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter keywords to search in library")
        self.search_input.returnPressed.connect(self.search_library)
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_library)
        search_layout.addWidget(self.search_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_library)
        search_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(search_layout)
        
        # 스플리터 (논문 목록 | 상세 정보)
        splitter = QSplitter(Qt.Horizontal)
        
        # 왼쪽: 논문 목록
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 논문 수 표시
        self.papers_count_label = QLabel("No papers in library")
        left_layout.addWidget(self.papers_count_label)
        
        # 논문 목록
        self.papers_list = QListWidget()
        self.papers_list.setAlternatingRowColors(True)
        self.papers_list.currentItemChanged.connect(self.on_paper_selected)
        left_layout.addWidget(self.papers_list)
        
        # 오른쪽: 상세 정보 탭
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.detail_tabs = QTabWidget()
        
        # 정보 탭
        self.info_tab = QWidget()
        info_layout = QVBoxLayout(self.info_tab)
        
        # 논문 메타데이터
        meta_group = QGroupBox("Paper Information")
        meta_layout = QGridLayout()
        meta_group.setLayout(meta_layout)
        
        meta_layout.addWidget(QLabel("Title:"), 0, 0)
        self.paper_title = QLabel()
        self.paper_title.setWordWrap(True)
        self.paper_title.setFont(QFont("Arial", 10, QFont.Bold))
        meta_layout.addWidget(self.paper_title, 0, 1)
        
        meta_layout.addWidget(QLabel("Authors:"), 1, 0)
        self.paper_authors = QLabel()
        self.paper_authors.setWordWrap(True)
        meta_layout.addWidget(self.paper_authors, 1, 1)
        
        meta_layout.addWidget(QLabel("Published:"), 2, 0)
        self.paper_date = QLabel()
        meta_layout.addWidget(self.paper_date, 2, 1)
        
        meta_layout.addWidget(QLabel("Categories:"), 3, 0)
        self.paper_categories = QLabel()
        meta_layout.addWidget(self.paper_categories, 3, 1)
        
        meta_layout.addWidget(QLabel("arXiv ID:"), 4, 0)
        self.paper_id = QLabel()
        meta_layout.addWidget(self.paper_id, 4, 1)
        
        info_layout.addWidget(meta_group)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        
        self.view_button = QPushButton("View Details")
        self.view_button.clicked.connect(self.view_paper)
        button_layout.addWidget(self.view_button)
        
        self.open_pdf_button = QPushButton("Open PDF")
        self.open_pdf_button.clicked.connect(self.open_pdf)
        button_layout.addWidget(self.open_pdf_button)
        
        self.open_arxiv_button = QPushButton("Open arXiv Page")
        self.open_arxiv_button.clicked.connect(self.open_arxiv_page)
        button_layout.addWidget(self.open_arxiv_button)
        
        self.delete_button = QPushButton("Delete from Library")
        self.delete_button.clicked.connect(self.delete_paper)
        button_layout.addWidget(self.delete_button)
        
        info_layout.addLayout(button_layout)
        
        # 초록 표시
        abstract_group = QGroupBox("Abstract")
        abstract_layout = QVBoxLayout()
        abstract_group.setLayout(abstract_layout)
        
        self.abstract_text = QTextEdit()
        self.abstract_text.setReadOnly(True)
        abstract_layout.addWidget(self.abstract_text)
        
        info_layout.addWidget(abstract_group)
        
        # 키워드 탭
        self.keywords_tab = QWidget()
        keywords_layout = QVBoxLayout(self.keywords_tab)
        
        keywords_label = QLabel("Keywords extracted from this paper:")
        keywords_layout.addWidget(keywords_label)
        
        self.keywords_table = QTableWidget(0, 3)
        self.keywords_table.setHorizontalHeaderLabels(["Keyword", "Score", "Type"])
        self.keywords_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.keywords_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.keywords_table.setAlternatingRowColors(True)
        
        keywords_layout.addWidget(self.keywords_table)
        
        # 요약 탭
        self.summary_tab = QWidget()
        summary_layout = QVBoxLayout(self.summary_tab)
        
        summary_label = QLabel("Paper Summary:")
        summary_layout.addWidget(summary_label)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        # 탭 추가
        self.detail_tabs.addTab(self.info_tab, "Information")
        self.detail_tabs.addTab(self.keywords_tab, "Keywords")
        self.detail_tabs.addTab(self.summary_tab, "Summary")
        
        right_layout.addWidget(self.detail_tabs)
        
        # 스플리터에 위젯 추가
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])  # 초기 분할 비율
        
        main_layout.addWidget(splitter)
        
        # 상태 표시
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(self.status_label)
        
        # 초기 UI 상태 설정
        self.reset_detail_view()
        
        # VectorDB 사용 가능 시 라이브러리 로드
        if self.db_handler:
            self.load_library()
        else:
            self.papers_count_label.setText("Error: Vector database not available")
    
    def load_library(self):
        """라이브러리 로드"""
        if not self.db_handler:
            QMessageBox.warning(self, "Error", "Vector database not available")
            return
            
        # 검색어 초기화
        self.search_input.clear()
        
        # UI 업데이트
        self.refresh_button.setEnabled(False)
        self.search_button.setEnabled(False)
        self.status_label.setText("Loading library...")
        logger.info("Refreshing library contents...")
        
        try:
            # 로딩 워커 스레드 생성 및 시작
            self.load_worker = LibraryLoadWorker(self.db_handler)
            
            # 시그널 연결
            self.load_worker.load_complete.connect(self.on_load_complete)
            self.load_worker.load_error.connect(self.on_load_error)
            self.load_worker.progress_update.connect(self.update_status)
            
            # 로드 시작
            self.load_worker.start()
        except Exception as e:
            logger.error(f"Error loading library: {e}")
            self.refresh_button.setEnabled(True)
            self.search_button.setEnabled(True)
            self.status_label.setText(f"Error loading library: {str(e)}")
            QMessageBox.critical(self, "Library Error", f"Could not load library: {str(e)}")
    
    def search_library(self):
        """라이브러리 검색"""
        if not self.db_handler:
            QMessageBox.warning(self, "Error", "Vector database not available")
            return
            
        # 검색어 가져오기
        query = self.search_input.text().strip()
        if not query:
            # 검색어 없으면 전체 목록 로드
            self.load_library()
            return
            
        # UI 업데이트
        self.refresh_button.setEnabled(False)
        self.search_button.setEnabled(False)
        self.status_label.setText(f"Searching for '{query}'...")
        logger.info(f"Searching library for: {query}")
        
        try:
            # 검색 워커 스레드 생성 및 시작
            self.load_worker = LibraryLoadWorker(self.db_handler, query=query)
            
            # 시그널 연결
            self.load_worker.load_complete.connect(self.on_load_complete)
            self.load_worker.load_error.connect(self.on_load_error)
            self.load_worker.progress_update.connect(self.update_status)
            
            # 검색 시작
            self.load_worker.start()
        except Exception as e:
            logger.error(f"Error starting search: {e}")
            self.refresh_button.setEnabled(True)
            self.search_button.setEnabled(True)
            self.status_label.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Search Error", f"An error occurred: {str(e)}")
    
    def on_load_complete(self, papers):
        """로드 완료 이벤트 처리"""
        # UI 업데이트
        self.refresh_button.setEnabled(True)
        self.search_button.setEnabled(True)
        
        # 결과 저장
        self.library_papers = papers
        
        # 디버그 로깅
        logger.info(f"Received {len(papers)} papers from database")
        if len(papers) > 0:
            logger.info(f"First paper: {papers[0].get('title', 'No title')} (ID: {papers[0].get('id', 'No ID')})")
        
        # 논문 목록 업데이트
        self.update_papers_list()
        
        # 논문 수 표시
        num_papers = len(papers)
        if num_papers > 0:
            self.papers_count_label.setText(f"{num_papers} papers in library")
        else:
            self.papers_count_label.setText("No papers in library")
        
        # 상태 업데이트
        self.status_label.setText(f"Library loaded ({num_papers} papers)")
        
        # 로그 추가
        logger.info(f"Library loaded with {num_papers} papers")
    
    def on_load_error(self, error_message):
        """로드 오류 이벤트 처리"""
        # UI 업데이트
        self.refresh_button.setEnabled(True)
        self.search_button.setEnabled(True)
        self.status_label.setText(f"Error: {error_message}")
        
        # 오류 메시지 표시
        QMessageBox.critical(self, "Loading Error", f"An error occurred while loading the library:\n{error_message}")
    
    def update_status(self, message):
        """상태 메시지 업데이트"""
        self.status_label.setText(message)
        if self.parent:
            self.parent.update_status(message)
    
    def update_papers_list(self):
        """논문 목록 업데이트"""
        self.papers_list.clear()
        
        if not self.library_papers:
            logger.warning("No papers found in library_papers list")
            return
        
        logger.info(f"Updating papers list with {len(self.library_papers)} papers")
            
        for i, paper in enumerate(self.library_papers):
            try:
                item = QListWidgetItem()
                
                # 제목 및 저자 정보
                title = paper.get('title', 'Untitled')
                authors = paper.get('authors', [])
                
                # 저자가 문자열인 경우 리스트로 변환
                if isinstance(authors, str):
                    authors = [authors]
                
                if authors:
                    author_text = ", ".join(authors[:3])
                    if len(authors) > 3:
                        author_text += f" et al."
                else:
                    author_text = "Unknown author"
                    
                # 날짜 정보
                date_str = ""
                if 'published' in paper:
                    try:
                        pub_date = paper['published']
                        if isinstance(pub_date, str):
                            if 'T' in pub_date:
                                date_str = pub_date.split('T')[0]  # ISO 형식 날짜 추출
                            else:
                                date_str = pub_date
                        else:
                            date_str = pub_date.strftime("%Y-%m-%d") if hasattr(pub_date, 'strftime') else str(pub_date)
                    except Exception as e:
                        logger.warning(f"Failed to parse date for paper {i}: {e}")
                        date_str = "Unknown date"
                
                # 아이템 텍스트 설정
                display_text = f"{title}\n{author_text}"
                if date_str:
                    display_text += f" ({date_str})"
                    
                item.setText(display_text)
                item.setData(Qt.UserRole, paper)  # 논문 데이터 저장
                
                self.papers_list.addItem(item)
                
            except Exception as e:
                logger.error(f"Error adding paper {i} to list: {e}")
    
    def on_paper_selected(self, current, previous):
        """논문 선택 이벤트 처리"""
        if not current:
            self.reset_detail_view()
            return
            
        # 선택된 논문 데이터 가져오기
        paper = current.data(Qt.UserRole)
        self.selected_paper = paper
        
        # 메타데이터 표시
        self.display_paper_metadata(paper)
        
        # 초록 표시
        summary = paper.get('summary', '')
        self.abstract_text.setText(summary)
        
        # 키워드 표시
        keywords = paper.get('keywords', [])
        self.display_keywords(keywords)
        
        # 요약 표시
        extractive_summary = paper.get('extractive_summary', '')
        llm_summary = paper.get('llm_summary', '')
        
        if llm_summary:
            self.summary_text.setText(llm_summary)
        elif extractive_summary:
            self.summary_text.setText(extractive_summary)
        else:
            self.summary_text.setText("No summary available.")
    
    def display_paper_metadata(self, paper):
        """논문 메타데이터 표시"""
        # 제목
        self.paper_title.setText(paper.get('title', 'Untitled'))
        
        # 저자
        authors = paper.get('authors', [])
        self.paper_authors.setText(", ".join(authors))
        
        # 날짜
        pub_date = paper.get('published', '')
        if isinstance(pub_date, str):
            try:
                # ISO 형식 날짜 처리 (Z나 타임존 정보가 있는 경우 처리)
                if 'Z' in pub_date:
                    pub_date = pub_date.replace('Z', '+00:00')
                date_obj = datetime.fromisoformat(pub_date)
                date_str = date_obj.strftime("%Y-%m-%d")
            except Exception as e:
                # 변환 실패시 원본 문자열 사용
                logger.warning(f"Failed to parse date string: {pub_date} - {e}")
                date_str = pub_date
        elif isinstance(pub_date, datetime):
            # datetime 객체인 경우 직접 포맷팅
            date_str = pub_date.strftime("%Y-%m-%d")
        else:
            # 기타 타입
            date_str = str(pub_date)
        
        self.paper_date.setText(date_str)
        
        # 카테고리
        categories = paper.get('categories', [])
        self.paper_categories.setText(", ".join(categories))
        
        # arXiv ID
        arxiv_id = paper.get('entry_id', '') or paper.get('id', '')
        self.paper_id.setText(arxiv_id)
    
    def display_keywords(self, keywords):
        """키워드 표시"""
        self.keywords_table.setRowCount(0)
        
        if not keywords:
            return
            
        self.keywords_table.setRowCount(len(keywords))
        
        for i, kw in enumerate(keywords):
            # 키워드가 문자열인 경우 (단순 태그)
            if isinstance(kw, str):
                self.keywords_table.setItem(i, 0, QTableWidgetItem(kw))
                self.keywords_table.setItem(i, 1, QTableWidgetItem("N/A"))
                self.keywords_table.setItem(i, 2, QTableWidgetItem("Tag"))
                continue
                
            # 키워드가 사전인 경우 (추출된 키워드)
            keyword = kw.get('keyword', '')
            score = kw.get('score', 0)
            
            self.keywords_table.setItem(i, 0, QTableWidgetItem(keyword))
            
            # 점수
            score_item = QTableWidgetItem(f"{score:.4f}" if isinstance(score, float) else str(score))
            self.keywords_table.setItem(i, 1, score_item)
            
            # 타입 (TF-IDF vs TextRank)
            tfidf_score = kw.get('tfidf_score', 0)
            textrank_score = kw.get('textrank_score', 0)
            
            if tfidf_score > textrank_score:
                kw_type = "TF-IDF"
            elif textrank_score > tfidf_score:
                kw_type = "TextRank"
            else:
                kw_type = "Unknown"
                
            self.keywords_table.setItem(i, 2, QTableWidgetItem(kw_type))
    
    def reset_detail_view(self):
        """상세 정보 초기화"""
        self.paper_title.setText("")
        self.paper_authors.setText("")
        self.paper_date.setText("")
        self.paper_categories.setText("")
        self.paper_id.setText("")
        
        self.abstract_text.setText("")
        self.keywords_table.setRowCount(0)
        self.summary_text.setText("")
        
        self.selected_paper = None
    
    def view_paper(self):
        """논문 상세 정보 보기"""
        if not self.selected_paper:
            return
            
        # 결과 탭으로 데이터 전달
        if self.parent:
            self.parent.on_search_complete([self.selected_paper])
    
    def open_pdf(self):
        """PDF 파일 열기"""
        if not self.selected_paper:
            return
            
        # PDF 파일 경로 확인
        file_path = self.selected_paper.get('file_path', '')
        if not file_path:
            paper_id = self.selected_paper.get('entry_id', '') or self.selected_paper.get('id', '')
            download_dir = os.path.join(parent_dir, "papers")
            
            # 파일 이름 추정
            if os.path.exists(download_dir):
                potential_files = [
                    os.path.join(download_dir, f) 
                    for f in os.listdir(download_dir) 
                    if f.startswith(paper_id)
                ]
                if potential_files:
                    file_path = potential_files[0]
        
        # PDF 파일 열기
        if file_path and os.path.exists(file_path):
            try:
                # 플랫폼에 맞는 방식으로 파일 열기
                if sys.platform == 'win32':
                    os.startfile(file_path)
                elif sys.platform == 'darwin':
                    os.system(f'open "{file_path}"')
                else:
                    os.system(f'xdg-open "{file_path}"')
                    
                self.update_status(f"Opened PDF: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open PDF: {e}")
        else:
            QMessageBox.warning(self, "Warning", "PDF file not found")
    
    def open_arxiv_page(self):
        """arXiv 페이지 열기"""
        if not self.selected_paper:
            return
            
        # arXiv ID 확인
        paper_id = self.selected_paper.get('entry_id', '') or self.selected_paper.get('id', '')
        if not paper_id:
            QMessageBox.warning(self, "Warning", "arXiv ID not found")
            return
            
        # arXiv URL 구성
        if '/' in paper_id:
            # 이미 전체 ID인 경우
            arxiv_url = f"https://arxiv.org/abs/{paper_id}"
        else:
            # 숫자 ID만 있는 경우
            arxiv_url = f"https://arxiv.org/abs/{paper_id}"
            
        # URL 열기
        try:
            webbrowser.open(arxiv_url)
            self.update_status(f"Opened arXiv page: {arxiv_url}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open arXiv page: {e}")
    
    def delete_paper(self):
        """라이브러리에서 논문 삭제"""
        if not self.selected_paper or not self.db_handler:
            return
            
        # 삭제 확인
        reply = QMessageBox.question(
            self, 
            "Delete Paper", 
            "Are you sure you want to delete this paper from the library?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
            
        try:
            # 논문 ID 확인
            doc_id = self.selected_paper.get('id', '')
            if not doc_id:
                QMessageBox.warning(self, "Warning", "Document ID not found")
                return
                
            # 삭제 실행
            result = self.db_handler.delete_paper(doc_id)
            
            if result:
                # 목록에서 제거
                for i, paper in enumerate(self.library_papers):
                    if paper.get('id') == doc_id:
                        del self.library_papers[i]
                        break
                        
                # 목록 업데이트
                self.update_papers_list()
                
                # 상세 정보 초기화
                self.reset_detail_view()
                
                # 논문 수 업데이트
                num_papers = len(self.library_papers)
                if num_papers > 0:
                    self.papers_count_label.setText(f"{num_papers} papers in library")
                else:
                    self.papers_count_label.setText("No papers in library")
                
                # 상태 업데이트
                self.update_status("Paper deleted from library")
                
                QMessageBox.information(self, "Success", "Paper successfully deleted from library")
            else:
                QMessageBox.warning(self, "Warning", "Failed to delete paper from library")
                
        except Exception as e:
            logger.error(f"Error deleting paper: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred while deleting the paper:\n{e}")

# 테스트용
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    library_panel = LibraryPanel()
    library_panel.show()
    sys.exit(app.exec_())
