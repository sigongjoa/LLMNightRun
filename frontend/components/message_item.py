"""
MessageItem is a widget that displays a single message in the chat.
"""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QSizePolicy, QMenu, QApplication, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QIcon, QFont, QAction, QContextMenuEvent, QCursor, QClipboard

class MessageItem(QFrame):
    def __init__(self, role, content):
        super().__init__()
        
        self.role = role
        self.content = content
        self.timestamp = time.time()
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Set properties based on role
        if self.role == "user":
            self.setObjectName("userMessage")
        else:
            self.setObjectName("assistantMessage")
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(8)
        
        # Header layout
        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 5)
        self.header_layout.setSpacing(10)
        
        # Role label
        role_text = "You" if self.role == "user" else "Assistant"
        self.role_label = QLabel(role_text)
        self.role_label.setObjectName("roleLabel")
        self.role_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        # Timestamp label
        timestamp_text = time.strftime("%H:%M", time.localtime(self.timestamp))
        self.timestamp_label = QLabel(timestamp_text)
        self.timestamp_label.setObjectName("timestampLabel")
        self.timestamp_label.setFont(QFont("Arial", 9))
        self.timestamp_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.header_layout.addWidget(self.role_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.timestamp_label)
        
        # Use QLabel for content with proper word wrapping
        self.content_label = QLabel(self.content)
        self.content_label.setObjectName("contentLabel")
        self.content_label.setWordWrap(True)
        self.content_label.setTextFormat(Qt.TextFormat.PlainText)
        self.content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        
        # Add widgets to layout
        self.layout.addLayout(self.header_layout)
        self.layout.addWidget(self.content_label)
        
        # Set frame style
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # Set up context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, position):
        """Show context menu."""
        menu = QMenu(self)
        
        # Copy message action
        copy_action = QAction("Copy Message", self)
        copy_action.triggered.connect(self._copy_message)
        menu.addAction(copy_action)
        
        # If assistant message, add more options
        if self.role == "assistant":
            # Copy code blocks action
            code_blocks = self._extract_code_blocks(self.content)
            if code_blocks:
                copy_code_action = QAction("Copy Code Blocks", self)
                copy_code_action.triggered.connect(self._copy_code_blocks)
                menu.addAction(copy_code_action)
        
        # Show menu
        menu.exec(self.mapToGlobal(position))
    
    def _copy_message(self):
        """Copy message content to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.content)
    
    def _copy_code_blocks(self):
        """Copy code blocks to clipboard."""
        code_blocks = self._extract_code_blocks(self.content)
        if not code_blocks:
            return
        
        # Combine all code blocks
        combined_code = "\n\n".join([block.get("code", "") for block in code_blocks])
        
        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(combined_code)
    
    def _extract_code_blocks(self, text):
        """Extract code blocks from text."""
        import re
        
        code_blocks = []
        pattern = r'```(\w*)\n(.*?)```'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            language = match.group(1).strip().lower() or "text"
            code = match.group(2).strip()
            code_blocks.append({
                "language": language,
                "code": code
            })
        
        return code_blocks
    
    def get_content(self):
        """Get message content."""
        return self.content
    
    def get_role(self):
        """Get message role."""
        return self.role
    
    def get_timestamp(self):
        """Get message timestamp."""
        return self.timestamp
