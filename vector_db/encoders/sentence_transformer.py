"""
SentenceTransformer 인코더

SentenceTransformers 라이브러리를 활용한 의미론적 텍스트 인코딩을 제공합니다.
이 인코더는 외부 패키지인 sentence-transformers가 필요합니다.
"""

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError("이 인코더를 사용하려면 'pip install sentence-transformers'를 실행하세요.")

import numpy as np
from typing import List, Union, Optional

from .base import Encoder
from core.logging import get_logger

logger = get_logger("vector_db.encoders.sentence_transformer")

class SentenceTransformerEncoder(Encoder):
    """SentenceTransformer 기반 인코더"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        SentenceTransformer 인코더 초기화
        
        Args:
            model_name: 사용할 모델 이름 (기본값: "all-MiniLM-L6-v2")
        """
        try:
            self._model = SentenceTransformer(model_name)
            self._model_name = model_name
            self._dim = self._model.get_sentence_embedding_dimension()
            logger.info(f"SentenceTransformer 모델 로드됨: {model_name} (차원: {self._dim})")
        except Exception as e:
            logger.error(f"SentenceTransformer 모델 로드 실패: {str(e)}")
            raise
    
    def encode(self, text: str) -> np.ndarray:
        """
        텍스트를 벡터로 인코딩
        
        Args:
            text: 인코딩할 텍스트
        
        Returns:
            인코딩된 벡터
        """
        if not text:
            return np.zeros(self._dim)
        
        # 모델을 사용하여 임베딩 생성
        embedding = self._model.encode(text, show_progress_bar=False)
        return embedding
    
    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        텍스트 배치를 벡터로 인코딩
        
        Args:
            texts: 인코딩할 텍스트 목록
        
        Returns:
            인코딩된 벡터 배열
        """
        if not texts:
            return np.zeros((0, self._dim))
        
        # 빈 텍스트를 더미 텍스트로 대체 (SentenceTransformer는 빈 문자열을 처리하지 못함)
        processed_texts = ["." if not text else text for text in texts]
        
        # 배치 인코딩 (훨씬 효율적)
        embeddings = self._model.encode(processed_texts, show_progress_bar=False)
        return embeddings
    
    @property
    def dimension(self) -> int:
        """
        인코더 출력 차원
        
        Returns:
            벡터 차원 수
        """
        return self._dim
    
    def get_info(self) -> dict:
        """
        인코더 정보 반환
        
        Returns:
            인코더 정보 딕셔너리
        """
        return {
            "type": "sentence_transformer",
            "model_name": self._model_name,
            "dimension": self._dim
        }
