#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
메인 GUI 애플리케이션

Tkinter 기반 메인 애플리케이션 클래스를 제공합니다.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import threading
import queue
from typing import Dict, List, Any, Optional, Tuple

from core.logging import get_logger
from core.config import get_config
from core.events import subscribe, publish, get_event_bus
from local_llm.api import get_status as llm_get_status, chat as llm_chat
from conversation import ConversationManager, Conversation, Message
from vector_db import VectorDB, Document
from plugin_system import get_registry, load_plugins
from gui.app_modules_tab import ModulesTabInterface

logger = get_logger("gui")

class LLMNightRunApp:
    """메인 애플리케이션 클래스"""
    
    def __init__(self, root: Optional[tk.Tk] = None):
        """
        메인 애플리케이션 초기화
        
        Args:
            root: Tkinter 루트 윈도우 (기본값: 자동 생성)
        """
        # 루트 윈도우 생성 또는 사용
        self.root = root or tk.Tk()
        self.root.title("LLM Night Run")
        
        # 설정 로드
        self.config = get_config()
        
        # 창 크기 설정
        window_size = self.config.get("gui", "window_size", [800, 600])
        self.root.geometry(f"{window_size[0]}x{window_size[1]}")
        
        # 스레드 간 통신을 위한 대기열 생성
        self.ui_queue = queue.Queue()
        
        # 구성 요소
        self._setup_variables()
        self._setup_styles()
        self._setup_ui()
        self._bind_events()
        
        # 컴포넌트 초기화
        self._initialize_components()
        
        # UI 업데이트 타이머 시작 (대기열 처리)
        self._start_ui_update_timer()
        
        logger.info("GUI 애플리케이션 초기화됨")
    
    def _setup_variables(self):
        """변수 초기화"""
        # LLM 상태 변수
        self.llm_status = {
            "enabled": tk.BooleanVar(value=False),
            "connected": tk.BooleanVar(value=False),
            "model_id": tk.StringVar(value=""),
            "status_text": tk.StringVar(value="연결 대기 중...")
        }
        
        # 대화 상태 변수
        self.conversation_status = {
            "active_id": tk.StringVar(value=""),
            "active_title": tk.StringVar(value=""),
            "message_count": tk.IntVar(value=0)
        }
        
        # 메시지 변수
        self.user_message = tk.StringVar(value="")
    
    def _setup_styles(self):
        """스타일 설정"""
        self.style = ttk.Style()
        
        # 테마 설정
        theme = self.config.get("gui", "theme", "light")
        try:
            if theme == "dark":
                self.style.theme_use("clam")  # 어두운 테마에 적합한 기본 테마
                # 어두운 색상으로 재정의
                self.style.configure("TFrame", background="#2d2d2d")
                self.style.configure("TLabel", background="#2d2d2d", foreground="#ffffff")
                self.style.configure("TButton", background="#444444", foreground="#ffffff")
                # 더 많은 스타일 설정...
            else:
                # 기본 테마 사용
                # 또는 테마 설정 및 기본 색상 재정의
                pass
        except Exception as e:
            logger.warning(f"테마 설정 중 오류 발생: {str(e)}")
        
        # 폰트 크기 설정
        font_size = self.config.get("gui", "font_size", 10)
        default_font = ("TkDefaultFont", font_size)
        text_font = ("TkTextFont", font_size)
        
        self.style.configure(".", font=default_font)
        
        # 사용자 정의 스타일
        self.style.configure("Title.TLabel", font=("TkDefaultFont", font_size + 2, "bold"))
        self.style.configure("Status.TLabel", font=("TkDefaultFont", font_size - 1))
        self.style.configure("UserMessage.TFrame", background="#e6f7ff")
        self.style.configure("AssistantMessage.TFrame", background="#f0f0f0")
    
    def _setup_ui(self):
        """UI 레이아웃 설정"""
        # 메인 프레임
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 상단 프레임
        self.top_frame = ttk.Frame(self.main_frame, padding="5")
        self.top_frame.pack(fill=tk.X)
        
        # LLM 상태 표시
        self.llm_frame = ttk.LabelFrame(self.top_frame, text="LLM 상태", padding="5")
        self.llm_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Label(self.llm_frame, textvariable=self.llm_status["status_text"]).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.llm_frame, text="연결 확인", 
                  command=self._check_llm_connection).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(self.llm_frame, text="설정", 
                  command=self._open_llm_settings).pack(side=tk.RIGHT, padx=5)
        
        # 대화 관리 프레임
        self.conversation_frame = ttk.LabelFrame(self.top_frame, text="대화 관리", padding="5")
        self.conversation_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        ttk.Button(self.conversation_frame, text="새 대화", 
                  command=self._new_conversation).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.conversation_frame, text="대화 열기", 
                  command=self._open_conversation).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.conversation_frame, text="대화 저장", 
                  command=self._save_conversation).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(self.conversation_frame, text="대화 내보내기", 
                  command=self._export_conversation).pack(side=tk.LEFT, padx=5)
        
        # 메인 영역 분할
        self.main_notebook = ttk.Notebook(self.main_frame)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 대화 탭
        self.chat_tab = ttk.Frame(self.main_notebook, padding="5")
        self.main_notebook.add(self.chat_tab, text="대화")
        
        # 분할 창
        self.paned_window = ttk.PanedWindow(self.chat_tab, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 왼쪽 패널 (대화 목록)
        self.left_panel = ttk.Frame(self.paned_window, padding="5")
        self.paned_window.add(self.left_panel, weight=1)
        
        # 대화 목록 프레임
        self.conversation_list_frame = ttk.LabelFrame(self.left_panel, text="대화 목록", padding="5")
        self.conversation_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 대화 목록 트리뷰
        self.conversation_tree = ttk.Treeview(self.conversation_list_frame, columns=("title", "date"), show="headings")
        self.conversation_tree.heading("title", text="제목")
        self.conversation_tree.heading("date", text="날짜")
        self.conversation_tree.column("title", width=150)
        self.conversation_tree.column("date", width=100)
        self.conversation_tree.pack(fill=tk.BOTH, expand=True)
        
        # 대화 목록 스크롤바
        conversation_scrollbar = ttk.Scrollbar(self.conversation_tree, orient=tk.VERTICAL, command=self.conversation_tree.yview)
        self.conversation_tree.configure(yscrollcommand=conversation_scrollbar.set)
        conversation_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 대화 목록 새로고침 버튼
        ttk.Button(self.conversation_list_frame, text="새로고침", 
                  command=self._refresh_conversation_list).pack(fill=tk.X, pady=(5, 0))
        
        # 오른쪽 패널 (대화 내용 및 입력)
        self.right_panel = ttk.Frame(self.paned_window, padding="5")
        self.paned_window.add(self.right_panel, weight=3)
        
        # 대화 내용 프레임
        self.chat_frame = ttk.LabelFrame(self.right_panel, text="대화 내용", padding="5")
        self.chat_frame.pack(fill=tk.BOTH, expand=True)
        
        # 대화 표시 영역 (Canvas + Frame으로 구현하여 스크롤 지원)
        self.chat_canvas = tk.Canvas(self.chat_frame)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 대화 내용 스크롤바
        chat_scrollbar = ttk.Scrollbar(self.chat_frame, orient=tk.VERTICAL, command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=chat_scrollbar.set)
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 대화 내용을 담을 프레임
        self.message_frame = ttk.Frame(self.chat_canvas)
        self.chat_canvas.create_window((0, 0), window=self.message_frame, anchor=tk.NW, tags="message_frame")
        
        # 프레임 크기 변경 시 Canvas 스크롤 영역 업데이트
        self.message_frame.bind("<Configure>", self._on_frame_configure)
        
        # 입력 프레임
        self.input_frame = ttk.Frame(self.right_panel, padding="5")
        self.input_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 메시지 입력 영역
        self.message_entry = scrolledtext.ScrolledText(self.input_frame, height=3, wrap=tk.WORD)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # 전송 버튼
        ttk.Button(self.input_frame, text="전송", 
                  command=self._send_message).pack(side=tk.RIGHT)
        
        # 상태 표시줄
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="준비 완료", padding=(5, 2))
        self.status_label.pack(side=tk.LEFT)
        
        # 벡터 DB 검색 프레임
        self.vector_search_frame = ttk.LabelFrame(self.left_panel, text="벡터 DB 검색", padding="5")
        self.vector_search_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.search_entry = ttk.Entry(self.vector_search_frame)
        self.search_entry.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(self.vector_search_frame, text="검색", 
                  command=self._search_vector_db).pack(fill=tk.X, padx=5, pady=(0, 5))
                  
        # 모듈 탭 추가
        self.modules_tab = ModulesTabInterface(self.main_notebook)
        self.main_notebook.add(self.modules_tab, text="모듈")
        
        # 모듈 탭에 접근하기 위한 버튼 추가
        ttk.Button(self.top_frame, text="모듈 탭 표시", 
                  command=lambda: self.main_notebook.select(1)).pack(side=tk.RIGHT, padx=5)
    
    def _bind_events(self):
        """이벤트 바인딩"""
        # 윈도우 종료 이벤트
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 메시지 입력 단축키
        self.message_entry.bind("<Control-Return>", self._send_message)
        
        # 대화 목록 선택 이벤트
        self.conversation_tree.bind("<<TreeviewSelect>>", self._on_conversation_select)
        
        # 이벤트 구독
        subscribe("llm.chat.response", self._on_llm_response)
        subscribe("conversation.message.added", self._on_message_added)
        subscribe("conversation.loaded", self._on_conversation_loaded)
        
        # 모듈간 통신을 위한 이벤트 구독
        subscribe("conversation.add_reference", self._on_add_reference)
    
    def _initialize_components(self):
        """컴포넌트 초기화"""
        # 대화 관리자 생성
        self.conversation_manager = ConversationManager()
        
        # 벡터 DB 생성
        try:
            self.vector_db = VectorDB()
            logger.info("벡터 DB 초기화됨")
        except Exception as e:
            self.vector_db = None
            logger.error(f"벡터 DB 초기화 실패: {str(e)}")
        
        # 플러그인 로드
        try:
            load_plugins()
            logger.info("플러그인 로드됨")
        except Exception as e:
            logger.error(f"플러그인 로드 실패: {str(e)}")
        
        # LLM 상태 확인
        self._check_llm_connection()
        
        # 대화 목록 로드
        self._refresh_conversation_list()
        
        # 새 대화 생성
        self._new_conversation()
        
        # 모듈 탭 초기화
        self.modules_tab.refresh_all()
    
    def _start_ui_update_timer(self):
        """대기열에서 작업을 처리하는 타이머 시작"""
        def process_queue():
            try:
                # 대기열에서 작업 가져오기 (대기하지 않고 즉시 리턴)
                while not self.ui_queue.empty():
                    task = self.ui_queue.get_nowait()
                    if task:
                        func, args, kwargs = task
                        try:
                            func(*args, **kwargs)
                        except Exception as e:
                            logger.error(f"UI 작업 처리 중 오류: {str(e)}")
                        finally:
                            self.ui_queue.task_done()
            except Exception as e:
                logger.error(f"대기열 처리 중 오류: {str(e)}")
            finally:
                # 다시 타이머 설정 (50ms 후)
                if self.root and self.root.winfo_exists():
                    self.root.after(50, process_queue)
        
        # 최초 타이머 시작
        self.root.after(50, process_queue)
        
    def _queue_ui_task(self, func, *args, **kwargs):
        """스레드 안전한 방식으로 UI 작업 대기열에 추가"""
        self.ui_queue.put((func, args, kwargs))
        
    # 이벤트 핸들러 및 기능 메서드
    
    def run(self):
        """애플리케이션 실행"""
        # 중요: main.py에서 이미 mainloop()가 호출되었으므로 여기에서는 아무 것도 하지 않음
        pass
        
    def _on_frame_configure(self, event):
        """캔버스 스크롤 영역 업데이트"""
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))
    
    def _on_close(self):
        """애플리케이션 종료"""
        # 활성 대화 저장
        if self.conversation_manager.get_active_conversation():
            self.conversation_manager.save_conversation()
        
        # 설정 저장
        if self.config.get("gui", "save_layout", True):
            # 현재 창 크기 저장
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            self.config.set("gui", "window_size", [width, height])
            self.config.save()
        
        # 종료
        self.root.destroy()
        logger.info("애플리케이션 종료됨")
    
    def _check_llm_connection(self):
        """LLM 연결 상태 확인"""
        def check():
            try:
                enabled, connected, error = llm_get_status()
                
                # UI 업데이트를 대기열에 요청
                self._queue_ui_task(self._update_llm_status, enabled, connected, error)
            
            except Exception as e:
                logger.error(f"LLM 연결 확인 중 오류 발생: {str(e)}")
                self._queue_ui_task(self._update_llm_status, False, False, str(e))
        
        # 별도 스레드에서 실행 (UI 블로킹 방지)
        threading.Thread(target=check, daemon=True).start()
    
    def _on_llm_response(self, request_messages=None, response=None):
        """LLM 응답 이벤트 핸들러"""
        if response is None:
            return
        
        # UI 작업 대기열에 추가
        self._queue_ui_task(self._handle_llm_response, response)
    
    def _update_llm_status(self, enabled: bool, connected: bool, error: Optional[str] = None):
        """LLM 상태 UI 업데이트"""
        self.llm_status["enabled"].set(enabled)
        self.llm_status["connected"].set(connected)
        
        if not enabled:
            status_text = "LLM이 비활성화됨"
            self.llm_status["status_text"].set(status_text)
            return
        
        if connected:
            status_text = "LLM 연결됨"
            if self.llm_status["model_id"].get():
                status_text += f" ({self.llm_status['model_id'].get()})"
        else:
            status_text = "LLM 연결 실패"
            if error:
                status_text += f": {error}"
        
        self.llm_status["status_text"].set(status_text)
        
    def _open_llm_settings(self):
        """LLM 설정 창 열기"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("LLM 설정")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 설정 프레임
        settings_frame = ttk.Frame(settings_window, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # 활성화 설정
        enabled_var = tk.BooleanVar(value=self.config.get("local_llm", "enabled", True))
        ttk.Checkbutton(settings_frame, text="LLM 활성화", variable=enabled_var).pack(anchor=tk.W, pady=5)
        
        # 기본 URL 설정
        ttk.Label(settings_frame, text="LLM 서버 URL:").pack(anchor=tk.W, pady=(10, 0))
        base_url_var = tk.StringVar(value=self.config.get("local_llm", "base_url"))
        ttk.Entry(settings_frame, textvariable=base_url_var).pack(fill=tk.X, pady=5)
        
        # 모델 ID 설정
        ttk.Label(settings_frame, text="모델 ID:").pack(anchor=tk.W, pady=(10, 0))
        model_id_var = tk.StringVar(value=self.config.get("local_llm", "model_id"))
        ttk.Entry(settings_frame, textvariable=model_id_var).pack(fill=tk.X, pady=5)
        
        # 온도 설정
        ttk.Label(settings_frame, text="온도 (Temperature):").pack(anchor=tk.W, pady=(10, 0))
        temp_var = tk.DoubleVar(value=self.config.get("local_llm", "temperature"))
        ttk.Scale(settings_frame, from_=0.0, to=1.0, variable=temp_var, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        ttk.Label(settings_frame, textvariable=temp_var).pack(anchor=tk.E)
        
        # 최대 토큰 설정
        ttk.Label(settings_frame, text="최대 토큰:").pack(anchor=tk.W, pady=(10, 0))
        max_tokens_var = tk.IntVar(value=self.config.get("local_llm", "max_tokens"))
        ttk.Entry(settings_frame, textvariable=max_tokens_var).pack(fill=tk.X, pady=5)
        
        # 버튼 프레임
        button_frame = ttk.Frame(settings_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # 저장 및 취소 버튼
        ttk.Button(button_frame, text="저장", command=lambda: self._save_llm_settings(
            enabled_var.get(), base_url_var.get(), model_id_var.get(), 
            max_tokens_var.get(), temp_var.get(), settings_window
        )).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="취소", command=settings_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _save_llm_settings(self, enabled: bool, base_url: str, model_id: str, 
                          max_tokens: int, temperature: float, window: tk.Toplevel):
        """LLM 설정 저장"""
        from ..local_llm.api import update_config
        
        try:
            # 유효성 검사
            if not base_url:
                messagebox.showerror("오류", "LLM 서버 URL을 입력하세요.", parent=window)
                return
            
            if not model_id:
                messagebox.showerror("오류", "모델 ID를 입력하세요.", parent=window)
                return
            
            # 설정 업데이트
            update_config(
                enabled=enabled,
                base_url=base_url,
                model_id=model_id,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # 상태 업데이트
            self._check_llm_connection()
            
            # 설정 창 닫기
            window.destroy()
            
            # 성공 메시지
            messagebox.showinfo("설정 저장", "LLM 설정이 저장되었습니다.")
        
        except Exception as e:
            logger.error(f"LLM 설정 저장 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"설정 저장 중 오류 발생: {str(e)}", parent=window)
    
    def _new_conversation(self):
        """새 대화 생성"""
        # 제목 입력 창
        title = simpledialog.askstring("새 대화", "대화 제목:", initialvalue="새 대화")
        
        if not title:
            return
        
        # 대화 생성
        conversation = self.conversation_manager.create_conversation(title)
        
        # UI 업데이트
        self.conversation_status["active_id"].set(conversation.conversation_id)
        self.conversation_status["active_title"].set(conversation.title)
        self.conversation_status["message_count"].set(0)
        
        # 대화 내용 지우기
        self._clear_messages()
        
        # 대화 목록 업데이트
        self._refresh_conversation_list()
        
        # 입력 포커스
        self.message_entry.focus_set()
    
    def _open_conversation(self):
        """저장된 대화 열기"""
        # 대화 선택 창
        open_window = tk.Toplevel(self.root)
        open_window.title("대화 열기")
        open_window.geometry("600x400")
        open_window.transient(self.root)
        open_window.grab_set()
        
        # 대화 목록 프레임
        list_frame = ttk.Frame(open_window, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 대화 목록 트리뷰
        columns = ("id", "title", "created", "updated", "messages")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        tree.heading("id", text="ID")
        tree.heading("title", text="제목")
        tree.heading("created", text="생성 시간")
        tree.heading("updated", text="업데이트 시간")
        tree.heading("messages", text="메시지 수")
        
        tree.column("id", width=50)
        tree.column("title", width=150)
        tree.column("created", width=120)
        tree.column("updated", width=120)
        tree.column("messages", width=80)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 대화 목록 로드
        conversations = self.conversation_manager.list_conversations()
        
        for conversation in conversations:
            tree.insert("", tk.END, values=(
                conversation["conversation_id"],
                conversation["title"],
                conversation["created_at"],
                conversation["updated_at"],
                conversation["message_count"]
            ))
        
        # 버튼 프레임
        button_frame = ttk.Frame(open_window, padding="10")
        button_frame.pack(fill=tk.X)
        
        # 열기 및 취소 버튼
        ttk.Button(button_frame, text="열기", command=lambda: self._load_selected_conversation(
            tree, open_window
        )).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="취소", command=open_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 삭제 버튼
        ttk.Button(button_frame, text="삭제", command=lambda: self._delete_selected_conversation(
            tree
        )).pack(side=tk.LEFT, padx=5)
    
    def _load_selected_conversation(self, tree, window):
        """선택한 대화 로드"""
        selected_items = tree.selection()
        
        if not selected_items:
            messagebox.showinfo("알림", "로드할 대화를 선택하세요.", parent=window)
            return
        
        # 첫 번째 선택된 항목의 대화 ID 가져오기
        item = selected_items[0]
        conversation_id = tree.item(item, "values")[0]
        
        # 대화 로드
        conversation = self.conversation_manager.load_conversation(conversation_id)
        
        if not conversation:
            messagebox.showerror("오류", "대화를 로드할 수 없습니다.", parent=window)
            return
        
        # 활성 대화 설정
        self.conversation_manager.set_active_conversation(conversation)
        
        # UI 업데이트
        self.conversation_status["active_id"].set(conversation.conversation_id)
        self.conversation_status["active_title"].set(conversation.title)
        self.conversation_status["message_count"].set(len(conversation.messages))
        
        # 대화 내용 표시
        self._display_conversation(conversation)
        
        # 창 닫기
        window.destroy()
    
    def _delete_selected_conversation(self, tree):
        """선택한 대화 삭제"""
        selected_items = tree.selection()
        
        if not selected_items:
            messagebox.showinfo("알림", "삭제할 대화를 선택하세요.")
            return
        
        # 확인 메시지
        if not messagebox.askyesno("확인", "선택한 대화를 삭제하시겠습니까?"):
            return
        
        # 각 선택된 항목 삭제
        for item in selected_items:
            conversation_id = tree.item(item, "values")[0]
            
            # 대화 삭제
            success = self.conversation_manager.delete_conversation(conversation_id)
            
            if success:
                # 트리에서 항목 제거
                tree.delete(item)
                
                # 활성 대화인 경우 새 대화 생성
                if self.conversation_status["active_id"].get() == conversation_id:
                    self._new_conversation()
            else:
                messagebox.showerror("오류", f"대화 ID '{conversation_id}'를 삭제할 수 없습니다.")
        
        # 대화 목록 새로고침
        self._refresh_conversation_list()
    
    def _refresh_conversation_list(self):
        """대화 목록 새로고침"""
        # 트리뷰 내용 지우기
        for item in self.conversation_tree.get_children():
            self.conversation_tree.delete(item)
        
        # 대화 목록 가져오기
        conversations = self.conversation_manager.list_conversations()
        
        # 트리뷰에 추가
        for conversation in conversations:
            # 날짜 형식 변환
            try:
                import datetime
                date_str = conversation["updated_at"]
                date_obj = datetime.datetime.fromisoformat(date_str)
                formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = conversation["updated_at"]
            
            item_id = self.conversation_tree.insert("", tk.END, values=(
                conversation["title"],
                formatted_date
            ))
            
            # 활성 대화 선택
            if conversation["conversation_id"] == self.conversation_status["active_id"].get():
                self.conversation_tree.selection_set(item_id)
    
    def _on_conversation_select(self, event):
        """대화 목록에서 대화 선택 시 처리"""
        selected_items = self.conversation_tree.selection()
        
        if not selected_items:
            return
        
        # 선택된 항목의 인덱스
        item = selected_items[0]
        index = self.conversation_tree.index(item)
        
        # 대화 목록에서 해당 인덱스의 대화 가져오기
        conversations = self.conversation_manager.list_conversations()
        
        if index >= len(conversations):
            return
        
        conversation_id = conversations[index]["conversation_id"]
        
        # 이미 활성화된 대화인 경우 아무것도 하지 않음
        if conversation_id == self.conversation_status["active_id"].get():
            return
        
        # 현재 대화 저장
        if self.conversation_manager.get_active_conversation():
            self.conversation_manager.save_conversation()
        
        # 선택한 대화 로드
        conversation = self.conversation_manager.load_conversation(conversation_id)
        
        if not conversation:
            messagebox.showerror("오류", "대화를 로드할 수 없습니다.")
            return
        
        # 활성 대화 설정
        self.conversation_manager.set_active_conversation(conversation)
        
        # UI 업데이트
        self.conversation_status["active_id"].set(conversation.conversation_id)
        self.conversation_status["active_title"].set(conversation.title)
        self.conversation_status["message_count"].set(len(conversation.messages))
        
        # 대화 내용 표시
        self._display_conversation(conversation)
    
    def _display_conversation(self, conversation: Conversation):
        """대화 내용 표시"""
        # 기존 메시지 지우기
        self._clear_messages()
        
        # 각 메시지 표시
        for message in conversation.messages:
            self._add_message_bubble(message.role, message.content, message.timestamp)
        
        # 스크롤을 아래로 이동
        self.chat_canvas.yview_moveto(1.0)
    
    def _clear_messages(self):
        """대화 내용 지우기"""
        # 메시지 프레임의 모든 위젯 제거
        for widget in self.message_frame.winfo_children():
            widget.destroy()
    
    def _save_conversation(self):
        """현재 대화 저장"""
        conversation = self.conversation_manager.get_active_conversation()
        
        if not conversation:
            messagebox.showinfo("알림", "저장할 대화가 없습니다.")
            return
        
        # 대화 저장
        success = self.conversation_manager.save_conversation()
        
        if success:
            messagebox.showinfo("성공", "대화가 저장되었습니다.")
        else:
            messagebox.showerror("오류", "대화 저장 중 오류가 발생했습니다.")
    
    def _export_conversation(self):
        """대화 내보내기"""
        conversation = self.conversation_manager.get_active_conversation()
        
        if not conversation:
            messagebox.showinfo("알림", "내보낼 대화가 없습니다.")
            return
        
        # 내보내기 형식 선택 창
        export_window = tk.Toplevel(self.root)
        export_window.title("대화 내보내기")
        export_window.geometry("300x200")
        export_window.transient(self.root)
        export_window.grab_set()
        
        # 형식 선택 프레임
        format_frame = ttk.Frame(export_window, padding="10")
        format_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(format_frame, text="내보내기 형식:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # 형식 선택 라디오 버튼
        format_var = tk.StringVar(value="json")
        
        ttk.Radiobutton(format_frame, text="JSON", value="json", variable=format_var).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(format_frame, text="Markdown", value="markdown", variable=format_var).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(format_frame, text="텍스트", value="text", variable=format_var).pack(anchor=tk.W, pady=2)
        
        # 옵션 체크박스
        include_metadata_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(format_frame, text="메타데이터 포함", variable=include_metadata_var).pack(anchor=tk.W, pady=(10, 2))
        
        include_timestamps_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(format_frame, text="타임스탬프 포함", variable=include_timestamps_var).pack(anchor=tk.W, pady=2)
        
        # 버튼 프레임
        button_frame = ttk.Frame(format_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 내보내기 및 취소 버튼
        ttk.Button(button_frame, text="내보내기", command=lambda: self._do_export_conversation(
            format_var.get(),
            include_metadata_var.get(),
            include_timestamps_var.get(),
            export_window
        )).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="취소", command=export_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _do_export_conversation(self, format: str, include_metadata: bool, 
                               include_timestamps: bool, window: tk.Toplevel):
        """대화 내보내기 실행"""
        # 파일 확장자 설정
        if format == "json":
            file_ext = ".json"
            file_types = [("JSON 파일", "*.json"), ("모든 파일", "*.*")]
        elif format == "markdown":
            file_ext = ".md"
            file_types = [("Markdown 파일", "*.md"), ("모든 파일", "*.*")]
        else:  # text
            file_ext = ".txt"
            file_types = [("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
        
        # 저장 경로 선택
        conversation = self.conversation_manager.get_active_conversation()
        default_filename = f"{conversation.title}{file_ext}".replace(" ", "_")
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=file_ext,
            filetypes=file_types,
            initialfile=default_filename
        )
        
        if not save_path:
            return
        
        # 내보내기 실행
        file_path = self.conversation_manager.save_export(
            format=format,
            include_metadata=include_metadata,
            include_timestamps=include_timestamps,
            file_path=save_path
        )
        
        # 결과 처리
        if file_path:
            messagebox.showinfo("성공", f"대화가 {file_path}로 내보내기되었습니다.")
        else:
            messagebox.showerror("오류", "대화 내보내기 중 오류가 발생했습니다.")
        
        # 창 닫기
        window.destroy()
    
    def _send_message(self, event=None):
        """메시지 전송"""
        # 활성 대화 확인
        conversation = self.conversation_manager.get_active_conversation()
        
        if not conversation:
            messagebox.showinfo("알림", "먼저 대화를 생성하거나 열어야 합니다.")
            return
        
        # 메시지 텍스트 가져오기
        message_text = self.message_entry.get("1.0", tk.END).strip()
        
        if not message_text:
            return
        
        # 메시지 추가
        message = self.conversation_manager.add_message("user", message_text)
        
        if not message:
            messagebox.showerror("오류", "메시지를 추가할 수 없습니다.")
            return
        
        # UI 업데이트
        self._add_message_bubble("user", message_text, message.timestamp)
        
        # 입력 필드 지우기
        self.message_entry.delete("1.0", tk.END)
        
        # LLM 응답 요청
        self._request_llm_response(conversation)
    
    def _add_message_bubble(self, role: str, content: str, timestamp=None):
        """메시지 버블 추가"""
        # 메시지 프레임
        style = "UserMessage.TFrame" if role == "user" else "AssistantMessage.TFrame"
        msg_frame = ttk.Frame(self.message_frame, style=style, padding=10)
        msg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 역할 라벨
        role_text = "사용자" if role == "user" else "어시스턴트" if role == "assistant" else role.capitalize()
        role_label = ttk.Label(msg_frame, text=role_text, font=("TkDefaultFont", 9, "bold"))
        role_label.pack(anchor=tk.W)
        
        # 타임스탬프 라벨 (있는 경우)
        if timestamp:
            if isinstance(timestamp, str):
                time_text = timestamp
            else:
                time_text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            time_label = ttk.Label(msg_frame, text=time_text, font=("TkDefaultFont", 8))
            time_label.pack(anchor=tk.W)
        
        # 내용 텍스트
        text_widget = scrolledtext.ScrolledText(msg_frame, wrap=tk.WORD, height=min(15, content.count('\n') + 2),
                                               width=60, font=("TkTextFont", 10))
        text_widget.insert(tk.END, content)
        text_widget.configure(state=tk.DISABLED)  # 읽기 전용으로 설정
        text_widget.pack(fill=tk.X, pady=(5, 0))
        
        # 스크롤을 아래로 이동
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
    
    def _request_llm_response(self, conversation: Conversation):
        """LLM 응답 요청"""
        # LLM 상태 확인
        enabled, connected, error = llm_get_status()
        
        if not enabled or not connected:
            messagebox.showerror("오류", f"LLM이 연결되지 않았습니다: {error}")
            return
        
        # 로딩 메시지 표시
        loading_frame = ttk.Frame(self.message_frame, padding=10)
        loading_frame.pack(fill=tk.X, padx=10, pady=5)
        
        loading_label = ttk.Label(loading_frame, text="응답 생성 중...")
        loading_label.pack(anchor=tk.W)
        
        # 스크롤을 아래로 이동
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)
        
        # 로딩 프레임 정보 저장
        self.loading_frame_ref = loading_frame
        
        # 대화 메시지 준비
        messages = [{"role": msg.role, "content": msg.content} for msg in conversation.messages]
        
        def request_response():
            try:
                # LLM API 호출
                response = llm_chat(messages)
                
                # UI 작업 대기열에 추가
                if loading_frame and loading_frame.winfo_exists():
                    self._queue_ui_task(loading_frame.destroy)
                
                # 응답이 없는 경우
                if not response:
                    self._queue_ui_task(messagebox.showerror, "오류", "LLM 응답을 받지 못했습니다.")
                    return
                
                # 응답 처리
                self._queue_ui_task(self._handle_llm_response, response)
            
            except Exception as e:
                logger.error(f"LLM 응답 요청 중 오류 발생: {str(e)}")
                
                # 로딩 프레임 제거
                if loading_frame and loading_frame.winfo_exists():
                    self._queue_ui_task(loading_frame.destroy)
                
                # 오류 메시지 표시
                self._queue_ui_task(messagebox.showerror, "오류", f"LLM 응답 요청 중 오류 발생: {str(e)}")
        
        # 별도 스레드에서 실행 (UI 블로킹 방지)
        threading.Thread(target=request_response, daemon=True).start()
    
    def _handle_llm_response(self, response):
        """응답 처리 함수"""
        # 응답 메시지 추가
        message = self.conversation_manager.add_message("assistant", response)
        
        if not message:
            return
        
        # UI 업데이트
        self._add_message_bubble("assistant", response, message.timestamp)
        
        # 대화 저장
        self.conversation_manager.save_conversation()
    

    
    def _on_message_added(self, conversation_id=None, message_id=None, role=None):
        """메시지 추가 이벤트 핸들러"""
        # 활성 대화에 대한 이벤트만 처리
        if conversation_id != self.conversation_status["active_id"].get():
            return
        
        # 메시지 카운트 업데이트
        conversation = self.conversation_manager.get_active_conversation()
        if conversation:
            self.conversation_status["message_count"].set(len(conversation.messages))
    
    def _on_conversation_loaded(self, conversation_id=None):
        """대화 로드 이벤트 핸들러"""
        # 이미 활성화된 대화인 경우 아무것도 하지 않음
        if conversation_id == self.conversation_status["active_id"].get():
            return
        
        # 대화 가져오기
        conversation = self.conversation_manager.get_active_conversation()
        
        if not conversation or conversation.conversation_id != conversation_id:
            return
        
        # UI 업데이트
        self.conversation_status["active_id"].set(conversation.conversation_id)
        self.conversation_status["active_title"].set(conversation.title)
        self.conversation_status["message_count"].set(len(conversation.messages))
        
        # 대화 내용 표시
        self._display_conversation(conversation)
    
    def _search_vector_db(self):
        """벡터 DB 검색"""
        if not self.vector_db:
            messagebox.showinfo("알림", "벡터 DB가 초기화되지 않았습니다.")
            return
        
        # 검색어 가져오기
        query = self.search_entry.get().strip()
        
        if not query:
            messagebox.showinfo("알림", "검색어를 입력하세요.")
            return
        
        # 검색 결과 창
        results_window = tk.Toplevel(self.root)
        results_window.title("검색 결과")
        results_window.geometry("600x400")
        results_window.transient(self.root)
        
        # 검색 결과 프레임
        results_frame = ttk.Frame(results_window, padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # 검색 중 메시지
        loading_label = ttk.Label(results_frame, text="검색 중...")
        loading_label.pack(pady=20)
        
        def perform_search():
            try:
                # 검색 실행
                results = self.vector_db.search(query, k=5)
                
                # 로딩 라벨 제거
                results_window.after(0, lambda: loading_label.destroy())
                
                if not results:
                    # 결과 없음 메시지
                    results_window.after(0, lambda: ttk.Label(
                        results_frame, text="검색 결과가 없습니다."
                    ).pack(pady=20))
                    return
                
                # 결과 표시
                results_window.after(0, lambda: self._display_search_results(results_frame, results))
            
            except Exception as e:
                logger.error(f"벡터 DB 검색 중 오류 발생: {str(e)}")
                
                # 로딩 라벨 제거
                results_window.after(0, lambda: loading_label.destroy())
                
                # 오류 메시지
                results_window.after(0, lambda: ttk.Label(
                    results_frame, text=f"검색 중 오류 발생: {str(e)}"
                ).pack(pady=20))
        
        # 별도 스레드에서 실행 (UI 블로킹 방지)
        threading.Thread(target=perform_search, daemon=True).start()
    
    def _display_search_results(self, parent: ttk.Frame, results: List[Tuple[Document, float]]):
        """검색 결과 표시"""
        # 결과 캔버스 (스크롤 지원)
        canvas = tk.Canvas(parent)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 결과 내용 프레임
        results_content = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=results_content, anchor=tk.NW, tags="content")
        
        # 각 결과 표시
        for i, (doc, score) in enumerate(results):
            # 결과 프레임
            result_frame = ttk.Frame(results_content, padding=10)
            result_frame.pack(fill=tk.X, pady=5)
            
            # 순위 및 점수
            header_frame = ttk.Frame(result_frame)
            header_frame.pack(fill=tk.X)
            
            ttk.Label(header_frame, text=f"#{i+1}", font=("TkDefaultFont", 10, "bold")).pack(side=tk.LEFT)
            ttk.Label(header_frame, text=f"유사도: {score:.4f}", font=("TkDefaultFont", 9)).pack(side=tk.RIGHT)
            
            # 문서 ID
            id_label = ttk.Label(result_frame, text=f"ID: {doc.id}", font=("TkDefaultFont", 8))
            id_label.pack(anchor=tk.W, pady=(5, 0))
            
            # 문서 내용
            text_frame = ttk.Frame(result_frame, padding=5)
            text_frame.pack(fill=tk.X, pady=5)
            
            text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=4, width=60)
            text_widget.insert(tk.END, doc.text)
            text_widget.configure(state=tk.DISABLED)  # 읽기 전용으로 설정
            text_widget.pack(fill=tk.X)
            
            # 메타데이터 (있는 경우)
            if doc.metadata:
                meta_label = ttk.Label(result_frame, text="메타데이터:", font=("TkDefaultFont", 8))
                meta_label.pack(anchor=tk.W, pady=(5, 0))
                
                import json
                meta_text = json.dumps(doc.metadata, ensure_ascii=False, indent=2)
                
                meta_widget = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=2, width=60)
                meta_widget.insert(tk.END, meta_text)
                meta_widget.configure(state=tk.DISABLED)  # 읽기 전용으로 설정
                meta_widget.pack(fill=tk.X, pady=(0, 5))
            
            # 추가 버튼 (대화에 추가)
            ttk.Button(result_frame, text="대화에 추가", 
                       command=lambda text=doc.text: self._add_to_conversation(text)).pack(anchor=tk.E)
        
        # 프레임 크기 변경 시 Canvas 스크롤 영역 업데이트
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        results_content.bind("<Configure>", on_frame_configure)
    
    def _add_to_conversation(self, text: str):
        """검색 결과를 현재 대화에 추가"""
        # 활성 대화 확인
        conversation = self.conversation_manager.get_active_conversation()
        
        if not conversation:
            messagebox.showinfo("알림", "먼저 대화를 생성하거나 열어야 합니다.")
            return
        
        # 메시지 입력 필드에 텍스트 추가
        self.message_entry.delete("1.0", tk.END)
        self.message_entry.insert(tk.END, text)

    def _on_add_reference(self, text=None):
        """다른 모듈에서 현재 대화에 참조 정보 추가 시 호출되는 핸들러"""
        if not text:
            return
            
        # 노트북에서 대화 탭으로 전환
        self.main_notebook.select(0)  # 첫 번째 탭(대화 탭)으로 전환
        
        # 메시지 입력 필드에 텍스트 추가
        self.message_entry.delete("1.0", tk.END)
        self.message_entry.insert(tk.END, text)
        
        # 입력 필드에 포커스
        self.message_entry.focus_set()
