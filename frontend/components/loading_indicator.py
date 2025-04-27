"""
LoadingIndicator is a widget that displays a loading animation during model response generation.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QMovie

class LoadingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName("loadingIndicator")
        self.setFixedHeight(40)
        
        # Create layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 5, 20, 5)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create label for the loading text
        self.text_label = QLabel("Generating response...")
        self.text_label.setObjectName("loadingText")
        
        # Create label for the loading animation
        self.animation_label = QLabel()
        self.animation_label.setObjectName("loadingAnimation")
        
        # Create dots animation
        self.dots = ""
        self.dot_timer = QTimer(self)
        self.dot_timer.timeout.connect(self._update_dots)
        
        # Add widgets to layout
        self.layout.addWidget(self.animation_label)
        self.layout.addWidget(self.text_label)
        
        # Start animation
        self._create_animation()
    
    def _create_animation(self):
        """Create a loading animation."""
        # This would be better with an actual animated GIF,
        # but for simplicity we'll use a text-based animation
        
        # Start the dot timer
        self.dot_timer.start(500)  # Update every 500ms
    
    def _update_dots(self):
        """Update the loading dots animation."""
        self.dots = (self.dots + ".") if len(self.dots) < 3 else ""
        self.text_label.setText(f"Generating response{self.dots}")
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self.dot_timer.start(500)
    
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        self.dot_timer.stop()
