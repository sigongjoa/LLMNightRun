"""
이 파일에는 HuggingFace 탭을 개선하는 코드가 포함되어 있습니다.
"""

def update_huggingface_tab():
    """
    models_view.py 파일에서 HuggingFace 탭을 개선하여 모델을 추가하고 관리할 수 있도록 합니다.
    """
    import os
    
    # models_view.py 파일 경로
    models_view_path = "frontend/views/models_view.py"
    
    # 실행 가능한 전체 경로 생성
    current_dir = os.getcwd()
    full_path = os.path.join(current_dir, models_view_path)
    
    # 파일이 존재하는지 확인
    if not os.path.exists(full_path):
        print(f"Error: {full_path} 파일을 찾을 수 없습니다.")
        return False
    
    # 수정하기 위해 파일 내용 읽기
    with open(full_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # 수정: 필요한 import 추가
    imports = """import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame, QSizePolicy, QSpacerItem, QMessageBox,
    QApplication, QLineEdit
)"""
    
    # 원래 import 문 찾아서 교체
    import_pattern = r"import logging\s*from PyQt6\.QtWidgets import \([^)]*\)"
    content = content.replace("""import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QFrame, QSizePolicy, QSpacerItem, QMessageBox,
    QApplication
)""", imports)
    
    # HuggingFace 탭 구현 교체
    huggingface_tab = """        # HuggingFace tab
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
        self.huggingface_layout.addWidget(self.hf_table)"""
    
    # HuggingFace 탭 플레이스홀더 교체
    content = content.replace("""        # HuggingFace tab (placeholder)
        self.huggingface_tab = QWidget()
        self.huggingface_layout = QVBoxLayout(self.huggingface_tab)
        self.huggingface_layout.setContentsMargins(10, 10, 10, 10)
        self.huggingface_layout.setSpacing(10)
        
        self.huggingface_label = QLabel("HuggingFace models will be supported in a future update.")
        self.huggingface_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.huggingface_layout.addWidget(self.huggingface_label)""", huggingface_tab)
    
    # showEvent 메서드 업데이트하여 HuggingFace 모델도 로드하도록 수정
    show_event = """    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        
        # Reload models when view is shown
        self._load_models()
        # Load HuggingFace models
        self._load_hf_models()
        
        # Start status timer
        self._start_status_timer()"""
    
    # showEvent 메서드 찾아서 교체
    content = content.replace("""    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        
        # Reload models when view is shown
        self._load_models()
        
        # Start status timer
        self._start_status_timer()""", show_event)
    
    # 클래스 끝에 HuggingFace 관련 메서드 추가
    hf_methods = """
    def _add_recommended_model(self, model_id: str, params: str):
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
        
    def _add_hf_model(self, model_id: str, model_name: str, size: str, params: str):
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
    
    def _on_remove_hf_model(self, model_id: str):
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
            logging.error(f"Error removing HuggingFace model: {e}")"""
    
    # 클래스 끝에 새 메서드 추가
    content += hf_methods
    
    # 변경된 내용 저장
    with open(full_path, "w", encoding="utf-8") as file:
        file.write(content)
    
    print(f"{full_path} 파일이 성공적으로 업데이트되었습니다.")
    return True

# 실행
if __name__ == "__main__":
    update_huggingface_tab()
