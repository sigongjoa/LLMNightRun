"""
Arxiv 모듈 탭 컴포넌트

Arxiv 논문 검색, 다운로드 및 관리를 위한 UI 탭 컴포넌트를 제공합니다.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import threading
from typing import Dict, List, Any, Optional, Tuple

from core.logging import get_logger
from core.events import subscribe, publish
from arxiv_module import search_papers, download_paper, ArxivManager

logger = get_logger("gui.components.arxiv_tab")

class ArxivTab(ttk.Frame):
    """Arxiv 논문 검색 및 관리 탭"""
    
    def __init__(self, parent):
        """
        Arxiv 탭 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, padding="10")
        
        # Arxiv 관리자 초기화
        self.arxiv_manager = ArxivManager()
        
        # 검색 결과
        self.search_results = []
        
        # 컴포넌트 초기화
        self._setup_variables()
        self._create_widgets()
        self._bind_events()
        
        logger.info("Arxiv 탭 초기화됨")
    
    def _setup_variables(self):
        """변수 초기화"""
        # 검색 변수
        self.search_query = tk.StringVar()
        self.max_results = tk.IntVar(value=10)
        self.sort_by = tk.StringVar(value="relevance")
        
        # 상태 변수
        self.status_text = tk.StringVar(value="준비 완료")
        self.progress_var = tk.DoubleVar(value=0.0)
    
    def _create_widgets(self):
        """UI 구성요소 생성"""
        # 메인 영역 분할
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # === 왼쪽 패널 (검색 및 컬렉션) ===
        self.left_panel = ttk.Frame(self.paned_window, padding="5")
        self.paned_window.add(self.left_panel, weight=1)
        
        # 검색 프레임
        search_frame = ttk.LabelFrame(self.left_panel, text="논문 검색", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 검색어 입력
        ttk.Label(search_frame, text="검색어:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(search_frame, textvariable=self.search_query, width=30).grid(
            row=0, column=1, columnspan=2, sticky=tk.EW, pady=5, padx=5)
        
        # 최대 결과 수
        ttk.Label(search_frame, text="최대 결과:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(search_frame, from_=1, to=100, textvariable=self.max_results, width=5).grid(
            row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 정렬 기준
        ttk.Label(search_frame, text="정렬 기준:").grid(row=2, column=0, sticky=tk.W, pady=5)
        sort_combo = ttk.Combobox(search_frame, textvariable=self.sort_by, width=10)
        sort_combo['values'] = ('relevance', 'lastUpdatedDate', 'submittedDate')
        sort_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 검색 버튼
        ttk.Button(search_frame, text="검색", command=self._search_papers).grid(
            row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # 컬렉션 프레임
        collections_frame = ttk.LabelFrame(self.left_panel, text="논문 컬렉션", padding="10")
        collections_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 컬렉션 리스트
        self.collections_tree = ttk.Treeview(collections_frame, columns=("name", "papers"), show="headings")
        self.collections_tree.heading("name", text="이름")
        self.collections_tree.heading("papers", text="논문 수")
        self.collections_tree.column("name", width=150)
        self.collections_tree.column("papers", width=50)
        self.collections_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 컬렉션 스크롤바
        scrollbar = ttk.Scrollbar(collections_frame, orient=tk.VERTICAL, command=self.collections_tree.yview)
        self.collections_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 컬렉션 버튼 프레임
        collection_buttons = ttk.Frame(collections_frame)
        collection_buttons.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(collection_buttons, text="새 컬렉션", command=self._create_collection).pack(side=tk.LEFT, padx=2)
        ttk.Button(collection_buttons, text="컬렉션에 추가", command=self._add_to_collection).pack(side=tk.LEFT, padx=2)
        ttk.Button(collection_buttons, text="삭제", command=self._delete_collection).pack(side=tk.LEFT, padx=2)
        
        # === 오른쪽 패널 (검색 결과 및 논문 세부 정보) ===
        self.right_panel = ttk.Frame(self.paned_window, padding="5")
        self.paned_window.add(self.right_panel, weight=2)
        
        # 검색 결과 프레임
        results_frame = ttk.LabelFrame(self.right_panel, text="검색 결과", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 검색 결과 리스트
        self.results_tree = ttk.Treeview(results_frame, columns=("title", "authors", "date"), show="headings")
        self.results_tree.heading("title", text="제목")
        self.results_tree.heading("authors", text="저자")
        self.results_tree.heading("date", text="출판일")
        self.results_tree.column("title", width=300)
        self.results_tree.column("authors", width=150)
        self.results_tree.column("date", width=100)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 결과 스크롤바
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 논문 세부 정보 프레임
        details_frame = ttk.LabelFrame(self.right_panel, text="논문 세부 정보", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 논문 세부 정보 텍스트 영역
        self.details_text = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, height=10)
        self.details_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 논문 버튼 프레임
        paper_buttons = ttk.Frame(details_frame)
        paper_buttons.pack(fill=tk.X)
        
        ttk.Button(paper_buttons, text="PDF 다운로드", command=self._download_paper).pack(side=tk.LEFT, padx=2)
        ttk.Button(paper_buttons, text="인용 복사", command=self._copy_citation).pack(side=tk.LEFT, padx=2)
        ttk.Button(paper_buttons, text="벡터 DB에 추가", command=self._add_to_vector_db).pack(side=tk.LEFT, padx=2)
        ttk.Button(paper_buttons, text="대화에 추가", command=self._add_to_conversation).pack(side=tk.LEFT, padx=2)
        
        # 상태 바
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(status_frame, textvariable=self.status_text).pack(side=tk.RIGHT, padx=(5, 0))
    
    def _bind_events(self):
        """이벤트 바인딩"""
        # 검색 결과 선택 시 세부 정보 표시
        self.results_tree.bind("<<TreeviewSelect>>", self._on_result_select)
        
        # 컬렉션 선택 시 컬렉션 내 논문 표시
        self.collections_tree.bind("<<TreeviewSelect>>", self._on_collection_select)
        
        # 이벤트 구독
        subscribe("arxiv.search.complete", self._on_search_complete)
        subscribe("arxiv.download.complete", self._on_download_complete)
    
    def refresh(self):
        """데이터 새로고침"""
        # 컬렉션 목록 로드
        self._load_collections()
    
    def _load_collections(self):
        """컬렉션 목록 로드"""
        # 기존 항목 삭제
        for item in self.collections_tree.get_children():
            self.collections_tree.delete(item)
        
        # 컬렉션 로드
        collections = self.arxiv_manager.list_collections()
        
        for collection in collections:
            self.collections_tree.insert("", tk.END, values=(
                collection["name"],
                collection["paper_count"]
            ))
    
    def _search_papers(self):
        """논문 검색 수행"""
        query = self.search_query.get().strip()
        
        if not query:
            messagebox.showinfo("알림", "검색어를 입력하세요.")
            return
        
        # 상태 업데이트
        self.status_text.set("검색 중...")
        self.progress_var.set(10)
        
        # 기존 결과 삭제
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 검색 설정
        max_results = self.max_results.get()
        sort_by = self.sort_by.get()
        
        def do_search():
            try:
                # 검색 수행
                self.search_results = self.arxiv_manager.search(
                    query=query,
                    max_results=max_results,
                    sort_by=sort_by
                )
                
                # 이벤트 발행은 내부적으로 이루어짐
            except Exception as e:
                logger.error(f"논문 검색 중 오류 발생: {str(e)}")
                self.status_text.set(f"검색 실패: {str(e)}")
                
                # 에러 메시지 표시
                messagebox.showerror("검색 오류", f"논문 검색 중 오류가 발생했습니다:\n{str(e)}")
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_search, daemon=True).start()
    
    def _on_search_complete(self, query=None, result_count=None):
        """검색 완료 이벤트 핸들러"""
        # 결과 표시
        for idx, paper in enumerate(self.search_results):
            title = paper.get("title", "").replace("\n", " ")
            authors = ", ".join([author.get("name", "") for author in paper.get("authors", [])])
            date = paper.get("published", "")
            
            self.results_tree.insert("", tk.END, values=(title, authors, date))
        
        # 상태 업데이트
        self.status_text.set(f"검색 완료: {result_count}개 결과")
        self.progress_var.set(100)
    
    def _on_result_select(self, event):
        """검색 결과 선택 시 처리"""
        selected_items = self.results_tree.selection()
        
        if not selected_items:
            return
        
        # 선택된 항목 인덱스
        item = selected_items[0]
        idx = self.results_tree.index(item)
        
        if idx >= len(self.search_results):
            return
        
        # 선택된 논문 정보
        paper = self.search_results[idx]
        
        # 세부 정보 표시
        self._display_paper_details(paper)
    
    def _display_paper_details(self, paper):
        """논문 세부 정보 표시"""
        # 텍스트 영역 초기화
        self.details_text.delete("1.0", tk.END)
        
        # 정보 표시
        title = paper.get("title", "").replace("\n", " ")
        authors = ", ".join([author.get("name", "") for author in paper.get("authors", [])])
        date = paper.get("published", "")
        abstract = paper.get("abstract", "").replace("\n", " ")
        
        details = f"제목: {title}\n\n"
        details += f"저자: {authors}\n\n"
        details += f"출판일: {date}\n\n"
        details += f"초록:\n{abstract}\n\n"
        details += f"URL: {paper.get('pdf_url', '')}\n\n"
        details += f"arXiv ID: {paper.get('id', '')}"
        
        self.details_text.insert(tk.END, details)
    
    def _download_paper(self):
        """선택된 논문 PDF 다운로드"""
        selected_items = self.results_tree.selection()
        
        if not selected_items:
            messagebox.showinfo("알림", "다운로드할 논문을 선택하세요.")
            return
        
        # 선택된 항목 인덱스
        item = selected_items[0]
        idx = self.results_tree.index(item)
        
        if idx >= len(self.search_results):
            return
        
        # 선택된 논문 정보
        paper = self.search_results[idx]
        paper_id = paper.get("id", "")
        
        if not paper_id:
            messagebox.showerror("오류", "논문 ID를 찾을 수 없습니다.")
            return
        
        # 상태 업데이트
        self.status_text.set("PDF 다운로드 중...")
        self.progress_var.set(10)
        
        def do_download():
            try:
                # 다운로드 수행
                pdf_path = self.arxiv_manager.download_paper_pdf(paper_id)
                
                if pdf_path:
                    # UI 스레드에서 업데이트
                    self.master.after(0, lambda: self._show_download_success(pdf_path))
                else:
                    self.master.after(0, lambda: messagebox.showerror(
                        "다운로드 실패", "PDF를 다운로드할 수 없습니다."))
                    self.status_text.set("다운로드 실패")
            
            except Exception as e:
                logger.error(f"PDF 다운로드 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: messagebox.showerror(
                    "다운로드 오류", f"PDF 다운로드 중 오류가 발생했습니다:\n{str(e)}"))
                self.status_text.set(f"다운로드 실패: {str(e)}")
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_download, daemon=True).start()
    
    def _show_download_success(self, pdf_path):
        """다운로드 성공 메시지 표시"""
        self.status_text.set(f"다운로드 완료: {os.path.basename(pdf_path)}")
        self.progress_var.set(100)
        
        # 파일 열기 여부 확인
        result = messagebox.askyesno(
            "다운로드 완료", 
            f"PDF가 다운로드되었습니다:\n{pdf_path}\n\n파일을 열겠습니까?"
        )
        
        if result:
            try:
                import subprocess
                import platform
                
                if platform.system() == 'Darwin':  # macOS
                    subprocess.call(('open', pdf_path))
                elif platform.system() == 'Windows':  # Windows
                    os.startfile(pdf_path)
                else:  # Linux
                    subprocess.call(('xdg-open', pdf_path))
            
            except Exception as e:
                logger.error(f"PDF 파일 열기 실패: {str(e)}")
                messagebox.showerror("파일 열기 실패", f"PDF 파일을 열지 못했습니다:\n{str(e)}")
    
    def _on_download_complete(self, paper_id=None, file_path=None):
        """다운로드 완료 이벤트 핸들러"""
        if file_path:
            self.status_text.set(f"다운로드 완료: {os.path.basename(file_path)}")
            self.progress_var.set(100)
    
    def _copy_citation(self):
        """선택된 논문 인용 정보 복사"""
        selected_items = self.results_tree.selection()
        
        if not selected_items:
            messagebox.showinfo("알림", "인용할 논문을 선택하세요.")
            return
        
        # 선택된 항목 인덱스
        item = selected_items[0]
        idx = self.results_tree.index(item)
        
        if idx >= len(self.search_results):
            return
        
        # 선택된 논문 정보
        paper = self.search_results[idx]
        
        # BibTeX 인용 정보 생성
        try:
            authors = " and ".join([author.get("name", "").replace(" ", ", ") for author in paper.get("authors", [])])
            title = paper.get("title", "").replace("\n", " ")
            year = paper.get("published", "")[:4]  # 첫 4자리 (연도)
            paper_id = paper.get("id", "").split("/")[-1]  # ID의 마지막 부분
            
            bibtex = f"@article{{{paper_id},\n"
            bibtex += f"  author = {{{authors}}},\n"
            bibtex += f"  title = {{{title}}},\n"
            bibtex += f"  journal = {{arXiv preprint arXiv:{paper_id}}},\n"
            bibtex += f"  year = {{{year}}},\n"
            bibtex += f"  url = {{https://arxiv.org/abs/{paper_id}}}\n"
            bibtex += "}"
            
            # 클립보드에 복사
            self.clipboard_clear()
            self.clipboard_append(bibtex)
            
            # 상태 업데이트
            self.status_text.set("인용 정보 복사됨")
            messagebox.showinfo("복사 완료", "BibTeX 인용 정보가 클립보드에 복사되었습니다.")
        
        except Exception as e:
            logger.error(f"인용 정보 생성 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"인용 정보를 생성할 수 없습니다:\n{str(e)}")
    
    def _add_to_vector_db(self):
        """선택된 논문을 벡터 DB에 추가"""
        selected_items = self.results_tree.selection()
        
        if not selected_items:
            messagebox.showinfo("알림", "벡터 DB에 추가할 논문을 선택하세요.")
            return
        
        # 벡터 DB 사용 가능 여부 확인
        if not hasattr(self.arxiv_manager, "vector_db") or not self.arxiv_manager.vector_db:
            messagebox.showerror("오류", "벡터 DB가 초기화되지 않았습니다.")
            return
        
        # 선택된 모든 항목에 대해 처리
        added_count = 0
        
        for item in selected_items:
            idx = self.results_tree.index(item)
            
            if idx >= len(self.search_results):
                continue
            
            # 선택된 논문 정보
            paper = self.search_results[idx]
            
            # 벡터 DB에 추가
            try:
                document_id = self.arxiv_manager._add_to_vector_db(paper)
                
                if document_id:
                    added_count += 1
            
            except Exception as e:
                logger.error(f"벡터 DB 추가 중 오류 발생: {str(e)}")
                messagebox.showerror("오류", f"벡터 DB에 추가하는 중 오류가 발생했습니다:\n{str(e)}")
                break
        
        # 결과 메시지
        if added_count > 0:
            self.status_text.set(f"{added_count}개 논문을 벡터 DB에 추가함")
            messagebox.showinfo("추가 완료", f"{added_count}개 논문이 벡터 DB에 추가되었습니다.")
        else:
            self.status_text.set("벡터 DB에 추가 실패")
    
    def _add_to_conversation(self):
        """선택된 논문 정보를 대화에 추가"""
        selected_items = self.results_tree.selection()
        
        if not selected_items:
            messagebox.showinfo("알림", "대화에 추가할 논문을 선택하세요.")
            return
        
        # 선택된 항목 인덱스
        item = selected_items[0]
        idx = self.results_tree.index(item)
        
        if idx >= len(self.search_results):
            return
        
        # 선택된 논문 정보
        paper = self.search_results[idx]
        
        # 대화에 추가할 텍스트 생성
        title = paper.get("title", "").replace("\n", " ")
        authors = ", ".join([author.get("name", "") for author in paper.get("authors", [])])
        abstract = paper.get("abstract", "").replace("\n", " ")
        paper_id = paper.get("id", "")
        
        text = f"논문: {title}\n"
        text += f"저자: {authors}\n"
        text += f"arXiv ID: {paper_id}\n\n"
        text += f"초록: {abstract}\n\n"
        text += f"URL: https://arxiv.org/abs/{paper_id.split('/')[-1]}"
        
        # 이벤트 발행 (현재 대화에 추가)
        publish("conversation.add_reference", text=text)
        
        # 상태 업데이트
        self.status_text.set("논문 정보를 대화에 추가함")
        messagebox.showinfo("추가 완료", "논문 정보가 현재 대화에 추가되었습니다.")
    
    def _create_collection(self):
        """새 컬렉션 생성"""
        # 컬렉션 이름 입력 창
        name = simpledialog.askstring("새 컬렉션", "컬렉션 이름:", parent=self)
        
        if not name:
            return
        
        # 컬렉션 설명 입력 창
        description = simpledialog.askstring("컬렉션 설명", "설명 (선택사항):", parent=self) or ""
        
        # 컬렉션 생성
        try:
            collection_path = self.arxiv_manager.create_collection(name, description)
            
            if collection_path:
                self.status_text.set(f"컬렉션 생성됨: {name}")
                messagebox.showinfo("생성 완료", f"컬렉션 '{name}'이(가) 생성되었습니다.")
                
                # 컬렉션 목록 새로고침
                self._load_collections()
            else:
                messagebox.showerror("오류", "컬렉션을 생성할 수 없습니다.")
        
        except Exception as e:
            logger.error(f"컬렉션 생성 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"컬렉션 생성 중 오류가 발생했습니다:\n{str(e)}")
    
    def _add_to_collection(self):
        """선택된 논문을 컬렉션에 추가"""
        # 논문 선택 확인
        selected_papers = self.results_tree.selection()
        
        if not selected_papers:
            messagebox.showinfo("알림", "컬렉션에 추가할 논문을 선택하세요.")
            return
        
        # 컬렉션 선택 확인
        selected_collections = self.collections_tree.selection()
        
        if not selected_collections:
            messagebox.showinfo("알림", "논문을 추가할 컬렉션을 선택하세요.")
            return
        
        # 컬렉션 ID 가져오기 (이름 기반)
        collection_item = selected_collections[0]
        collection_name = self.collections_tree.item(collection_item, "values")[0]
        collection_id = collection_name.lower().replace(" ", "_")
        
        # 선택된 논문 ID 목록
        paper_ids = []
        
        for item in selected_papers:
            idx = self.results_tree.index(item)
            
            if idx < len(self.search_results):
                paper_id = self.search_results[idx].get("id", "")
                
                if paper_id:
                    paper_ids.append(paper_id)
        
        if not paper_ids:
            messagebox.showinfo("알림", "유효한 논문을 선택하세요.")
            return
        
        # 컬렉션에 논문 추가
        try:
            success = self.arxiv_manager.add_to_collection(collection_id, paper_ids)
            
            if success:
                self.status_text.set(f"{len(paper_ids)}개 논문이 컬렉션에 추가됨")
                messagebox.showinfo("추가 완료", f"{len(paper_ids)}개 논문이 '{collection_name}' 컬렉션에 추가되었습니다.")
                
                # 컬렉션 목록 새로고침
                self._load_collections()
            else:
                messagebox.showerror("오류", "논문을 컬렉션에 추가할 수 없습니다.")
        
        except Exception as e:
            logger.error(f"컬렉션에 논문 추가 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"논문 추가 중 오류가 발생했습니다:\n{str(e)}")
    
    def _delete_collection(self):
        """선택된 컬렉션 삭제"""
        selected_items = self.collections_tree.selection()
        
        if not selected_items:
            messagebox.showinfo("알림", "삭제할 컬렉션을 선택하세요.")
            return
        
        # 삭제 확인
        if not messagebox.askyesno("삭제 확인", "선택한 컬렉션을 삭제하시겠습니까?"):
            return
        
        # 컬렉션 삭제
        for item in selected_items:
            collection_name = self.collections_tree.item(item, "values")[0]
            collection_id = collection_name.lower().replace(" ", "_")
            
            try:
                success = self.arxiv_manager.delete_collection(collection_id)
                
                if success:
                    self.status_text.set(f"컬렉션 삭제됨: {collection_name}")
                else:
                    messagebox.showerror("오류", f"컬렉션 '{collection_name}'을(를) 삭제할 수 없습니다.")
            
            except Exception as e:
                logger.error(f"컬렉션 삭제 중 오류 발생: {str(e)}")
                messagebox.showerror("오류", f"컬렉션 삭제 중 오류가 발생했습니다:\n{str(e)}")
        
        # 컬렉션 목록 새로고침
        self._load_collections()
    
    def _on_collection_select(self, event):
        """컬렉션 선택 시 처리"""
        selected_items = self.collections_tree.selection()
        
        if not selected_items:
            return
        
        # 선택된 컬렉션 이름
        item = selected_items[0]
        collection_name = self.collections_tree.item(item, "values")[0]
        collection_id = collection_name.lower().replace(" ", "_")
        
        # 컬렉션 정보 가져오기
        collection = self.arxiv_manager.get_collection(collection_id)
        
        if not collection:
            return
        
        # 컬렉션 내 논문 로드 및 표시
        paper_ids = collection.get("papers", [])
        
        # 결과 트리 초기화
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 검색 결과 초기화
        self.search_results = []
        
        # 컬렉션 내 각 논문 로드
        for paper_id in paper_ids:
            paper = self.arxiv_manager.get_paper(paper_id)
            
            if paper:
                self.search_results.append(paper)
                
                # 트리에 추가
                title = paper.get("title", "").replace("\n", " ")
                authors = ", ".join([author.get("name", "") for author in paper.get("authors", [])])
                date = paper.get("published", "")
                
                self.results_tree.insert("", tk.END, values=(title, authors, date))
        
        # 상태 업데이트
        self.status_text.set(f"컬렉션 '{collection_name}'에 {len(paper_ids)}개 논문이 있습니다.")
