"""
메시지 버블 구성 요소

대화 내용을 표시하기 위한 메시지 버블 위젯을 제공합니다.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, Any

class MessageBubble(ttk.Frame):
    """메시지 버블 위젯"""
    
    def __init__(self, parent, role: str, content: str, timestamp=None, **kwargs):
        """
        메시지 버블 초기화
        
        Args:
            parent: 부모 위젯
            role: 메시지 역할 ('user', 'assistant', 'system' 등)
            content: 메시지 내용
            timestamp: 타임스탬프 (선택 사항)
            **kwargs: 추가 위젯 옵션
        """
        # 역할에 따른 스타일 결정
        style = "UserMessage.TFrame" if role == "user" else "AssistantMessage.TFrame"
        
        # 부모 초기화
        super().__init__(parent, style=style, padding=10, **kwargs)
        
        # 역할 라벨
        role_text = "사용자" if role == "user" else "어시스턴트" if role == "assistant" else role.capitalize()
        self.role_label = ttk.Label(self, text=role_text, font=("TkDefaultFont", 9, "bold"))
        self.role_label.pack(anchor=tk.W)
        
        # 타임스탬프 라벨 (있는 경우)
        if timestamp:
            if isinstance(timestamp, str):
                time_text = timestamp
            else:
                time_text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            self.time_label = ttk.Label(self, text=time_text, font=("TkDefaultFont", 8))
            self.time_label.pack(anchor=tk.W)
        
        # 내용 텍스트
        line_count = content.count('\n') + 2
        height = min(15, line_count)  # 최대 높이 제한
        
        self.content_text = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, height=height, width=60, font=("TkTextFont", 10)
        )
        self.content_text.insert(tk.END, content)
        self.content_text.configure(state=tk.DISABLED)  # 읽기 전용으로 설정
        self.content_text.pack(fill=tk.X, pady=(5, 0))

    def get_content(self) -> str:
        """
        메시지 내용 가져오기
        
        Returns:
            메시지 내용
        """
        # 내용 가져오기 (읽기 전용 상태 임시 해제)
        self.content_text.configure(state=tk.NORMAL)
        content = self.content_text.get("1.0", tk.END).strip()
        self.content_text.configure(state=tk.DISABLED)
        
        return content
