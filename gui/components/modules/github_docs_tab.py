"""
GitHub 문서 자동생성 탭 컴포넌트

GitHub 저장소 코드 분석 및 문서 자동 생성을 위한 UI 탭 컴포넌트를 제공합니다.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import threading
from typing import Dict, List, Any, Optional, Tuple

from core.logging import get_logger
from core.events import subscribe, publish
from github_docs.code_analyzer import analyze_repository, get_repository_structure, find_entry_points
from github_docs.templates import get_available_templates, generate_documentation

logger = get_logger("gui.components.github_docs_tab")

class GitHubDocsTab(ttk.Frame):
    """GitHub 문서 자동생성 탭"""
    
    def __init__(self, parent):
        """
        GitHub 문서 탭 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, padding="10")
        
        # 변수 초기화
        self.repo_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.template_var = tk.StringVar()
        self.include_code_snippets = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="준비 완료")
        self.progress_var = tk.DoubleVar(value=0.0)
        
        # 분석 결과 저장
        self.analysis_result = None
        self.repository_structure = None
        
        # UI 구성
        self._create_widgets()
        
        logger.info("GitHub 문서 탭 초기화됨")
    
    def _create_widgets(self):
        """UI 구성요소 생성"""
        # 메인 영역 분할
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # === 왼쪽 패널 (설정) ===
        self.left_panel = ttk.Frame(self.paned_window, padding="5")
        self.paned_window.add(self.left_panel, weight=1)
        
        # 저장소 설정 프레임
        repo_frame = ttk.LabelFrame(self.left_panel, text="저장소 설정", padding="10")
        repo_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 저장소 경로 입력
        ttk.Label(repo_frame, text="저장소 경로:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(repo_frame, textvariable=self.repo_path, width=30).grid(
            row=0, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Button(repo_frame, text="찾기", command=self._browse_repo).grid(
            row=0, column=2, pady=5, padx=5)
        
        # 출력 경로 입력
        ttk.Label(repo_frame, text="출력 경로:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(repo_frame, textvariable=self.output_path, width=30).grid(
            row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Button(repo_frame, text="찾기", command=self._browse_output).grid(
            row=1, column=2, pady=5, padx=5)
        
        # 문서 설정 프레임
        doc_frame = ttk.LabelFrame(self.left_panel, text="문서 설정", padding="10")
        doc_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 템플릿 선택
        ttk.Label(doc_frame, text="문서 템플릿:").grid(row=0, column=0, sticky=tk.W, pady=5)
        template_combo = ttk.Combobox(doc_frame, textvariable=self.template_var, width=20)
        templates = get_available_templates()
        template_combo['values'] = templates
        if templates:
            self.template_var.set(templates[0])
        template_combo.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=5, padx=5)
        
        # 코드 스니펫 포함 여부
        ttk.Checkbutton(doc_frame, text="코드 스니펫 포함", variable=self.include_code_snippets).grid(
            row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # 버튼 영역
        button_frame = ttk.Frame(self.left_panel)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="저장소 분석", command=self._analyze_repository).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="문서 생성", command=self._generate_docs).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="벡터 DB에 추가", command=self._add_to_vector_db).pack(
            side=tk.LEFT, padx=5)
        
        # 저장소 구조 트리
        structure_frame = ttk.LabelFrame(self.left_panel, text="저장소 구조", padding="10")
        structure_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.structure_tree = ttk.Treeview(structure_frame)
        self.structure_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(structure_frame, orient=tk.VERTICAL, command=self.structure_tree.yview)
        self.structure_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === 오른쪽 패널 (결과) ===
        self.right_panel = ttk.Frame(self.paned_window, padding="5")
        self.paned_window.add(self.right_panel, weight=2)
        
        # 분석 결과 프레임
        analysis_frame = ttk.LabelFrame(self.right_panel, text="분석 결과", padding="10")
        analysis_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 분석 결과 탭
        self.result_notebook = ttk.Notebook(analysis_frame)
        self.result_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 결과 요약 탭
        summary_frame = ttk.Frame(self.result_notebook, padding="5")
        self.result_notebook.add(summary_frame, text="요약")
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # 파일 분석 탭
        files_frame = ttk.Frame(self.result_notebook, padding="5")
        self.result_notebook.add(files_frame, text="파일")
        
        self.files_tree = ttk.Treeview(files_frame, columns=("path", "language", "size"), show="headings")
        self.files_tree.heading("path", text="경로")
        self.files_tree.heading("language", text="언어")
        self.files_tree.heading("size", text="크기")
        self.files_tree.column("path", width=200)
        self.files_tree.column("language", width=80)
        self.files_tree.column("size", width=60)
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 함수 목록 탭
        functions_frame = ttk.Frame(self.result_notebook, padding="5")
        self.result_notebook.add(functions_frame, text="함수")
        
        self.functions_tree = ttk.Treeview(functions_frame, columns=("name", "file", "lines"), show="headings")
        self.functions_tree.heading("name", text="함수명")
        self.functions_tree.heading("file", text="파일")
        self.functions_tree.heading("lines", text="줄 수")
        self.functions_tree.column("name", width=150)
        self.functions_tree.column("file", width=150)
        self.functions_tree.column("lines", width=50)
        self.functions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(functions_frame, orient=tk.VERTICAL, command=self.functions_tree.yview)
        self.functions_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 클래스 목록 탭
        classes_frame = ttk.Frame(self.result_notebook, padding="5")
        self.result_notebook.add(classes_frame, text="클래스")
        
        self.classes_tree = ttk.Treeview(classes_frame, columns=("name", "file", "methods"), show="headings")
        self.classes_tree.heading("name", text="클래스명")
        self.classes_tree.heading("file", text="파일")
        self.classes_tree.heading("methods", text="메서드 수")
        self.classes_tree.column("name", width=150)
        self.classes_tree.column("file", width=150)
        self.classes_tree.column("methods", width=70)
        self.classes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(classes_frame, orient=tk.VERTICAL, command=self.classes_tree.yview)
        self.classes_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 미리보기 프레임
        preview_frame = ttk.LabelFrame(self.right_panel, text="문서 미리보기", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # 상태 바
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(status_frame, textvariable=self.status_text).pack(side=tk.RIGHT, padx=(5, 0))
    
    def refresh(self):
        """데이터 새로고침"""
        pass
    
    def _browse_repo(self):
        """저장소 경로 선택"""
        path = filedialog.askdirectory(title="GitHub 저장소 경로 선택")
        if path:
            self.repo_path.set(path)
            
            # 기본 출력 경로 생성
            default_output = os.path.join(path, "docs")
            self.output_path.set(default_output)
    
    def _browse_output(self):
        """출력 경로 선택"""
        path = filedialog.askdirectory(title="문서 출력 경로 선택")
        if path:
            self.output_path.set(path)
    
    def _analyze_repository(self):
        """저장소 분석 수행"""
        repo_path = self.repo_path.get().strip()
        
        if not repo_path:
            messagebox.showinfo("알림", "저장소 경로를 선택하세요.")
            return
        
        if not os.path.isdir(repo_path):
            messagebox.showerror("오류", f"유효한 디렉토리가 아닙니다: {repo_path}")
            return
        
        # UI 초기화
        self._clear_ui()
        
        # 상태 업데이트
        self.status_text.set("저장소 분석 중...")
        self.progress_var.set(10)
        
        def do_analyze():
            try:
                # 저장소 분석
                self.analysis_result = analyze_repository(repo_path)
                
                # 저장소 구조 분석
                self.repository_structure = get_repository_structure(repo_path)
                
                # 진입점 분석
                entry_points = find_entry_points(repo_path)
                
                # UI 업데이트 (스레드 안전을 위해 after 사용)
                self.master.after(0, lambda: self._update_analysis_ui(entry_points))
            
            except Exception as e:
                logger.error(f"저장소 분석 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: self._handle_analysis_error(str(e)))
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_analyze, daemon=True).start()
    
    def _clear_ui(self):
        """UI 컴포넌트 초기화"""
        # 트리 초기화
        for tree in [self.structure_tree, self.files_tree, self.functions_tree, self.classes_tree]:
            for item in tree.get_children():
                tree.delete(item)
        
        # 텍스트 초기화
        self.summary_text.delete("1.0", tk.END)
        self.preview_text.delete("1.0", tk.END)
    
    def _update_analysis_ui(self, entry_points):
        """분석 결과로 UI 업데이트"""
        if not self.analysis_result:
            self.status_text.set("분석 실패")
            return
        
        # 상태 업데이트
        self.status_text.set("분석 완료")
        self.progress_var.set(100)
        
        # 요약 정보 업데이트
        self._update_summary(entry_points)
        
        # 파일 목록 업데이트
        self._update_files_tree()
        
        # 함수 목록 업데이트
        self._update_functions_tree()
        
        # 클래스 목록 업데이트
        self._update_classes_tree()
        
        # 저장소 구조 트리 업데이트
        self._update_structure_tree()
    
    def _handle_analysis_error(self, error_msg):
        """분석 오류 처리"""
        self.status_text.set("분석 실패")
        self.progress_var.set(0)
        messagebox.showerror("분석 오류", f"저장소 분석 중 오류가 발생했습니다:\n{error_msg}")
    
    def _update_summary(self, entry_points):
        """요약 정보 업데이트"""
        if not self.analysis_result:
            return
        
        # 기본 정보 추출
        file_count = self.analysis_result.get("file_count", 0)
        language_stats = self.analysis_result.get("language_stats", {})
        functions = self.analysis_result.get("functions", [])
        classes = self.analysis_result.get("classes", [])
        
        # 요약 텍스트 구성
        summary = f"저장소 경로: {self.analysis_result.get('repo_path', '')}\n\n"
        summary += f"총 파일 수: {file_count}개\n\n"
        
        # 언어 통계
        summary += "언어 통계:\n"
        for lang, count in language_stats.items():
            summary += f"- {lang}: {count}개 파일\n"
        
        summary += f"\n함수 수: {len(functions)}개\n"
        summary += f"클래스 수: {len(classes)}개\n\n"
        
        # 주요 진입점
        if entry_points:
            summary += "주요 진입점:\n"
            for entry in entry_points:
                summary += f"- {entry}\n"
        
        # 텍스트 위젯에 표시
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, summary)
    
    def _update_files_tree(self):
        """파일 목록 트리 업데이트"""
        if not self.analysis_result:
            return
        
        # 파일 통계 추출
        file_stats = self.analysis_result.get("file_stats", [])
        
        # 트리 초기화
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # 파일 추가
        for file_info in file_stats:
            path = file_info.get("path", "")
            language = file_info.get("language", "")
            size = self._format_size(file_info.get("size", 0))
            
            self.files_tree.insert("", tk.END, values=(path, language, size))
    
    def _update_functions_tree(self):
        """함수 목록 트리 업데이트"""
        if not self.analysis_result:
            return
        
        # 함수 목록 추출
        functions = self.analysis_result.get("functions", [])
        
        # 트리 초기화
        for item in self.functions_tree.get_children():
            self.functions_tree.delete(item)
        
        # 함수 추가
        for func_info in functions:
            name = func_info.get("name", "")
            file = func_info.get("file", "")
            lines = func_info.get("line_count", 0)
            
            self.functions_tree.insert("", tk.END, values=(name, file, lines))
    
    def _update_classes_tree(self):
        """클래스 목록 트리 업데이트"""
        if not self.analysis_result:
            return
        
        # 클래스 목록 추출
        classes = self.analysis_result.get("classes", [])
        
        # 트리 초기화
        for item in self.classes_tree.get_children():
            self.classes_tree.delete(item)
        
        # 클래스 추가
        for class_info in classes:
            name = class_info.get("name", "")
            file = class_info.get("file", "")
            methods = len(class_info.get("methods", []))
            
            self.classes_tree.insert("", tk.END, values=(name, file, methods))
    
    def _update_structure_tree(self):
        """저장소 구조 트리 업데이트"""
        if not self.repository_structure:
            return
        
        # 트리 초기화
        for item in self.structure_tree.get_children():
            self.structure_tree.delete(item)
        
        # 루트 노드 추가
        root_node = self.repository_structure
        root_id = self.structure_tree.insert("", tk.END, text=root_node["name"], open=True)
        
        # 재귀적으로 하위 항목 추가
        self._add_structure_node(root_node.get("children", []), root_id)
    
    def _add_structure_node(self, children, parent_id):
        """구조 트리 노드 추가 (재귀)"""
        for child in children:
            name = child["name"]
            node_type = child["type"]
            
            # 아이콘 설정
            if node_type == "directory":
                text = name + "/"
                icon = "folder"
            else:
                text = name
                icon = "file"
            
            # 노드 추가
            child_id = self.structure_tree.insert(parent_id, tk.END, text=text, tags=(icon,))
            
            # 하위 디렉토리가 있으면 재귀 호출
            if node_type == "directory" and "children" in child:
                self._add_structure_node(child["children"], child_id)
    
    def _generate_docs(self):
        """문서 자동 생성"""
        if not self.analysis_result:
            messagebox.showinfo("알림", "먼저 저장소를 분석해야 합니다.")
            return
        
        repo_path = self.repo_path.get().strip()
        output_path = self.output_path.get().strip()
        template = self.template_var.get()
        include_snippets = self.include_code_snippets.get()
        
        if not repo_path or not output_path:
            messagebox.showinfo("알림", "저장소 경로와 출력 경로를 모두 설정하세요.")
            return
        
        if not template:
            messagebox.showinfo("알림", "문서 템플릿을 선택하세요.")
            return
        
        # 출력 디렉토리 확인 및 생성
        os.makedirs(output_path, exist_ok=True)
        
        # 상태 업데이트
        self.status_text.set("문서 생성 중...")
        self.progress_var.set(10)
        
        def do_generate():
            try:
                # 문서 생성 옵션
                options = {
                    "include_code_snippets": include_snippets,
                    "max_code_lines": 50,
                    "include_private": False,
                    "repository_url": None
                }
                
                # 문서 생성
                result = generate_documentation(
                    repo_path=repo_path,
                    output_path=output_path,
                    template_name=template,
                    analysis_result=self.analysis_result,
                    options=options
                )
                
                # 미리보기 업데이트
                self.master.after(0, lambda: self._update_preview(result))
                
            except Exception as e:
                logger.error(f"문서 생성 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: messagebox.showerror(
                    "생성 오류", f"문서 생성 중 오류가 발생했습니다:\n{str(e)}"))
                self.status_text.set("문서 생성 실패")
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_generate, daemon=True).start()
    
    def _update_preview(self, result):
        """문서 미리보기 업데이트"""
        if not result:
            self.status_text.set("문서 생성 실패")
            return
        
        # 상태 업데이트
        self.status_text.set("문서 생성 완료")
        self.progress_var.set(100)
        
        # 생성된 파일 정보 추출
        files = result.get("files", [])
        readme_path = None
        
        # README.md 파일 찾기
        for file_info in files:
            if file_info["name"].lower() == "readme.md":
                readme_path = file_info["path"]
                break
        
        # README.md 내용 표시
        if readme_path and os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                self.preview_text.delete("1.0", tk.END)
                self.preview_text.insert(tk.END, readme_content)
            except Exception as e:
                logger.error(f"README 읽기 실패: {str(e)}")
                self.preview_text.delete("1.0", tk.END)
                self.preview_text.insert(tk.END, f"README 읽기 실패: {str(e)}")
        else:
            # 메시지
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert(tk.END, "생성된 문서 파일:\n\n")
            
            for file_info in files:
                name = file_info["name"]
                path = file_info["path"]
                self.preview_text.insert(tk.END, f"- {name}: {path}\n")
        
        # 성공 메시지
        messagebox.showinfo("생성 완료", f"문서가 성공적으로 생성되었습니다.\n위치: {self.output_path.get()}")
    
    def _add_to_vector_db(self):
        """생성된 문서를 벡터 DB에 추가"""
        if not self.analysis_result:
            messagebox.showinfo("알림", "먼저 저장소를 분석해야 합니다.")
            return
        
        output_path = self.output_path.get().strip()
        
        if not output_path or not os.path.exists(output_path):
            messagebox.showinfo("알림", "먼저 문서를 생성해야 합니다.")
            return
        
        # 벡터 DB 확인
        try:
            from vector_db import VectorDB
            vector_db = VectorDB()
        except Exception as e:
            logger.error(f"벡터 DB 초기화 실패: {str(e)}")
            messagebox.showerror("오류", f"벡터 DB에 접근할 수 없습니다:\n{str(e)}")
            return
        
        # 상태 업데이트
        self.status_text.set("벡터 DB에 추가 중...")
        self.progress_var.set(10)
        
        def do_add_to_db():
            try:
                # 마크다운 파일 찾기
                added_count = 0
                md_files = []
                
                for root, dirs, files in os.walk(output_path):
                    for file in files:
                        if file.endswith(".md"):
                            md_files.append(os.path.join(root, file))
                
                # 진행률 계산을 위한 준비
                total_files = len(md_files)
                if total_files == 0:
                    self.master.after(0, lambda: messagebox.showinfo(
                        "알림", "추가할 마크다운 문서가 없습니다."))
                    self.status_text.set("추가할 문서 없음")
                    self.progress_var.set(0)
                    return
                
                # 각 파일을 벡터 DB에 추가
                for i, file_path in enumerate(md_files):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 메타데이터 생성
                        rel_path = os.path.relpath(file_path, output_path)
                        filename = os.path.basename(file_path)
                        repo_name = os.path.basename(self.repo_path.get().strip())
                        
                        metadata = {
                            "type": "github_docs",
                            "repository": repo_name,
                            "file": filename,
                            "path": rel_path
                        }
                        
                        # 벡터 DB에 추가
                        doc_id = vector_db.add(content, metadata=metadata)
                        
                        if doc_id:
                            added_count += 1
                        
                        # 진행률 업데이트 (10%-90%)
                        progress = 10 + int(80 * (i + 1) / total_files)
                        self.progress_var.set(progress)
                    
                    except Exception as e:
                        logger.error(f"파일 추가 중 오류 발생: {file_path} - {str(e)}")
                
                # 완료 메시지
                self.master.after(0, lambda: self._show_vectordb_result(added_count, total_files))
            
            except Exception as e:
                logger.error(f"벡터 DB 추가 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: messagebox.showerror(
                    "오류", f"벡터 DB에 추가하는 중 오류가 발생했습니다:\n{str(e)}"))
                self.status_text.set("벡터 DB 추가 실패")
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_add_to_db, daemon=True).start()
    
    def _show_vectordb_result(self, added_count, total_files):
        """벡터 DB 추가 결과 표시"""
        self.progress_var.set(100)
        
        if added_count > 0:
            self.status_text.set(f"벡터 DB에 {added_count}개 문서 추가됨")
            messagebox.showinfo("추가 완료", f"{total_files}개 중 {added_count}개 문서가 벡터 DB에 추가되었습니다.")
        else:
            self.status_text.set("벡터 DB에 추가 실패")
            messagebox.showwarning("추가 실패", "문서를 벡터 DB에 추가하지 못했습니다.")
    
    def _format_size(self, size_bytes):
        """바이트 크기를 가독성 있는 형식으로 변환"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
