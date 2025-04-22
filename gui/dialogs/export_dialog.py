"""
대화 내보내기 대화 상자

대화를 다양한 형식으로 내보내기 위한 대화 상자를 제공합니다.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any, Callable

class ExportDialog:
    """대화 내보내기 대화 상자"""
    
    def __init__(self, parent, conversation_title: str,
                on_export: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        """
        대화 내보내기 대화 상자 초기화
        
        Args:
            parent: 부모 윈도우
            conversation_title: 대화 제목 (파일명 제안용)
            on_export: 내보내기 콜백 (형식과 옵션을 인자로 받음)
        """
        self.parent = parent
        self.conversation_title = conversation_title
        self.on_export = on_export
        
        # 대화 상자 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("대화 내보내기")
        self.dialog.geometry("350x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 설정 프레임
        self.format_frame = ttk.Frame(self.dialog, padding="10")
        self.format_frame.pack(fill=tk.BOTH, expand=True)
        
        # UI 요소 추가
        self._create_ui()
    
    def _create_ui(self):
        """UI 요소 생성"""
        # 형식 선택 라벨
        ttk.Label(self.format_frame, text="내보내기 형식:", 
                 font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # 형식 선택 라디오 버튼
        self.format_var = tk.StringVar(value="json")
        
        ttk.Radiobutton(self.format_frame, text="JSON", value="json", 
                       variable=self.format_var).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(self.format_frame, text="Markdown", value="markdown", 
                       variable=self.format_var).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(self.format_frame, text="텍스트", value="text", 
                       variable=self.format_var).pack(anchor=tk.W, pady=2)
        
        # 형식 선택에 따른 파일 확장자 변경
        def update_file_extension(*args):
            selected_format = self.format_var.get()
            if selected_format == "json":
                self.file_ext_label.configure(text="파일 확장자: .json")
            elif selected_format == "markdown":
                self.file_ext_label.configure(text="파일 확장자: .md")
            else:  # text
                self.file_ext_label.configure(text="파일 확장자: .txt")
        
        # 파일 확장자 표시 라벨
        self.file_ext_label = ttk.Label(self.format_frame, text="파일 확장자: .json")
        self.file_ext_label.pack(anchor=tk.W, pady=(5, 10))
        
        # 형식 변경 시 확장자 업데이트
        self.format_var.trace_add("write", update_file_extension)
        
        # 옵션 체크박스
        ttk.Label(self.format_frame, text="옵션:").pack(anchor=tk.W, pady=(5, 0))
        
        self.include_metadata_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.format_frame, text="메타데이터 포함", 
                       variable=self.include_metadata_var).pack(anchor=tk.W, pady=(5, 0))
        
        self.include_timestamps_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.format_frame, text="타임스탬프 포함", 
                       variable=self.include_timestamps_var).pack(anchor=tk.W, pady=(5, 0))
        
        # 버튼 프레임
        button_frame = ttk.Frame(self.format_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # 내보내기 및 취소 버튼
        ttk.Button(button_frame, text="내보내기", 
                  command=self._on_export).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="취소", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _on_export(self):
        """내보내기 버튼 클릭 이벤트"""
        # 선택한 형식 가져오기
        selected_format = self.format_var.get()
        
        # 파일 확장자 설정
        if selected_format == "json":
            file_ext = ".json"
            file_types = [("JSON 파일", "*.json"), ("모든 파일", "*.*")]
        elif selected_format == "markdown":
            file_ext = ".md"
            file_types = [("Markdown 파일", "*.md"), ("모든 파일", "*.*")]
        else:  # text
            file_ext = ".txt"
            file_types = [("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
        
        # 대화 제목에서 파일명 제안
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in self.conversation_title)
        default_filename = f"{safe_title}{file_ext}"
        
        # 저장 경로 선택
        save_path = filedialog.asksaveasfilename(
            parent=self.dialog,
            defaultextension=file_ext,
            filetypes=file_types,
            initialfile=default_filename
        )
        
        if not save_path:
            return  # 사용자가 취소함
        
        # 내보내기 옵션 수집
        options = {
            "format": selected_format,
            "include_metadata": self.include_metadata_var.get(),
            "include_timestamps": self.include_timestamps_var.get(),
            "file_path": save_path
        }
        
        # 콜백 호출
        if self.on_export:
            self.on_export(selected_format, options)
        
        # 대화 상자 닫기
        self.dialog.destroy()
