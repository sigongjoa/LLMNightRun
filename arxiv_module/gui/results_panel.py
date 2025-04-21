"""
arXiv Module GUI - 결과 패널 구현
"""

import sys
import os
import logging
from datetime import datetime
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QSplitter, QTextEdit, 
    QGroupBox, QGridLayout, QMessageBox, QFrame, QProgressBar,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

# 부모 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# 필요한 모듈 import
from processor import TextProcessor
from keyword_extractor import KeywordExtractor
from summarizer import Summarizer
from vector_db_handler import ArxivVectorDBHandler

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcessWorker(QThread):
    """논문 처리 워커 스레드"""
    process_complete = pyqtSignal(dict)
    process_error = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(self, paper_data, download_dir="papers"):
        """
        ProcessWorker 초기화
        
        Args:
            paper_data (dict): 처리할 논문 데이터
            download_dir (str): 다운로드 디렉토리
        """
        super().__init__()
        self.paper_data = paper_data
        self.download_dir = download_dir
        
    def run(self):
        """논문 처리 실행"""
        try:
            # 필요한 정보 추출
            paper_id = self.paper_data.get('entry_id', '')
            title = self.paper_data.get('title', '')
            
            # PDF 파일 경로 확인
            file_path = self.paper_data.get('file_path', '')
            if not file_path and 'entry_id' in self.paper_data:
                # 파일 이름 추정
                potential_files = [
                    os.path.join(self.download_dir, f) 
                    for f in os.listdir(self.download_dir) 
                    if f.startswith(paper_id)
                ]
                if potential_files:
                    file_path = potential_files[0]
            
            # 결과 초기화
            result = {
                'paper_data': self.paper_data,
                'success': False
            }
            
            # PDF 파일이 없는 경우
            if not file_path or not os.path.exists(file_path):
                self.progress_update.emit(f"PDF file not found for {title}")
                result['error'] = "PDF file not found"
                self.process_complete.emit(result)
                return
                
            # PDF 처리 진행
            self.progress_update.emit(f"Processing PDF: {title}")
            
            # 텍스트 추출 및 전처리
            self.progress_update.emit("Extracting and preprocessing text...")
            processor = TextProcessor()
            text_data = processor.process_pdf(file_path)
            
            if not text_data.get('success', False):
                self.progress_update.emit(f"Failed to extract text from PDF")
                result['error'] = "Text extraction failed"
                self.process_complete.emit(result)
                return
                
            # 키워드 추출
            self.progress_update.emit("Extracting keywords...")
            extractor = KeywordExtractor()
            keywords = extractor.extract_keywords(text_data, top_n=15)
            
            # 요약 생성
            self.progress_update.emit("Generating summary...")
            summarizer = Summarizer()
            summary_result = summarizer.generate_summary(
                text_data,
                keywords,
                title=title,
                use_llm=True
            )
            
            # 결과 저장
            result['text_data'] = text_data
            result['keywords'] = keywords
            result['summary'] = summary_result
            result['success'] = True
            
            # VectorDB 저장 (옵션)
            try:
                self.progress_update.emit("Saving to vector database...")
                db_handler = ArxivVectorDBHandler()
                
                # 저장할 데이터 준비
                db_data = {
                    **self.paper_data,
                    'keywords': keywords,
                    'extractive_summary': summary_result.get('extractive_summary', ''),
                    'llm_summary': summary_result.get('llm_summary', '')
                }
                
                # 이미 존재하는지 확인
                if db_handler.paper_exists(paper_id):
                    # 업데이트
                    self.progress_update.emit("Paper already exists in database, updating...")
                    
                    # 검색하여 문서 ID 찾기
                    existing_papers = db_handler.search_papers(paper_id)
                    
                    if existing_papers:
                        # 문서 ID 추출
                        doc_id = None
                        for p in existing_papers:
                            if p.get('entry_id') == paper_id or p.get('id') == paper_id:
                                doc_id = p.get('id')
                                break
                        
                        if doc_id:
                            # 업데이트 실행
                            success = db_handler.update_paper(doc_id, db_data)
                            if success:
                                self.progress_update.emit(f"Updated paper in database (ID: {doc_id})")
                                result['doc_id'] = doc_id
                                result['doc_updated'] = True
                            else:
                                self.progress_update.emit("Failed to update paper in database")
                                result['db_error'] = "Failed to update paper"
                        else:
                            self.progress_update.emit("Could not determine document ID for update")
                            result['db_error'] = "Could not determine document ID"
                    else:
                        self.progress_update.emit("Paper exists but could not be found in search")
                        result['db_error'] = "Paper exists but could not be found in search"
                else:
                    # 새 항목 추가
                    doc_id = db_handler.add_paper(db_data)
                    self.progress_update.emit(f"Added paper to database (ID: {doc_id})")
                    result['doc_id'] = doc_id
                    result['doc_added'] = True
                    
            except Exception as e:
                logger.error(f"Error saving to vector DB: {e}")
                result['db_error'] = str(e)
            
            # 완료
            self.progress_update.emit(f"Processing complete for {title}")
            self.process_complete.emit(result)
            
        except Exception as e:
            logger.error(f"Error in process worker: {e}")
            self.process_error.emit(str(e))

