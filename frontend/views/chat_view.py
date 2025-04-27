"""
ChatView is the main chat interface of the application.
It displays the conversation messages and allows sending new messages.
"""

import os
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QLabel,
    QPushButton, QTextEdit, QFrame, QSizePolicy, QSpacerItem,
    QMenu, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer, QThread
from PyQt6.QtGui import QIcon, QFont, QAction, QTextCursor, QColor

from frontend.components.message_item import MessageItem
from frontend.components.code_block import CodeBlock
from frontend.components.loading_indicator import LoadingIndicator

class ResponseThread(QThread):
    """Thread for generating responses in the background."""
    
    response_ready = pyqtSignal(dict)  # Signal for response (message object)
    error_occurred = pyqtSignal(str)   # Signal for errors (error message)
    
    def __init__(self, chat_engine, conversation_id):
        super().__init__()
        self.chat_engine = chat_engine
        self.conversation_id = conversation_id
    
    def run(self):
        """Run the response thread."""
        try:
            # Generate response
            response = self.chat_engine.generate_response(self.conversation_id)
            self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

class ChatView(QWidget):
    def __init__(self, chat_engine, model_manager, storage_manager):
        super().__init__()
        
        self.chat_engine = chat_engine
        self.model_manager = model_manager
        self.storage_manager = storage_manager
        
        self.current_conversation_id = None
        self.is_generating = False
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header
        self.header = QFrame()
        self.header.setObjectName("chatHeader")
        self.header.setMinimumHeight(50)
        self.header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(20, 10, 20, 10)
        
        self.model_label = QLabel("Model: Not selected")
        self.model_label.setObjectName("modelLabel")
        
        self.regenerate_button = QPushButton("Regenerate")
        self.regenerate_button.setObjectName("regenerateButton")
        self.regenerate_button.setEnabled(False)
        self.regenerate_button.clicked.connect(self._on_regenerate)
        
        self.header_layout.addWidget(self.model_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.regenerate_button)
        
        # Messages area with better handling for long content
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setWidgetResizable(True)  # Allow the content to resize
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.messages_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.messages_scroll.setObjectName("messagesScroll")
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(20, 20, 20, 20)
        self.messages_layout.setSpacing(20)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add a stretching spacer to push messages up
        self.messages_layout.addStretch()
        
        self.messages_scroll.setWidget(self.messages_container)
        
        # Input area
        self.input_frame = QFrame()
        self.input_frame.setObjectName("inputFrame")
        self.input_frame.setMinimumHeight(120)
        self.input_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.input_layout = QVBoxLayout(self.input_frame)
        self.input_layout.setContentsMargins(20, 10, 20, 10)
        
        self.text_input = QTextEdit()
        self.text_input.setObjectName("textInput")
        self.text_input.setPlaceholderText("Type a message...")
        self.text_input.setAcceptRichText(False)
        self.text_input.setMinimumHeight(80)
        self.text_input.setMaximumHeight(150)
        self.text_input.textChanged.connect(self._on_text_changed)
        
        # Button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        
        self.button_layout.addStretch()
        
        self.send_button = QPushButton("Send")
        self.send_button.setObjectName("sendButton")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self._on_send)
        
        self.button_layout.addWidget(self.send_button)
        
        self.input_layout.addWidget(self.text_input)
        self.input_layout.addLayout(self.button_layout)
        
        # Loading indicator
        self.loading_indicator = LoadingIndicator()
        self.loading_indicator.setVisible(False)
        
        # Add widgets to main layout
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.messages_scroll)
        self.layout.addWidget(self.loading_indicator)
        self.layout.addWidget(self.input_frame)
        
        # Set up key press event
        self.text_input.installEventFilter(self)
    
    def eventFilter(self, source, event):
        """Filter events for handling Enter key in text input."""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QKeyEvent
        
        if (source is self.text_input and event.type() == QEvent.Type.KeyPress):
            key_event = event
            
            # Check for Enter key (without shift)
            if (key_event.key() == Qt.Key.Key_Return or key_event.key() == Qt.Key.Key_Enter) and not key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Send message
                self._on_send()
                return True
            
            # Allow Shift+Enter for new line
            elif (key_event.key() == Qt.Key.Key_Return or key_event.key() == Qt.Key.Key_Enter) and key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                return False  # Let the text edit handle it
        
        # Pass event on
        return super().eventFilter(source, event)
    
    def load_conversation(self, conversation_id):
        """Load a conversation into the chat view."""
        self.current_conversation_id = conversation_id
        conversation = self.chat_engine.get_conversation(conversation_id)
        
        if not conversation:
            return
        
        # Clear messages
        self._clear_messages()
        
        # Update model label
        model_id = conversation.get("model_id")
        if model_id:
            model_info = self.model_manager.get_model_info(model_id)
            if model_info:
                self.model_label.setText(f"Model: {model_info.get('name', model_id)}")
            else:
                self.model_label.setText(f"Model: {model_id}")
        else:
            self.model_label.setText("Model: Not selected")
        
        # Add messages
        for message in conversation.get("messages", []):
            role = message.get("role")
            content = message.get("content")
            
            # Skip system messages
            if role == "system":
                continue
            
            # Add message to UI
            self._add_message(role, content)
        
        # Scroll to bottom
        QTimer.singleShot(100, self._scroll_to_bottom)
        
        # Enable regenerate button if there's at least one assistant message
        has_assistant_message = any(m.get("role") == "assistant" for m in conversation.get("messages", []))
        self.regenerate_button.setEnabled(has_assistant_message)
    
    def _clear_messages(self):
        """Clear all messages from the view."""
        # Remove all message widgets except the stretcher at the end
        while self.messages_layout.count() > 1:  # Keep the stretcher
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _add_message(self, role, content):
        """Add a message to the chat view."""
        # Insert the message before the stretcher
        insert_index = self.messages_layout.count() - 1
        
        # Create and add message item
        message_item = MessageItem(role, content)
        self.messages_layout.insertWidget(insert_index, message_item)
        
        # Process code blocks
        code_blocks = self._extract_code_blocks(content)
        for code_block in code_blocks:
            language = code_block.get("language")
            code = code_block.get("code")
            
            # Create code block widget
            code_widget = CodeBlock(language, code)
            insert_index += 1
            self.messages_layout.insertWidget(insert_index, code_widget)
    
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
    
    def _scroll_to_bottom(self):
        """Scroll to the bottom of the messages area."""
        scrollbar = self.messages_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _on_text_changed(self):
        """Handle text input changes."""
        # Enable/disable send button based on text content
        has_text = bool(self.text_input.toPlainText().strip())
        self.send_button.setEnabled(has_text)
    
    def _check_model_selected(self):
        """Check if a model is selected for the current conversation."""
        if not self.current_conversation_id:
            return False
            
        conversation = self.chat_engine.get_conversation(self.current_conversation_id)
        if not conversation:
            return False
            
        model_id = conversation.get("model_id")
        if not model_id:
            QMessageBox.warning(
                self,
                "No Model Selected",
                "Please select a model from the Models tab before sending a message."
            )
            return False
            
        return True
    
    def _on_send(self):
        """Handle send button click."""
        if self.is_generating or not self.current_conversation_id:
            return
            
        # Check if a model is selected
        if not self._check_model_selected():
            return
        
        # Get message text
        message_text = self.text_input.toPlainText().strip()
        if not message_text:
            return
        
        # Clear input
        self.text_input.clear()
        
        # Add user message to UI and conversation
        self._add_message("user", message_text)
        self.chat_engine.add_message(self.current_conversation_id, "user", message_text)
        
        # Show loading indicator
        self.loading_indicator.setVisible(True)
        self.is_generating = True
        
        # Disable UI elements
        self.text_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.regenerate_button.setEnabled(False)
        
        # Scroll to bottom
        self._scroll_to_bottom()
        
        # Generate response in a separate thread
        self.response_thread = ResponseThread(self.chat_engine, self.current_conversation_id)
        self.response_thread.response_ready.connect(self._on_response_ready)
        self.response_thread.error_occurred.connect(self._on_response_error)
        self.response_thread.start()
    
    def _on_response_ready(self, response):
        """Handle response from the model."""
        # Add response to UI
        self._add_message("assistant", response.get("content", ""))
        
        # Hide loading indicator
        self.loading_indicator.setVisible(False)
        self.is_generating = False
        
        # Enable UI elements
        self.text_input.setEnabled(True)
        self.text_input.setFocus()
        self.regenerate_button.setEnabled(True)
        
        # Scroll to bottom
        self._scroll_to_bottom()
    
    def _on_response_error(self, error_message):
        """Handle error during response generation."""
        # Hide loading indicator
        self.loading_indicator.setVisible(False)
        self.is_generating = False
        
        # Enable UI elements
        self.text_input.setEnabled(True)
        self.text_input.setFocus()
        
        # Show error message
        QMessageBox.warning(
            self,
            "Response Error",
            f"Error generating response: {error_message}"
        )
    
    def _on_regenerate(self):
        """Handle regenerate button click."""
        if self.is_generating or not self.current_conversation_id:
            return
            
        # Check if a model is selected
        if not self._check_model_selected():
            return
        
        # Get conversation
        conversation = self.chat_engine.get_conversation(self.current_conversation_id)
        if not conversation:
            return
        
        # Get model ID to ensure it stays loaded
        model_id = conversation.get("model_id")
        if not model_id and self.model_manager:
            # If model isn't already loaded, make sure it gets loaded
            self.model_manager.load_model(model_id)
        
        # Find the last assistant message
        messages = conversation.get("messages", [])
        assistant_messages = [i for i, m in enumerate(messages) if m.get("role") == "assistant"]
        
        if not assistant_messages:
            return
        
        # Remove the last assistant message
        last_assistant_index = assistant_messages[-1]
        last_user_message = None
        
        # Find the user message before this assistant message
        for i in range(last_assistant_index - 1, -1, -1):
            if i < len(messages) and messages[i].get("role") == "user":
                last_user_message = messages[i].get("content")
                break
        
        if not last_user_message:
            return
            
        # Delete the assistant message
        del messages[last_assistant_index]
        
        # Update conversation
        conversation["messages"] = messages
        conversation["updated_at"] = time.time()
        
        # Save conversation
        if self.storage_manager:
            self.storage_manager.save_conversation(conversation)
        
        # Reload conversation
        self.load_conversation(self.current_conversation_id)
        
        # Re-add the user message to trigger generation
        self._add_message("user", last_user_message)
        
        # Show loading indicator
        self.loading_indicator.setVisible(True)
        self.is_generating = True
        
        # Disable UI elements
        self.text_input.setEnabled(False)
        self.send_button.setEnabled(False)
        self.regenerate_button.setEnabled(False)
        
        # Scroll to bottom
        self._scroll_to_bottom()
        
        # Generate response in a separate thread
        self.response_thread = ResponseThread(self.chat_engine, self.current_conversation_id)
        self.response_thread.response_ready.connect(self._on_response_ready)
        self.response_thread.error_occurred.connect(self._on_response_error)
        self.response_thread.start()
    
    def resizeEvent(self, event):
        """Handle resize event to adjust message display."""
        super().resizeEvent(event)
        QTimer.singleShot(100, self._scroll_to_bottom)
