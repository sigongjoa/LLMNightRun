"""
플러그인 기본 클래스

모든 플러그인 구현의 기본이 되는 추상 클래스입니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class BasePlugin(ABC):
    """플러그인 추상 기본 클래스"""
    
    @property
    @abstractmethod
    def plugin_id(self) -> str:
        """
        플러그인 고유 ID
        
        Returns:
            플러그인 ID
        """
        pass
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """
        플러그인 표시 이름
        
        Returns:
            플러그인 이름
        """
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """
        플러그인 버전
        
        Returns:
            버전 문자열
        """
        pass
    
    @property
    def description(self) -> str:
        """
        플러그인 설명
        
        Returns:
            설명 문자열
        """
        return "플러그인 설명이 없습니다."
    
    @property
    def author(self) -> str:
        """
        플러그인 작성자
        
        Returns:
            작성자 문자열
        """
        return "알 수 없음"
    
    @property
    def hooks(self) -> Dict[str, List[str]]:
        """
        플러그인이 등록하는 훅 목록
        
        Returns:
            훅 딕셔너리 {훅 이름: [메서드 이름 목록]}
        """
        return {}
    
    def initialize(self) -> bool:
        """
        플러그인 초기화 (활성화 시 호출)
        
        Returns:
            성공 여부
        """
        return True
    
    def cleanup(self) -> bool:
        """
        플러그인 정리 (비활성화 시 호출)
        
        Returns:
            성공 여부
        """
        return True
    
    def get_config(self) -> Dict[str, Any]:
        """
        플러그인 설정 가져오기
        
        Returns:
            설정 딕셔너리
        """
        return {}
    
    def set_config(self, config: Dict[str, Any]) -> bool:
        """
        플러그인 설정 변경
        
        Args:
            config: 새 설정 딕셔너리
        
        Returns:
            성공 여부
        """
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """
        플러그인 정보 가져오기
        
        Returns:
            정보 딕셔너리
        """
        return {
            "id": self.plugin_id,
            "name": self.plugin_name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "hooks": self.hooks
        }
