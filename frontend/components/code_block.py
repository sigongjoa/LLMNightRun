"""
CodeBlock is a widget that displays a code block with syntax highlighting.
It also provides buttons for copying, saving, and executing the code.
"""

import os
import tempfile
import subprocess
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFileDialog, QMessageBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QSyntaxHighlighter, QTextCharFormat, QTextOption

class SyntaxHighlighter(QSyntaxHighlighter):
    """Simple syntax highlighter for code blocks."""
    
    def __init__(self, parent, language):
        super().__init__(parent)
        self.language = language.lower()
        self._init_formats()
    
    def _init_formats(self):
        """Initialize text formats for different syntax elements."""
        self.formats = {}
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))  # Blue
        keyword_format.setFontWeight(QFont.Weight.Bold)
        self.formats["keyword"] = keyword_format
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))  # Orange
        self.formats["string"] = string_format
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))  # Light green
        self.formats["number"] = number_format
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))  # Green
        comment_format.setFontItalic(True)
        self.formats["comment"] = comment_format
        
        # Function calls
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#DCDCAA"))  # Light yellow
        self.formats["function"] = function_format
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        import re
        
        # For all languages
        
        # Highlight strings (double quotes)
        string_pattern = r'"[^"\\]*(\\.[^"\\]*)*"'
        for match in re.finditer(string_pattern, text):
            start, end = match.span()
            self.setFormat(start, end - start, self.formats["string"])
        
        # Highlight strings (single quotes)
        string_pattern = r"'[^'\\]*(\\.[^'\\]*)*'"
        for match in re.finditer(string_pattern, text):
            start, end = match.span()
            self.setFormat(start, end - start, self.formats["string"])
        
        # Highlight numbers
        number_pattern = r'\b\d+\b'
        for match in re.finditer(number_pattern, text):
            start, end = match.span()
            self.setFormat(start, end - start, self.formats["number"])
        
        # Language-specific highlighting
        if self.language == "python":
            # Python keywords
            keywords = [
                "and", "as", "assert", "break", "class", "continue", "def", "del", "elif", "else",
                "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is",
                "lambda", "None", "nonlocal", "not", "or", "pass", "raise", "return", "True", "try",
                "while", "with", "yield"
            ]
            keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
            for match in re.finditer(keyword_pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, self.formats["keyword"])
            
            # Python comments
            comment_pattern = r'#.*$'
            for match in re.finditer(comment_pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, self.formats["comment"])
                
            # Python function calls
            function_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            for match in re.finditer(function_pattern, text):
                start, end = match.span(1)  # Only highlight the function name
                self.setFormat(start, end - start, self.formats["function"])
        
        elif self.language in ["javascript", "js"]:
            # JavaScript keywords
            keywords = [
                "await", "break", "case", "catch", "class", "const", "continue", "debugger", "default",
                "delete", "do", "else", "export", "extends", "false", "finally", "for", "function",
                "if", "import", "in", "instanceof", "new", "null", "return", "super", "switch", "this",
                "throw", "true", "try", "typeof", "var", "void", "while", "with", "yield", "let"
            ]
            keyword_pattern = r'\b(' + '|'.join(keywords) + r')\b'
            for match in re.finditer(keyword_pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, self.formats["keyword"])
            
            # JavaScript comments (single line)
            comment_pattern = r'//.*$'
            for match in re.finditer(comment_pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, self.formats["comment"])
            
            # JavaScript function calls
            function_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            for match in re.finditer(function_pattern, text):
                start, end = match.span(1)  # Only highlight the function name
                self.setFormat(start, end - start, self.formats["function"])
        
        elif self.language in ["css"]:
            # CSS properties
            properties = [
                "color", "background", "margin", "padding", "font", "border", "display",
                "position", "width", "height", "top", "right", "bottom", "left",
                "z-index", "float", "clear", "cursor", "text-align", "vertical-align",
                "line-height", "text-decoration", "text-transform", "font-family",
                "font-size", "font-weight", "background-color", "border-radius"
            ]
            property_pattern = r'\b(' + '|'.join(properties) + r')\s*:'
            for match in re.finditer(property_pattern, text):
                start, end = match.span(1)  # Only highlight the property name
                self.setFormat(start, end - start, self.formats["keyword"])
            
            # CSS values
            values = [
                "none", "block", "inline", "inline-block", "flex", "grid", "absolute",
                "relative", "fixed", "sticky", "static", "hidden", "visible", "auto",
                "inherit", "initial", "unset", "center", "left", "right", "bold",
                "normal", "italic"
            ]
            value_pattern = r':\s*\b(' + '|'.join(values) + r')\b'
            for match in re.finditer(value_pattern, text):
                start, end = match.span(1)
                self.setFormat(start, end - start, self.formats["function"])
            
            # CSS colors
            color_pattern = r'#[0-9a-fA-F]{3,6}'
            for match in re.finditer(color_pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, self.formats["string"])
            
            # CSS comments
            comment_pattern = r'/\*.*?\*/'
            for match in re.finditer(comment_pattern, text, re.DOTALL):
                start, end = match.span()
                self.setFormat(start, end - start, self.formats["comment"])

