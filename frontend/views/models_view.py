"""
ModelsView is the view for managing language models.
It allows browsing, downloading, and managing available models.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame, QSizePolicy, QSpacerItem, QMessageBox,
    QApplication, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt6.QtGui import QIcon, QFont, QAction, QColor

class ModelDownloadThread(QThread):
    """Thread for downloading models in the background."""
    
    progress = pyqtSignal(int)  # Signal for download progress
    status_update = pyqtSignal(str, str)  # Signal for status update (model_id, status)
    completed = pyqtSignal(bool, str)  # Signal for download completion (success, message)
    
    def __init__(self, model_manager, model_id):
        super().__init__()
        
        self.model_manager = model_manager
        self.model_id = model_id
    
    def run(self):
        """Run the download thread."""
        try:
            # Update status to show download started
            self.status_update.emit(self.model_id, "Downloading...")
            
            # In a real implementation, this would pass a progress callback
            success = self.model_manager.download_model(self.model_id)
            
            # Update status based on result
            if success:
                self.status_update.emit(self.model_id, "Download Complete")
            else:
                self.status_update.emit(self.model_id, "Download Failed")
            
            # Emit completion signal
            if success:
                self.completed.emit(True, f"Downloaded {self.model_id} successfully")
            else:
                self.completed.emit(False, f"Failed to download {self.model_id}")
        except Exception as e:
            self.status_update.emit(self.model_id, "Download Error")
            self.completed.emit(False, f"Error downloading {self.model_id}: {str(e)}")

class ModelsView(QWidget):
    """View for managing language models."""
    
    # Signal when a model is loaded, unloaded, downloaded, or deleted
    model_changed = pyqtSignal(str)  # Emits model_id
    
    def __init__(self, model_manager, parent=None):
        super().__init__(parent)
        
        self.model_manager = model_manager
        self.download_threads = {}  # Map of model ID to download thread
        
        # Store reference to main window if available
        self.main_window = None
        if parent:
            # Try to find the main window by traversing parent hierarchy
            current = parent
            while current:
                if current.__class__.__name__ == 'MainWindow':
                    self.main_window = current
                    break
                current = current.parent()
        
        self._init_ui()
        self._load_models()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(20)
        
        # Header
        self.header_label = QLabel("Models")
        self.header_label.setObjectName("viewHeader")
        self.header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("modelsTabWidget")
        
        # HuggingFace tab
        self.huggingface_tab = QWidget()
        self.huggingface_layout = QVBoxLayout(self.huggingface_tab)
        self.huggingface_layout.setContentsMargins(10, 10, 10, 10)
        self.huggingface_layout.setSpacing(10)
        
        # 모델 추가 UI
        self.hf_add_model_frame = QFrame()
        self.hf_add_model_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.hf_add_model_layout = QHBoxLayout(self.hf_add_model_frame)
        
        # 모델 ID 레이블 및 입력 필드
        self.hf_model_id_label = QLabel("HuggingFace Model ID:")
        self.hf_model_id_field = QLineEdit()
        self.hf_model_id_field.setPlaceholderText("예: Qwen/Qwen2.5-3B")
        
        # 모델 추가 버튼
        self.hf_add_model_button = QPushButton("Add Model")
        self.hf_add_model_button.clicked.connect(self._on_add_hf_model)
        
        # 레이아웃에 위젯 추가
        self.hf_add_model_layout.addWidget(self.hf_model_id_label)
        self.hf_add_model_layout.addWidget(self.hf_model_id_field, 1)  # 1은 stretch factor
        self.hf_add_model_layout.addWidget(self.hf_add_model_button)
        
        # HuggingFace 테이블
        self.hf_table = QTableWidget()
        self.hf_table.setObjectName("hfModelsTable")
        self.hf_table.setColumnCount(6)
        self.hf_table.setHorizontalHeaderLabels(["Name", "Size", "Parameters", "Status", "Actions", ""])
        self.hf_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.hf_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.hf_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.hf_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.hf_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.hf_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.hf_table.setColumnWidth(5, 0)  # 모델 ID 열 숨기기
        self.hf_table.verticalHeader().setVisible(False)
        self.hf_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.hf_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # 기본 추천 모델 섹션
        self.hf_recommended_frame = QFrame()
        self.hf_recommended_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.hf_recommended_layout = QVBoxLayout(self.hf_recommended_frame)
        
        self.hf_recommended_label = QLabel("<b>Recommended Models:</b>")
        self.hf_recommended_layout.addWidget(self.hf_recommended_label)
        
        # 추천 모델 버튼들
        self.hf_recommended_buttons_layout = QHBoxLayout()
        
        self.hf_add_qwen_button = QPushButton("Qwen/Qwen2.5-3B")
        self.hf_add_qwen_button.clicked.connect(lambda: self._add_recommended_model("Qwen/Qwen2.5-3B", "3B"))
        
        self.hf_add_llama_button = QPushButton("meta-llama/Llama-2-7b-chat-hf")
        self.hf_add_llama_button.clicked.connect(lambda: self._add_recommended_model("meta-llama/Llama-2-7b-chat-hf", "7B"))
        
        self.hf_add_mistral_button = QPushButton("mistralai/Mistral-7B-v0.1")
        self.hf_add_mistral_button.clicked.connect(lambda: self._add_recommended_model("mistralai/Mistral-7B-v0.1", "7B"))
        
        self.hf_recommended_buttons_layout.addWidget(self.hf_add_qwen_button)
        self.hf_recommended_buttons_layout.addWidget(self.hf_add_llama_button)
        self.hf_recommended_buttons_layout.addWidget(self.hf_add_mistral_button)
        
        self.hf_recommended_layout.addLayout(self.hf_recommended_buttons_layout)
        
        # 탭 레이아웃에 위젯 추가
        self.huggingface_layout.addWidget(self.hf_add_model_frame)
        self.huggingface_layout.addWidget(self.hf_recommended_frame)
        self.huggingface_layout.addWidget(self.hf_table)
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.huggingface_tab, "HuggingFace")
        
        # Add widgets to layout
        self.layout.addWidget(self.header_label)
        self.layout.addWidget(self.tab_widget)
    
    def _load_models(self):
        """Load models from model manager."""
        # This method is now a stub - all loading happens in _load_hf_models
        self._load_hf_models()
    
    def _on_download_model(self, model_id):
        """Handle model download button click."""
        # Check if already downloading
        if model_id in self.download_threads:
            return
        
        # Update UI
        self._update_model_status(model_id, "Downloading...")
        
        # Create and start download thread
        thread = ModelDownloadThread(self.model_manager, model_id)
        thread.status_update.connect(self._update_model_status)  # Connect status update signal
        thread.completed.connect(lambda success, message, mid=model_id: self._on_download_completed(mid, success, message))
        thread.start()
        
        # Save thread reference
        self.download_threads[model_id] = thread
    
    def _on_download_completed(self, model_id, success, message):
        """Handle model download completion."""
        # Update UI
        self._load_models()
        
        # Clean up thread
        if model_id in self.download_threads:
            del self.download_threads[model_id]
            
        # Show message
        if success:
            QMessageBox.information(self, "Download Complete", message)
            
            # Automatically load the model
            self._on_load_model(model_id)
        else:
            QMessageBox.warning(self, "Download Failed", message)
    
    def _on_delete_model(self, model_id):
        """Handle model delete button click."""
        # Ask for confirmation
        confirm = QMessageBox.question(
            self,
            "Delete Model",
            f"Are you sure you want to delete this model?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
            
        # Delete model
        success = self.model_manager.delete_model(model_id)
        
        # Update UI
        self._load_models()
        
        # Emit model changed signal
        self.model_changed.emit(model_id)
    
    def _on_load_model(self, model_id):
        """Handle model load button click."""
        # Load model
        success = self.model_manager.load_model(model_id)
        
        # Update UI
        self._load_models()
        self._load_hf_models()
        
        if success:
            # Emit model changed signal
            self.model_changed.emit(model_id)
    
    def _on_unload_model(self, model_id):
        """Handle model unload button click."""
        # Unload model
        success = self.model_manager.unload_model(model_id)
        
        # Update UI
        self._load_models()
        self._load_hf_models()
        
        # Emit model changed signal
        self.model_changed.emit(model_id)
    
    def _on_use_model(self, model_id):
        """Handle use model button click."""
        # Get model info
        model_info = self.model_manager.get_model_info(model_id)
        if not model_info:
            QMessageBox.warning(self, "Model Error", "Could not find model information.")
            return
            
        # Make sure the model is loaded
        is_loaded = model_info.get("is_loaded", False)
        if not is_loaded:
            # Load the model first
            success = self.model_manager.load_model(model_id)
            if not success:
                QMessageBox.warning(self, "Model Error", f"Could not load model {model_id}.")
                return
            # Update model info
            model_info = self.model_manager.get_model_info(model_id)
        
        # Emit model changed signal
        self.model_changed.emit(model_id)
        
        # Show message
        model_name = model_info.get("name", model_id)
        QMessageBox.information(
            self, 
            "Model Selected", 
            f"{model_name} has been selected for use in conversations."
        )
    
    def _update_model_status(self, model_id, status):
        """Update model status in the table."""
        # Find row with model ID
        for i in range(self.hf_table.rowCount()):
            id_item = self.hf_table.item(i, 5)
            if id_item and id_item.text() == model_id:
                # Update status
                status_item = QTableWidgetItem(status)
                self.hf_table.setItem(i, 3, status_item)
                # Force visual refresh of the cell
                self.hf_table.update()
                # Process pending events to ensure UI updates immediately
                QApplication.processEvents()
                break
    
    def _start_status_timer(self):
        """Start timer for periodic status updates."""
        if not hasattr(self, 'status_timer'):
            from PyQt6.QtCore import QTimer
            self.status_timer = QTimer(self)
            self.status_timer.timeout.connect(self._refresh_model_statuses)
            # 타이머 주기를 2초로 설정하여 너무 빈번한 업데이트를 방지합니다
            self.status_timer.start(2000)  # Update every 2 seconds for better stability
    
    def _stop_status_timer(self):
        """Stop the status update timer."""
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
    
    def _refresh_model_statuses(self):
        """Refresh all model statuses from the model manager."""
        if not self.model_manager:
            return
        
        # 상태 업데이트 중 방해받지 않도록 로그 메시지 수준 일시 감소
        original_level = logging.getLogger().level
        logging.getLogger().setLevel(logging.WARNING)
            
        try:
            # Get fresh model data directly from model manager
            models = self.model_manager.get_available_models()
            
            # Check if there's an active model in the chat engine
            active_model_id = None
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'chat_engine'):
                # If we can access the chat engine, check for active conversations
                conversations = self.main_window.chat_engine.get_all_conversations()
                if conversations:
                    # Find the most recently updated conversation
                    latest_conversation = max(conversations, key=lambda x: x.get("updated_at", 0))
                    active_model_id = latest_conversation.get("model_id")
            
            # Track changes to avoid unnecessary updates
            changed = False
            
            # Update status column for each model
            for model in models:
                model_id = model.get("id", "")
                if not model_id:
                    continue
                
                # Filter to only HuggingFace models
                if not ('/' in model_id or model.get("type") == "huggingface"):
                    continue
                    
                # First ensure the actual loaded_models dictionary has this model if it should be loaded
                if model.get("is_loaded", False) and self.model_manager and model_id not in self.model_manager.loaded_models:
                    # The model is marked as loaded but isn't in loaded_models - fix this discrepancy
                    # 모델 로드 이슈를 해결하기 위한 추가 예외 처리
                    try:
                        self.model_manager.load_model(model_id)
                        changed = True
                    except Exception as e:
                        # 예외를 무시하고 계속 진행
                        logging.error(f"Error loading model {model_id}: {e}")
                    
                # Determine status text with enhanced states
                status_text = "Not Installed"
                if model.get("is_installed", False):
                    status_text = "Installed"
                    if model.get("is_loaded", False):
                        status_text = "Loaded"
                        # Check if this model is currently active/running
                        if model_id == active_model_id:
                            status_text = "Running"
                        
                # Also check model_manager's internal state which might have more up-to-date information
                if model_id in self.model_manager.loaded_models:
                    model_obj = self.model_manager.loaded_models[model_id]
                    if isinstance(model_obj, dict) and model_obj.get("status") == "running":
                        status_text = "Running"
                        
                # Find this model in the table and update status
                for i in range(self.hf_table.rowCount()):
                    id_item = self.hf_table.item(i, 5)
                    if id_item and id_item.text() == model_id:
                        current_status = self.hf_table.item(i, 3).text() if self.hf_table.item(i, 3) else ""
                        
                        # Only update if status has changed or is marked as Running
                        # This prevents flickering during normal operation
                        if current_status != status_text or status_text == "Running":
                            # Don't override downloading status during downloads
                            if not current_status.startswith("Downloading") or status_text == "Running":
                                status_item = QTableWidgetItem(status_text)
                                
                                # Special formatting for different statuses
                                if status_text == "Running":
                                    # Make running status stand out with blue color
                                    status_item.setForeground(QColor(0, 100, 255))  # Blue color
                                    # Use bold font for running status
                                    font = status_item.font()
                                    font.setBold(True)
                                    status_item.setFont(font)
                                elif status_text == "Loaded":
                                    # Green color for loaded status
                                    status_item.setForeground(QColor(0, 150, 0))  # Green color
                                
                                self.hf_table.setItem(i, 3, status_item)
                                changed = True
                        break
            
            # Only update the UI if something changed
            if changed:
                # 상태 변경이 있을 때만 UI 업데이트
                self.hf_table.update()
                # 특별한 경우에만 지연된 이벤트 처리를 사용하여 성능 향상
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(10, lambda: QApplication.processEvents())
        finally:
            # 로그 수준 복원
            logging.getLogger().setLevel(original_level)
    
    def hideEvent(self, event):
        """Handle hide event."""
        super().hideEvent(event)
        # Stop the status timer when the view is hidden
        self._stop_status_timer()
    
    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        
        # Load only HuggingFace models
        self._load_hf_models()
        
        # Start status timer
        self._start_status_timer()
        
    def _add_recommended_model(self, model_id, params):
        """추천 모델 버튼을 통해 모델 추가"""
        # 모델 정보 생성
        model_name = model_id.split('/')[-1]  # 예: "Qwen2.5-3B"
        
        # 파라미터에 따른 사이즈 추정
        size = "1.9GB"
        if params == "7B":
            size = "4.5GB"
        elif params == "13B":
            size = "8GB"
            
        # 모델 매니저에 모델 추가
        self._add_hf_model(model_id, model_name, size, params)
        
    def _on_add_hf_model(self):
        """모델 ID 필드에서 모델 추가"""
        model_id = self.hf_model_id_field.text().strip()
        if not model_id:
            QMessageBox.warning(self, "Error", "Please enter a valid HuggingFace model ID")
            return
        
        # 모델 정보 추출
        parts = model_id.split('/')
        if len(parts) < 2:
            QMessageBox.warning(self, "Error", "Invalid model ID format. Expected format: org/model")
            return
            
        model_name = parts[-1]
        
        # 모델 파라미터 추정
        params = "Unknown"
        if "3b" in model_id.lower() or "3B" in model_id:
            params = "3B"
        elif "7b" in model_id.lower() or "7B" in model_id:
            params = "7B"
        elif "13b" in model_id.lower() or "13B" in model_id:
            params = "13B"
            
        # 사이즈 추정
        size = "Unknown"
        if params == "3B":
            size = "1.9GB"
        elif params == "7B":
            size = "4.5GB"
        elif params == "13B":
            size = "8GB"
            
        # 모델 추가
        self._add_hf_model(model_id, model_name, size, params)
        
        # 입력 필드 초기화
        self.hf_model_id_field.clear()
        
    def _add_hf_model(self, model_id, model_name, size, params):
        """모델 매니저에 HuggingFace 모델 추가"""
        try:
            # 이미 있는 모델인지 확인
            if model_id in [m.get("id") for m in self.model_manager.get_available_models()]:
                QMessageBox.information(self, "Info", f"Model {model_id} is already added.")
                return
                
            # 모델 정보 구성
            model_info = {
                "id": model_id,
                "name": model_name,
                "description": f"HuggingFace model: {model_id}",
                "size": size,
                "ram_required": "8GB",
                "parameters": params,
                "quant": "None",
                "type": "huggingface",
                "is_installed": True,  # HuggingFace에서 직접 로드하므로 설치된 것으로 처리
                "is_loaded": False
            }
            
            # 모델 매니저에 모델 추가
            success = self.model_manager.add_model_source(model_info)
            
            if success:
                QMessageBox.information(self, "Success", f"Model {model_id} has been added successfully.")
                # HuggingFace 테이블 업데이트
                self._load_hf_models()
                # 전체 모델 뷰 업데이트
                self._load_models()
            else:
                QMessageBox.warning(self, "Error", f"Failed to add model {model_id}.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error adding model: {str(e)}")
            logging.error(f"Error adding HuggingFace model: {e}")
    
    def _load_hf_models(self):
        """모델 매니저에서 HuggingFace 모델 로드하여 테이블에 표시"""
        try:
            # 모델 가져오기
            all_models = self.model_manager.get_available_models()
            # HuggingFace 타입의 모델만 필터링
            hf_models = [m for m in all_models if m.get("type") == "huggingface" or '/' in m.get("id", "")]
            
            # 테이블 초기화
            self.hf_table.setRowCount(0)
            
            # 각 모델을 행으로 추가
            for i, model in enumerate(hf_models):
                self.hf_table.insertRow(i)
                
                # 이름
                name_item = QTableWidgetItem(model.get("name", "Unknown"))
                self.hf_table.setItem(i, 0, name_item)
                
                # 사이즈
                size_item = QTableWidgetItem(model.get("size", "Unknown"))
                self.hf_table.setItem(i, 1, size_item)
                
                # 파라미터
                params_item = QTableWidgetItem(model.get("parameters", "Unknown"))
                self.hf_table.setItem(i, 2, params_item)
                
                # 상태
                status_text = "Installed" if model.get("is_installed", False) else "Not Installed"
                if model.get("is_loaded", False):
                    status_text = "Loaded"
                
                status_item = QTableWidgetItem(status_text)
                self.hf_table.setItem(i, 3, status_item)
                
                # 액션 버튼
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 0, 5, 0)
                action_layout.setSpacing(5)
                
                # 버튼 추가
                model_id = model.get("id", "")
                is_loaded = model.get("is_loaded", False)
                
                # 로드/언로드 버튼
                if is_loaded:
                    unload_button = QPushButton("Unload")
                    unload_button.setObjectName("unloadButton")
                    unload_button.clicked.connect(lambda checked=False, mid=model_id: self._on_unload_model(mid))
                    action_layout.addWidget(unload_button)
                else:
                    load_button = QPushButton("Load")
                    load_button.setObjectName("loadButton")
                    load_button.clicked.connect(lambda checked=False, mid=model_id: self._on_load_model(mid))
                    action_layout.addWidget(load_button)
                
                # 사용 버튼
                use_button = QPushButton("Use Model")
                use_button.setObjectName("useButton")
                use_button.clicked.connect(lambda checked=False, mid=model_id: self._on_use_model(mid))
                action_layout.addWidget(use_button)
                
                # 삭제 버튼
                delete_button = QPushButton("Remove")
                delete_button.setObjectName("deleteButton")
                delete_button.clicked.connect(lambda checked=False, mid=model_id: self._on_remove_hf_model(mid))
                action_layout.addWidget(delete_button)
                
                self.hf_table.setCellWidget(i, 4, action_widget)
                
                # 숨겨진 모델 ID 열
                id_item = QTableWidgetItem(model_id)
                self.hf_table.setItem(i, 5, id_item)
        except Exception as e:
            logging.error(f"Error loading HuggingFace models: {e}")
    
    def _on_remove_hf_model(self, model_id):
        """모델 매니저에서 HuggingFace 모델 제거"""
        # 확인 창 표시
        confirm = QMessageBox.question(
            self,
            "Remove Model",
            f"Are you sure you want to remove model {model_id} from the list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
            
        try:
            # 모델이 로드되어 있는 경우 먼저 언로드
            model_info = self.model_manager.get_model_info(model_id)
            if model_info and model_info.get("is_loaded", False):
                self.model_manager.unload_model(model_id)
                
            # available_models에서 모델 제거
            if model_id in self.model_manager.available_models:
                del self.model_manager.available_models[model_id]
                self.model_manager._save_models_info()
                QMessageBox.information(self, "Success", f"Model {model_id} has been removed.")
            else:
                QMessageBox.warning(self, "Warning", f"Model {model_id} not found in available models.")
                
            # UI 업데이트
            self._load_hf_models()
            self._load_models()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error removing model: {str(e)}")
            logging.error(f"Error removing HuggingFace model: {e}")
