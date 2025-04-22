"""
벡터 인코더 모듈

텍스트를 벡터로 변환하는 다양한 인코더를 제공합니다.
"""

from .base import Encoder
from .default import DefaultEncoder

# 인코더 팩토리 함수
def get_encoder(encoder_type: str, **kwargs):
    """
    인코더 타입에 따른 인코더 인스턴스 생성
    
    Args:
        encoder_type: 인코더 타입 ('default', 'sentence_transformer' 등)
        **kwargs: 인코더별 추가 매개변수
    
    Returns:
        인코더 인스턴스
    
    Raises:
        ValueError: 지원되지 않는 인코더 타입
    """
    if encoder_type == "default":
        return DefaultEncoder(**kwargs)
    elif encoder_type == "sentence_transformer":
        try:
            from .sentence_transformer import SentenceTransformerEncoder
            return SentenceTransformerEncoder(**kwargs)
        except ImportError:
            raise ImportError("SentenceTransformer를 사용하려면 'sentence-transformers' 패키지를 설치하세요.")
    else:
        raise ValueError(f"지원되지 않는 인코더 타입: {encoder_type}")