class CodeBlock(QFrame):
    """Widget for displaying code blocks with syntax highlighting."""
    
    execution_result = pyqtSignal(str, bool)  # Signal for execution result (output, success)
    
    def __init__(self, language, code):
        super().__init__()
        
        self.language = language
        self.code = code
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Set frame style
        self.setObjectName("codeBlock")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Header
        self.header = QFrame()
        self.header.setObjectName("codeHeader")
        self.header.setMaximumHeight(40)
        
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(10, 5, 10, 5)
        self.header_layout.setSpacing(5)
        
        # Language label
        lang_label_text = self.language.capitalize() if self.language else "Code"
        self.lang_label = QLabel(lang_label_text)
        self.lang_label.setObjectName("langLabel")
        
        # Buttons
        self.copy_button = QPushButton("Copy")
        self.copy_button.setObjectName("copyButton")
        self.copy_button.setToolTip("Copy code to clipboard")
        self.copy_button.clicked.connect(self._on_copy)
        
        self.save_button = QPushButton("Save")
        self.save_button.setObjectName("saveButton")
        self.save_button.setToolTip("Save code to file")
        self.save_button.clicked.connect(self._on_save)
        
        # Execute button (only for supported languages)
        self.execute_button = None
        if self.language.lower() in ["python", "javascript", "js", "bash", "sh"]:
            self.execute_button = QPushButton("Run")
            self.execute_button.setObjectName("executeButton")
            self.execute_button.setToolTip(f"Execute {self.language} code")
            self.execute_button.clicked.connect(self._on_execute)
        
        # Add widgets to header layout
        self.header_layout.addWidget(self.lang_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.copy_button)
        self.header_layout.addWidget(self.save_button)
        if self.execute_button:
            self.header_layout.addWidget(self.execute_button)
        
        # Code display
        self.code_edit = QTextEdit()
        self.code_edit.setObjectName("codeEdit")
        self.code_edit.setReadOnly(True)
        self.code_edit.setFont(QFont("Consolas", 10))
        self.code_edit.setText(self.code)
        
        # Ensure proper word wrapping and line handling
        self.code_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        word_wrap_options = QTextOption()
        word_wrap_options.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.code_edit.document().setDefaultTextOption(word_wrap_options)
        
        # Set an appropriate height based on content
        document_height = self.code_edit.document().size().height()
        self.code_edit.setMinimumHeight(min(300, int(document_height + 30)))
        
        # Apply syntax highlighting
        self.highlighter = SyntaxHighlighter(self.code_edit.document(), self.language)
        
        # Add widgets to main layout
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.code_edit)
        
        # Result area (hidden by default, shown after execution)
        self.result_frame = QFrame()
        self.result_frame.setObjectName("resultFrame")
        self.result_frame.setVisible(False)
        
        self.result_layout = QVBoxLayout(self.result_frame)
        self.result_layout.setContentsMargins(10, 10, 10, 10)
        
        self.result_label = QLabel("Execution Result:")
        self.result_label.setObjectName("resultLabel")
        
        self.result_edit = QTextEdit()
        self.result_edit.setObjectName("resultEdit")
        self.result_edit.setReadOnly(True)
        self.result_edit.setFont(QFont("Consolas", 10))
        
        self.result_layout.addWidget(self.result_label)
        self.result_layout.addWidget(self.result_edit)
        
        self.layout.addWidget(self.result_frame)
    
    def _on_copy(self):
        """Copy code to clipboard."""
        from PyQt6.QtWidgets import QApplication
        
        QApplication.clipboard().setText(self.code)
    
    def _on_save(self):
        """Save code to file."""
        # Get default extension based on language
        extension = self._get_extension_for_language()
        
        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Code",
            os.path.expanduser("~/Desktop"),
            f"{self.language.capitalize()} Files (*{extension});;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Add extension if not present
        if not os.path.splitext(file_path)[1]:
            file_path += extension
        
        # Save code to file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.code)
            
            QMessageBox.information(
                self,
                "File Saved",
                f"Code saved to {file_path}"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Save Error",
                f"Error saving file: {str(e)}"
            )
    
    def _on_execute(self):
        """Execute code."""
        # Create temporary file
        extension = self._get_extension_for_language()
        
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False, mode='w', encoding='utf-8') as temp_file:
            temp_file.write(self.code)
            temp_path = temp_file.name
        
        # Execute based on language
        try:
            if self.language.lower() == "python":
                process = subprocess.Popen(
                    ["python", temp_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            elif self.language.lower() in ["javascript", "js"]:
                process = subprocess.Popen(
                    ["node", temp_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            elif self.language.lower() in ["bash", "sh"]:
                process = subprocess.Popen(
                    ["bash", temp_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                # Should not happen, but just in case
                self.result_edit.setText("Execution not supported for this language.")
                self.result_frame.setVisible(True)
                return
            
            # Wait for process to complete (with timeout)
            stdout, stderr = process.communicate(timeout=30)
            
            # Show result
            if process.returncode == 0:
                self.result_edit.setText(stdout)
                self.execution_result.emit(stdout, True)
            else:
                self.result_edit.setText(f"Error:\n{stderr}")
                self.execution_result.emit(stderr, False)
            
            self.result_frame.setVisible(True)
            
        except subprocess.TimeoutExpired:
            self.result_edit.setText("Execution timed out after 30 seconds.")
            self.result_frame.setVisible(True)
            self.execution_result.emit("Execution timed out after 30 seconds.", False)
        except Exception as e:
            self.result_edit.setText(f"Error executing code: {str(e)}")
            self.result_frame.setVisible(True)
            self.execution_result.emit(str(e), False)
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def _get_extension_for_language(self):
        """Get file extension for the current language."""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "js": ".js",
            "bash": ".sh",
            "sh": ".sh",
            "html": ".html",
            "css": ".css",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp",
            "csharp": ".cs",
            "cs": ".cs",
            "go": ".go",
            "rust": ".rs",
            "ruby": ".rb",
            "php": ".php",
            "swift": ".swift",
            "typescript": ".ts",
            "ts": ".ts",
            "kotlin": ".kt",
            "sql": ".sql",
            "r": ".R"
        }
        
        return extensions.get(self.language.lower(), ".txt")
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        
        # Adjust code edit height based on content
        document_height = self.code_edit.document().size().height()
        min_height = min(300, int(document_height + 30))
        if min_height != self.code_edit.minimumHeight():
            self.code_edit.setMinimumHeight(min_height)
