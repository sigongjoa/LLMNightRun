"""
벡터 DB 검색 탭 컴포넌트

벡터 DB 검색 및 관리를 위한 UI 탭 컴포넌트를 제공합니다.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import threading
from typing import Dict, List, Any, Optional, Tuple

from core.logging import get_logger
from core.events import subscribe, publish
from vector_db import VectorDB, Document

logger = get_logger("gui.components.vector_db_tab")

class VectorDBTab(ttk.Frame):
    """벡터 DB 검색 탭"""
    
    def __init__(self, parent):
        """
        벡터 DB 검색 탭 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, padding="10")
        
        # 변수 초기화
        self.query = tk.StringVar()
        self.selected_document = None
        self.status_text = tk.StringVar(value="준비 완료")
        self.progress_var = tk.DoubleVar(value=0.0)
        self.filter_var = tk.StringVar()
        self.limit_var = tk.IntVar(value=10)
        self.threshold_var = tk.DoubleVar(value=0.5)
        
        # Vector DB 인스턴스
        try:
            self.vector_db = VectorDB()
            logger.info("벡터 DB 초기화됨")
        except Exception as e:
            self.vector_db = None
            logger.error(f"벡터 DB 초기화 실패: {str(e)}")
        
        # UI 구성
        self._create_widgets()
        
        logger.info("벡터 DB 탭 초기화됨")
    
    def _create_widgets(self):
        """UI 구성요소 생성"""
        # 메인 영역 분할
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # === 왼쪽 패널 (설정) ===
        self.left_panel = ttk.Frame(self.paned_window, padding="5")
        self.paned_window.add(self.left_panel, weight=1)
        
        # 검색 설정 프레임
        search_frame = ttk.LabelFrame(self.left_panel, text="검색 설정", padding="10")
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 검색어 입력
        ttk.Label(search_frame, text="검색어:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(search_frame, textvariable=self.query, width=30).grid(
            row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        
        # 필터 입력
        ttk.Label(search_frame, text="필터 (JSON):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(search_frame, textvariable=self.filter_var, width=30).grid(
            row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        
        # 결과 수 입력
        ttk.Label(search_frame, text="결과 수:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(search_frame, from_=1, to=100, textvariable=self.limit_var, width=5).grid(
            row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 임계값 입력
        ttk.Label(search_frame, text="유사도 임계값:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Scale(search_frame, from_=0.0, to=1.0, variable=self.threshold_var, orient=tk.HORIZONTAL).grid(
            row=3, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Label(search_frame, textvariable=self.threshold_var).grid(row=3, column=2, padx=5)
        
        # 검색 버튼
        ttk.Button(search_frame, text="검색", command=self._search).grid(
            row=4, column=0, columnspan=3, sticky=tk.EW, pady=(10, 0))
        
        # DB 정보 프레임
        info_frame = ttk.LabelFrame(self.left_panel, text="DB 정보", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        # DB 정보 텍스트
        self.info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, height=5)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # 관리 프레임
        manage_frame = ttk.LabelFrame(self.left_panel, text="관리", padding="10")
        manage_frame.pack(fill=tk.X, pady=5)
        
        # 파일 추가 버튼
        ttk.Button(manage_frame, text="파일 추가", command=self._add_file).pack(
            fill=tk.X, pady=(0, 5))
        
        # 텍스트 추가 버튼
        ttk.Button(manage_frame, text="텍스트 추가", command=self._add_text).pack(
            fill=tk.X, pady=(0, 5))
        
        # 삭제 버튼
        ttk.Button(manage_frame, text="선택 항목 삭제", command=self._delete_selected).pack(
            fill=tk.X, pady=(0, 5))
        
        # 벡터 DB 초기화 버튼
        ttk.Button(manage_frame, text="벡터 DB 초기화", command=self._reset_db).pack(
            fill=tk.X, pady=(0, 5))
        
        # === 오른쪽 패널 (결과) ===
        self.right_panel = ttk.Frame(self.paned_window, padding="5")
        self.paned_window.add(self.right_panel, weight=2)
        
        # 검색 결과 프레임
        results_frame = ttk.LabelFrame(self.right_panel, text="검색 결과", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # 결과 트리뷰
        self.results_tree = ttk.Treeview(results_frame, columns=("id", "text", "score"), show="headings")
        self.results_tree.heading("id", text="ID")
        self.results_tree.heading("text", text="텍스트")
        self.results_tree.heading("score", text="유사도")
        self.results_tree.column("id", width=80)
        self.results_tree.column("text", width=300)
        self.results_tree.column("score", width=80)
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 결과 트리뷰 스크롤바
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 선택 시 이벤트 바인딩
        self.results_tree.bind("<<TreeviewSelect>>", self._on_result_select)
        
        # 문서 상세 프레임
        detail_frame = ttk.LabelFrame(self.right_panel, text="문서 상세", padding="10")
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 문서 상세 텍스트
        self.detail_text = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True)
        
        # 대화에 추가 버튼
        ttk.Button(detail_frame, text="대화에 추가", command=self._add_to_conversation).pack(
            anchor=tk.E, pady=(5, 0))
        
        # 상태 바
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(status_frame, textvariable=self.status_text).pack(side=tk.RIGHT, padx=(5, 0))
        
        # DB 정보 업데이트
        self._update_db_info()
    
    def refresh(self):
        """데이터 새로고침"""
        self._update_db_info()
        self._clear_results()
    
    def _update_db_info(self):
        """DB 정보 업데이트"""
        if not self.vector_db:
            self.info_text.delete("1.0", tk.END)
            self.info_text.insert(tk.END, "벡터 DB가 초기화되지 않았습니다.")
            return
        
        try:
            # DB 정보 가져오기
            # 실제 구현 시 VectorDB 클래스에 get_stats 등의 메서드 추가 필요
            doc_count = len(self.vector_db.list_documents()) if hasattr(self.vector_db, 'list_documents') else "N/A"
            encoder_name = self.vector_db.encoder.__class__.__name__ if hasattr(self.vector_db, 'encoder') else "기본 인코더"
            dim = self.vector_db.dimension if hasattr(self.vector_db, 'dimension') else "N/A"
            
            # 정보 표시
            self.info_text.delete("1.0", tk.END)
            info_text = f"문서 수: {doc_count}\n"
            info_text += f"인코더: {encoder_name}\n"
            info_text += f"벡터 차원: {dim}\n"
            info_text += f"저장 경로: {self.vector_db.storage_dir if hasattr(self.vector_db, 'storage_dir') else 'N/A'}"
            
            self.info_text.insert(tk.END, info_text)
        
        except Exception as e:
            logger.error(f"DB 정보 업데이트 중 오류 발생: {str(e)}")
            self.info_text.delete("1.0", tk.END)
            self.info_text.insert(tk.END, f"정보 가져오기 실패: {str(e)}")
    
    def _search(self):
        """벡터 DB 검색"""
        if not self.vector_db:
            messagebox.showinfo("알림", "벡터 DB가 초기화되지 않았습니다.")
            return
        
        # 검색어 가져오기
        query = self.query.get().strip()
        
        if not query:
            messagebox.showinfo("알림", "검색어를 입력하세요.")
            return
        
        # 결과 지우기
        self._clear_results()
        
        # 상태 업데이트
        self.status_text.set("검색 중...")
        self.progress_var.set(10)
        
        # 검색 옵션
        limit = self.limit_var.get()
        threshold = self.threshold_var.get()
        
        # 필터 처리
        filter_json = self.filter_var.get().strip()
        filter_metadata = None
        
        if filter_json:
            try:
                import json
                filter_metadata = json.loads(filter_json)
            except json.JSONDecodeError:
                messagebox.showerror("오류", "필터 JSON 형식이 올바르지 않습니다.")
                self.status_text.set("검색 취소됨")
                self.progress_var.set(0)
                return
        
        def do_search():
            try:
                # 검색 실행
                results = self.vector_db.search(
                    query=query,
                    k=limit,
                    threshold=threshold,
                    filter_metadata=filter_metadata
                )
                
                # UI 업데이트 (스레드 안전을 위해 after 사용)
                self.master.after(0, lambda: self._update_results(results))
            
            except Exception as e:
                logger.error(f"검색 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: self._handle_search_error(str(e)))
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_search, daemon=True).start()
    
    def _clear_results(self):
        """검색 결과 지우기"""
        # 결과 트리 지우기
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 상세 정보 지우기
        self.detail_text.delete("1.0", tk.END)
    
    def _update_results(self, results):
        """검색 결과 업데이트"""
        # 상태 업데이트
        self.status_text.set(f"검색 완료: {len(results)}개 결과")
        self.progress_var.set(100)
        
        if not results:
            # 결과 없음 메시지
            self.detail_text.delete("1.0", tk.END)
            self.detail_text.insert(tk.END, "검색 결과가 없습니다.")
            return
        
        # 결과 트리에 추가
        for i, (doc, score) in enumerate(results):
            # 텍스트 축약
            short_text = doc.text[:50] + "..." if len(doc.text) > 50 else doc.text
            
            # 결과 추가
            self.results_tree.insert("", tk.END, values=(
                doc.id,
                short_text,
                f"{score:.4f}"
            ))
    
    def _handle_search_error(self, error_msg):
        """검색 오류 처리"""
        self.status_text.set("검색 실패")
        self.progress_var.set(0)
        messagebox.showerror("검색 오류", f"검색 중 오류가 발생했습니다:\n{error_msg}")
    
    def _on_result_select(self, event):
        """결과 선택 이벤트 처리"""
        selected_items = self.results_tree.selection()
        
        if not selected_items:
            return
        
        # 선택된 항목의 ID 가져오기
        item = selected_items[0]
        doc_id = self.results_tree.item(item, "values")[0]
        
        if not self.vector_db:
            return
        
        # 문서 가져오기
        try:
            document = self.vector_db.get_document(doc_id) if hasattr(self.vector_db, 'get_document') else None
            
            if not document:
                return
            
            # 선택된 문서 저장
            self.selected_document = document
            
            # 상세 정보 표시
            self._show_document_details(document)
            
        except Exception as e:
            logger.error(f"문서 가져오기 중 오류 발생: {str(e)}")
    
    def _show_document_details(self, document):
        """문서 상세 정보 표시"""
        # 상세 정보 텍스트 위젯 지우기
        self.detail_text.delete("1.0", tk.END)
        
        # 기본 정보 추가
        self.detail_text.insert(tk.END, f"문서 ID: {document.id}\n\n")
        self.detail_text.insert(tk.END, "내용:\n")
        self.detail_text.insert(tk.END, document.text)
        self.detail_text.insert(tk.END, "\n\n")
        
        # 메타데이터 추가 (있는 경우)
        if document.metadata:
            self.detail_text.insert(tk.END, "메타데이터:\n")
            
            import json
            meta_text = json.dumps(document.metadata, ensure_ascii=False, indent=2)
            self.detail_text.insert(tk.END, meta_text)
    
    def _add_file(self):
        """파일 추가"""
        if not self.vector_db:
            messagebox.showinfo("알림", "벡터 DB가 초기화되지 않았습니다.")
            return
        
        # 파일 선택
        file_paths = filedialog.askopenfilenames(
            title="추가할 파일 선택",
            filetypes=[
                ("텍스트 파일", "*.txt"),
                ("마크다운 파일", "*.md"),
                ("JSON 파일", "*.json"),
                ("모든 파일", "*.*")
            ]
        )
        
        if not file_paths:
            return
        
        # 메타데이터 입력 창
        metadata_window = tk.Toplevel(self)
        metadata_window.title("메타데이터 입력")
        metadata_window.geometry("400x300")
        metadata_window.transient(self)
        metadata_window.grab_set()
        
        # 메타데이터 프레임
        metadata_frame = ttk.Frame(metadata_window, padding="10")
        metadata_frame.pack(fill=tk.BOTH, expand=True)
        
        # 메타데이터 라벨
        ttk.Label(metadata_frame, text="메타데이터 (JSON 형식):", 
                 font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # 메타데이터 텍스트 입력
        metadata_text = scrolledtext.ScrolledText(metadata_frame, wrap=tk.WORD, height=10)
        metadata_text.insert(tk.END, '{\n  "source": "file",\n  "type": "document"\n}')
        metadata_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 체크 버튼
        chunk_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(metadata_frame, text="파일을 청크로 분할", variable=chunk_var).pack(anchor=tk.W)
        
        chunk_size_var = tk.IntVar(value=1000)
        chunk_frame = ttk.Frame(metadata_frame)
        chunk_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(chunk_frame, text="청크 크기:").pack(side=tk.LEFT)
        ttk.Spinbox(chunk_frame, from_=100, to=5000, increment=100, textvariable=chunk_size_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # 버튼 프레임
        button_frame = ttk.Frame(metadata_frame)
        button_frame.pack(fill=tk.X)
        
        # 취소 및 추가 버튼
        ttk.Button(button_frame, text="취소", command=metadata_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="추가", command=lambda: self._process_files(
            file_paths, metadata_text.get("1.0", tk.END), chunk_var.get(), chunk_size_var.get(), metadata_window
        )).pack(side=tk.RIGHT, padx=5)
    
    def _process_files(self, file_paths, metadata_text, chunk, chunk_size, window):
        """파일 처리 및 벡터 DB에 추가"""
        # 메타데이터 파싱
        try:
            import json
            metadata = json.loads(metadata_text)
            
        except json.JSONDecodeError as e:
            messagebox.showerror("오류", f"메타데이터 JSON 파싱 오류: {str(e)}", parent=window)
            return
        
        # 창 닫기
        window.destroy()
        
        # 상태 업데이트
        self.status_text.set("파일 처리 중...")
        self.progress_var.set(10)
        
        def do_process():
            try:
                total_files = len(file_paths)
                added_count = 0
                
                for i, file_path in enumerate(file_paths):
                    # 파일 읽기
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 파일별 메타데이터
                    file_metadata = metadata.copy()
                    file_metadata["filename"] = os.path.basename(file_path)
                    file_metadata["path"] = file_path
                    
                    # 청크 처리
                    if chunk and len(content) > chunk_size:
                        chunks = self._split_text_to_chunks(content, chunk_size)
                        
                        for j, chunk_text in enumerate(chunks):
                            # 청크별 메타데이터
                            chunk_metadata = file_metadata.copy()
                            chunk_metadata["chunk_index"] = j
                            chunk_metadata["total_chunks"] = len(chunks)
                            
                            # 벡터 DB에 추가
                            self.vector_db.add(chunk_text, metadata=chunk_metadata)
                            added_count += 1
                    else:
                        # 벡터 DB에 추가
                        self.vector_db.add(content, metadata=file_metadata)
                        added_count += 1
                    
                    # 진행률 업데이트
                    progress = 10 + int(80 * (i + 1) / total_files)
                    self.master.after(0, lambda p=progress: self.progress_var.set(p))
                
                # UI 업데이트
                self.master.after(0, lambda: self._handle_files_processed(added_count, total_files))
                
            except Exception as e:
                logger.error(f"파일 처리 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: self._handle_process_error(str(e)))
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_process, daemon=True).start()
    
    def _split_text_to_chunks(self, text, chunk_size):
        """텍스트를 청크로 분할"""
        # 간단하게 문자 단위로 분할
        # 실제로는 문장이나 단락 단위로 분할하는 것이 좋음
        chunks = []
        current_chunk = ""
        
        # 줄 단위 분할
        lines = text.splitlines()
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 > chunk_size:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _handle_files_processed(self, added_count, total_files):
        """파일 처리 완료 처리"""
        self.status_text.set(f"처리 완료: {added_count} 항목 추가됨")
        self.progress_var.set(100)
        
        # DB 정보 업데이트
        self._update_db_info()
        
        # 메시지 표시
        messagebox.showinfo("처리 완료", f"{total_files}개 파일에서 {added_count}개 항목이 추가되었습니다.")
    
    def _handle_process_error(self, error_msg):
        """처리 오류 처리"""
        self.status_text.set("처리 실패")
        self.progress_var.set(0)
        messagebox.showerror("처리 오류", f"파일 처리 중 오류가 발생했습니다:\n{error_msg}")
    
    def _add_text(self):
        """텍스트 추가"""
        if not self.vector_db:
            messagebox.showinfo("알림", "벡터 DB가 초기화되지 않았습니다.")
            return
        
        # 텍스트 입력 창
        text_window = tk.Toplevel(self)
        text_window.title("텍스트 추가")
        text_window.geometry("600x400")
        text_window.transient(self)
        text_window.grab_set()
        
        # 메인 프레임
        main_frame = ttk.Frame(text_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 텍스트 입력
        ttk.Label(main_frame, text="텍스트:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        text_input = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10)
        text_input.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 메타데이터 입력
        ttk.Label(main_frame, text="메타데이터 (JSON):", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        metadata_input = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=5)
        metadata_input.insert(tk.END, '{\n  "source": "manual",\n  "type": "text"\n}')
        metadata_input.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # 취소 및 추가 버튼
        ttk.Button(button_frame, text="취소", command=text_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="추가", command=lambda: self._add_text_to_db(
            text_input.get("1.0", tk.END), metadata_input.get("1.0", tk.END), text_window
        )).pack(side=tk.RIGHT, padx=5)
    
    def _add_text_to_db(self, text, metadata_text, window):
        """텍스트를 벡터 DB에 추가"""
        # 텍스트 확인
        text = text.strip()
        if not text:
            messagebox.showinfo("알림", "추가할 텍스트를 입력하세요.", parent=window)
            return
        
        # 메타데이터 파싱
        try:
            import json
            metadata = json.loads(metadata_text)
            
        except json.JSONDecodeError as e:
            messagebox.showerror("오류", f"메타데이터 JSON 파싱 오류: {str(e)}", parent=window)
            return
        
        # 창 닫기
        window.destroy()
        
        try:
            # 벡터 DB에 추가
            doc_id = self.vector_db.add(text, metadata=metadata)
            
            # DB 정보 업데이트
            self._update_db_info()
            
            # 메시지 표시
            messagebox.showinfo("추가 완료", f"텍스트가 추가되었습니다. (ID: {doc_id})")
            
        except Exception as e:
            logger.error(f"텍스트 추가 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"텍스트 추가 중 오류가 발생했습니다:\n{str(e)}")
    
    def _delete_selected(self):
        """선택한 항목 삭제"""
        if not self.vector_db:
            messagebox.showinfo("알림", "벡터 DB가 초기화되지 않았습니다.")
            return
        
        selected_items = self.results_tree.selection()
        
        if not selected_items:
            messagebox.showinfo("알림", "삭제할 항목을 선택하세요.")
            return
        
        # 확인 메시지
        if not messagebox.askyesno("확인", "선택한 항목을 삭제하시겠습니까?"):
            return
        
        # 각 선택된 항목 삭제
        deleted_count = 0
        
        for item in selected_items:
            doc_id = self.results_tree.item(item, "values")[0]
            
            try:
                # 벡터 DB에서 삭제
                if hasattr(self.vector_db, 'delete'):
                    self.vector_db.delete(doc_id)
                    deleted_count += 1
                    
                    # 트리에서 항목 제거
                    self.results_tree.delete(item)
            
            except Exception as e:
                logger.error(f"항목 삭제 중 오류 발생: {str(e)}")
        
        if deleted_count > 0:
            # DB 정보 업데이트
            self._update_db_info()
            
            # 메시지 표시
            messagebox.showinfo("삭제 완료", f"{deleted_count}개 항목이 삭제되었습니다.")
            
            # 상세 정보 지우기
            self.detail_text.delete("1.0", tk.END)
        else:
            messagebox.showinfo("알림", "삭제된 항목이 없습니다.")
    
    def _reset_db(self):
        """벡터 DB 초기화"""
        if not self.vector_db:
            messagebox.showinfo("알림", "벡터 DB가 초기화되지 않았습니다.")
            return
        
        # 확인 메시지
        if not messagebox.askyesno("확인", "벡터 DB를 초기화하면 모든 데이터가 삭제됩니다. 계속하시겠습니까?",
                                   icon="warning"):
            return
        
        try:
            # 모든 데이터 삭제
            if hasattr(self.vector_db, 'reset'):
                self.vector_db.reset()
            
            # 결과 지우기
            self._clear_results()
            
            # DB 정보 업데이트
            self._update_db_info()
            
            # 메시지 표시
            messagebox.showinfo("초기화 완료", "벡터 DB가 초기화되었습니다.")
            
        except Exception as e:
            logger.error(f"벡터 DB 초기화 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"벡터 DB 초기화 중 오류가 발생했습니다:\n{str(e)}")
    
    def _add_to_conversation(self):
        """선택한 문서를 대화에 추가"""
        if not self.selected_document:
            messagebox.showinfo("알림", "먼저 문서를 선택하세요.")
            return
        
        # 이벤트 발행 (대화 탭에서 처리)
        publish("conversation.add_reference", text=self.selected_document.text)
