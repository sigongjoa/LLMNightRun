"""
채팅 패널 구성 요소

대화 내용을 표시하고 스크롤을 지원하는 패널 위젯입니다.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, List, Dict, Any

from .message_bubble import MessageBubble

class ChatPanel(ttk.Frame):
    """채팅 패널 위젯"""
    
    def __init__(self, parent, **kwargs):
        """
        채팅 패널 초기화
        
        Args:
            parent: 부모 위젯
            **kwargs: 추가 위젯 옵션
        """
        # 부모 초기화
        super().__init__(parent, **kwargs)
        
        # 캔버스와 프레임 생성
        self._create_canvas()
    
    def _create_canvas(self):
        """캔버스 및 메시지 프레임 생성"""
        # 캔버스 생성 (스크롤 지원)
        self.canvas = tk.Canvas(self, bg="#ffffff")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 메시지를 담을 프레임
        self.message_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.message_frame, anchor=tk.NW, tags="message_frame"
        )
        
        # 프레임 크기 변경 시 캔버스 스크롤 영역 업데이트
        self.message_frame.bind("<Configure>", self._on_frame_configure)
        
        # 캔버스 크기 변경 시 내부 윈도우 너비 조정
        self.canvas.bind("<Configure>", self._on_canvas_configure)
    
    def _on_frame_configure(self, event):
        """프레임 크기 변경 이벤트 처리"""
        # 스크롤 영역 업데이트
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_canvas_configure(self, event):
        """캔버스 크기 변경 이벤트 처리"""
        # 내부 윈도우 너비 조정
        width = event.width
        self.canvas.itemconfig(self.canvas_window, width=width)
    
    def add_message(self, role: str, content: str, timestamp=None) -> MessageBubble:
        """
        메시지 추가
        
        Args:
            role: 메시지 역할 ('user', 'assistant', 'system' 등)
            content: 메시지 내용
            timestamp: 타임스탬프 (선택 사항)
        
        Returns:
            생성된 메시지 버블 위젯
        """
        # 메시지 버블 생성
        message = MessageBubble(
            self.message_frame, role=role, content=content, timestamp=timestamp
        )
        message.pack(fill=tk.X, padx=10, pady=5)
        
        # 스크롤을 아래로 이동
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        
        return message
    
    def clear(self):
        """모든 메시지 지우기"""
        # 프레임 내 모든 위젯 제거
        for widget in self.message_frame.winfo_children():
            widget.destroy()
        
        # 스크롤 영역 업데이트
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """
        모든 메시지 가져오기
        
        Returns:
            메시지 목록 (딕셔너리 형태)
        """
        messages = []
        
        # 모든 메시지 버블 위젯 찾기
        for widget in self.message_frame.winfo_children():
            if isinstance(widget, MessageBubble):
                # 역할 결정
                role_text = widget.role_label["text"]
                role = "user" if role_text == "사용자" else "assistant" if role_text == "어시스턴트" else role_text.lower()
                
                # 내용 가져오기
                content = widget.get_content()
                
                # 딕셔너리 추가
                messages.append({
                    "role": role,
                    "content": content
                })
        
        return messages
    
    def scroll_to_bottom(self):
        """스크롤을 아래로 이동"""
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
    
    def add_loading_indicator(self) -> ttk.Frame:
        """
        로딩 표시기 추가
        
        Returns:
            로딩 표시기 프레임 (나중에 제거할 수 있도록)
        """
        # 로딩 프레임
        loading_frame = ttk.Frame(self.message_frame, padding=10)
        loading_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 로딩 라벨
        loading_label = ttk.Label(loading_frame, text="응답 생성 중...")
        loading_label.pack(anchor=tk.W)
        
        # 스크롤을 아래로 이동
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        
        return loading_frame
