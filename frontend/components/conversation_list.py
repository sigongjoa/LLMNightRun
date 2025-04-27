"""
ConversationList is a widget that displays a list of conversations.
It allows creating new conversations and selecting existing ones.
"""

import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QSizePolicy, QScrollArea, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QIcon, QFont, QAction

class ConversationItem(QFrame):
    """Widget representing a single conversation in the list."""
    
    clicked = pyqtSignal(str)  # Signal when item is clicked (conversation ID)
    deleted = pyqtSignal(str)  # Signal when item is deleted (conversation ID)
    
    def __init__(self, conversation, parent=None):
        super().__init__(parent)
        
        self.conversation = conversation
        self.conversation_id = conversation.get("id")
        
        self.setObjectName("conversationItem")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(60)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(2)
        
        # Title
        self.title_label = QLabel(self._get_title())
        self.title_label.setObjectName("conversationTitle")
        self.title_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)
        
        # Timestamp
        timestamp_text = self._format_timestamp(self.conversation.get("updated_at", 0))
        self.timestamp_label = QLabel(timestamp_text)
        self.timestamp_label.setObjectName("conversationTimestamp")
        self.timestamp_label.setFont(QFont("Arial", 8))
        
        # Add widgets to layout
        self.layout.addWidget(self.title_label)
        self.layout.addWidget(self.timestamp_label)
        
        # Set up context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
    
    def _get_title(self):
        """Get conversation title from first user message."""
        messages = self.conversation.get("messages", [])
        
        # Get first user message
        user_messages = [m for m in messages if m.get("role") == "user"]
        if user_messages:
            # Use first line of first user message as title
            content = user_messages[0].get("content", "")
            title = content.split("\n")[0]
            
            # Truncate if too long
            if len(title) > 40:
                title = title[:37] + "..."
            
            return title
        
        # Fallback title
        return "New Conversation"
    
    def _format_timestamp(self, timestamp):
        """Format timestamp for display."""
        if not timestamp:
            return ""
        
        # Get current time
        current_time = time.time()
        delta = current_time - timestamp
        
        # Format based on age
        if delta < 60:  # Less than a minute
            return "Just now"
        elif delta < 3600:  # Less than an hour
            minutes = int(delta / 60)
            return f"{minutes}m ago"
        elif delta < 86400:  # Less than a day
            hours = int(delta / 3600)
            return f"{hours}h ago"
        else:  # More than a day
            return time.strftime("%Y-%m-%d", time.localtime(timestamp))
    
    def _show_context_menu(self, position):
        """Show context menu."""
        menu = QMenu(self)
        
        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(delete_action)
        
        # Show menu
        menu.exec(self.mapToGlobal(position))
    
    def _on_delete(self):
        """Handle delete action."""
        self.deleted.emit(self.conversation_id)
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        super().mousePressEvent(event)
        self.clicked.emit(self.conversation_id)
    
    def setSelected(self, selected):
        """Set selected state."""
        if selected:
            self.setProperty("selected", True)
        else:
            self.setProperty("selected", False)
        
        # Force style update
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

class ConversationList(QWidget):
    """Widget displaying a list of conversations."""
    
    conversation_selected = pyqtSignal(str)  # Signal when conversation is selected (conversation ID)
    new_conversation = pyqtSignal()  # Signal when new conversation is requested
    
    def __init__(self, chat_engine, parent=None):
        super().__init__(parent)
        
        self.chat_engine = chat_engine
        self.conversation_items = {}  # Map of conversation ID to ConversationItem
        self.selected_conversation_id = None
        
        self._init_ui()
        self._load_conversations()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header
        self.header = QFrame()
        self.header.setObjectName("conversationListHeader")
        self.header.setMinimumHeight(50)
        
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(15, 5, 15, 5)
        
        self.new_chat_button = QPushButton("+ New Chat")
        self.new_chat_button.setObjectName("newChatButton")
        self.new_chat_button.clicked.connect(self._on_new_chat)
        
        self.header_layout.addWidget(self.new_chat_button)
        
        # List container
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("conversationScrollArea")
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(10, 10, 10, 10)
        self.list_layout.setSpacing(5)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.list_container)
        
        # Today label
        self.today_label = QLabel("Today")
        self.today_label.setObjectName("todayLabel")
        self.today_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.list_layout.addWidget(self.today_label)
        
        # Add widgets to main layout
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.scroll_area)
    
    def _load_conversations(self):
        """Load conversations from chat engine."""
        # Clear current items
        self._clear_items()
        
        # Get conversations from chat engine
        conversations = self.chat_engine.get_all_conversations()
        
        # Add items for each conversation
        for conversation in conversations:
            self._add_conversation_item(conversation)
        
        # Update today label visibility
        self.today_label.setVisible(len(conversations) > 0)
    
    def _clear_items(self):
        """Clear all conversation items."""
        # Remove all items after the "Today" label
        for i in range(self.list_layout.count() - 1, 0, -1):
            item = self.list_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear item map
        self.conversation_items = {}
    
    def _add_conversation_item(self, conversation):
        """Add an item for a conversation."""
        conversation_id = conversation.get("id")
        
        # Create item
        item = ConversationItem(conversation)
        item.clicked.connect(self._on_conversation_clicked)
        item.deleted.connect(self._on_conversation_deleted)
        
        # Add to layout and map
        self.list_layout.addWidget(item)
        self.conversation_items[conversation_id] = item
        
        # Set selected if this is the selected conversation
        if conversation_id == self.selected_conversation_id:
            item.setSelected(True)
    
    def _on_conversation_clicked(self, conversation_id):
        """Handle conversation item click."""
        # Update selected state
        if self.selected_conversation_id:
            if self.selected_conversation_id in self.conversation_items:
                self.conversation_items[self.selected_conversation_id].setSelected(False)
        
        self.selected_conversation_id = conversation_id
        self.conversation_items[conversation_id].setSelected(True)
        
        # Emit signal
        self.conversation_selected.emit(conversation_id)
    
    def _on_conversation_deleted(self, conversation_id):
        """Handle conversation item deletion."""
        # Delete conversation from chat engine
        self.chat_engine.delete_conversation(conversation_id)
        
        # Remove item
        if conversation_id in self.conversation_items:
            item = self.conversation_items[conversation_id]
            self.list_layout.removeWidget(item)
            item.deleteLater()
            del self.conversation_items[conversation_id]
        
        # If this was the selected conversation, select another one or create a new one
        if conversation_id == self.selected_conversation_id:
            self.selected_conversation_id = None
            
            if self.conversation_items:
                # Select the first available conversation
                first_id = next(iter(self.conversation_items))
                self.select_conversation(first_id)
            else:
                # Create a new conversation
                self.new_conversation.emit()
        
        # Update today label visibility
        self.today_label.setVisible(len(self.conversation_items) > 0)
    
    def _on_new_chat(self):
        """Handle new chat button click."""
        self.new_conversation.emit()
    
    def select_conversation(self, conversation_id):
        """Select a conversation programmatically."""
        if conversation_id in self.conversation_items:
            self._on_conversation_clicked(conversation_id)
    
    def refresh(self):
        """Refresh the conversation list."""
        # Save selected ID
        selected_id = self.selected_conversation_id
        
        # Reload conversations
        self._load_conversations()
        
        # Restore selection
        if selected_id and selected_id in self.conversation_items:
            self.select_conversation(selected_id)
    
    def has_conversations(self):
        """Check if there are any conversations in the list."""
        return len(self.conversation_items) > 0
