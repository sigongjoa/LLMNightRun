"""
프롬프트 엔지니어링 제어 모듈

사용자 정의 프롬프트 템플릿 및 프롬프트 엔지니어링 설정을 관리합니다.

# DO NOT CHANGE CODE: 이 파일은 프롬프트 엔지니어링 핵심 기능입니다.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("mcp.prompt_engineering")

class PromptEngineering:
    """프롬프트 엔지니어링 관리 클래스
    
    # DO NOT CHANGE CODE: 프롬프트 엔지니어링 관리 핵심 클래스
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        초기화
        
        Args:
            config_dir: 구성 디렉토리 (None인 경우 기본 디렉토리 사용)
        """
        # 기본 구성 디렉토리 설정
        if config_dir is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            config_dir = os.path.join(project_root, "config", "prompts")
        
        self.config_dir = config_dir
        
        # 구성 디렉토리 생성
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        # 기본 설정 파일 경로
        self.settings_file = os.path.join(self.config_dir, "settings.json")
        self.templates_dir = os.path.join(self.config_dir, "templates")
        
        # 템플릿 디렉토리 생성
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        
        # 기본 설정 로드 또는 생성
        self._load_or_create_settings()
        
        logger.info(f"Initialized PromptEngineering with config_dir: {self.config_dir}")
    
    def _load_or_create_settings(self):
        """설정 로드 또는 기본 설정 생성"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                logger.info("Prompt engineering settings loaded")
            except Exception as e:
                logger.error(f"Error loading settings: {str(e)}")
                self._create_default_settings()
        else:
            self._create_default_settings()
    
    def _create_default_settings(self):
        """기본 설정 생성"""
        self.settings = {
            "defaultTemplate": "standard",
            "activeTemplate": "standard",
            "temperature": 0.7,
            "maxTokens": 1000,
            "systemPrompt": "당신은 유능한 AI 비서로, 사용자의 질문에 명확하고 도움이 되는 응답을 제공합니다.",
            "customSettings": {
                "useReasoning": True,
                "reasoningFormat": "thinking",
                "enableTools": True,
                "responseStyle": "balanced",
                "topP": 0.95,
                "enableFunctionCalling": True
            },
            "created": datetime.utcnow().isoformat(),
            "modified": datetime.utcnow().isoformat()
        }
        
        # 기본 설정 저장
        self._save_settings()
        
        # 기본 템플릿 생성
        self._create_default_templates()
        
        logger.info("Default prompt engineering settings created")
    
    def _save_settings(self):
        """설정 저장"""
        try:
            # 수정 시간 업데이트
            self.settings["modified"] = datetime.utcnow().isoformat()
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            logger.info("Prompt engineering settings saved")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {str(e)}")
            return False
    
    def _create_default_templates(self):
        """기본 템플릿 생성"""
        templates = {
            "standard": {
                "name": "표준",
                "description": "균형 잡힌 표준 응답 템플릿",
                "systemPrompt": "당신은 유능한 AI 비서로, 사용자의 질문에 명확하고 도움이 되는 응답을 제공합니다.",
                "temperature": 0.7,
                "maxTokens": 1000,
                "topP": 0.95,
                "format": "balanced",
                "created": datetime.utcnow().isoformat()
            },
            "creative": {
                "name": "창의적",
                "description": "더 창의적이고 다양한 응답을 제공하는 템플릿",
                "systemPrompt": "당신은 창의적인 AI 비서로, 사용자의 질문에 독창적이고 흥미로운 관점으로 답변합니다.",
                "temperature": 0.9,
                "maxTokens": 1500,
                "topP": 0.98,
                "format": "creative",
                "created": datetime.utcnow().isoformat()
            },
            "technical": {
                "name": "기술적",
                "description": "기술적이고 정확한 응답을 제공하는 템플릿",
                "systemPrompt": "당신은 기술 전문가 AI로, 정확하고 사실에 근거한 기술적 응답을 제공합니다.",
                "temperature": 0.3,
                "maxTokens": 2000,
                "topP": 0.85,
                "format": "technical",
                "created": datetime.utcnow().isoformat()
            },
            "reasoning": {
                "name": "추론 기반",
                "description": "단계별 추론 과정을 보여주는 템플릿",
                "systemPrompt": "당신은 분석적인 AI로, 문제를 단계별로 분석하고 추론하여 해결책을 제시합니다.",
                "temperature": 0.5,
                "maxTokens": 2000,
                "topP": 0.9,
                "useReasoning": True,
                "reasoningFormat": "step-by-step",
                "format": "analytical",
                "created": datetime.utcnow().isoformat()
            }
        }
        
        # 각 템플릿 저장
        for template_id, template_data in templates.items():
            template_file = os.path.join(self.templates_dir, f"{template_id}.json")
            try:
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"Error creating template {template_id}: {str(e)}")
    
    def get_settings(self) -> Dict[str, Any]:
        """현재 설정 조회"""
        return {
            "success": True,
            "settings": self.settings
        }
    
    def update_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        """설정 업데이트"""
        try:
            # 설정 업데이트
            for key, value in new_settings.items():
                if key != "created":  # 생성 시간은 변경하지 않음
                    self.settings[key] = value
            
            # 설정 저장
            success = self._save_settings()
            
            return {
                "success": success,
                "settings": self.settings,
                "message": "Settings updated successfully" if success else "Failed to save settings"
            }
                
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_templates(self) -> Dict[str, Any]:
        """템플릿 목록 조회"""
        try:
            templates = {}
            
            for filename in os.listdir(self.templates_dir):
                if filename.endswith(".json"):
                    template_id = os.path.splitext(filename)[0]
                    template_path = os.path.join(self.templates_dir, filename)
                    
                    try:
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                            templates[template_id] = template_data
                    except Exception as e:
                        logger.error(f"Error loading template {template_id}: {str(e)}")
            
            return {
                "success": True,
                "templates": templates,
                "count": len(templates),
                "activeTemplate": self.settings.get("activeTemplate")
            }
                
        except Exception as e:
            logger.error(f"Error getting templates: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """특정 템플릿 조회"""
        try:
            template_path = os.path.join(self.templates_dir, f"{template_id}.json")
            
            if not os.path.exists(template_path):
                return {
                    "success": False,
                    "error": f"Template not found: {template_id}"
                }
            
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            return {
                "success": True,
                "template": template_data,
                "id": template_id
            }
                
        except Exception as e:
            logger.error(f"Error getting template {template_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_template(self, template_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """템플릿 생성"""
        try:
            # 템플릿 ID 유효성 검사
            template_id = template_id.strip().lower()
            if not template_id or not template_id.isalnum():
                return {
                    "success": False,
                    "error": "Invalid template ID. Use alphanumeric characters only."
                }
            
            template_path = os.path.join(self.templates_dir, f"{template_id}.json")
            
            # 기존 템플릿 존재 여부 확인
            if os.path.exists(template_path):
                return {
                    "success": False,
                    "error": f"Template already exists: {template_id}"
                }
            
            # 필수 필드 확인
            required_fields = ["name", "description", "systemPrompt"]
            for field in required_fields:
                if field not in template_data:
                    return {
                        "success": False,
                        "error": f"Missing required field: {field}"
                    }
            
            # 생성 시간 추가
            if "created" not in template_data:
                template_data["created"] = datetime.utcnow().isoformat()
            
            # 템플릿 저장
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "template": template_data,
                "id": template_id,
                "message": f"Template '{template_id}' created successfully"
            }
                
        except Exception as e:
            logger.error(f"Error creating template {template_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """템플릿 업데이트"""
        try:
            template_path = os.path.join(self.templates_dir, f"{template_id}.json")
            
            if not os.path.exists(template_path):
                return {
                    "success": False,
                    "error": f"Template not found: {template_id}"
                }
            
            # 기존 템플릿 로드
            with open(template_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            # 생성 시간 보존
            if "created" in existing_data:
                template_data["created"] = existing_data["created"]
            
            # 수정 시간 추가
            template_data["modified"] = datetime.utcnow().isoformat()
            
            # 템플릿 저장
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "template": template_data,
                "id": template_id,
                "message": f"Template '{template_id}' updated successfully"
            }
                
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_template(self, template_id: str) -> Dict[str, Any]:
        """템플릿 삭제"""
        try:
            # 기본 템플릿은 삭제 불가
            if template_id in ["standard", "creative", "technical", "reasoning"]:
                return {
                    "success": False,
                    "error": f"Cannot delete built-in template: {template_id}"
                }
            
            template_path = os.path.join(self.templates_dir, f"{template_id}.json")
            
            if not os.path.exists(template_path):
                return {
                    "success": False,
                    "error": f"Template not found: {template_id}"
                }
            
            # 현재 활성 템플릿인 경우 기본 템플릿으로 변경
            if self.settings.get("activeTemplate") == template_id:
                self.settings["activeTemplate"] = "standard"
                self._save_settings()
            
            # 템플릿 삭제
            os.remove(template_path)
            
            return {
                "success": True,
                "id": template_id,
                "message": f"Template '{template_id}' deleted successfully"
            }
                
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def set_active_template(self, template_id: str) -> Dict[str, Any]:
        """활성 템플릿 설정"""
        try:
            template_path = os.path.join(self.templates_dir, f"{template_id}.json")
            
            if not os.path.exists(template_path):
                return {
                    "success": False,
                    "error": f"Template not found: {template_id}"
                }
            
            # 활성 템플릿 설정
            self.settings["activeTemplate"] = template_id
            success = self._save_settings()
            
            return {
                "success": success,
                "activeTemplate": template_id,
                "message": f"Active template set to '{template_id}'" if success else "Failed to save settings"
            }
                
        except Exception as e:
            logger.error(f"Error setting active template {template_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def apply_template_to_conversation(self, template_id: str, conversation_id: str) -> Dict[str, Any]:
        """템플릿을 대화에 적용"""
        try:
            template_path = os.path.join(self.templates_dir, f"{template_id}.json")
            
            if not os.path.exists(template_path):
                return {
                    "success": False,
                    "error": f"Template not found: {template_id}"
                }
            
            # 템플릿 로드
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # 필요한 작업을 위한 템플릿 데이터 전달
            # 이 부분은 대화 관리 모듈과 연계하여 추가 구현 필요
            
            return {
                "success": True,
                "template": template_data,
                "conversationId": conversation_id,
                "message": f"Template '{template_id}' applied to conversation '{conversation_id}'"
            }
                
        except Exception as e:
            logger.error(f"Error applying template {template_id} to conversation {conversation_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_active_template_settings(self) -> Dict[str, Any]:
        """현재 활성 템플릿 설정 조회"""
        try:
            active_template_id = self.settings.get("activeTemplate", "standard")
            template_path = os.path.join(self.templates_dir, f"{active_template_id}.json")
            
            if not os.path.exists(template_path):
                # 활성 템플릿이 없으면 기본 템플릿으로 변경
                active_template_id = "standard"
                self.settings["activeTemplate"] = active_template_id
                self._save_settings()
                
                template_path = os.path.join(self.templates_dir, f"{active_template_id}.json")
                if not os.path.exists(template_path):
                    return {
                        "success": False,
                        "error": "Default template not found. System configuration error."
                    }
            
            # 템플릿 로드
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # LLM 생성 옵션으로 변환
            llm_options = {
                "temperature": template_data.get("temperature", 0.7),
                "max_tokens": template_data.get("maxTokens", 1000),
                "top_p": template_data.get("topP", 0.95),
                "system_prompt": template_data.get("systemPrompt", ""),
                "use_reasoning": template_data.get("useReasoning", False),
                "reasoning_format": template_data.get("reasoningFormat", "thinking"),
                "template_id": active_template_id,
                "template_name": template_data.get("name", "Unknown")
            }
            
            return {
                "success": True,
                "template": template_data,
                "id": active_template_id,
                "llmOptions": llm_options
            }
                
        except Exception as e:
            logger.error(f"Error getting active template settings: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
