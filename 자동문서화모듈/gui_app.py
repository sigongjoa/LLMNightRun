"""
자동 문서화 모듈의 GUI 애플리케이션
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from config import (
    BASE_DIR, TEMPLATES_DIR, LOGS_DIR, GENERATED_DOCS_DIR,
    LLM_API_URL, MODEL_NAME, DOC_TYPES,
    INTENT_EXTRACTION_PROMPT, DOC_GENERATION_PROMPT, COMMIT_MESSAGE_PROMPT,
    GUI_TITLE, GUI_WIDTH, GUI_HEIGHT
)
from utils.llm_client import LLMClient
from utils.conversation_analyzer import ConversationAnalyzer
from utils.document_processor import DocumentProcessor
from utils.git_handler import GitHandler

class AutoDocGUI:
    """자동 문서화 모듈의 GUI 클래스"""
    
    def __init__(self, root):
        """
        GUI 초기화
        
        Args:
            root: tkinter 루트 윈도우
        """
        self.root = root
        self.root.title(GUI_TITLE)
        self.root.geometry(f"{GUI_WIDTH}x{GUI_HEIGHT}")
        
        # 상태 변수들
        self.conversation_file = tk.StringVar()
        self.selected_doc_type = tk.StringVar(value="README")
        self.api_url = tk.StringVar(value=LLM_API_URL)
        self.model_name = tk.StringVar(value=MODEL_NAME)
        self.git_enabled = tk.BooleanVar(value=False)
        self.git_repo_path = tk.StringVar()
        
        # 모듈 인스턴스들
        self.llm_client = LLMClient(self.api_url.get(), self.model_name.get())
        self.conversation_analyzer = ConversationAnalyzer(self.llm_client)
        self.document_processor = DocumentProcessor(TEMPLATES_DIR, GENERATED_DOCS_DIR, DOC_TYPES)
        self.git_handler = GitHandler()
        
        # 현재 작업 중인 데이터
        self.current_conversation = None
        self.current_intent_data = None
        self.current_document = None
        self.current_commit_info = None
        
        # UI 구성
        self._create_widgets()
        self._update_document_list()
        
    def _create_widgets(self):
        """UI 위젯 생성"""
        # 프레임 생성
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 왼쪽 패널 (설정 및 대화 로그)
        self.left_frame = ttk.LabelFrame(self.main_frame, text="설정 및 대화 로그", padding=10)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # API 설정
        api_frame = ttk.LabelFrame(self.left_frame, text="LLM API 설정", padding=5)
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(api_frame, text="API URL:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(api_frame, textvariable=self.api_url).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(api_frame, text="모델 이름:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Entry(api_frame, textvariable=self.model_name).grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Button(api_frame, text="연결 테스트", command=self._test_llm_connection).grid(row=2, column=0, columnspan=2, pady=5)
        
        api_frame.columnconfigure(1, weight=1)
        
        # 대화 로그 선택
        log_frame = ttk.LabelFrame(self.left_frame, text="대화 로그", padding=5)
        log_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Entry(log_frame, textvariable=self.conversation_file, state="readonly").pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(log_frame, text="대화 로그 파일 선택", command=self._select_conversation_file).pack(pady=5)
        
        # 문서 유형 선택
        doc_type_frame = ttk.LabelFrame(self.left_frame, text="문서 유형", padding=5)
        doc_type_frame.pack(fill=tk.X, pady=(0, 10))
        
        for i, doc_type in enumerate(DOC_TYPES.keys()):
            ttk.Radiobutton(
                doc_type_frame, 
                text=doc_type, 
                value=doc_type, 
                variable=self.selected_doc_type
            ).grid(row=i//3, column=i%3, sticky=tk.W, padx=5, pady=2)
        
        # Git 설정
        git_frame = ttk.LabelFrame(self.left_frame, text="Git 설정", padding=5)
        git_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(git_frame, text="Git 커밋 활성화", variable=self.git_enabled).pack(anchor=tk.W, padx=5, pady=2)
        
        repo_frame = ttk.Frame(git_frame)
        repo_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(repo_frame, text="저장소 경로:").pack(side=tk.LEFT)
        ttk.Entry(repo_frame, textvariable=self.git_repo_path).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        ttk.Button(repo_frame, text="...", width=3, command=self._select_repo_path).pack(side=tk.RIGHT)
        
        # Git 버튼 프레임
        git_buttons = ttk.Frame(git_frame)
        git_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(git_buttons, text="Git 상태 확인", command=self._check_git_status).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(git_buttons, text="원격 저장소에 푸시", command=self._push_to_remote).pack(side=tk.LEFT)
        
        # 대화 내용 미리보기
        preview_frame = ttk.LabelFrame(self.left_frame, text="대화 내용 미리보기", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.conversation_preview = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, height=10)
        self.conversation_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.conversation_preview.config(state=tk.DISABLED)
        
        # 오른쪽 패널 (문서 생성 및 관리)
        self.right_frame = ttk.LabelFrame(self.main_frame, text="문서 생성 및 관리", padding=10)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 문서 생성 버튼
        button_frame = ttk.Frame(self.right_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="의도 분석", command=self._extract_intent).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="문서 생성", command=self._generate_document).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="커밋 메시지 생성", command=self._generate_commit_message).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Git에 커밋", command=self._commit_to_git).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="커밋 후 푸시", command=self._commit_and_push).pack(side=tk.LEFT)
        
        # 생성된 문서 미리보기
        doc_preview_frame = ttk.LabelFrame(self.right_frame, text="문서 미리보기", padding=5)
        doc_preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.document_preview = scrolledtext.ScrolledText(doc_preview_frame, wrap=tk.WORD, height=20)
        self.document_preview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 하단 프레임 (생성된 문서 목록)
        doc_list_frame = ttk.LabelFrame(self.right_frame, text="생성된 문서 목록", padding=5)
        doc_list_frame.pack(fill=tk.BOTH, pady=(0, 5))
        
        # 문서 리스트 테이블
        columns = ("name", "type", "size", "created")
        self.doc_list = ttk.Treeview(doc_list_frame, columns=columns, show="headings", height=6)
        
        # 열 제목 설정
        self.doc_list.heading("name", text="파일명")
        self.doc_list.heading("type", text="유형")
        self.doc_list.heading("size", text="크기")
        self.doc_list.heading("created", text="생성일")
        
        # 열 너비 설정
        self.doc_list.column("name", width=150)
        self.doc_list.column("type", width=100)
        self.doc_list.column("size", width=80)
        self.doc_list.column("created", width=150)
        
        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(doc_list_frame, orient=tk.VERTICAL, command=self.doc_list.yview)
        self.doc_list.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.doc_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 문서 리스트 클릭 이벤트 바인딩
        self.doc_list.bind("<Double-1>", self._on_doc_list_double_click)
        
        # 하단 버튼
        doc_list_buttons = ttk.Frame(doc_list_frame)
        doc_list_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(doc_list_buttons, text="새로고침", command=self._update_document_list).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(doc_list_buttons, text="열기", command=self._open_selected_document).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(doc_list_buttons, text="삭제", command=self._delete_selected_document).pack(side=tk.LEFT)
        
        # 상태 바
        self.status_var = tk.StringVar(value="준비")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _update_status(self, message: str):
        """상태 바 메시지 업데이트"""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def _select_conversation_file(self):
        """대화 로그 파일 선택 다이얼로그"""
        file_path = filedialog.askopenfilename(
            title="대화 로그 파일 선택",
            filetypes=[("JSON 파일", "*.json"), ("모든 파일", "*.*")],
            initialdir=LOGS_DIR
        )
        
        if file_path:
            self.conversation_file.set(file_path)
            self._load_conversation()
    
    def _select_repo_path(self):
        """Git 저장소 경로 선택 다이얼로그"""
        dir_path = filedialog.askdirectory(
            title="Git 저장소 선택",
            initialdir=os.getcwd()
        )
        
        if dir_path:
            self.git_repo_path.set(dir_path)
            # Git 핸들러 업데이트
            self.git_handler = GitHandler(dir_path)
    
    def _load_conversation(self):
        """선택한 대화 로그 파일 로드"""
        file_path = self.conversation_file.get()
        if not file_path:
            messagebox.showerror("오류", "대화 로그 파일을 선택해주세요.")
            return
            
        self._update_status(f"대화 로그 로드 중: {os.path.basename(file_path)}")
        
        self.current_conversation = self.conversation_analyzer.load_conversation(file_path)
        if not self.current_conversation:
            messagebox.showerror("오류", "대화 로그 파일을 로드하지 못했습니다.")
            self._update_status("대화 로그 로드 실패")
            return
            
        # 대화 내용 미리보기 업데이트
        conversation_text = self.conversation_analyzer.get_conversation_text(self.current_conversation)
        self.conversation_preview.config(state=tk.NORMAL)
        self.conversation_preview.delete(1.0, tk.END)
        self.conversation_preview.insert(tk.END, conversation_text)
        self.conversation_preview.config(state=tk.DISABLED)
        
        self._update_status(f"대화 로그 로드 완료: {os.path.basename(file_path)}")
    
    def _test_llm_connection(self):
        """LLM API 연결 테스트"""
        self._update_status("LLM API 연결 테스트 중...")
        
        # API URL과 모델 이름 업데이트
        api_url = self.api_url.get()
        model_name = self.model_name.get()
        
        if not api_url:
            messagebox.showerror("오류", "API URL을 입력해주세요.")
            self._update_status("API URL이 비어있습니다.")
            return
            
        # LLM 클라이언트 업데이트
        self.llm_client = LLMClient(api_url, model_name)
        self.conversation_analyzer = ConversationAnalyzer(self.llm_client)
        
        # 간단한 테스트 메시지
        messages = [{"role": "user", "content": "안녕하세요! 테스트 메시지입니다."}]
        
        response = self.llm_client.chat_completion(messages, temperature=0.7, max_tokens=50)
        if response:
            messagebox.showinfo("성공", f"LLM API 연결 성공!\n\n응답: {response[:100]}...")
            self._update_status("LLM API 연결 성공")
        else:
            messagebox.showerror("오류", "LLM API 연결 실패. URL과 모델 이름을 확인해주세요.")
            self._update_status("LLM API 연결 실패")
    
    def _check_git_status(self):
        """Git 저장소 상태 확인"""
        repo_path = self.git_repo_path.get()
        if not repo_path:
            messagebox.showerror("오류", "Git 저장소 경로를 입력해주세요.")
            self._update_status("Git 저장소 경로가 비어있습니다.")
            return
            
        self.git_handler = GitHandler(repo_path)
        
        self._update_status("Git 상태 확인 중...")
        
        if not self.git_handler.is_git_repo():
            messagebox.showerror("오류", "유효한 Git 저장소가 아닙니다: " + repo_path)
            self._update_status("Git 저장소 확인 실패")
            return
            
        success, status = self.git_handler.get_status()
        if success:
            if status.strip():
                messagebox.showinfo("Git 상태", f"변경 사항이 있습니다:\n\n{status}")
            else:
                messagebox.showinfo("Git 상태", "변경 사항이 없습니다.")
            self._update_status("Git 상태 확인 완료")
        else:
            messagebox.showerror("오류", f"Git 상태 확인 실패: {status}")
            self._update_status("Git 상태 확인 실패")
    
    def _extract_intent(self):
        """대화 내용에서 의도 추출"""
        if not self.current_conversation:
            messagebox.showerror("오류", "대화 로그를 먼저 로드해주세요.")
            return
            
        self._update_status("의도 분석 중...")
        
        self.current_intent_data = self.conversation_analyzer.extract_intent(
            self.current_conversation,
            INTENT_EXTRACTION_PROMPT
        )
        
        # 문서 유형 라디오 버튼 업데이트
        doc_type = self.current_intent_data.get("doc_type", "README")
        if doc_type in DOC_TYPES:
            self.selected_doc_type.set(doc_type)
        
        # 결과 표시
        keywords = ", ".join(self.current_intent_data.get("keywords", []))
        intent = self.current_intent_data.get("intent", "")
        doc_type = self.current_intent_data.get("doc_type", "")
        
        result_message = f"분석 결과:\n\n키워드: {keywords}\n\n의도: {intent}\n\n추천 문서 유형: {doc_type}"
        messagebox.showinfo("의도 분석 결과", result_message)
        
        self._update_status("의도 분석 완료")
    
    def _generate_document(self):
        """문서 생성"""
        if not self.current_conversation:
            messagebox.showerror("오류", "대화 로그를 먼저 로드해주세요.")
            return
            
        doc_type = self.selected_doc_type.get()
        if not doc_type:
            messagebox.showerror("오류", "문서 유형을 선택해주세요.")
            return
            
        self._update_status(f"{doc_type} 문서 생성 중...")
        
        # 템플릿 가져오기
        template = self.document_processor.get_template(doc_type)
        
        # 문서 생성
        self.current_document = self.conversation_analyzer.generate_document(
            self.current_conversation,
            doc_type,
            template,
            DOC_GENERATION_PROMPT
        )
        
        # 미리보기 업데이트
        self.document_preview.delete(1.0, tk.END)
        self.document_preview.insert(tk.END, self.current_document)
        
        self._update_status(f"{doc_type} 문서 생성 완료")
        
        # 저장 확인
        if messagebox.askyesno("문서 저장", "생성된 문서를 저장하시겠습니까?"):
            self._save_document()
    
    def _save_document(self):
        """생성된 문서 저장"""
        if not self.current_document:
            messagebox.showerror("오류", "저장할 문서가 없습니다.")
            return
            
        doc_type = self.selected_doc_type.get()
        
        # 파일명 제안
        suggest_name = ""
        if self.current_conversation and "logs" in self.current_conversation:
            # 첫 번째 메시지에서 키워드를 추출하여 파일명 제안
            first_message = self.current_conversation["logs"][0].get("content", "") if self.current_conversation["logs"] else ""
            words = first_message.split()[:3]  # 첫 3단어만 사용
            suggest_name = "_".join(words).lower().replace(" ", "_")
            suggest_name = re.sub(r'[^\w\-\.]', '_', suggest_name)  # 특수문자 제거
            
            if not suggest_name or len(suggest_name) < 3:
                suggest_name = f"{doc_type.lower()}_doc"
        else:
            suggest_name = f"{doc_type.lower()}_doc"
        
        # 파일명 입력 대화상자
        from tkinter.simpledialog import askstring
        base_name = askstring("파일명 입력", "문서 파일명을 입력하세요 (확장자 제외):", initialvalue=suggest_name)
        
        if not base_name:
            return  # 취소됨
            
        self._update_status(f"문서 저장 중: {base_name}")
        
        # 문서 저장
        file_path, file_name = self.document_processor.save_document(doc_type, self.current_document, base_name)
        
        messagebox.showinfo("저장 완료", f"문서가 저장되었습니다:\n{file_path}")
        self._update_status(f"문서 저장 완료: {file_name}")
        
        # 문서 목록 갱신
        self._update_document_list()
        
        # Git 커밋 여부 확인
        if self.git_enabled.get() and self.git_handler.is_git_repo():
            if messagebox.askyesno("Git 커밋", "저장된 문서를 Git에 커밋하시겠습니까?"):
                self._generate_commit_message(file_path)
    
    def _generate_commit_message(self, file_path: Optional[str] = None):
        """
        커밋 메시지 생성
        
        Args:
            file_path: 특정 파일 경로 (없으면 현재 문서 사용)
        """
        if not self.current_document:
            messagebox.showerror("오류", "문서를 먼저 생성해주세요.")
            return
            
        if not self.current_conversation:
            messagebox.showerror("오류", "대화 로그가 없습니다.")
            return
            
        doc_type = self.selected_doc_type.get()
        
        self._update_status("커밋 메시지 생성 중...")
        
        # 커밋 메시지 생성
        self.current_commit_info = self.conversation_analyzer.generate_commit_message(
            doc_type,
            self.current_document,
            self.current_conversation,
            COMMIT_MESSAGE_PROMPT
        )
        
        # 커밋 메시지 표시
        commit_type = self.current_commit_info.get("type", "docs")
        scope = self.current_commit_info.get("scope", "")
        message = self.current_commit_info.get("message", "")
        
        if scope:
            full_message = f"{commit_type}({scope}): {message}"
        else:
            full_message = f"{commit_type}: {message}"
            
        messagebox.showinfo("커밋 메시지", f"생성된 커밋 메시지:\n\n{full_message}")
        
        self._update_status("커밋 메시지 생성 완료")
        
        # 특정 파일이 지정된 경우 바로 커밋 수행
        if file_path and self.git_enabled.get() and self.git_handler.is_git_repo():
            if messagebox.askyesno("Git 커밋", f"다음 메시지로 커밋하시겠습니까?\n\n{full_message}"):
                self._commit_to_git(file_path)
    
    def _commit_to_git(self, file_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Git에 커밋
        
        Args:
            file_path: 특정 파일 경로 (없으면 선택된 문서 사용)
            
        Returns:
            (성공 여부, 메시지, 커밋된 파일 경로) 튜플
        """
        if not self.git_enabled.get():
            messagebox.showerror("오류", "Git 커밋이 비활성화되어 있습니다.")
            return False, "Git 커밋이 비활성화되어 있습니다.", None
            
        repo_path = self.git_repo_path.get()
        if not repo_path:
            messagebox.showerror("오류", "Git 저장소 경로를 입력해주세요.")
            return False, "Git 저장소 경로가 비어있습니다.", None
            
        # Git 핸들러 업데이트
        self.git_handler = GitHandler(repo_path)
            
        if not self.git_handler.is_git_repo():
            messagebox.showerror("오류", "유효한 Git 저장소가 아닙니다.")
            return False, "유효한 Git 저장소가 아닙니다.", None
            
        if not self.current_commit_info:
            messagebox.showerror("오류", "커밋 메시지를 먼저 생성해주세요.")
            return False, "커밋 메시지가 없습니다.", None
            
        # 파일 경로가 지정되지 않은 경우 선택된 문서 사용
        if not file_path:
            selected = self.doc_list.selection()
            if not selected:
                messagebox.showerror("오류", "커밋할 문서를 선택해주세요.")
                return False, "선택된 문서가 없습니다.", None
                
            item = self.doc_list.item(selected[0])
            item_values = item["values"]
            
            # 문서 목록에서 파일 경로 가져오기
            documents = self.document_processor.get_saved_documents()
            for doc in documents:
                if doc["name"] == item_values[0]:  # 파일명으로 비교
                    file_path = doc["path"]
                    break
                    
            if not file_path:
                messagebox.showerror("오류", "선택한 문서의 경로를 찾을 수 없습니다.")
                return False, "문서 경로를 찾을 수 없습니다.", None
        
        self._update_status(f"Git 커밋 중: {os.path.basename(file_path)}")
        
        # 저장소 내 저장 위치 선택 대화상자
        target_dir = "docs"
        from tkinter.simpledialog import askstring
        suggested_dir = askstring("저장 위치", "저장소 내 저장 위치 (상대 경로):", initialvalue=target_dir)
        
        if suggested_dir is None:  # 취소됨
            self._update_status("Git 커밋 취소됨")
            return False, "저장 위치 선택이 취소되었습니다.", None
            
        if suggested_dir:
            target_dir = suggested_dir
        
        # 커밋 수행 (자동으로 저장소 내부로 복사)
        success, message = self.git_handler.commit_document(file_path, self.current_commit_info, target_dir)
        
        if success:
            messagebox.showinfo("커밋 성공", f"문서가 성공적으로 커밋되었습니다:\n\n{message}")
            self._update_status("Git 커밋 완료")
            return True, message, file_path
        else:
            messagebox.showerror("커밋 실패", f"문서 커밋 중 오류가 발생했습니다:\n\n{message}")
            self._update_status("Git 커밋 실패")
            return False, message, None

    def _push_to_remote(self):
        """
        원격 저장소에 푸시
        """
        if not self.git_enabled.get():
            messagebox.showerror("오류", "Git 기능이 비활성화되어 있습니다.")
            return
            
        repo_path = self.git_repo_path.get()
        if not repo_path:
            messagebox.showerror("오류", "Git 저장소 경로를 입력해주세요.")
            return
            
        # Git 핸들러 업데이트
        self.git_handler = GitHandler(repo_path)
            
        if not self.git_handler.is_git_repo():
            messagebox.showerror("오류", "유효한 Git 저장소가 아닙니다.")
            return
        
        # 현재 브랜치 확인
        branch_success, branch = self.git_handler.get_current_branch()
        if not branch_success:
            messagebox.showerror("오류", f"브랜치 확인 실패: {branch}")
            return
        
        # 원격 저장소 목록 확인
        remotes_success, remotes = self.git_handler.get_remotes()
        if not remotes_success or not remotes:
            messagebox.showerror("오류", "원격 저장소를 찾을 수 없습니다.")
            return
        
        # 원격 저장소 선택 (기본값: origin)
        remote = "origin"
        if len(remotes) > 1:
            from tkinter.simpledialog import askstring
            remote = askstring("원격 저장소 선택", "푸시할 원격 저장소를 입력하세요:", initialvalue=remote)
            if not remote:
                self._update_status("푸시 취소됨")
                return
        
        # 푸시 수행
        self._update_status(f"Git 푸시 중: {remote}/{branch}")
        success, message = self.git_handler.push(remote, branch)
        
        if success:
            messagebox.showinfo("푸시 성공", f"변경사항이 원격 저장소에 푸시되었습니다:\n\n{message}")
            self._update_status("Git 푸시 완료")
        else:
            messagebox.showerror("푸시 실패", f"원격 저장소 푸시 중 오류가 발생했습니다:\n\n{message}")
            self._update_status("Git 푸시 실패")
    
    def _commit_and_push(self):
        """
        문서 커밋 후 원격 저장소에 푸시
        """
        # 커밋 수행
        commit_success, commit_message, file_path = self._commit_to_git()
        
        if not commit_success:
            return
            
        # 푸시 여부 확인
        if messagebox.askyesno("원격 저장소 푸시", "커밋된 변경사항을 원격 저장소에 푸시하시겠습니까?"):
            self._push_to_remote()
    
    def _update_document_list(self):
        """생성된 문서 목록 업데이트"""
        # 기존 항목 삭제
        for item in self.doc_list.get_children():
            self.doc_list.delete(item)
            
        # 문서 목록 가져오기
        documents = self.document_processor.get_saved_documents()
        
        # 목록에 추가
        for doc in documents:
            self.doc_list.insert("", tk.END, values=(
                doc["name"],
                doc["type"],
                doc["size"],
                doc["created"]
            ))
    
    def _on_doc_list_double_click(self, event):
        """문서 목록 더블 클릭 이벤트 처리"""
        self._open_selected_document()
    
    def _open_selected_document(self):
        """선택된 문서 열기"""
        selected = self.doc_list.selection()
        if not selected:
            messagebox.showerror("오류", "문서를 선택해주세요.")
            return
            
        item = self.doc_list.item(selected[0])
        item_values = item["values"]
        
        # 문서 목록에서 파일 경로 가져오기
        file_path = None
        documents = self.document_processor.get_saved_documents()
        for doc in documents:
            if doc["name"] == item_values[0]:  # 파일명으로 비교
                file_path = doc["path"]
                break
                
        if not file_path:
            messagebox.showerror("오류", "선택한 문서의 경로를 찾을 수 없습니다.")
            return
            
        # 파일 내용 로드
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 문서 미리보기 업데이트
            self.document_preview.delete(1.0, tk.END)
            self.document_preview.insert(tk.END, content)
            
            # 현재 문서 업데이트
            self.current_document = content
            
            # 문서 유형 업데이트
            doc_type = item_values[1]  # 문서 유형
            if doc_type in DOC_TYPES:
                self.selected_doc_type.set(doc_type)
            
            self._update_status(f"문서 로드 완료: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("오류", f"문서를 열지 못했습니다: {str(e)}")
    
    def _delete_selected_document(self):
        """선택된 문서 삭제"""
        selected = self.doc_list.selection()
        if not selected:
            messagebox.showerror("오류", "삭제할 문서를 선택해주세요.")
            return
            
        item = self.doc_list.item(selected[0])
        item_values = item["values"]
        
        # 문서 목록에서 파일 경로 가져오기
        file_path = None
        documents = self.document_processor.get_saved_documents()
        for doc in documents:
            if doc["name"] == item_values[0]:  # 파일명으로 비교
                file_path = doc["path"]
                break
                
        if not file_path:
            messagebox.showerror("오류", "선택한 문서의 경로를 찾을 수 없습니다.")
            return
            
        # 삭제 확인
        if not messagebox.askyesno("삭제 확인", f"다음 문서를 삭제하시겠습니까?\n\n{os.path.basename(file_path)}"):
            return
            
        # 파일 삭제
        try:
            os.remove(file_path)
            self._update_status(f"문서 삭제 완료: {os.path.basename(file_path)}")
            
            # 문서 목록 갱신
            self._update_document_list()
        except Exception as e:
            messagebox.showerror("오류", f"문서 삭제 중 오류가 발생했습니다: {str(e)}")

def main():
    """메인 함수"""
    # 기본 디렉토리 생성
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(GENERATED_DOCS_DIR, exist_ok=True)
    
    # Tkinter 루트 윈도우 생성
    root = tk.Tk()
    app = AutoDocGUI(root)
    
    # 예제 대화 로그 생성 (없는 경우)
    sample_log_path = os.path.join(LOGS_DIR, "sample_conversation.json")
    if not os.path.exists(sample_log_path):
        sample_conversation = {
            "session_id": "sample_session_001",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "logs": [
                {
                    "role": "user",
                    "content": "FastAPI에서 PDF 업로드 후 텍스트를 추출하려고 하는데, PyMuPDF로 처리해도 한글이 깨져서 나와."
                },
                {
                    "role": "assistant",
                    "content": "PyMuPDF에서 한글이 깨지는 경우, 폰트 문제일 수 있습니다. `text = page.get_text('text')` 대신 `'blocks'` 또는 `'rawdict'` 모드로 추출해 보세요. 예:\n\n```python\nblocks = page.get_text('blocks')\n```\n\n또한, `fitz.TOOLS.set_aa_level(0)` 설정으로 렌더링 문제를 완화할 수 있습니다."
                },
                {
                    "role": "user",
                    "content": "오, blocks로 하니까 텍스트는 나오는데 줄바꿈이 엉망이야. 깔끔하게 한 문단으로 이어지게 하려면 어떻게 해?"
                },
                {
                    "role": "assistant",
                    "content": "각 블록의 내용을 정렬하고, 좌표 기준으로 같은 줄에 있는 텍스트를 병합해보세요. 예:\n\n```python\nblocks.sort(key=lambda b: (b[1], b[0]))\ntext = ' '.join([b[4] for b in blocks])\n```"
                },
                {
                    "role": "user",
                    "content": "텍스트 추출 잘 됐어. 그럼 이제 업로드된 PDF에서 텍스트 뽑고 저장하는 FastAPI 엔드포인트 하나 만들어줘."
                },
                {
                    "role": "assistant",
                    "content": "아래는 FastAPI용 PDF 업로드 및 텍스트 추출 엔드포인트입니다:\n\n```python\n@app.post(\"/upload-pdf\")\nasync def upload_pdf(file: UploadFile = File(...)):\n    contents = await file.read()\n    with open(\"temp.pdf\", \"wb\") as f:\n        f.write(contents)\n    doc = fitz.open(\"temp.pdf\")\n    result = []\n    for page in doc:\n        blocks = page.get_text(\"blocks\")\n        blocks.sort(key=lambda b: (b[1], b[0]))\n        result.append(' '.join([b[4] for b in blocks]))\n    return {\"text\": '\\n'.join(result)}\n```"
                }
            ]
        }
        
        with open(sample_log_path, "w", encoding="utf-8") as f:
            json.dump(sample_conversation, f, ensure_ascii=False, indent=2)
    
    # GUI 실행
    root.mainloop()

if __name__ == "__main__":
    main()
