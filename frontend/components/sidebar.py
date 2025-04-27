"""
Sidebar is a navigation panel on the left side of the main window.
It contains buttons for switching between different views.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel,
    QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont

class SidebarButton(QPushButton):
    """Custom button for the sidebar."""
    
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(text, parent)
        
        self.setObjectName("sidebarButton")
        self.setCheckable(True)
        self.setFlat(True)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(50)
        
        # Set icon if provided
        if icon_path:
            icon = QIcon(icon_path)
            self.setIcon(icon)
            self.setIconSize(QSize(20, 20))

class Sidebar(QFrame):
    """Sidebar navigation panel."""
    
    item_clicked = pyqtSignal(int)  # Signal when item is clicked (index)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName("sidebar")
        self.setMinimumWidth(200)
        self.setMaximumWidth(200)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 20, 10, 20)
        self.layout.setSpacing(10)
        
        # App title/logo
        self.title_label = QLabel("LLM Forge")
        self.title_label.setObjectName("appTitle")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        
        # Navigation buttons
        self.buttons = []
        
        # Home/Chat button
        self.home_button = SidebarButton("Home")
        self.home_button.setObjectName("homeButton")
        
        # Models button
        self.models_button = SidebarButton("Models")
        self.models_button.setObjectName("modelsButton")
        
        # Local Docs button
        self.docs_button = SidebarButton("LocalDocs")
        self.docs_button.setObjectName("docsButton")
        
        # Settings button
        self.settings_button = SidebarButton("Settings")
        self.settings_button.setObjectName("settingsButton")
        
        # Add buttons to list
        self.buttons.append(self.home_button)
        self.buttons.append(self.models_button)
        self.buttons.append(self.docs_button)
        self.buttons.append(self.settings_button)
        
        # Connect signals
        for i, button in enumerate(self.buttons):
            button.clicked.connect(lambda checked, idx=i: self._on_button_clicked(idx))
        
        # Add widgets to layout
        self.layout.addWidget(self.title_label)
        self.layout.addSpacing(20)
        
        for button in self.buttons:
            self.layout.addWidget(button)
        
        # Add spacer at the bottom
        self.layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Version label
        self.version_label = QLabel("Version 0.1.0")
        self.version_label.setObjectName("versionLabel")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.version_label)
        
        # Set initial selection
        self.select_item(0)  # Select Home by default
    
    def _on_button_clicked(self, index):
        """Handle button click."""
        # Update button states
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)
        
        # Emit signal
        self.item_clicked.emit(index)
    
    def select_item(self, index):
        """Select an item programmatically."""
        if 0 <= index < len(self.buttons):
            self._on_button_clicked(index)
