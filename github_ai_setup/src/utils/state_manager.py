"""
상태 관리자 (State Manager)

워크플로우의 각 단계의 상태를 추적하고 관리합니다.
오류가 발생했을 때 이전 상태로 돌아갈 수 있도록 상태 정보를 저장합니다.
"""

import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class StateManager:
    """
    워크플로우 상태를 관리하는 클래스
    
    상태(state)는 다음 중 하나일 수 있습니다:
    - init: 초기 상태
    - download: GitHub 레포지토리 다운로드 중
    - setup: 환경 설정 중
    - preprocess: 데이터 전처리 중
    - train: 모델 학습 중
    - visualize: 결과 시각화 중
    - complete: 워크플로우 완료
    - error: 오류 발생
    """
    
    def __init__(self, state_file_path):
        """
        상태 관리자를 초기화합니다.
        
        Args:
            state_file_path (str): 상태 정보를 저장할 파일 경로
        """
        self.state_file_path = state_file_path
        self.states = [
            "init", "download", "setup", "preprocess", 
            "train", "visualize", "complete", "error"
        ]
        
        # 상태 파일 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(state_file_path), exist_ok=True)
        
        # 상태 파일이 없으면 초기 상태로 생성
        if not os.path.exists(state_file_path):
            self._save_state({
                "state": "init",
                "timestamp": self._get_timestamp(),
                "details": {},
                "error": None
            })
    
    def _get_timestamp(self):
        """현재 타임스탬프를 반환합니다."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _load_state(self):
        """상태 파일에서 현재 상태를 로드합니다."""
        try:
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"상태 파일을 찾을 수 없습니다: {self.state_file_path}")
            return {"state": "init", "timestamp": self._get_timestamp(), "details": {}, "error": None}
        except json.JSONDecodeError:
            logger.error(f"상태 파일 파싱 오류: {self.state_file_path}")
            return {"state": "error", "timestamp": self._get_timestamp(), "details": {}, "error": "상태 파일 파싱 오류"}
    
    def _save_state(self, state_data):
        """상태 정보를 파일에 저장합니다."""
        try:
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"상태 파일 저장 오류: {e}")
    
    def get_state(self):
        """현재 상태를 반환합니다."""
        state_data = self._load_state()
        return state_data.get("state", "init")
    
    def set_state(self, state):
        """
        상태를 설정합니다.
        
        Args:
            state (str): 설정할 상태
        
        Raises:
            ValueError: 유효하지 않은 상태가 주어진 경우
        """
        if state not in self.states:
            raise ValueError(f"유효하지 않은 상태: {state}. 유효한 상태: {', '.join(self.states)}")
        
        state_data = self._load_state()
        state_data["state"] = state
        state_data["timestamp"] = self._get_timestamp()
        
        if state == "error":
            logger.error(f"상태가 'error'로 설정되었습니다.")
        else:
            logger.info(f"상태가 '{state}'로 변경되었습니다.")
        
        self._save_state(state_data)
    
    def set_error(self, error_message):
        """
        오류 상태를 설정합니다.
        
        Args:
            error_message (str): 오류 메시지
        """
        state_data = self._load_state()
        state_data["state"] = "error"
        state_data["timestamp"] = self._get_timestamp()
        state_data["error"] = error_message
        
        logger.error(f"오류 발생: {error_message}")
        self._save_state(state_data)
    
    def get_details(self, key=None):
        """
        상태 세부 정보를 반환합니다.
        
        Args:
            key (str, optional): 특정 세부 정보의 키. 기본값은 None으로, 모든 세부 정보를 반환합니다.
            
        Returns:
            dict 또는 값: 키가 주어진 경우 해당 값을, 그렇지 않으면 모든 세부 정보를 반환합니다.
        """
        state_data = self._load_state()
        details = state_data.get("details", {})
        
        if key is not None:
            return details.get(key)
        return details
    
    def set_details(self, key, value):
        """
        상태 세부 정보를 설정합니다.
        
        Args:
            key (str): 세부 정보의 키
            value: 저장할 값
        """
        state_data = self._load_state()
        if "details" not in state_data:
            state_data["details"] = {}
        
        state_data["details"][key] = value
        logger.debug(f"상태 세부 정보 설정: {key}={value}")
        self._save_state(state_data)
    
    def get_error(self):
        """오류 메시지를 반환합니다."""
        state_data = self._load_state()
        return state_data.get("error")
    
    def clear_error(self):
        """오류 상태를 지웁니다."""
        state_data = self._load_state()
        state_data["error"] = None
        logger.info("오류 상태가 지워졌습니다.")
        self._save_state(state_data)