class ResultsPanel(QWidget):
    """arXiv 결과 패널 클래스"""
    
    def __init__(self, parent=None):
        """
        ResultsPanel 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__()
        self.parent = parent
        self.search_results = []
        self.current_paper = None
        self.processed_papers = {}  # 처리된 논문 캐시
        
        self.init_ui()
        logger.info("ResultsPanel initialized")
        
    def init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        main_layout = QVBoxLayout(self)
        
        # 제목 레이블
        title_label = QLabel("Search Results")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 결과 개수 표시
        self.results_count_label = QLabel("No results yet")
        self.results_count_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.results_count_label)
        
        # 스플리터 (결과 목록 | 상세 정보)
        splitter = QSplitter(Qt.Horizontal)
        
        # 왼쪽: 결과 목록
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        self.results_list = QListWidget()
        self.results_list.setAlternatingRowColors(True)
        self.results_list.currentItemChanged.connect(self.on_paper_selected)
        left_layout.addWidget(self.results_list)
        
        # 오른쪽: 상세 정보 탭
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        self.detail_tabs = QTabWidget()
        
        # 요약 탭
        self.summary_tab = QWidget()
        summary_layout = QVBoxLayout(self.summary_tab)
        
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
        
        summary_layout.addWidget(meta_group)
        
        # 요약 그룹
        summary_group = QGroupBox("Summary")
        summary_content_layout = QVBoxLayout()
        summary_group.setLayout(summary_content_layout)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_content_layout.addWidget(self.summary_text)
        
        summary_layout.addWidget(summary_group)
        
        # 키워드 탭
        self.keywords_tab = QWidget()
        keywords_layout = QVBoxLayout(self.keywords_tab)
        
        self.keywords_table = QTableWidget(0, 3)
        self.keywords_table.setHorizontalHeaderLabels(["Keyword", "Score", "Type"])
        self.keywords_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.keywords_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.keywords_table.setAlternatingRowColors(True)
        
        keywords_layout.addWidget(self.keywords_table)
        
        # 초록 탭
        self.abstract_tab = QWidget()
        abstract_layout = QVBoxLayout(self.abstract_tab)
        
        self.abstract_text = QTextEdit()
        self.abstract_text.setReadOnly(True)
        abstract_layout.addWidget(self.abstract_text)
        
        # 텍스트 탭
        self.text_tab = QWidget()
        text_layout = QVBoxLayout(self.text_tab)
        
        self.full_text = QTextEdit()
        self.full_text.setReadOnly(True)
        text_layout.addWidget(self.full_text)
        
        # 조치 탭
        self.actions_tab = QWidget()
        actions_layout = QVBoxLayout(self.actions_tab)
        
        actions_group = QGroupBox("Available Actions")
        actions_grid = QGridLayout()
        actions_group.setLayout(actions_grid)
        
        # PDF 열기 버튼
        self.open_pdf_button = QPushButton("Open PDF")
        self.open_pdf_button.clicked.connect(self.open_pdf)
        actions_grid.addWidget(self.open_pdf_button, 0, 0)
        
        # arXiv 페이지 열기 버튼
        self.open_arxiv_button = QPushButton("Open arXiv Page")
        self.open_arxiv_button.clicked.connect(self.open_arxiv_page)
        actions_grid.addWidget(self.open_arxiv_button, 0, 1)
        
        # 저장 버튼
        self.save_button = QPushButton("Save to My Library")
        self.save_button.clicked.connect(self.save_to_library)
        actions_grid.addWidget(self.save_button, 1, 0)
        
        # 처리 버튼
        self.process_button = QPushButton("Process/Analyze Again")
        self.process_button.clicked.connect(self.process_paper)
        actions_grid.addWidget(self.process_button, 1, 1)
        
        actions_layout.addWidget(actions_group)
        
        # 진행 상태 표시
        self.process_progress = QProgressBar()
        self.process_progress.setTextVisible(False)
        self.process_progress.setRange(0, 100)
        self.process_progress.setValue(0)
        actions_layout.addWidget(self.process_progress)
        
        self.process_status = QLabel("Select a paper to process")
        self.process_status.setAlignment(Qt.AlignCenter)
        actions_layout.addWidget(self.process_status)
        
        actions_layout.addStretch()
        
        # 탭 추가
        self.detail_tabs.addTab(self.summary_tab, "Summary")
        self.detail_tabs.addTab(self.keywords_tab, "Keywords")
        self.detail_tabs.addTab(self.abstract_tab, "Abstract")
        self.detail_tabs.addTab(self.text_tab, "Full Text")
        self.detail_tabs.addTab(self.actions_tab, "Actions")
        
        right_layout.addWidget(self.detail_tabs)
        
        # 스플리터에 위젯 추가
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([300, 700])  # 초기 분할 비율
        
        main_layout.addWidget(splitter)
        
        # 초기 UI 상태 설정
        self.reset_detail_view()
    
    def set_results(self, results):
        """검색 결과 설정"""
        self.search_results = results
        self.update_results_list()
    
    def update_results_list(self):
        """결과 목록 업데이트"""
        self.results_list.clear()
        
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
            
            # 이미 처리된 논문인지 확인
            if paper.get('entry_id') in self.processed_papers:
                item.setBackground(QColor(230, 255, 230))  # 연한 녹색
                
            self.results_list.addItem(item)
    
    def on_paper_selected(self, current, previous):
        """논문 선택 이벤트 처리"""
        if not current:
            self.reset_detail_view()
            return
            
        # 선택된 논문 데이터 가져오기
        paper = current.data(Qt.UserRole)
        self.current_paper = paper
        
        # 메타데이터 표시
        self.display_paper_metadata(paper)
        
        # 초록 표시
        summary = paper.get('summary', '')
        self.abstract_text.setText(summary)
        
        # 이미 처리된 논문인지 확인
        paper_id = paper.get('entry_id', '')
        if paper_id in self.processed_papers:
            # 저장된 처리 결과 표시
            self.display_processed_results(self.processed_papers[paper_id])
        else:
            # 결과 초기화
            self.summary_text.setText("Paper not yet processed. Go to Actions tab to process this paper.")
            self.keywords_table.setRowCount(0)
            self.full_text.setText("")
            
            # 진행 상태 초기화
            self.process_progress.setValue(0)
            self.process_status.setText("Ready to process")
    
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
                date_obj = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                date_str = date_obj.strftime("%Y-%m-%d")
            except:
                date_str = pub_date
        else:
            try:
                date_str = pub_date.strftime("%Y-%m-%d")
            except:
                date_str = str(pub_date)
        self.paper_date.setText(date_str)
        
        # 카테고리
        categories = paper.get('categories', [])
        self.paper_categories.setText(", ".join(categories))
        
        # arXiv ID
        arxiv_id = paper.get('entry_id', '')
        self.paper_id.setText(arxiv_id)
    
    def display_processed_results(self, result):
        """처리 결과 표시"""
        if not result.get('success', False):
            self.summary_text.setText(f"Processing error: {result.get('error', 'Unknown error')}")
            return
            
        # 요약 표시
        summary_result = result.get('summary', {})
        summary_text = ""
        
        if 'llm_summary' in summary_result:
            summary_text = summary_result['llm_summary']
        elif 'extractive_summary' in summary_result:
            summary_text = summary_result['extractive_summary']
        else:
            summary_text = "No summary available."
            
        self.summary_text.setText(summary_text)
        
        # 키워드 표시
        keywords = result.get('keywords', [])
        self.keywords_table.setRowCount(len(keywords))
        
        for i, kw in enumerate(keywords):
            # 키워드
            self.keywords_table.setItem(i, 0, QTableWidgetItem(kw['keyword']))
            
            # 점수
            score_item = QTableWidgetItem(f"{kw['score']:.4f}")
            self.keywords_table.setItem(i, 1, score_item)
            
            # 타입 (TF-IDF vs TextRank 비교)
            if kw['tfidf_score'] > kw['textrank_score']:
                kw_type = "TF-IDF"
            else:
                kw_type = "TextRank"
            self.keywords_table.setItem(i, 2, QTableWidgetItem(kw_type))
        
        # 전체 텍스트 표시
        text_data = result.get('text_data', {})
        if 'clean_text' in text_data:
            self.full_text.setText(text_data['clean_text'])
        else:
            self.full_text.setText("Full text not available")
        
        # 진행 상태 업데이트
        self.process_progress.setValue(100)
        self.process_status.setText("Processing complete")
    
    def reset_detail_view(self):
        """상세 정보 초기화"""
        self.paper_title.setText("")
        self.paper_authors.setText("")
        self.paper_date.setText("")
        self.paper_categories.setText("")
        self.paper_id.setText("")
        
        self.summary_text.setText("")
        self.keywords_table.setRowCount(0)
        self.abstract_text.setText("")
        self.full_text.setText("")
        
        self.process_progress.setValue(0)
        self.process_status.setText("No paper selected")
        
        self.current_paper = None
    
    def process_paper(self):
        """현재 선택된 논문 처리"""
        if not self.current_paper:
            QMessageBox.warning(self, "Warning", "No paper selected")
            return
            
        # 다운로드 디렉토리 확인
        download_dir = os.path.join(parent_dir, "papers")
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        # 이미 처리된 논문인지 확인
        paper_id = self.current_paper.get('entry_id', '')
        if paper_id in self.processed_papers:
            reply = QMessageBox.question(
                self, 
                "Already Processed", 
                "This paper has already been processed. Process again?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
        # PDF 파일 존재 확인
        has_pdf = False
        file_path = self.current_paper.get('file_path', '')
        
        # 파일 경로가 없는 경우 자동으로 추정
        if not file_path and 'entry_id' in self.current_paper:
            potential_files = [
                os.path.join(download_dir, f) 
                for f in os.listdir(download_dir) 
                if os.path.isfile(os.path.join(download_dir, f)) and f.startswith(paper_id)
            ]
            if potential_files:
                file_path = potential_files[0]
                self.current_paper['file_path'] = file_path
                has_pdf = True
        elif file_path and os.path.exists(file_path):
            has_pdf = True
            
        # PDF가 없는 경우 다운로드 여부 확인
        if not has_pdf:
            reply = QMessageBox.question(
                self, 
                "PDF Not Found", 
                "The PDF file for this paper was not found. Download it now?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # 다운로드 시작
                self.process_status.setText("Downloading PDF...")
                QApplication.processEvents()  # UI 업데이트
                
                from crawler import ArxivCrawler
                crawler = ArxivCrawler(download_dir=download_dir)
                
                try:
                    file_path = crawler.download_paper(paper_id)
                    if file_path:
                        self.current_paper['file_path'] = file_path
                        has_pdf = True
                    else:
                        QMessageBox.warning(self, "Download Failed", 
                                          "Could not download the PDF. Processing may not work correctly.")
                except Exception as e:
                    QMessageBox.warning(self, "Download Error", 
                                      f"Error downloading PDF: {str(e)}\nProcessing may not work correctly.")
        
        # UI 업데이트
        self.process_button.setEnabled(False)
        self.process_progress.setRange(0, 0)  # 불확정 진행 상태
        self.process_status.setText("Processing paper...")
        
        try:
            # 처리 워커 스레드 생성 및 시작
            self.process_worker = ProcessWorker(
                paper_data=self.current_paper,
                download_dir=download_dir
            )
            
            # 시그널 연결
            self.process_worker.process_complete.connect(self.on_process_complete)
            self.process_worker.process_error.connect(self.on_process_error)
            self.process_worker.progress_update.connect(self.update_process_progress)
            
            # 처리 시작
            self.process_worker.start()
            
            logger.info(f"Started processing paper: {self.current_paper.get('title')}")
        except Exception as e:
            logger.error(f"Error starting paper processing: {e}")
            self.process_button.setEnabled(True)
            self.process_progress.setRange(0, 100)
            self.process_progress.setValue(0)
            self.process_status.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Processing Error", f"Could not start processing: {str(e)}")

    
    def on_process_complete(self, result):
        """처리 완료 이벤트 처리"""
        # UI 업데이트
        self.process_button.setEnabled(True)
        self.process_progress.setRange(0, 100)
        self.process_progress.setValue(100)
        
        paper_data = result.get('paper_data', {})
        paper_id = paper_data.get('entry_id', '')
        
        if result.get('success', False):
            # 결과 캐시에 저장
            self.processed_papers[paper_id] = result
            
            # 결과 표시
            self.display_processed_results(result)
            
            # 결과 목록 업데이트 (처리 완료 상태 표시)
            for i in range(self.results_list.count()):
                item = self.results_list.item(i)
                item_data = item.data(Qt.UserRole)
                if item_data.get('entry_id') == paper_id:
                    item.setBackground(QColor(230, 255, 230))  # 연한 녹색
                    break
            
            # 상태 업데이트
            self.process_status.setText("Processing complete")
            
            if self.parent:
                self.parent.update_status(f"Paper processed: {paper_data.get('title', '')}")
                
            # 자동 저장 여부 묻기
            reply = QMessageBox.question(
                self,
                "Save to Library",
                "Processing complete. Would you like to save this paper to your library?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.save_to_library()
                
        else:
            # 오류 메시지 표시
            error_msg = result.get('error', 'Unknown error')
            self.process_status.setText(f"Error: {error_msg}")
            
            if self.parent:
                self.parent.update_status(f"Paper processing error: {error_msg}")
    
    def on_process_error(self, error_message):
        """처리 오류 이벤트 처리"""
        # UI 업데이트
        self.process_button.setEnabled(True)
        self.process_progress.setRange(0, 100)
        self.process_progress.setValue(0)
        self.process_status.setText(f"Error: {error_message}")
        
        # 오류 메시지 표시
        QMessageBox.critical(self, "Processing Error", f"An error occurred during processing:\n{error_message}")
        
        if self.parent:
            self.parent.update_status(f"Processing error: {error_message}")
    
    def update_process_progress(self, message):
        """처리 진행 상태 업데이트"""
        self.process_status.setText(message)
        if self.parent:
            self.parent.update_status(message)
    
    def open_pdf(self):
        """PDF 파일 열기"""
        if not self.current_paper:
            return
            
        # PDF 파일 경로 확인
        file_path = self.current_paper.get('file_path', '')
        if not file_path:
            paper_id = self.current_paper.get('entry_id', '')
            download_dir = os.path.join(parent_dir, "papers")
            
            # 파일 이름 추정
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
                    
                if self.parent:
                    self.parent.update_status(f"Opened PDF: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open PDF: {e}")
        else:
            QMessageBox.warning(self, "Warning", "PDF file not found")
    
    def open_arxiv_page(self):
        """arXiv 페이지 열기"""
        if not self.current_paper:
            return
            
        # arXiv URL 구성
        paper_id = self.current_paper.get('entry_id', '')
        if paper_id:
            if '/' in paper_id:
                # 이미 전체 ID인 경우
                arxiv_url = f"https://arxiv.org/abs/{paper_id}"
            else:
                # 숫자 ID만 있는 경우
                arxiv_url = f"https://arxiv.org/abs/{paper_id}"
                
            # URL 열기
            try:
                webbrowser.open(arxiv_url)
                if self.parent:
                    self.parent.update_status(f"Opened arXiv page: {arxiv_url}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open arXiv page: {e}")
        else:
            QMessageBox.warning(self, "Warning", "arXiv ID not found")
    
    def save_to_library(self):
        """라이브러리에 저장"""
        if not self.current_paper:
            return
            
        # 이미 처리된 논문인지 확인
        paper_id = self.current_paper.get('entry_id', '')
        if paper_id not in self.processed_papers:
            # 처리되지 않은 경우 처리를 먼저 수행할지 물어보기
            reply = QMessageBox.question(
                self, 
                "Process Paper", 
                "This paper needs to be processed before saving to library. Process now?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # 자동으로 처리 진행
                self.process_paper()
                
                # 처리가 완료될 때까지 대기 메시지
                QMessageBox.information(
                    self,
                    "Processing",
                    "The paper is being processed. Please wait until processing is complete,\n"
                    "then try saving to library again."
                )
                return
            else:
                return
            
        try:
            # Vector DB에 저장
            db_handler = ArxivVectorDBHandler()
            
            # 처리 결과 가져오기
            process_result = self.processed_papers[paper_id]
            
            # 저장할 데이터 준비
            paper_data = process_result.get('paper_data', {})
            keywords = process_result.get('keywords', [])
            summary_result = process_result.get('summary', {})
            
            db_data = {
                **paper_data,
                'keywords': keywords,
                'extractive_summary': summary_result.get('extractive_summary', ''),
                'llm_summary': summary_result.get('llm_summary', '')
            }
            
            # 이미 존재하는지 확인
            if db_handler.paper_exists(paper_id):
                # 업데이트 기능 구현
                # 기존 문서 ID 가져오기
                reply = QMessageBox.question(
                    self, 
                    "Update Paper", 
                    "This paper already exists in your library. Do you want to update it with the latest information?",
                    QMessageBox.Yes | QMessageBox.No, 
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.No:
                    return
                
                # 검색하여 문서 ID 찾기
                existing_papers = db_handler.search_papers(paper_id)
                if not existing_papers:
                    QMessageBox.warning(self, "Error", "Could not find existing paper in database")
                    return
                    
                # 문서 ID 추출
                doc_id = None
                for p in existing_papers:
                    if p.get('entry_id') == paper_id or p.get('id') == paper_id:
                        doc_id = p.get('id')
                        break
                
                if not doc_id:
                    QMessageBox.warning(self, "Error", "Could not determine document ID for update")
                    return
                    
                # 업데이트 실행
                success = db_handler.update_paper(doc_id, db_data)
                
                if success:
                    QMessageBox.information(
                        self,
                        "Success",
                        f"Paper successfully updated in library (ID: {doc_id})"
                    )
                    
                    if self.parent:
                        self.parent.update_status(f"Updated in library: {paper_data.get('title', '')}")
                else:
                    QMessageBox.warning(self, "Warning", "Failed to update paper in library")
            else:
                # 새 항목 추가
                doc_id = db_handler.add_paper(db_data)
                
                QMessageBox.information(
                    self,
                    "Success",
                    f"Paper successfully saved to library (ID: {doc_id})"
                )
                
                if self.parent:
                    self.parent.update_status(f"Saved to library: {paper_data.get('title', '')}")
                
        except Exception as e:
            logger.error(f"Error saving to library: {e}")
            QMessageBox.critical(self, "Error", f"Could not save to library: {e}")

# 테스트용
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    results_panel = ResultsPanel()
    results_panel.show()
    sys.exit(app.exec_())
