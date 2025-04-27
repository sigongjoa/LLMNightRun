"""
MainWindow is the primary window of the application.
It contains the sidebar, conversation list, and chat interface.
"""

import os
import sys
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QStackedWidget, QLabel, QPushButton,
    QApplication, QFrame, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QFont, QAction

# Import custom views
from frontend.views.chat_view import ChatView
from frontend.views.models_view import ModelsView
from frontend.views.local_docs_view import LocalDocsView
from frontend.views.settings_view import SettingsView
from frontend.components.sidebar import Sidebar
from frontend.components.conversation_list import ConversationList

# Import backend managers
from backend.models.model_manager import ModelManager
from backend.chat.chat_engine import ChatEngine
from backend.documents.document_store import DocumentStore
from backend.documents.vector_store import VectorStore
from backend.storage.storage_manager import StorageManager
from backend.code_listener.code_listener import CodeListener

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize backend components
        self._init_backend()
        
        # Set window properties
        self.setWindowTitle("LLM Forge")
        self.setMinimumSize(1200, 800)
        
        # Create main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = Sidebar()
        self.sidebar.item_clicked.connect(self._on_sidebar_item_clicked)
        
        # Create splitter for main content
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create conversation list panel
        self.conversation_list = ConversationList(self.chat_engine)
        self.conversation_list.conversation_selected.connect(self._on_conversation_selected)
        self.conversation_list.new_conversation.connect(self._on_new_conversation)
        
        # Create stacked widget for main content
        self.stacked_widget = QStackedWidget()
        
        # Create views
        self.chat_view = ChatView(
            self.chat_engine, 
            self.model_manager, 
            self.storage_manager
        )
        # Pass self as parent to models_view so it can access the main window
        self.models_view = ModelsView(self.model_manager, self)
        self.models_view.model_changed.connect(self._on_model_changed)
        
        self.local_docs_view = LocalDocsView(
            self.document_store, 
            self.vector_store, 
            self.chat_engine
        )
        self.settings_view = SettingsView(
            self.storage_manager, 
            self.model_manager, 
            self.code_listener
        )
        
        # Add views to stacked widget
        self.stacked_widget.addWidget(self.chat_view)
        self.stacked_widget.addWidget(self.models_view)
        self.stacked_widget.addWidget(self.local_docs_view)
        self.stacked_widget.addWidget(self.settings_view)
        
        # Add widgets to splitter
        self.main_splitter.addWidget(self.conversation_list)
        self.main_splitter.addWidget(self.stacked_widget)
        
        # Set splitter proportions
        self.main_splitter.setSizes([250, 950])
        self.main_splitter.setCollapsible(1, False)  # Don't allow collapsing the main content
        
        # Add sidebar and splitter to main layout
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.main_splitter)
        
        # Apply stylesheet
        self._apply_stylesheet()
        
        # Start with the chat view
        self.stacked_widget.setCurrentIndex(0)
        self.sidebar.select_item(0)  # Select Home/Chat
        
        # Find default model to use
        self.default_model_id = self._get_default_model()
        
        # Create a new conversation if none exists
        if not self.conversation_list.has_conversations():
            self._on_new_conversation()
    
    def _init_backend(self):
        """Initialize backend components."""
        # Initialize managers
        self.model_manager = ModelManager()
        self.storage_manager = StorageManager()
        self.vector_store = VectorStore()
        self.document_store = DocumentStore(vector_store=self.vector_store)
        self.code_listener = CodeListener()
        
        # Initialize chat engine
        self.chat_engine = ChatEngine(
            model_manager=self.model_manager,
            storage_manager=self.storage_manager,
            code_listener=self.code_listener
        )
    
    def _apply_stylesheet(self):
        """Apply the application stylesheet."""
        # Read the stylesheet file
        stylesheet_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "resources", 
            "styles.qss"
        )
        
        # If the stylesheet file exists, load and apply it
        if os.path.exists(stylesheet_path):
            with open(stylesheet_path, 'r') as f:
                stylesheet = f.read()
                self.setStyleSheet(stylesheet)
        else:
            # Apply a basic stylesheet
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #FAFAFA;
                }
                
                QSplitter::handle {
                    background-color: #E0E0E0;
                }
                
                QScrollArea {
                    border: none;
                }
                
                QPushButton {
                    padding: 8px 16px;
                    border-radius: 4px;
                    background-color: #2962FF;
                    color: white;
                }
                
                QPushButton:hover {
                    background-color: #1E88E5;
                }
                
                QPushButton:pressed {
                    background-color: #1565C0;
                }
            """)
    
    def _on_sidebar_item_clicked(self, index):
        """Handle sidebar item click."""
        # Set the current view in the stacked widget
        self.stacked_widget.setCurrentIndex(index)
        
        # Show/hide conversation list based on the selected view
        if index == 0:  # Home/Chat
            self.conversation_list.setVisible(True)
        else:
            self.conversation_list.setVisible(False)
    
    def _on_conversation_selected(self, conversation_id):
        """Handle conversation selection."""
        self.chat_view.load_conversation(conversation_id)
    
    def _get_default_model(self):
        """Get default model ID from settings or installed models."""
        # Try to get default model from settings
        if self.storage_manager:
            settings = self.storage_manager.get_settings()
            default_model = settings.get("default_model")
            if default_model:
                # Check if this model is installed
                model_info = self.model_manager.get_model_info(default_model)
                if model_info and model_info.get("is_installed", False):
                    # Make sure the model is loaded
                    if not model_info.get("is_loaded", False):
                        self.model_manager.load_model(default_model)
                    return default_model
        
        # Otherwise use the first installed model
        installed_models = self.model_manager.get_installed_models()
        if installed_models:
            model_id = installed_models[0].get("id")
            # Make sure the model is loaded
            if not installed_models[0].get("is_loaded", False):
                self.model_manager.load_model(model_id)
            return model_id
            
        # If no installed models, install and use a mock model
        model_id = "gpt4all-j"  # Default model
        self.model_manager.download_model(model_id)
        self.model_manager.load_model(model_id)
        return model_id
    
    def _on_new_conversation(self):
        """Handle new conversation creation."""
        # Create a new conversation with default model
        conversation = self.chat_engine.create_conversation(model_id=self.default_model_id)
        
        # Select the new conversation
        self.conversation_list.select_conversation(conversation["id"])
        
        # Load the new conversation in the chat view
        self.chat_view.load_conversation(conversation["id"])
    
    def _on_model_changed(self, model_id):
        """Handle model change."""
        # Update default model ID
        self.default_model_id = model_id
        
        # Update current conversation if one is active
        if self.chat_view.current_conversation_id:
            success = self.chat_engine.update_conversation_model(
                self.chat_view.current_conversation_id,
                model_id
            )
            
            if success:
                # Reload conversation to update UI
                self.chat_view.load_conversation(self.chat_view.current_conversation_id)
                
                # Update settings with default model
                if self.storage_manager:
                    settings = self.storage_manager.get_settings()
                    settings["default_model"] = model_id
                    self.storage_manager.update_settings(settings)
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Perform any cleanup or saving before closing
        # For example, save settings
        self.storage_manager.save_settings()
        
        # Accept the close event
        event.accept()
