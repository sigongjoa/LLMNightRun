"""
Vector DB GUI 애플리케이션
기존 Vector DB와 연동되는 그래픽 사용자 인터페이스
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union

# 경로 설정 - 상위 디렉토리의 vector_db 모듈을 가져옴
parent_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(parent_dir)

# 벡터 DB 모듈 임포트
try:
    from vector_db import VectorDB, Document
    from vector_db.encoders import DefaultEncoder
    
    # SentenceTransformer 인코더 임포트 시도
    try:
        from vector_db.encoders import SentenceTransformerEncoder
        SENTENCE_TRANSFORMER_AVAILABLE = True
    except ImportError:
        SENTENCE_TRANSFORMER_AVAILABLE = False
        
except ImportError as e:
    print(f"Vector DB 모듈 임포트 실패: {e}")
    print("먼저 Vector DB 모듈이 설치되어 있는지 확인하세요.")
    sys.exit(1)

# GUI 라이브러리 임포트
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# 상수 정의
DEFAULT_DB_DIR = os.path.join(parent_dir, "vector_db_data")
DEFAULT_ENCODER = "default"
DEFAULT_DIMENSION = 768
DEFAULT_ST_MODEL = "all-MiniLM-L6-v2"
MAX_DISPLAY_ITEMS = 100


class VectorDBApp:
    """
    Vector DB GUI 애플리케이션 메인 클래스
    """
    def __init__(self, root: tk.Tk):
        """애플리케이션 초기화"""
        self.root = root
        self.root.title("Vector DB 관리 도구")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        
        # 벡터 DB 인스턴스
        self.db = None
        self.db_path = tk.StringVar(value=DEFAULT_DB_DIR)
        self.encoder_type = tk.StringVar(value=DEFAULT_ENCODER)
        self.dimension = tk.IntVar(value=DEFAULT_DIMENSION)
        self.st_model = tk.StringVar(value=DEFAULT_ST_MODEL)
        
        # 상태 변수
        self.status_message = tk.StringVar(value="준비됨")
        self.document_count = tk.IntVar(value=0)
        self.search_count = tk.IntVar(value=0)
        self.current_doc_id = tk.StringVar(value="")
        
        # 검색 변수
        self.search_query = tk.StringVar(value="")
        self.search_results = []
        self.search_limit = tk.IntVar(value=5)
        self.search_threshold = tk.DoubleVar(value=0.0)
        
        # 메타데이터 필터링
        self.filter_enabled = tk.BooleanVar(value=False)
        self.filter_key = tk.StringVar(value="")
        self.filter_value = tk.StringVar(value="")
        
        # 문서 변수
        self.doc_text = tk.StringVar(value="")
        self.doc_metadata = {}
        
        # UI 구성
        self._setup_ui()
        
        # 초기 데이터베이스 설정
        self._on_db_connect()
    
    def _setup_ui(self):
        """UI 레이아웃 구성"""
        # 메인 프레임 생성
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 좌측 패널 (설정 및 문서 추가)
        left_panel = ttk.Frame(main_frame, padding="5", width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        
        # DB 연결 프레임
        db_frame = ttk.LabelFrame(left_panel, text="데이터베이스 연결", padding="5")
        db_frame.pack(fill=tk.X, pady=(0, 5))
        
        # DB 경로
        ttk.Label(db_frame, text="DB 경로:").pack(fill=tk.X, pady=2)
        path_frame = ttk.Frame(db_frame)
        path_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(path_frame, textvariable=self.db_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="...", width=3, 
                   command=self._select_db_directory).pack(side=tk.RIGHT)
        
        # 인코더 설정
        ttk.Label(db_frame, text="인코더:").pack(fill=tk.X, pady=2)
        encoder_frame = ttk.Frame(db_frame)
        encoder_frame.pack(fill=tk.X, pady=2)
        
        # 인코더 선택 라디오 버튼
        encoder_options = [
            ("기본 인코더", "default"),
            ("SentenceTransformer", "sentence_transformer", SENTENCE_TRANSFORMER_AVAILABLE)
        ]
        
        for i, option in enumerate(encoder_options):
            if len(option) == 3:  # 가용성 정보가 있는 경우
                text, value, available = option
                if not available:
                    text += " (설치 필요)"
            else:
                text, value = option
                available = True
            
            rb = ttk.Radiobutton(encoder_frame, text=text, value=value, 
                                 variable=self.encoder_type,
                                 state="normal" if available else "disabled")
            rb.pack(anchor=tk.W)
        
        # 인코더 옵션 프레임
        encoder_options_frame = ttk.Frame(db_frame)
        encoder_options_frame.pack(fill=tk.X, pady=2)
        
        # 기본 인코더 차원
        ttk.Label(encoder_options_frame, text="차원 (기본 인코더):").pack(fill=tk.X, pady=2)
        ttk.Entry(encoder_options_frame, textvariable=self.dimension, width=10).pack(fill=tk.X, pady=2)
        
        # SentenceTransformer 모델
        ttk.Label(encoder_options_frame, text="모델 (SentenceTransformer):").pack(fill=tk.X, pady=2)
        ttk.Entry(encoder_options_frame, textvariable=self.st_model).pack(fill=tk.X, pady=2)
        
        # 연결 버튼
        ttk.Button(db_frame, text="연결", command=self._on_db_connect).pack(fill=tk.X, pady=5)
        
        # 문서 관리 프레임
        doc_frame = ttk.LabelFrame(left_panel, text="문서 관리", padding="5")
        doc_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 문서 텍스트
        ttk.Label(doc_frame, text="문서 내용:").pack(anchor=tk.W, pady=2)
        self.text_entry = scrolledtext.ScrolledText(doc_frame, wrap=tk.WORD, height=10)
        self.text_entry.pack(fill=tk.BOTH, expand=True, pady=2)
        
        # 메타데이터 
        ttk.Label(doc_frame, text="메타데이터 (JSON):").pack(anchor=tk.W, pady=2)
        self.metadata_entry = scrolledtext.ScrolledText(doc_frame, wrap=tk.WORD, height=5)
        self.metadata_entry.pack(fill=tk.BOTH, pady=2)
        self.metadata_entry.insert(tk.END, "{}")
        
        # 문서 조작 버튼
        button_frame = ttk.Frame(doc_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="추가", 
                   command=self._on_add_document).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="업데이트", 
                   command=self._on_update_document).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(button_frame, text="삭제", 
                   command=self._on_delete_document).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # 파일에서 추가 버튼
        ttk.Button(doc_frame, text="파일에서 추가", 
                   command=self._on_add_from_file).pack(fill=tk.X, pady=2)
        
        # 벌크 추가 버튼
        ttk.Button(doc_frame, text="폴더에서 일괄 추가", 
                   command=self._on_bulk_add_from_directory).pack(fill=tk.X, pady=2)
        
        # 데이터베이스 정보
        info_frame = ttk.LabelFrame(left_panel, text="데이터베이스 정보", padding="5")
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="문서 수:").pack(side=tk.LEFT, padx=5)
        ttk.Label(info_frame, textvariable=self.document_count).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(info_frame, text="새로고침", 
                   command=self._refresh_document_count).pack(side=tk.RIGHT, padx=5)
        
        # 우측 패널 (검색 및 결과)
        right_panel = ttk.Frame(main_frame, padding="5")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 검색 프레임
        search_frame = ttk.LabelFrame(right_panel, text="검색", padding="5")
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 검색어
        ttk.Label(search_frame, text="검색어:").pack(anchor=tk.W, pady=2)
        search_entry_frame = ttk.Frame(search_frame)
        search_entry_frame.pack(fill=tk.X, pady=2)
        ttk.Entry(search_entry_frame, textvariable=self.search_query).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(search_entry_frame, text="검색", 
                   command=self._on_search).pack(side=tk.RIGHT, padx=5)
        
        # 검색 옵션
        options_frame = ttk.Frame(search_frame)
        options_frame.pack(fill=tk.X, pady=2)
        
        # 결과 개수
        ttk.Label(options_frame, text="결과 개수:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(options_frame, from_=1, to=100, width=5, 
                    textvariable=self.search_limit).pack(side=tk.LEFT, padx=5)
        
        # 유사도 임계값
        ttk.Label(options_frame, text="유사도 임계값:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(options_frame, from_=0.0, to=1.0, increment=0.05, width=5, 
                    textvariable=self.search_threshold).pack(side=tk.LEFT, padx=5)
        
        # 메타데이터 필터
        filter_frame = ttk.LabelFrame(search_frame, text="메타데이터 필터", padding="5")
        filter_frame.pack(fill=tk.X, pady=2)
        
        ttk.Checkbutton(filter_frame, text="필터 사용", 
                         variable=self.filter_enabled).pack(anchor=tk.W)
        
        filter_options = ttk.Frame(filter_frame)
        filter_options.pack(fill=tk.X, pady=2)
        
        ttk.Label(filter_options, text="키:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filter_options, textvariable=self.filter_key, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(filter_options, text="값:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(filter_options, textvariable=self.filter_value).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 검색 결과 프레임
        results_frame = ttk.LabelFrame(right_panel, text="검색 결과", padding="5")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 검색 결과 트리뷰
        columns = ("id", "score", "text", "metadata")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings")
        
        # 컬럼 설정
        self.results_tree.heading("id", text="ID")
        self.results_tree.heading("score", text="유사도")
        self.results_tree.heading("text", text="문서 내용")
        self.results_tree.heading("metadata", text="메타데이터")
        
        self.results_tree.column("id", width=50)
        self.results_tree.column("score", width=70)
        self.results_tree.column("text", width=300)
        self.results_tree.column("metadata", width=150)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)
        
        # 결과 트리 배치
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 결과 선택 이벤트 바인딩
        self.results_tree.bind("<<TreeviewSelect>>", self._on_result_selected)
        
        # 문서 리스트 프레임
        docs_frame = ttk.LabelFrame(right_panel, text="모든 문서", padding="5")
        docs_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 문서 목록 트리뷰
        doc_columns = ("id", "text", "metadata")
        self.docs_tree = ttk.Treeview(docs_frame, columns=doc_columns, show="headings")
        
        # 컬럼 설정
        self.docs_tree.heading("id", text="ID")
        self.docs_tree.heading("text", text="문서 내용")
        self.docs_tree.heading("metadata", text="메타데이터")
        
        self.docs_tree.column("id", width=50)
        self.docs_tree.column("text", width=350)
        self.docs_tree.column("metadata", width=150)
        
        # 스크롤바
        doc_scrollbar = ttk.Scrollbar(docs_frame, orient=tk.VERTICAL, command=self.docs_tree.yview)
        self.docs_tree.configure(yscroll=doc_scrollbar.set)
        
        # 문서 목록 트리 배치
        self.docs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        doc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 문서 선택 이벤트 바인딩
        self.docs_tree.bind("<<TreeviewSelect>>", self._on_document_selected)
        
        # 리스트 새로고침 버튼
        ttk.Button(docs_frame, text="문서 목록 새로고침", 
                   command=self._refresh_document_list).pack(fill=tk.X, pady=2)
        
        # 상태 표시줄
        status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(2, 0))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Label(status_bar, textvariable=self.status_message).pack(side=tk.LEFT, padx=5)
    
    def _select_db_directory(self):
        """데이터베이스 저장 디렉토리 선택"""
        current_path = self.db_path.get()
        dir_path = filedialog.askdirectory(initialdir=current_path)
        if dir_path:
            self.db_path.set(dir_path)
    
    def _on_db_connect(self):
        """데이터베이스 연결 버튼 클릭 이벤트"""
        try:
            # 경로 확인 및 생성
            db_path = self.db_path.get()
            if not os.path.exists(db_path):
                os.makedirs(db_path, exist_ok=True)
            
            # 인코더 설정
            encoder_type = self.encoder_type.get()
            encoder = None
            
            if encoder_type == "default":
                dimension = self.dimension.get()
                encoder = DefaultEncoder(dimension=dimension)
                self.status_message.set(f"기본 인코더 (차원: {dimension})로 설정됨")
            elif encoder_type == "sentence_transformer":
                if not SENTENCE_TRANSFORMER_AVAILABLE:
                    messagebox.showerror(
                        "오류", 
                        "SentenceTransformer가 설치되어 있지 않습니다.\n"
                        "pip install sentence-transformers 명령으로 설치하세요."
                    )
                    return
                
                model_name = self.st_model.get()
                encoder = SentenceTransformerEncoder(model_name=model_name)
                self.status_message.set(f"SentenceTransformer 인코더 (모델: {model_name})로 설정됨")
            
            # 벡터 DB 생성
            self.db = VectorDB(encoder=encoder, storage_dir=db_path)
            
            # 문서 수 업데이트
            self._refresh_document_count()
            
            # 문서 목록 새로고침
            self._refresh_document_list()
            
            messagebox.showinfo("연결 성공", f"Vector DB가 '{db_path}'에 연결되었습니다.")
            
        except Exception as e:
            messagebox.showerror("연결 오류", f"데이터베이스 연결 중 오류가 발생했습니다: {str(e)}")
            self.status_message.set(f"오류: {str(e)}")
    
    def _refresh_document_count(self):
        """문서 수 새로고침"""
        if self.db:
            count = self.db.count()
            self.document_count.set(count)
            self.status_message.set(f"데이터베이스에 {count}개의 문서가 있습니다.")
        else:
            self.document_count.set(0)
            self.status_message.set("데이터베이스가 연결되어 있지 않습니다.")
    
    def _refresh_document_list(self):
        """문서 목록 새로고침"""
        if not self.db:
            messagebox.showinfo("알림", "먼저 데이터베이스에 연결하세요.")
            return
        
        # 현재 목록 비우기
        for i in self.docs_tree.get_children():
            self.docs_tree.delete(i)
        
        # 모든 문서 가져오기
        try:
            documents = self.db.list_documents(limit=MAX_DISPLAY_ITEMS)
            
            for doc in documents:
                # 텍스트 및 메타데이터 준비
                text_preview = doc.text[:100] + "..." if len(doc.text) > 100 else doc.text
                metadata_str = json.dumps(doc.metadata, ensure_ascii=False)
                if len(metadata_str) > 100:
                    metadata_str = metadata_str[:100] + "..."
                
                # 트리뷰에 추가
                self.docs_tree.insert("", tk.END, values=(doc.id, text_preview, metadata_str))
            
            self.status_message.set(f"{len(documents)}개 문서 로드됨 (최대 {MAX_DISPLAY_ITEMS}개까지 표시)")
            
        except Exception as e:
            messagebox.showerror("오류", f"문서 목록을 가져오는 중 오류가 발생했습니다: {str(e)}")
            self.status_message.set(f"오류: {str(e)}")
    
    def _on_add_document(self):
        """문서 추가 버튼 클릭 이벤트"""
        if not self.db:
            messagebox.showinfo("알림", "먼저 데이터베이스에 연결하세요.")
            return
        
        # 문서 텍스트 가져오기
        text = self.text_entry.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("경고", "문서 내용을 입력하세요.")
            return
        
        # 메타데이터 가져오기
        try:
            metadata_str = self.metadata_entry.get(1.0, tk.END).strip()
            metadata = json.loads(metadata_str) if metadata_str else {}
        except json.JSONDecodeError:
            messagebox.showerror("오류", "메타데이터 JSON 형식이 올바르지 않습니다.")
            return
        
        # 문서 추가
        try:
            doc_id = self.db.add(text, metadata=metadata)
            
            self.status_message.set(f"문서 추가됨: ID={doc_id}")
            messagebox.showinfo("성공", f"문서가 추가되었습니다. (ID: {doc_id})")
            
            # 문서 수 및 목록 업데이트
            self._refresh_document_count()
            self._refresh_document_list()
            
            # 입력 필드 초기화
            self.text_entry.delete(1.0, tk.END)
            self.metadata_entry.delete(1.0, tk.END)
            self.metadata_entry.insert(1.0, "{}")
            
        except Exception as e:
            messagebox.showerror("오류", f"문서 추가 중 오류가 발생했습니다: {str(e)}")
            self.status_message.set(f"오류: {str(e)}")
    
    def _on_update_document(self):
        """문서 업데이트 버튼 클릭 이벤트"""
        if not self.db:
            messagebox.showinfo("알림", "먼저 데이터베이스에 연결하세요.")
            return
        
        # 현재 선택된 문서 ID 확인
        doc_id = self.current_doc_id.get()
        if not doc_id:
            messagebox.showwarning("경고", "업데이트할 문서를 먼저 선택하세요.")
            return
        
        # 문서가 존재하는지 확인
        doc = self.db.get(doc_id)
        if not doc:
            messagebox.showerror("오류", f"ID가 '{doc_id}'인 문서를 찾을 수 없습니다.")
            return
        
        # 새 텍스트 및 메타데이터 가져오기
        text = self.text_entry.get(1.0, tk.END).strip()
        
        try:
            metadata_str = self.metadata_entry.get(1.0, tk.END).strip()
            metadata = json.loads(metadata_str) if metadata_str else {}
        except json.JSONDecodeError:
            messagebox.showerror("오류", "메타데이터 JSON 형식이 올바르지 않습니다.")
            return
        
        # 문서 업데이트
        try:
            success = self.db.update(doc_id, text=text, metadata=metadata)
            
            if success:
                self.status_message.set(f"문서 업데이트됨: ID={doc_id}")
                messagebox.showinfo("성공", f"문서가 업데이트되었습니다. (ID: {doc_id})")
                
                # 문서 목록 업데이트
                self._refresh_document_list()
            else:
                self.status_message.set(f"문서 업데이트 실패: ID={doc_id}")
                messagebox.showerror("오류", f"문서 업데이트에 실패했습니다. (ID: {doc_id})")
            
        except Exception as e:
            messagebox.showerror("오류", f"문서 업데이트 중 오류가 발생했습니다: {str(e)}")
            self.status_message.set(f"오류: {str(e)}")
    
    def _on_delete_document(self):
        """문서 삭제 버튼 클릭 이벤트"""
        if not self.db:
            messagebox.showinfo("알림", "먼저 데이터베이스에 연결하세요.")
            return
        
        # 현재 선택된 문서 ID 확인
        doc_id = self.current_doc_id.get()
        if not doc_id:
            messagebox.showwarning("경고", "삭제할 문서를 먼저 선택하세요.")
            return
        
        # 확인 메시지
        if not messagebox.askyesno("확인", f"정말 ID가 '{doc_id}'인 문서를 삭제하시겠습니까?"):
            return
        
        # 문서 삭제
        try:
            success = self.db.delete(doc_id)
            
            if success:
                self.status_message.set(f"문서 삭제됨: ID={doc_id}")
                messagebox.showinfo("성공", f"문서가 삭제되었습니다. (ID: {doc_id})")
                
                # 문서 수 및 목록 업데이트
                self._refresh_document_count()
                self._refresh_document_list()
                
                # 입력 필드 초기화
                self.text_entry.delete(1.0, tk.END)
                self.metadata_entry.delete(1.0, tk.END)
                self.metadata_entry.insert(1.0, "{}")
                self.current_doc_id.set("")
            else:
                self.status_message.set(f"문서 삭제 실패: ID={doc_id}")
                messagebox.showerror("오류", f"문서 삭제에 실패했습니다. (ID: {doc_id})")
            
        except Exception as e:
            messagebox.showerror("오류", f"문서 삭제 중 오류가 발생했습니다: {str(e)}")
            self.status_message.set(f"오류: {str(e)}")
    
    def _on_add_from_file(self):
        """파일에서 문서 추가 버튼 클릭 이벤트"""
        if not self.db:
            messagebox.showinfo("알림", "먼저 데이터베이스에 연결하세요.")
            return
        
        # 파일 선택
        file_path = filedialog.askopenfilename(
            title="텍스트 파일 선택",
            filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # 파일 내용 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # 파일 이름을 메타데이터로 사용
            file_name = os.path.basename(file_path)
            metadata = {"source": "file", "file_name": file_name}
            
            # 문서 추가
            doc_id = self.db.add(text, metadata=metadata)
            
            self.status_message.set(f"파일에서 문서 추가됨: ID={doc_id}, 파일={file_name}")
            messagebox.showinfo("성공", f"파일 '{file_name}'에서 문서가 추가되었습니다. (ID: {doc_id})")
            
            # 문서 수 및 목록 업데이트
            self._refresh_document_count()
            self._refresh_document_list()
            
        except Exception as e:
            messagebox.showerror("오류", f"파일에서 문서 추가 중 오류가 발생했습니다: {str(e)}")
            self.status_message.set(f"오류: {str(e)}")
    
    def _on_bulk_add_from_directory(self):
        """폴더에서 일괄 추가 버튼 클릭 이벤트"""
        if not self.db:
            messagebox.showinfo("알림", "먼저 데이터베이스에 연결하세요.")
            return
        
        # 폴더 선택
        dir_path = filedialog.askdirectory(title="텍스트 파일이 있는 폴더 선택")
        
        if not dir_path:
            return
        
        try:
            # 폴더 내 모든 txt 파일 찾기
            txt_files = []
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.endswith(".txt"):
                        txt_files.append(os.path.join(root, file))
            
            if not txt_files:
                messagebox.showinfo("알림", "선택한 폴더에 .txt 파일이 없습니다.")
                return
            
            # 일괄 추가 확인
            if not messagebox.askyesno("확인", f"선택한 폴더에서 {len(txt_files)}개의 .txt 파일을 찾았습니다. 모두 추가하시겠습니까?"):
                return
            
            # 진행 상황을 보여주는 새 창
            progress_window = tk.Toplevel(self.root)
            progress_window.title("일괄 추가 진행 중")
            progress_window.geometry("400x150")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            progress_label = ttk.Label(progress_window, text="파일 추가 중...")
            progress_label.pack(pady=10)
            
            progress_bar = ttk.Progressbar(progress_window, mode='determinate', length=300, maximum=len(txt_files))
            progress_bar.pack(pady=10)
            
            status_label = ttk.Label(progress_window, text="0/{} 파일 처리됨".format(len(txt_files)))
            status_label.pack(pady=10)
            
            # 파일 처리 및 추가
            added_files = 0
            skipped_files = 0
            error_files = 0
            
            for i, file_path in enumerate(txt_files):
                try:
                    # 파일 내용 읽기
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                    
                    # 내용이 비어있으면 건너뛰기
                    if not text.strip():
                        skipped_files += 1
                        continue
                    
                    # 파일 이름과 경로를 메타데이터로 사용
                    file_name = os.path.basename(file_path)
                    rel_path = os.path.relpath(file_path, dir_path)
                    metadata = {
                        "source": "bulk_import", 
                        "file_name": file_name,
                        "relative_path": rel_path
                    }
                    
                    # 문서 추가
                    self.db.add(text, metadata=metadata)
                    added_files += 1
                    
                except Exception as e:
                    print(f"파일 추가 오류 ({file_path}): {str(e)}")
                    error_files += 1
                
                # 진행 상황 업데이트
                progress_bar['value'] = i + 1
                status_label['text'] = "{}/{} 파일 처리됨".format(i + 1, len(txt_files))
                progress_window.update()
            
            # 진행 창 닫기
            progress_window.destroy()
            
            # 결과 메시지
            result_msg = f"일괄 추가 완료:\n추가된 파일: {added_files}\n건너뛴 파일: {skipped_files}\n오류 발생: {error_files}"
            self.status_message.set(f"일괄 추가 완료: {added_files}개 추가됨, {error_files}개 오류")
            messagebox.showinfo("일괄 추가 완료", result_msg)
            
            # 문서 수 및 목록 업데이트
            self._refresh_document_count()
            self._refresh_document_list()
            
        except Exception as e:
            messagebox.showerror("오류", f"일괄 추가 중 오류가 발생했습니다: {str(e)}")
            self.status_message.set(f"오류: {str(e)}")
    
    def _on_search(self):
        """검색 버튼 클릭 이벤트"""
        if not self.db:
            messagebox.showinfo("알림", "먼저 데이터베이스에 연결하세요.")
            return
        
        # 검색어 확인
        query = self.search_query.get().strip()
        if not query:
            messagebox.showwarning("경고", "검색어를 입력하세요.")
            return
        
        # 검색 옵션
        limit = self.search_limit.get()
        threshold = self.search_threshold.get() if self.search_threshold.get() > 0 else None
        
        # 메타데이터 필터
        filter_metadata = None
        if self.filter_enabled.get():
            key = self.filter_key.get().strip()
            value = self.filter_value.get().strip()
            
            if key:
                filter_metadata = {key: value}
        
        # 검색 실행
        try:
            start_time = time.time()
            
            results = self.db.search(
                query=query, 
                k=limit, 
                threshold=threshold, 
                filter_metadata=filter_metadata
            )
            
            end_time = time.time()
            search_time = end_time - start_time
            
            # 결과 트리뷰 초기화
            for i in self.results_tree.get_children():
                self.results_tree.delete(i)
            
            # 결과가 없는 경우
            if not results:
                self.status_message.set(f"검색 결과 없음 (소요 시간: {search_time:.3f}초)")
                messagebox.showinfo("검색 결과", "검색 결과가 없습니다.")
                return
            
            # 결과 표시
            for doc, score in results:
                # 텍스트 및 메타데이터 준비
                text_preview = doc.text[:100] + "..." if len(doc.text) > 100 else doc.text
                metadata_str = json.dumps(doc.metadata, ensure_ascii=False)
                if len(metadata_str) > 100:
                    metadata_str = metadata_str[:100] + "..."
                
                # 트리뷰에 추가
                self.results_tree.insert("", tk.END, values=(doc.id, f"{score:.4f}", text_preview, metadata_str))
            
            # 검색 결과 정보 업데이트
            self.search_count.set(len(results))
            self.status_message.set(f"검색 완료: {len(results)}개 결과 (소요 시간: {search_time:.3f}초)")
            
        except Exception as e:
            messagebox.showerror("오류", f"검색 중 오류가 발생했습니다: {str(e)}")
            self.status_message.set(f"오류: {str(e)}")
    
    def _on_result_selected(self, event):
        """검색 결과 선택 이벤트"""
        selected_items = self.results_tree.selection()
        if not selected_items:
            return
        
        # 첫 번째 선택된 항목의 ID 가져오기
        item_id = selected_items[0]
        doc_id = self.results_tree.item(item_id, "values")[0]
        
        # 문서 정보 표시
        self._load_document(doc_id)
    
    def _on_document_selected(self, event):
        """문서 목록에서 문서 선택 이벤트"""
        selected_items = self.docs_tree.selection()
        if not selected_items:
            return
        
        # 첫 번째 선택된 항목의 ID 가져오기
        item_id = selected_items[0]
        doc_id = self.docs_tree.item(item_id, "values")[0]
        
        # 문서 정보 표시
        self._load_document(doc_id)
    
    def _load_document(self, doc_id):
        """문서 ID로 문서 정보 로드 및 표시"""
        if not self.db:
            return
        
        try:
            # 문서 가져오기
            doc = self.db.get(doc_id)
            if not doc:
                messagebox.showerror("오류", f"ID가 '{doc_id}'인 문서를 찾을 수 없습니다.")
                return
            
            # 현재 문서 ID 설정
            self.current_doc_id.set(doc_id)
            
            # 텍스트 필드 업데이트
            self.text_entry.delete(1.0, tk.END)
            self.text_entry.insert(1.0, doc.text)
            
            # 메타데이터 필드 업데이트
            self.metadata_entry.delete(1.0, tk.END)
            self.metadata_entry.insert(1.0, json.dumps(doc.metadata, indent=2, ensure_ascii=False))
            
            self.status_message.set(f"문서 로드됨: ID={doc_id}")
            
        except Exception as e:
            messagebox.showerror("오류", f"문서 로드 중 오류가 발생했습니다: {str(e)}")
            self.status_message.set(f"오류: {str(e)}")


def main():
    """애플리케이션 메인 함수"""
    root = tk.Tk()
    app = VectorDBApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
