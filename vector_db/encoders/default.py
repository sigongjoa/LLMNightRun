"""
기본 인코더

간단한 해싱 기반 텍스트 인코딩을 제공하는 기본 인코더 구현입니다.
실제 의미론적 검색에는 적합하지 않지만, 외부 의존성 없이 작동합니다.
"""

import hashlib
import numpy as np
from typing import List, Union, Optional

from .base import Encoder
from core.logging import get_logger

logger = get_logger("vector_db.encoders.default")

class DefaultEncoder(Encoder):
    """간단한 해싱 기반 인코더"""
    
    def __init__(self, dimension: int = 768, seed: int = 42):
        """
        기본 인코더 초기화
        
        Args:
            dimension: 출력 벡터 차원 (기본값: 768)
            seed: 난수 생성 시드 (기본값: 42)
        """
        self._dimension = dimension
        self._seed = seed
        self._rng = np.random.RandomState(seed)
        logger.debug(f"기본 인코더 초기화: 차원={dimension}, 시드={seed}")
    
    def encode(self, text: str) -> np.ndarray:
        """
        텍스트를 벡터로 인코딩
        
        텍스트를 여러 청크로 나누고, 각 청크의 해시를 계산하여
        의사 랜덤 벡터를 생성합니다.
        
        Args:
            text: 인코딩할 텍스트
        
        Returns:
            인코딩된 벡터 (차원: self._dimension)
        """
        if not text:
            return np.zeros(self._dimension)
        
        # 결과 벡터 초기화
        vector = np.zeros(self._dimension)
        
        # 텍스트 청크 분할 (중복 허용, 슬라이딩 윈도우)
        chunks = []
        words = text.split()
        
        # 단어 단위 청크
        chunks.extend(words)
        
        # 2단어 청크
        if len(words) >= 2:
            for i in range(len(words) - 1):
                chunks.append(words[i] + " " + words[i + 1])
        
        # 3단어 청크
        if len(words) >= 3:
            for i in range(len(words) - 2):
                chunks.append(words[i] + " " + words[i + 1] + " " + words[i + 2])
        
        # 전체 텍스트도 하나의 청크로 추가
        chunks.append(text)
        
        # 각 청크의 해시를 계산하여 벡터에 추가
        for chunk in chunks:
            # 청크의 SHA-256 해시 계산
            chunk_hash = hashlib.sha256(chunk.encode('utf-8')).digest()
            
            # 해시 값을 시드로 사용하여 의사 랜덤 벡터 생성
            chunk_seed = int.from_bytes(chunk_hash[:4], byteorder='big')
            chunk_rng = np.random.RandomState(chunk_seed)
            chunk_vector = chunk_rng.randn(self._dimension)
            
            # 정규화
            chunk_vector = chunk_vector / np.linalg.norm(chunk_vector)
            
            # 결과 벡터에 추가 (가중치 부여: 더 긴 청크에 더 높은 가중치)
            weight = len(chunk.split()) / len(words) if words else 1.0
            vector += chunk_vector * weight
        
        # 최종 벡터 정규화
        if np.linalg.norm(vector) > 0:
            vector = vector / np.linalg.norm(vector)
        
        return vector
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        텍스트 배치를 벡터로 인코딩
        
        Args:
            texts: 인코딩할 텍스트 목록
        
        Returns:
            인코딩된 벡터 배열 (shape: [len(texts), self._dimension])
        """
        vectors = []
        for text in texts:
            vectors.append(self.encode(text))
        return np.array(vectors)
    
    @property
    def dimension(self) -> int:
        """
        인코더 출력 차원
        
        Returns:
            벡터 차원 수
        """
        return self._dimension
    
    def get_info(self) -> dict:
        """
        인코더 정보 반환
        
        Returns:
            인코더 정보 딕셔너리
        """
        return {
            "type": "default",
            "dimension": self._dimension,
            "seed": self._seed
        }
