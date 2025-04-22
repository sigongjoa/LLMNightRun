"""
GitHub AI 설정 탭 컴포넌트

GitHub 저장소의 AI 환경 설정 및 구성을 위한 UI 탭 컴포넌트를 제공합니다.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import threading
import json
from typing import Dict, List, Any, Optional, Tuple

from core.logging import get_logger
from core.events import subscribe, publish
from github_ai_setup.analyzer import analyze_repository, get_ai_config_status
from github_ai_setup.config_generator import generate_ai_config, apply_ai_config
from github_ai_setup.environment import setup_environment, check_environment
from github_ai_setup.manager import GitHubAIManager

logger = get_logger("gui.components.github_ai_setup_tab")

class GitHubAISetupTab(ttk.Frame):
    """GitHub AI 설정 탭"""
    
    def __init__(self, parent):
        """
        GitHub AI 설정 탭 초기화
        
        Args:
            parent: 부모 위젯
        """
        super().__init__(parent, padding="10")
        
        # 변수 초기화
        self.repo_path = tk.StringVar()
        self.framework = tk.StringVar(value="pytorch")
        self.model_type = tk.StringVar(value="classification")
        self.output_format = tk.StringVar(value="json")
        self.status_text = tk.StringVar(value="준비 완료")
        self.progress_var = tk.DoubleVar(value=0.0)
        
        # AI 설정 관리자 초기화
        self.ai_manager = GitHubAIManager()
        
        # 분석 결과 저장
        self.analysis_result = None
        self.config = None
        
        # UI 구성
        self._create_widgets()
        
        logger.info("GitHub AI 설정 탭 초기화됨")
    
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
        
        # GitHub URL 복제 또는 가져오기
        ttk.Label(repo_frame, text="또는 GitHub URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.github_url = ttk.Entry(repo_frame, width=30)
        self.github_url.grid(row=1, column=1, sticky=tk.EW, pady=5, padx=5)
        ttk.Button(repo_frame, text="복제", command=self._clone_repository).grid(
            row=1, column=2, pady=5, padx=5)
        
        # AI 설정 프레임
        ai_frame = ttk.LabelFrame(self.left_panel, text="AI 설정", padding="10")
        ai_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 프레임워크 선택
        ttk.Label(ai_frame, text="프레임워크:").grid(row=0, column=0, sticky=tk.W, pady=5)
        framework_combo = ttk.Combobox(ai_frame, textvariable=self.framework, width=15)
        framework_combo['values'] = (
            "pytorch", "tensorflow", "huggingface", "langchain", "sklearn", "openai"
        )
        framework_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 모델 타입 선택
        ttk.Label(ai_frame, text="모델 타입:").grid(row=1, column=0, sticky=tk.W, pady=5)
        model_type_combo = ttk.Combobox(ai_frame, textvariable=self.model_type, width=15)
        model_type_combo['values'] = (
            "classification", "regression", "generation", "embedding", "reinforcement"
        )
        model_type_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 출력 형식 선택
        ttk.Label(ai_frame, text="출력 형식:").grid(row=2, column=0, sticky=tk.W, pady=5)
        output_format_combo = ttk.Combobox(ai_frame, textvariable=self.output_format, width=15)
        output_format_combo['values'] = ("json", "yaml")
        output_format_combo.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 고급 설정 체크박스
        self.advanced_options = tk.BooleanVar(value=False)
        ttk.Checkbutton(ai_frame, text="고급 설정 사용", variable=self.advanced_options).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 버튼 영역
        button_frame = ttk.Frame(self.left_panel)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="저장소 분석", command=self._analyze_repository).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="AI 설정 생성", command=self._generate_ai_config).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="설정 적용", command=self._apply_ai_config).pack(
            side=tk.LEFT, padx=5)
        
        # 저장소 목록 프레임
        repos_frame = ttk.LabelFrame(self.left_panel, text="관리된 저장소", padding="10")
        repos_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.repos_tree = ttk.Treeview(repos_frame, columns=("name", "has_config", "has_env"), show="headings")
        self.repos_tree.heading("name", text="저장소")
        self.repos_tree.heading("has_config", text="AI 설정")
        self.repos_tree.heading("has_env", text="환경 설정")
        self.repos_tree.column("name", width=150)
        self.repos_tree.column("has_config", width=60)
        self.repos_tree.column("has_env", width=60)
        self.repos_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 저장소 목록 스크롤바
        scrollbar = ttk.Scrollbar(repos_frame, orient=tk.VERTICAL, command=self.repos_tree.yview)
        self.repos_tree.configure(yscrollcommand=scrollbar.set)
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
        
        # 분석 요약 탭
        summary_frame = ttk.Frame(self.result_notebook, padding="5")
        self.result_notebook.add(summary_frame, text="분석")
        
        self.summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        
        # 패키지 목록 탭
        packages_frame = ttk.Frame(self.result_notebook, padding="5")
        self.result_notebook.add(packages_frame, text="패키지")
        
        self.packages_tree = ttk.Treeview(packages_frame, columns=("name", "type"), show="headings")
        self.packages_tree.heading("name", text="패키지 이름")
        self.packages_tree.heading("type", text="유형")
        self.packages_tree.column("name", width=200)
        self.packages_tree.column("type", width=100)
        self.packages_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(packages_frame, orient=tk.VERTICAL, command=self.packages_tree.yview)
        self.packages_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 환경 상태 탭
        env_frame = ttk.Frame(self.result_notebook, padding="5")
        self.result_notebook.add(env_frame, text="환경")
        
        self.env_text = scrolledtext.ScrolledText(env_frame, wrap=tk.WORD)
        self.env_text.pack(fill=tk.BOTH, expand=True)
        
        # AI 설정 미리보기 프레임
        config_frame = ttk.LabelFrame(self.right_panel, text="AI 설정 미리보기", padding="10")
        config_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.config_text = scrolledtext.ScrolledText(config_frame, wrap=tk.WORD)
        self.config_text.pack(fill=tk.BOTH, expand=True)
        
        # 상태 바
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(status_frame, textvariable=self.status_text).pack(side=tk.RIGHT, padx=(5, 0))
    
    def refresh(self):
        """데이터 새로고침"""
        # 저장소 목록 로드
        self._load_repositories()
    
    def _browse_repo(self):
        """저장소 경로 선택"""
        path = filedialog.askdirectory(title="GitHub 저장소 경로 선택")
        if path:
            self.repo_path.set(path)
    
    def _clone_repository(self):
        """GitHub URL에서 저장소 복제"""
        url = self.github_url.get().strip()
        
        if not url:
            messagebox.showinfo("알림", "GitHub URL을 입력하세요.")
            return
        
        # URL 형식 확인
        if not url.startswith(("https://github.com/", "git@github.com:")):
            messagebox.showinfo("알림", "유효한 GitHub URL을 입력하세요.")
            return
        
        # 상태 업데이트
        self.status_text.set("저장소 복제 중...")
        self.progress_var.set(10)
        
        def do_clone():
            try:
                # 저장소 복제
                repo_path = self.ai_manager.clone_repository(url)
                
                if repo_path:
                    # UI 스레드에서 업데이트
                    self.master.after(0, lambda: self._update_after_clone(repo_path))
                else:
                    # UI 스레드에서 업데이트
                    self.master.after(0, lambda: messagebox.showerror(
                        "복제 실패", "저장소를 복제할 수 없습니다."))
                    self.status_text.set("복제 실패")
            
            except Exception as e:
                logger.error(f"저장소 복제 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: messagebox.showerror(
                    "복제 오류", f"저장소 복제 중 오류가 발생했습니다:\n{str(e)}"))
                self.status_text.set("복제 실패")
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_clone, daemon=True).start()
    
    def _update_after_clone(self, repo_path):
        """복제 완료 후 UI 업데이트"""
        # 저장소 경로 설정
        self.repo_path.set(repo_path)
        
        # 상태 업데이트
        self.status_text.set("저장소 복제 완료")
        self.progress_var.set(100)
        
        # 저장소 목록 새로고침
        self._load_repositories()
        
        # 성공 메시지
        messagebox.showinfo("복제 완료", f"저장소가 성공적으로 복제되었습니다:\n{repo_path}")
        
        # 자동으로 분석 실행
        self._analyze_repository()
    
    def _load_repositories(self):
        """관리된 저장소 목록 로드"""
        # 트리 초기화
        for item in self.repos_tree.get_children():
            self.repos_tree.delete(item)
        
        # 저장소 목록 가져오기
        repositories = self.ai_manager.list_repositories()
        
        # 트리에 추가
        for repo in repositories:
            name = repo.get("name", "")
            has_config = "O" if repo.get("has_config", False) else "X"
            has_env = "O" if repo.get("has_environment", False) else "X"
            
            self.repos_tree.insert("", tk.END, values=(name, has_config, has_env))
        
        # 저장소 선택 이벤트 바인딩
        self.repos_tree.bind("<<TreeviewSelect>>", self._on_repository_select)
    
    def _on_repository_select(self, event):
        """저장소 목록에서 선택 시 처리"""
        selected_items = self.repos_tree.selection()
        
        if not selected_items:
            return
        
        # 선택된 항목 가져오기
        item = selected_items[0]
        repo_name = self.repos_tree.item(item, "values")[0]
        
        # 저장소 목록에서 경로 찾기
        repositories = self.ai_manager.list_repositories()
        selected_repo = None
        
        for repo in repositories:
            if repo.get("name") == repo_name:
                selected_repo = repo
                break
        
        if not selected_repo:
            return
        
        # 경로 설정
        repo_path = selected_repo.get("path", "")
        if repo_path:
            self.repo_path.set(repo_path)
            
            # 자동으로 분석 수행
            self._analyze_repository()
    
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
                self.analysis_result = self.ai_manager.analyze_repository(repo_path)
                
                if "error" in self.analysis_result:
                    # UI 스레드에서 업데이트
                    self.master.after(0, lambda: self._handle_analysis_error(self.analysis_result["error"]))
                    return
                
                # 환경 확인
                env_status = check_environment(repo_path)
                
                # UI 업데이트 (스레드 안전을 위해 after 사용)
                self.master.after(0, lambda: self._update_analysis_ui(env_status))
            
            except Exception as e:
                logger.error(f"저장소 분석 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: self._handle_analysis_error(str(e)))
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_analyze, daemon=True).start()
    
    def _clear_ui(self):
        """UI 컴포넌트 초기화"""
        # 트리 초기화
        for item in self.packages_tree.get_children():
            self.packages_tree.delete(item)
        
        # 텍스트 초기화
        self.summary_text.delete("1.0", tk.END)
        self.env_text.delete("1.0", tk.END)
        self.config_text.delete("1.0", tk.END)
    
    def _update_analysis_ui(self, env_status):
        """분석 결과로 UI 업데이트"""
        if not self.analysis_result:
            self.status_text.set("분석 실패")
            return
        
        # 상태 업데이트
        self.status_text.set("분석 완료")
        self.progress_var.set(100)
        
        # 요약 정보 업데이트
        self._update_summary()
        
        # 패키지 목록 업데이트
        self._update_packages_tree()
        
        # 환경 상태 업데이트
        self._update_environment_info(env_status)
        
        # 프레임워크 자동 선택
        self._auto_select_framework()
    
    def _handle_analysis_error(self, error_msg):
        """분석 오류 처리"""
        self.status_text.set("분석 실패")
        self.progress_var.set(0)
        messagebox.showerror("분석 오류", f"저장소 분석 중 오류가 발생했습니다:\n{error_msg}")
    
    def _update_summary(self):
        """요약 정보 업데이트"""
        if not self.analysis_result:
            return
        
        # 기본 정보 추출
        ai_score = self.analysis_result.get("ai_score", 0)
        has_ai = self.analysis_result.get("has_ai_components", False)
        recommendations = self.analysis_result.get("recommendations", [])
        
        # 패키지 및 파일 정보
        ai_packages = self.analysis_result.get("ai_packages", [])
        data_files = len(self.analysis_result.get("data_files", []))
        model_files = len(self.analysis_result.get("model_files", []))
        notebook_files = len(self.analysis_result.get("notebook_files", []))
        
        # 요약 텍스트 구성
        summary = f"저장소 경로: {self.analysis_result.get('repo_path', '')}\n\n"
        summary += f"AI 점수: {ai_score:.1f}/100 "
        summary += f"({'AI 구성 요소 있음' if has_ai else 'AI 구성 요소 없음'})\n\n"
        
        summary += f"AI 패키지: {len(ai_packages)}개\n"
        summary += f"데이터 파일: {data_files}개\n"
        summary += f"모델 파일: {model_files}개\n"
        summary += f"노트북 파일: {notebook_files}개\n\n"
        
        # 권장 사항
        if recommendations:
            summary += "권장 사항:\n"
            for rec in recommendations:
                summary += f"- {rec}\n"
        
        # 텍스트 위젯에 표시
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, summary)
    
    def _update_packages_tree(self):
        """패키지 목록 트리 업데이트"""
        if not self.analysis_result:
            return
        
        # 패키지 목록 추출
        packages = self.analysis_result.get("ai_packages", [])
        
        # 트리 초기화
        for item in self.packages_tree.get_children():
            self.packages_tree.delete(item)
        
        # 패키지 분류
        ml_frameworks = ["tensorflow", "torch", "pytorch", "keras", "sklearn", 
                       "scikit-learn", "xgboost", "lightgbm", "catboost"]
        
        llm_packages = ["transformers", "huggingface", "langchain", "openai", 
                       "llama-index", "gpt4all"]
        
        data_packages = ["numpy", "pandas", "scipy", "matplotlib", "seaborn", 
                        "plotly", "bokeh"]
        
        nlp_packages = ["nltk", "spacy", "gensim", "transformers"]
        
        # 패키지 추가
        for pkg in packages:
            pkg_type = "기타"
            
            if any(fw in pkg.lower() for fw in ml_frameworks):
                pkg_type = "ML 프레임워크"
            elif any(lm in pkg.lower() for lm in llm_packages):
                pkg_type = "LLM 도구"
            elif any(dp in pkg.lower() for dp in data_packages):
                pkg_type = "데이터 도구"
            elif any(nlp in pkg.lower() for nlp in nlp_packages):
                pkg_type = "NLP 도구"
            
            self.packages_tree.insert("", tk.END, values=(pkg, pkg_type))
    
    def _update_environment_info(self, env_status):
        """환경 상태 정보 업데이트"""
        if not env_status:
            return
        
        # 환경 정보 추출
        env_files = env_status.get("environment_files", [])
        python_version = env_status.get("python_version", "알 수 없음")
        cuda_available = env_status.get("cuda_available", False)
        missing_packages = env_status.get("missing_packages", [])
        
        # 환경 텍스트 구성
        env_text = f"현재 Python 버전: {python_version}\n"
        env_text += f"CUDA 사용 가능: {'예' if cuda_available else '아니오'}\n\n"
        
        # 환경 파일
        if env_files:
            env_text += "환경 설정 파일:\n"
            for file in env_files:
                env_text += f"- {file}\n"
        else:
            env_text += "환경 설정 파일 없음\n"
        
        env_text += "\n"
        
        # 패키지 정보
        required = env_status.get("required_packages", [])
        if required:
            env_text += f"필수 패키지 ({len(required)}개):\n"
            for pkg in required[:10]:  # 처음 10개만 표시
                env_text += f"- {pkg}\n"
            
            if len(required) > 10:
                env_text += f"  ... 외 {len(required) - 10}개\n"
            
            env_text += "\n"
        
        # 누락된 패키지
        if missing_packages:
            env_text += f"누락된 패키지 ({len(missing_packages)}개):\n"
            for pkg in missing_packages:
                env_text += f"- {pkg}\n"
        
        # 텍스트 위젯에 표시
        self.env_text.delete("1.0", tk.END)
        self.env_text.insert(tk.END, env_text)
    
    def _auto_select_framework(self):
        """분석 결과에 따라 프레임워크 자동 선택"""
        if not self.analysis_result:
            return
        
        packages = [pkg.lower() for pkg in self.analysis_result.get("ai_packages", [])]
        
        # 프레임워크 감지
        if any(fw in packages for fw in ["torch", "pytorch"]):
            self.framework.set("pytorch")
        elif any(fw in packages for fw in ["tensorflow", "keras"]):
            self.framework.set("tensorflow")
        elif "transformers" in packages or "huggingface" in packages:
            self.framework.set("huggingface")
        elif "langchain" in packages:
            self.framework.set("langchain")
        elif any(fw in packages for fw in ["sklearn", "scikit-learn"]):
            self.framework.set("sklearn")
        elif "openai" in packages:
            self.framework.set("openai")
        
        # 모델 타입 감지
        if any(name.endswith("classifier") for name in packages):
            self.model_type.set("classification")
        elif any(name.endswith("regressor") for name in packages):
            self.model_type.set("regression")
        elif any(gen in packages for gen in ["gpt", "llm", "generative"]):
            self.model_type.set("generation")
        elif any(emb in packages for emb in ["embedding", "encoder", "sentence-transformers"]):
            self.model_type.set("embedding")
    
    def _generate_ai_config(self):
        """AI 설정 생성"""
        if not self.analysis_result:
            messagebox.showinfo("알림", "먼저 저장소를 분석해야 합니다.")
            return
        
        repo_path = self.repo_path.get().strip()
        framework = self.framework.get()
        model_type = self.model_type.get()
        
        # 추가 파라미터 설정 (고급 옵션 활성화 시)
        parameters = None
        if self.advanced_options.get():
            # 고급 설정 대화상자 표시
            parameters = self._show_advanced_dialog()
            
            # 취소된 경우
            if parameters is None:
                return
        
        # 상태 업데이트
        self.status_text.set("AI 설정 생성 중...")
        self.progress_var.set(10)
        
        def do_generate():
            try:
                # 설정 생성
                self.config = self.ai_manager.generate_config(
                    repo_path=repo_path,
                    framework=framework,
                    model_type=model_type,
                    parameters=parameters
                )
                
                if "error" in self.config:
                    # UI 스레드에서 업데이트
                    self.master.after(0, lambda: self._handle_generation_error(self.config["error"]))
                    return
                
                # UI 업데이트 (스레드 안전을 위해 after 사용)
                self.master.after(0, lambda: self._update_config_preview())
            
            except Exception as e:
                logger.error(f"AI 설정 생성 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: self._handle_generation_error(str(e)))
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_generate, daemon=True).start()
    
    def _show_advanced_dialog(self):
        """고급 설정 대화상자 표시"""
        # 대화상자 생성
        dialog = tk.Toplevel(self)
        dialog.title("고급 AI 설정")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # 초기 설정
        params = {
            "learning_rate": tk.DoubleVar(value=0.001),
            "batch_size": tk.IntVar(value=32),
            "epochs": tk.IntVar(value=10),
            "optimizer": tk.StringVar(value="adam"),
            "temperature": tk.DoubleVar(value=0.7),
            "max_tokens": tk.IntVar(value=500)
        }
        
        # 결과 변수
        result = {}
        
        # 입력 프레임
        input_frame = ttk.Frame(dialog, padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        # 기본 ML 설정
        ttk.Label(input_frame, text="ML 설정:", font=("TkDefaultFont", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # 학습률
        ttk.Label(input_frame, text="학습률:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=params["learning_rate"], width=10).grid(
            row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 배치 크기
        ttk.Label(input_frame, text="배치 크기:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=params["batch_size"], width=10).grid(
            row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 에포크
        ttk.Label(input_frame, text="에포크:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=params["epochs"], width=10).grid(
            row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 옵티마이저
        ttk.Label(input_frame, text="옵티마이저:").grid(row=4, column=0, sticky=tk.W, pady=5)
        optimizer_combo = ttk.Combobox(input_frame, textvariable=params["optimizer"], width=10)
        optimizer_combo["values"] = ("adam", "sgd", "rmsprop", "adagrad")
        optimizer_combo.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
        
        # LLM 설정
        ttk.Label(input_frame, text="LLM 설정:", font=("TkDefaultFont", 10, "bold")).grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        # 온도
        ttk.Label(input_frame, text="온도:").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=params["temperature"], width=10).grid(
            row=6, column=1, sticky=tk.W, pady=5, padx=5)
        
        # 최대 토큰
        ttk.Label(input_frame, text="최대 토큰:").grid(row=7, column=0, sticky=tk.W, pady=5)
        ttk.Entry(input_frame, textvariable=params["max_tokens"], width=10).grid(
            row=7, column=1, sticky=tk.W, pady=5, padx=5)
        
        # JSON 직접 편집
        ttk.Label(input_frame, text="추가 설정 (JSON):", font=("TkDefaultFont", 10, "bold")).grid(
            row=8, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        json_text = scrolledtext.ScrolledText(input_frame, height=8, width=40)
        json_text.grid(row=9, column=0, columnspan=2, sticky=tk.EW, pady=5)
        json_text.insert(tk.END, "{}")
        
        # 버튼 프레임
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.pack(fill=tk.X)
        
        # 확인 버튼 처리
        def on_ok():
            try:
                # 기본 파라미터 가져오기
                result["learning_rate"] = params["learning_rate"].get()
                result["batch_size"] = params["batch_size"].get()
                result["epochs"] = params["epochs"].get()
                result["optimizer"] = params["optimizer"].get()
                
                # 프레임워크 및 모델 타입에 따라 추가 파라미터 선택
                if self.framework.get() in ["langchain", "openai"] or self.model_type.get() == "generation":
                    result["temperature"] = params["temperature"].get()
                    result["max_tokens"] = params["max_tokens"].get()
                
                # 추가 JSON 파라미터 파싱
                json_str = json_text.get("1.0", tk.END).strip()
                if json_str and json_str != "{}":
                    try:
                        additional_params = json.loads(json_str)
                        result.update(additional_params)
                    except json.JSONDecodeError:
                        messagebox.showerror("JSON 오류", "추가 설정의 JSON 형식이 잘못되었습니다.", parent=dialog)
                        return
                
                # 대화상자 닫기
                dialog.destroy()
            
            except Exception as e:
                messagebox.showerror("입력 오류", f"파라미터 값을 확인하세요: {str(e)}", parent=dialog)
        
        # 버튼 추가
        ttk.Button(button_frame, text="확인", command=on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="취소", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 대화상자가 닫힐 때까지 대기
        self.wait_window(dialog)
        
        # 취소된 경우 None 반환
        if not result:
            return None
        
        return result
    
    def _handle_generation_error(self, error_msg):
        """설정 생성 오류 처리"""
        self.status_text.set("설정 생성 실패")
        self.progress_var.set(0)
        messagebox.showerror("생성 오류", f"AI 설정 생성 중 오류가 발생했습니다:\n{error_msg}")
    
    def _update_config_preview(self):
        """설정 미리보기 업데이트"""
        if not self.config:
            self.status_text.set("설정 생성 실패")
            return
        
        # 상태 업데이트
        self.status_text.set("AI 설정 생성 완료")
        self.progress_var.set(100)
        
        # JSON 문자열로 변환
        try:
            config_str = json.dumps(self.config, indent=2, ensure_ascii=False)
            
            # 텍스트 위젯에 표시
            self.config_text.delete("1.0", tk.END)
            self.config_text.insert(tk.END, config_str)
        
        except Exception as e:
            logger.error(f"설정 미리보기 생성 중 오류 발생: {str(e)}")
            self.config_text.delete("1.0", tk.END)
            self.config_text.insert(tk.END, f"설정 미리보기 생성 실패: {str(e)}")
    
    def _apply_ai_config(self):
        """AI 설정 적용"""
        if not self.config:
            messagebox.showinfo("알림", "먼저 AI 설정을 생성해야 합니다.")
            return
        
        repo_path = self.repo_path.get().strip()
        output_format = self.output_format.get()
        
        # 상태 업데이트
        self.status_text.set("AI 설정 적용 중...")
        self.progress_var.set(10)
        
        def do_apply():
            try:
                # 설정 적용
                result = self.ai_manager.apply_config(
                    repo_path=repo_path,
                    config=self.config,
                    file_format=output_format
                )
                
                if not result.get("success", False):
                    # UI 스레드에서 업데이트
                    error = result.get("error", "알 수 없는 오류")
                    self.master.after(0, lambda: self._handle_apply_error(error))
                    return
                
                # UI 업데이트 (스레드 안전을 위해 after 사용)
                self.master.after(0, lambda: self._show_apply_success(result))
            
            except Exception as e:
                logger.error(f"AI 설정 적용 중 오류 발생: {str(e)}")
                
                # UI 스레드에서 업데이트
                self.master.after(0, lambda: self._handle_apply_error(str(e)))
        
        # 별도 스레드에서 실행
        threading.Thread(target=do_apply, daemon=True).start()
    
    def _handle_apply_error(self, error_msg):
        """설정 적용 오류 처리"""
        self.status_text.set("설정 적용 실패")
        self.progress_var.set(0)
        messagebox.showerror("적용 오류", f"AI 설정 적용 중 오류가 발생했습니다:\n{error_msg}")
    
    def _show_apply_success(self, result):
        """설정 적용 성공 처리"""
        # 상태 업데이트
        self.status_text.set("AI 설정 적용 완료")
        self.progress_var.set(100)
        
        # 생성된 파일 목록
        config_path = result.get("config_path", "")
        env_files = result.get("environment_setup", {}).get("files_created", [])
        
        # 메시지 구성
        message = f"AI 설정이 성공적으로 적용되었습니다.\n\n"
        message += f"설정 파일: {config_path}\n\n"
        
        if env_files:
            message += "생성된 환경 파일:\n"
            for file in env_files:
                message += f"- {file}\n"
        
        # 성공 메시지
        messagebox.showinfo("적용 완료", message)
        
        # 저장소 목록 새로고침
        self._load_repositories()
