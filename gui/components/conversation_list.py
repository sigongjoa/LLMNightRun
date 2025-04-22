"""
대화 목록 구성 요소

저장된 대화들을 목록으로 표시하고 관리하는 구성 요소입니다.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Dict, Any, Callable

class ConversationList(ttk.Frame):
    """대화 목록 위젯"""
    
    def __init__(self, parent, on_select: Optional[Callable[[str], None]] = None, **kwargs):
        """
        대화 목록 초기화
        
        Args:
            parent: 부모 위젯
            on_select: 대화 선택 콜백 (conversation_id를 인자로 받음)
            **kwargs: 추가 위젯 옵션
        """
        # 부모 초기화
        super().__init__(parent, **kwargs)
        
        # 콜백 저장
        self.on_select = on_select
        
        # 트리뷰 생성
        self._create_treeview()
        
        # 버튼 생성
        self._create_buttons()
    
    def _create_treeview(self):
        """트리뷰 생성"""
        # 프레임 생성
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 트리뷰 열 정의
        columns = ("title", "date")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.tree.heading("title", text="제목")
        self.tree.heading("date", text="날짜")
        self.tree.column("title", width=150)
        self.tree.column("date", width=100)
        
        # 스크롤바 추가
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 배치
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 선택 이벤트 바인딩
        self.tree.bind("<<TreeviewSelect>>", self._on_item_select)
    
    def _create_buttons(self):
        """버튼 생성"""
        # 버튼 프레임
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 새로고침 버튼
        self.refresh_button = ttk.Button(button_frame, text="새로고침", command=self._on_refresh)
        self.refresh_button.pack(fill=tk.X)
    
    def _on_item_select(self, event):
        """항목 선택 이벤트 처리"""
        if not self.on_select:
            return
        
        # 선택된 항목 가져오기
        selected_items = self.tree.selection()
        if not selected_items:
            return
        
        # 선택된 항목의 인덱스 (아이템 ID 아님)
        item = selected_items[0]
        
        # 커스텀 ID가 있으면 사용
        conversation_id = self.tree.item(item, "values")[-1] if len(self.tree.item(item, "values")) > 2 else None
        
        # 콜백 호출
        if conversation_id:
            self.on_select(conversation_id)
    
    def _on_refresh(self):
        """새로고침 버튼 이벤트 처리"""
        # 여기서는 외부에서 필요에 따라 set_conversations를 호출해야 함
        pass
    
    def set_conversations(self, conversations: List[Dict[str, Any]], active_id: Optional[str] = None):
        """
        대화 목록 설정
        
        Args:
            conversations: 대화 목록 (딕셔너리 리스트)
            active_id: 활성 대화 ID (선택 사항)
        """
        # 기존 항목 제거
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 대화 목록 추가
        for conversation in conversations:
            # 기본 표시 값
            values = [
                conversation.get("title", "Untitled"),
                conversation.get("updated_at", "")
            ]
            
            # 숨겨진 ID 추가
            if "conversation_id" in conversation:
                values.append(conversation["conversation_id"])
            
            # 트리뷰에 추가
            item_id = self.tree.insert("", tk.END, values=values)
            
            # 활성 대화 선택
            if active_id and conversation.get("conversation_id") == active_id:
                self.tree.selection_set(item_id)
                self.tree.see(item_id)  # 선택한 항목으로 스크롤
    
    def get_selected_id(self) -> Optional[str]:
        """
        선택된 대화 ID 가져오기
        
        Returns:
            선택된 대화 ID 또는 None
        """
        selected = self.tree.selection()
        if not selected:
            return None
        
        # 값 가져오기
        values = self.tree.item(selected[0], "values")
        
        # ID가 숨겨진 값으로 포함되어 있는 경우
        if len(values) > 2:
            return values[2]
        
        return None
