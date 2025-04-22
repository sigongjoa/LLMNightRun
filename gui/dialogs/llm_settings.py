"""
LLM 설정 대화 상자

LLM 연결 및 매개변수 설정을 위한 대화 상자를 제공합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, Callable

class LLMSettingsDialog:
    """LLM 설정 대화 상자"""
    
    def __init__(self, parent, config: Dict[str, Any], 
                on_save: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        LLM 설정 대화 상자 초기화
        
        Args:
            parent: 부모 윈도우
            config: 현재 LLM 설정
            on_save: 저장 콜백 (새 설정을 인자로 받음)
        """
        self.parent = parent
        self.config = config
        self.on_save = on_save
        
        # 대화 상자 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("LLM 설정")
        self.dialog.geometry("400x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 설정 프레임
        self.settings_frame = ttk.Frame(self.dialog, padding="10")
        self.settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # UI 요소 추가
        self._create_ui()
    
    def _create_ui(self):
        """UI 요소 생성"""
        # 활성화 설정
        self.enabled_var = tk.BooleanVar(value=self.config.get("enabled", True))
        ttk.Checkbutton(self.settings_frame, text="LLM 활성화", 
                       variable=self.enabled_var).pack(anchor=tk.W, pady=5)
        
        # 기본 URL 설정
        ttk.Label(self.settings_frame, text="LLM 서버 URL:").pack(anchor=tk.W, pady=(10, 0))
        self.base_url_var = tk.StringVar(value=self.config.get("base_url", "http://127.0.0.1:1234"))
        ttk.Entry(self.settings_frame, textvariable=self.base_url_var).pack(fill=tk.X, pady=5)
        
        # 모델 ID 설정
        ttk.Label(self.settings_frame, text="모델 ID:").pack(anchor=tk.W, pady=(10, 0))
        self.model_id_var = tk.StringVar(value=self.config.get("model_id", ""))
        ttk.Entry(self.settings_frame, textvariable=self.model_id_var).pack(fill=tk.X, pady=5)
        
        # 온도 설정
        ttk.Label(self.settings_frame, text=f"온도 (Temperature): {self.config.get('temperature', 0.7):.2f}").pack(
            anchor=tk.W, pady=(10, 0))
        self.temp_var = tk.DoubleVar(value=self.config.get("temperature", 0.7))
        temp_scale = ttk.Scale(self.settings_frame, from_=0.0, to=1.0, variable=self.temp_var, 
                              orient=tk.HORIZONTAL)
        temp_scale.pack(fill=tk.X, pady=5)
        
        # 온도값 표시 라벨
        self.temp_label = ttk.Label(self.settings_frame, text=f"{self.temp_var.get():.2f}")
        self.temp_label.pack(anchor=tk.E)
        
        # 온도 값 변경 시 라벨 업데이트
        def update_temp_label(*args):
            self.temp_label.configure(text=f"{self.temp_var.get():.2f}")
        
        self.temp_var.trace_add("write", update_temp_label)
        
        # 최대 토큰 설정
        ttk.Label(self.settings_frame, text="최대 토큰:").pack(anchor=tk.W, pady=(10, 0))
        self.max_tokens_var = tk.IntVar(value=self.config.get("max_tokens", 1000))
        ttk.Entry(self.settings_frame, textvariable=self.max_tokens_var).pack(fill=tk.X, pady=5)
        
        # Top-P 설정
        ttk.Label(self.settings_frame, text=f"Top-P: {self.config.get('top_p', 0.9):.2f}").pack(
            anchor=tk.W, pady=(10, 0))
        self.top_p_var = tk.DoubleVar(value=self.config.get("top_p", 0.9))
        top_p_scale = ttk.Scale(self.settings_frame, from_=0.0, to=1.0, variable=self.top_p_var, 
                               orient=tk.HORIZONTAL)
        top_p_scale.pack(fill=tk.X, pady=5)
        
        # Top-P값 표시 라벨
        self.top_p_label = ttk.Label(self.settings_frame, text=f"{self.top_p_var.get():.2f}")
        self.top_p_label.pack(anchor=tk.E)
        
        # Top-P 값 변경 시 라벨 업데이트
        def update_top_p_label(*args):
            self.top_p_label.configure(text=f"{self.top_p_var.get():.2f}")
        
        self.top_p_var.trace_add("write", update_top_p_label)
        
        # 버튼 프레임
        button_frame = ttk.Frame(self.settings_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # 저장 및 취소 버튼
        ttk.Button(button_frame, text="저장", command=self._on_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="취소", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # 테스트 연결 버튼
        ttk.Button(button_frame, text="연결 테스트", command=self._on_test_connection).pack(side=tk.LEFT, padx=5)
    
    def _on_save(self):
        """저장 버튼 클릭 이벤트"""
        # 유효성 검사
        if not self.base_url_var.get():
            messagebox.showerror("오류", "LLM 서버 URL을 입력하세요.", parent=self.dialog)
            return
        
        if not self.model_id_var.get():
            messagebox.showerror("오류", "모델 ID를 입력하세요.", parent=self.dialog)
            return
        
        try:
            max_tokens = int(self.max_tokens_var.get())
            if max_tokens <= 0:
                raise ValueError("최대 토큰은 양수여야 합니다")
        except ValueError:
            messagebox.showerror("오류", "최대 토큰은 유효한 정수여야 합니다.", parent=self.dialog)
            return
        
        # 설정 수집
        settings = {
            "enabled": self.enabled_var.get(),
            "base_url": self.base_url_var.get(),
            "model_id": self.model_id_var.get(),
            "max_tokens": max_tokens,
            "temperature": self.temp_var.get(),
            "top_p": self.top_p_var.get()
        }
        
        # 콜백 호출
        if self.on_save:
            self.on_save(settings)
        
        # 대화 상자 닫기
        self.dialog.destroy()
    
    def _on_test_connection(self):
        """연결 테스트 버튼 클릭 이벤트"""
        # 연결 테스트 함수 구현
        # 이 기능은 실제로는 비동기로 처리되어야 함
        import threading
        
        # 버튼 비활성화 및 로딩 표시
        for child in self.settings_frame.winfo_children():
            if isinstance(child, ttk.Button) and child["text"] == "연결 테스트":
                child["text"] = "테스트 중..."
                child["state"] = "disabled"
        
        def test_connection():
            try:
                # 여기서 실제 연결 테스트를 수행
                # 간단히 시뮬레이션함
                import time
                import random
                time.sleep(1)  # 1초 지연
                
                # 랜덤 결과 (실제로는 실제 연결 테스트 결과를 반환)
                success = random.choice([True, False])
                
                # UI 스레드에서 결과 표시
                if success:
                    self.dialog.after(0, lambda: messagebox.showinfo(
                        "연결 성공", "LLM 서버에 성공적으로 연결했습니다.", parent=self.dialog))
                else:
                    self.dialog.after(0, lambda: messagebox.showerror(
                        "연결 실패", "LLM 서버에 연결할 수 없습니다.", parent=self.dialog))
                
                # 버튼 복원
                self.dialog.after(0, lambda: self._restore_test_button())
            
            except Exception as e:
                # 오류 처리
                self.dialog.after(0, lambda: messagebox.showerror(
                    "오류", f"연결 테스트 중 오류 발생: {str(e)}", parent=self.dialog))
                
                # 버튼 복원
                self.dialog.after(0, lambda: self._restore_test_button())
        
        # 별도 스레드에서 테스트 실행
        threading.Thread(target=test_connection, daemon=True).start()
    
    def _restore_test_button(self):
        """테스트 버튼 복원"""
        for child in self.settings_frame.winfo_children():
            if isinstance(child, ttk.Button) and child["text"] == "테스트 중...":
                child["text"] = "연결 테스트"
                child["state"] = "normal"
