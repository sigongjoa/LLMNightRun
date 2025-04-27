"""
SettingsView is the view for managing application settings.
It allows configuring the application behavior, model parameters, and code listener.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QFrame, QCheckBox, QComboBox,
    QSpinBox, QDoubleSpinBox, QSlider, QLineEdit, QFileDialog,
    QFormLayout, QGroupBox, QSizePolicy, QSpacerItem, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QSettings
from PyQt6.QtGui import QIcon, QFont

class SettingsView(QWidget):
    """View for managing application settings."""
    
    settings_changed = pyqtSignal()  # Signal when settings are changed
    
    def __init__(self, storage_manager, model_manager, code_listener, parent=None):
        super().__init__(parent)
        
        self.storage_manager = storage_manager
        self.model_manager = model_manager
        self.code_listener = code_listener
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)
        
        # Header
        self.header_label = QLabel("Settings")
        self.header_label.setObjectName("viewHeader")
        self.header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("settingsTabWidget")
        
        # General settings tab
        self.general_tab = QWidget()
        self.general_layout = QVBoxLayout(self.general_tab)
        self.general_layout.setContentsMargins(20, 20, 20, 20)
        self.general_layout.setSpacing(20)
        
        # Appearance group
        self.appearance_group = QGroupBox("Appearance")
        self.appearance_layout = QFormLayout(self.appearance_group)
        
        self.theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        
        self.font_size_label = QLabel("Font Size:")
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["Small", "Medium", "Large"])
        
        self.appearance_layout.addRow(self.theme_label, self.theme_combo)
        self.appearance_layout.addRow(self.font_size_label, self.font_size_combo)
        
        # Behavior group
        self.behavior_group = QGroupBox("Behavior")
        self.behavior_layout = QFormLayout(self.behavior_group)
        
        self.show_timestamps_check = QCheckBox("Show message timestamps")
        self.show_model_info_check = QCheckBox("Show model information")
        self.max_conversations_label = QLabel("Max conversations to display:")
        self.max_conversations_spin = QSpinBox()
        self.max_conversations_spin.setMinimum(1)
        self.max_conversations_spin.setMaximum(50)
        self.max_conversations_spin.setValue(10)
        
        self.behavior_layout.addRow(self.show_timestamps_check)
        self.behavior_layout.addRow(self.show_model_info_check)
        self.behavior_layout.addRow(self.max_conversations_label, self.max_conversations_spin)
        
        # Default model group
        self.default_model_group = QGroupBox("Default Model")
        self.default_model_layout = QFormLayout(self.default_model_group)
        
        self.default_model_label = QLabel("Default Model:")
        self.default_model_combo = QComboBox()
        self.default_model_combo.addItem("None", None)
        
        # Add available models
        models = self.model_manager.get_available_models()
        for model in models:
            self.default_model_combo.addItem(model.get("name", "Unknown"), model.get("id"))
        
        self.default_model_layout.addRow(self.default_model_label, self.default_model_combo)
        
        # Add groups to general tab
        self.general_layout.addWidget(self.appearance_group)
        self.general_layout.addWidget(self.behavior_group)
        self.general_layout.addWidget(self.default_model_group)
        self.general_layout.addStretch()
        
        # Code Listener tab
        self.code_listener_tab = QWidget()
        self.code_listener_layout = QVBoxLayout(self.code_listener_tab)
        self.code_listener_layout.setContentsMargins(20, 20, 20, 20)
        self.code_listener_layout.setSpacing(20)
        
        # Code Listener settings group
        self.code_listener_group = QGroupBox("Code Listener Settings")
        self.code_listener_form = QFormLayout(self.code_listener_group)
        
        self.code_listener_enabled_check = QCheckBox("Enable Code Listener")
        self.auto_execute_check = QCheckBox("Automatically execute code when detected")
        
        self.code_listener_form.addRow(self.code_listener_enabled_check)
        self.code_listener_form.addRow(self.auto_execute_check)
        
        # Languages group
        self.languages_group = QGroupBox("Allowed Languages")
        self.languages_layout = QVBoxLayout(self.languages_group)
        
        # Create checkboxes for languages
        self.language_checks = {}
        languages = ["python", "javascript", "bash", "html", "css", "java", "cpp", "csharp"]
        
        for language in languages:
            check = QCheckBox(language.capitalize())
            self.language_checks[language] = check
            self.languages_layout.addWidget(check)
        
        # Add groups to code listener tab
        self.code_listener_layout.addWidget(self.code_listener_group)
        self.code_listener_layout.addWidget(self.languages_group)
        self.code_listener_layout.addStretch()
        
        # Advanced tab
        self.advanced_tab = QWidget()
        self.advanced_layout = QVBoxLayout(self.advanced_tab)
        self.advanced_layout.setContentsMargins(20, 20, 20, 20)
        self.advanced_layout.setSpacing(20)
        
        # Model parameters group
        self.model_params_group = QGroupBox("Model Parameters")
        self.model_params_layout = QFormLayout(self.model_params_group)
        
        self.temperature_label = QLabel("Temperature:")
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setMinimum(0)
        self.temperature_slider.setMaximum(100)
        self.temperature_slider.setValue(70)  # 0.7
        self.temperature_value = QLabel("0.7")
        self.temperature_slider.valueChanged.connect(
            lambda value: self.temperature_value.setText(f"{value / 100:.1f}")
        )
        
        self.top_p_label = QLabel("Top P:")
        self.top_p_slider = QSlider(Qt.Orientation.Horizontal)
        self.top_p_slider.setMinimum(0)
        self.top_p_slider.setMaximum(100)
        self.top_p_slider.setValue(100)  # 1.0
        self.top_p_value = QLabel("1.0")
        self.top_p_slider.valueChanged.connect(
            lambda value: self.top_p_value.setText(f"{value / 100:.1f}")
        )
        
        self.max_tokens_label = QLabel("Max Tokens:")
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setMinimum(1)
        self.max_tokens_spin.setMaximum(8192)
        self.max_tokens_spin.setValue(2048)
        
        # Create horizontal layouts for sliders with value labels
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_value)
        
        top_p_layout = QHBoxLayout()
        top_p_layout.addWidget(self.top_p_slider)
        top_p_layout.addWidget(self.top_p_value)
        
        self.model_params_layout.addRow(self.temperature_label, temp_layout)
        self.model_params_layout.addRow(self.top_p_label, top_p_layout)
        self.model_params_layout.addRow(self.max_tokens_label, self.max_tokens_spin)
        
        # Backup and restore group
        self.backup_group = QGroupBox("Backup and Restore")
        self.backup_layout = QVBoxLayout(self.backup_group)
        
        self.backup_button = QPushButton("Create Backup")
        self.backup_button.clicked.connect(self._on_create_backup)
        
        self.restore_button = QPushButton("Restore from Backup")
        self.restore_button.clicked.connect(self._on_restore_backup)
        
        self.backup_layout.addWidget(self.backup_button)
        self.backup_layout.addWidget(self.restore_button)
        
        # Add groups to advanced tab
        self.advanced_layout.addWidget(self.model_params_group)
        self.advanced_layout.addWidget(self.backup_group)
        self.advanced_layout.addStretch()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.general_tab, "General")
        self.tab_widget.addTab(self.code_listener_tab, "Code Listener")
        self.tab_widget.addTab(self.advanced_tab, "Advanced")
        
        # Button layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(10)
        
        self.button_layout.addStretch()
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._on_reset)
        
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self._on_save)
        
        self.button_layout.addWidget(self.reset_button)
        self.button_layout.addWidget(self.save_button)
        
        # Add widgets to main layout
        self.layout.addWidget(self.header_label)
        self.layout.addWidget(self.tab_widget)
        self.layout.addLayout(self.button_layout)
    
    def _load_settings(self):
        """Load settings from storage manager."""
        if not self.storage_manager:
            return
        
        settings = self.storage_manager.get_settings()
        
        # Update UI with settings
        
        # General - Appearance
        theme = settings.get("theme", "system").lower()
        if theme == "light":
            self.theme_combo.setCurrentIndex(1)
        elif theme == "dark":
            self.theme_combo.setCurrentIndex(2)
        else:
            self.theme_combo.setCurrentIndex(0)  # System
        
        font_size = settings.get("ui", {}).get("font_size", "medium").lower()
        if font_size == "small":
            self.font_size_combo.setCurrentIndex(0)
        elif font_size == "large":
            self.font_size_combo.setCurrentIndex(2)
        else:
            self.font_size_combo.setCurrentIndex(1)  # Medium
        
        # General - Behavior
        self.show_timestamps_check.setChecked(settings.get("ui", {}).get("show_timestamps", True))
        self.show_model_info_check.setChecked(settings.get("ui", {}).get("show_model_info", True))
        self.max_conversations_spin.setValue(settings.get("ui", {}).get("max_conversation_display", 10))
        
        # General - Default Model
        default_model = settings.get("default_model")
        if default_model:
            index = self.default_model_combo.findData(default_model)
            if index >= 0:
                self.default_model_combo.setCurrentIndex(index)
        
        # Code Listener
        code_listener_settings = settings.get("code_listener", {})
        self.code_listener_enabled_check.setChecked(code_listener_settings.get("enabled", True))
        self.auto_execute_check.setChecked(code_listener_settings.get("auto_execute", False))
        
        # Code Listener - Languages
        allowed_languages = code_listener_settings.get("languages_allowed", [])
        for language, check in self.language_checks.items():
            check.setChecked(language in allowed_languages)
        
        # Advanced - Model Parameters
        advanced_settings = settings.get("advanced", {})
        self.temperature_slider.setValue(int(advanced_settings.get("temperature", 0.7) * 100))
        self.top_p_slider.setValue(int(advanced_settings.get("top_p", 1.0) * 100))
        self.max_tokens_spin.setValue(advanced_settings.get("max_tokens", 2048))
    
    def _save_settings(self):
        """Save settings to storage manager."""
        if not self.storage_manager:
            return
        
        # Get current settings
        settings = self.storage_manager.get_settings()
        
        # Update with UI values
        
        # General - Appearance
        theme_index = self.theme_combo.currentIndex()
        if theme_index == 1:
            settings["theme"] = "light"
        elif theme_index == 2:
            settings["theme"] = "dark"
        else:
            settings["theme"] = "system"
        
        font_size_index = self.font_size_combo.currentIndex()
        if font_size_index == 0:
            settings["ui"]["font_size"] = "small"
        elif font_size_index == 2:
            settings["ui"]["font_size"] = "large"
        else:
            settings["ui"]["font_size"] = "medium"
        
        # General - Behavior
        settings["ui"]["show_timestamps"] = self.show_timestamps_check.isChecked()
        settings["ui"]["show_model_info"] = self.show_model_info_check.isChecked()
        settings["ui"]["max_conversation_display"] = self.max_conversations_spin.value()
        
        # General - Default Model
        model_index = self.default_model_combo.currentIndex()
        settings["default_model"] = self.default_model_combo.itemData(model_index)
        
        # Code Listener
        settings["code_listener"]["enabled"] = self.code_listener_enabled_check.isChecked()
        settings["code_listener"]["auto_execute"] = self.auto_execute_check.isChecked()
        
        # Code Listener - Languages
        allowed_languages = []
        for language, check in self.language_checks.items():
            if check.isChecked():
                allowed_languages.append(language)
        settings["code_listener"]["languages_allowed"] = allowed_languages
        
        # Advanced - Model Parameters
        settings["advanced"]["temperature"] = self.temperature_slider.value() / 100.0
        settings["advanced"]["top_p"] = self.top_p_slider.value() / 100.0
        settings["advanced"]["max_tokens"] = self.max_tokens_spin.value()
        
        # Save settings
        self.storage_manager.update_settings(settings)
        
        # Emit settings changed signal
        self.settings_changed.emit()
    
    def _on_reset(self):
        """Handle reset button click."""
        # Ask for confirmation
        confirm = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
        
        # Reset settings
        if self.storage_manager:
            self.storage_manager.settings = self.storage_manager._create_default_settings()
            self.storage_manager.save_settings()
            
            # Reload settings
            self._load_settings()
            
            # Emit settings changed signal
            self.settings_changed.emit()
    
    def _on_save(self):
        """Handle save button click."""
        self._save_settings()
        
        QMessageBox.information(
            self,
            "Settings Saved",
            "Settings have been saved successfully."
        )
    
    def _on_create_backup(self):
        """Handle create backup button click."""
        if not self.storage_manager:
            return
        
        # Get backup path
        backup_path = self.storage_manager.create_backup()
        
        if not backup_path:
            QMessageBox.warning(
                self,
                "Backup Failed",
                "Failed to create backup."
            )
            return
        
        QMessageBox.information(
            self,
            "Backup Created",
            f"Backup created successfully at:\n{backup_path}"
        )
    
    def _on_restore_backup(self):
        """Handle restore backup button click."""
        if not self.storage_manager:
            return
        
        # Ask for backup file
        backup_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            os.path.join(self.storage_manager.data_dir),
            "Backup Files (*.zip)"
        )
        
        if not backup_path:
            return
        
        # Ask for confirmation
        confirm = QMessageBox.question(
            self,
            "Restore Backup",
            "Restoring a backup will overwrite your current settings and conversations. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
        
        # Restore backup
        success = self.storage_manager.restore_backup(backup_path)
        
        if success:
            # Reload settings
            self._load_settings()
            
            # Emit settings changed signal
            self.settings_changed.emit()
            
            QMessageBox.information(
                self,
                "Backup Restored",
                "Backup restored successfully. Some changes may require restarting the application."
            )
        else:
            QMessageBox.warning(
                self,
                "Restore Failed",
                "Failed to restore backup."
            )
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        
        # Reload settings when view is shown
        self._load_settings()
