"""
인코더 기본 클래스

모든 인코더 구현의 기본이 되는 추상 클래스입니다.
"""

from abc import ABC, abstractmethod
import numpy as np
from typing import List, Union, Optional

class Encoder(ABC):
    """인코더 추상 클래스"""
    
    @abstractmethod
    def encode(self, text: str) -> np.ndarray:
        """
        텍스트를 벡터로 인코딩
        
        Args:
            text: 인코딩할 텍스트
        
        Returns:
            인코딩된 벡터
        """
        pass
    
    @abstractmethod
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        텍스트 배치를 벡터로 인코딩
        
        Args:
            texts: 인코딩할 텍스트 목록
        
        Returns:
            인코딩된 벡터 배열
        """
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """
        인코더 출력 차원
        
        Returns:
            벡터 차원 수
        """
        pass
    
    @abstractmethod
    def get_info(self) -> dict:
        """
        인코더 정보 반환
        
        Returns:
            인코더 정보 딕셔너리
        """
        pass
