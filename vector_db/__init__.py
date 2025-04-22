"""
벡터 데이터베이스 모듈

텍스트를 벡터화하고 저장, 검색하는 기능을 제공합니다.
"""

from .core import VectorDB, Document
from .encoders import Encoder, DefaultEncoder, get_encoder
