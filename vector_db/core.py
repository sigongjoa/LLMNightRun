"""
벡터 데이터베이스 코어

문서를 벡터화하고 저장, 검색하는 핵심 기능을 제공합니다.
"""

import os
import json
import uuid
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Union, Callable

from .encoders import Encoder, DefaultEncoder
from core.logging import get_logger
from core.config import get_config
from core.events import publish

logger = get_logger("vector_db")

class Document:
    """문서 클래스"""
    
    def __init__(self, id: str, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        문서 초기화
        
        Args:
            id: 문서 ID
            text: 문서 텍스트
            metadata: 문서 메타데이터 (기본값: {})
        """
        self.id = id
        self.text = text
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        딕셔너리로 변환
        
        Returns:
            문서 딕셔너리
        """
        return {
            "id": self.id,
            "text": self.text,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """
        딕셔너리에서 문서 생성
        
        Args:
            data: 문서 딕셔너리
            
        Returns:
            문서 객체
        """
        return cls(
            id=data["id"],
            text=data["text"],
            metadata=data.get("metadata", {})
        )
    
    def __str__(self) -> str:
        """문자열 표현"""
        return f"Document(id={self.id}, text={self.text[:50]}{'...' if len(self.text) > 50 else ''}, metadata={self.metadata})"

class VectorDB:
    """벡터 데이터베이스 클래스"""
    
    def __init__(self, storage_dir: Optional[str] = None, encoder: Optional[Encoder] = None):
        """
        벡터 데이터베이스 초기화
        
        Args:
            storage_dir: 저장 디렉토리 (기본값: 설정에서 가져옴)
            encoder: 벡터 인코더 (기본값: 설정에서 가져와 생성)
        """
        config = get_config()
        
        # 저장 디렉토리 설정
        self.storage_dir = storage_dir or config.get("vector_db", "storage_dir")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 문서 저장 디렉토리
        self.docs_dir = os.path.join(self.storage_dir, "documents")
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # 벡터 저장 디렉토리
        self.vectors_dir = os.path.join(self.storage_dir, "vectors")
        os.makedirs(self.vectors_dir, exist_ok=True)
        
        # 인덱스 파일
        self.index_file = os.path.join(self.storage_dir, "index.json")
        
        # 인코더 설정
        if encoder is None:
            encoder_type = config.get("vector_db", "default_encoder")
            if encoder_type == "default":
                dimension = config.get("vector_db", "dimension")
                encoder = DefaultEncoder(dimension=dimension)
            elif encoder_type == "sentence_transformer":
                try:
                    from .encoders.sentence_transformer import SentenceTransformerEncoder
                    model_name = config.get("vector_db", "sentence_transformer_model")
                    encoder = SentenceTransformerEncoder(model_name=model_name)
                except ImportError:
                    logger.warning("SentenceTransformer를 사용할 수 없어 기본 인코더로 대체합니다.")
                    dimension = config.get("vector_db", "dimension")
                    encoder = DefaultEncoder(dimension=dimension)
        
        self.encoder = encoder
        
        # 인덱스 로드 또는 생성
        self._load_index()
        
        logger.info(f"벡터 데이터베이스 초기화됨: {self.storage_dir} (차원: {self.encoder.dimension})")
    
    def _load_index(self) -> None:
        """인덱스 로드 또는 초기화"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
                logger.debug(f"인덱스 로드됨: {len(self.index['documents'])}개 문서")
            else:
                self.index = {
                    "documents": {},
                    "encoder_info": self.encoder.get_info()
                }
                self._save_index()
                logger.debug("새 인덱스 생성됨")
        except Exception as e:
            logger.error(f"인덱스 로드 중 오류 발생: {str(e)}")
            self.index = {
                "documents": {},
                "encoder_info": self.encoder.get_info()
            }
            self._save_index()
    
    def _save_index(self) -> None:
        """인덱스 저장"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
            logger.debug("인덱스 저장됨")
        except Exception as e:
            logger.error(f"인덱스 저장 중 오류 발생: {str(e)}")
    
    def add(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        문서 추가
        
        Args:
            text: 문서 텍스트
            metadata: 문서 메타데이터 (기본값: {})
        
        Returns:
            문서 ID
        """
        # 문서 ID 생성
        doc_id = str(uuid.uuid4())
        
        # 문서 생성
        doc = Document(id=doc_id, text=text, metadata=metadata or {})
        
        # 인코딩
        vector = self.encoder.encode(text)
        
        # 문서 저장
        doc_path = os.path.join(self.docs_dir, f"{doc_id}.json")
        with open(doc_path, 'w', encoding='utf-8') as f:
            json.dump(doc.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 벡터 저장
        vector_path = os.path.join(self.vectors_dir, f"{doc_id}.npy")
        np.save(vector_path, vector)
        
        # 인덱스 업데이트
        self.index["documents"][doc_id] = {
            "path": doc_path,
            "vector_path": vector_path
        }
        self._save_index()
        
        # 이벤트 발행
        publish("vector_db.document.added", doc_id=doc_id, text=text, metadata=metadata)
        
        logger.debug(f"문서 추가됨: {doc_id}")
        return doc_id
    
    def get(self, doc_id: str) -> Optional[Document]:
        """
        ID로 문서 가져오기
        
        Args:
            doc_id: 문서 ID
        
        Returns:
            문서 객체 또는 None (없는 경우)
        """
        if doc_id not in self.index["documents"]:
            logger.warning(f"문서를 찾을 수 없음: {doc_id}")
            return None
        
        try:
            doc_path = self.index["documents"][doc_id]["path"]
            with open(doc_path, 'r', encoding='utf-8') as f:
                doc_data = json.load(f)
            
            return Document.from_dict(doc_data)
        
        except Exception as e:
            logger.error(f"문서 로드 중 오류 발생: {str(e)}")
            return None
    
    def update(self, doc_id: str, text: Optional[str] = None, 
               metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        문서 업데이트
        
        Args:
            doc_id: 문서 ID
            text: 새 문서 텍스트 (기본값: None, 변경 없음)
            metadata: 새 메타데이터 (기본값: None, 변경 없음)
        
        Returns:
            성공 여부
        """
        # 문서 존재 확인
        doc = self.get(doc_id)
        if not doc:
            logger.warning(f"업데이트할 문서를 찾을 수 없음: {doc_id}")
            return False
        
        # 텍스트 업데이트
        updated = False
        if text is not None and text != doc.text:
            doc.text = text
            updated = True
            
            # 벡터 재생성
            vector = self.encoder.encode(text)
            vector_path = os.path.join(self.vectors_dir, f"{doc_id}.npy")
            np.save(vector_path, vector)
        
        # 메타데이터 업데이트
        if metadata is not None:
            doc.metadata = metadata
            updated = True
        
        if not updated:
            logger.debug(f"업데이트할 내용 없음: {doc_id}")
            return True
        
        # 문서 저장
        doc_path = self.index["documents"][doc_id]["path"]
        with open(doc_path, 'w', encoding='utf-8') as f:
            json.dump(doc.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 이벤트 발행
        publish("vector_db.document.updated", doc_id=doc_id, text=text, metadata=metadata)
        
        logger.debug(f"문서 업데이트됨: {doc_id}")
        return True
    
    def delete(self, doc_id: str) -> bool:
        """
        문서 삭제
        
        Args:
            doc_id: 문서 ID
        
        Returns:
            성공 여부
        """
        if doc_id not in self.index["documents"]:
            logger.warning(f"삭제할 문서를 찾을 수 없음: {doc_id}")
            return False
        
        try:
            # 파일 경로
            doc_path = self.index["documents"][doc_id]["path"]
            vector_path = self.index["documents"][doc_id]["vector_path"]
            
            # 파일 삭제
            if os.path.exists(doc_path):
                os.remove(doc_path)
            
            if os.path.exists(vector_path):
                os.remove(vector_path)
            
            # 인덱스 업데이트
            del self.index["documents"][doc_id]
            self._save_index()
            
            # 이벤트 발행
            publish("vector_db.document.deleted", doc_id=doc_id)
            
            logger.debug(f"문서 삭제됨: {doc_id}")
            return True
        
        except Exception as e:
            logger.error(f"문서 삭제 중 오류 발생: {str(e)}")
            return False
    
    def count(self) -> int:
        """
        총 문서 수 반환
        
        Returns:
            문서 수
        """
        return len(self.index["documents"])
    
    def list_documents(self, limit: Optional[int] = None, 
                      filter_metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        문서 목록 가져오기
        
        Args:
            limit: 최대 문서 수 (기본값: None, 모든 문서)
            filter_metadata: 메타데이터 필터링 (기본값: None)
        
        Returns:
            문서 목록
        """
        docs = []
        
        for doc_id in self.index["documents"]:
            # 최대 문서 수 확인
            if limit is not None and len(docs) >= limit:
                break
            
            # 문서 가져오기
            doc = self.get(doc_id)
            if not doc:
                continue
            
            # 메타데이터 필터링
            if filter_metadata:
                match = True
                for key, value in filter_metadata.items():
                    if key not in doc.metadata or doc.metadata[key] != value:
                        match = False
                        break
                
                if not match:
                    continue
            
            docs.append(doc)
        
        return docs
    
    def search(self, query: str, k: int = 5, threshold: Optional[float] = None,
              filter_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[Document, float]]:
        """
        유사도 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 결과 수 (기본값: 5)
            threshold: 유사도 임계값 (기본값: None)
            filter_metadata: 메타데이터 필터링 (기본값: None)
        
        Returns:
            (문서, 유사도 점수) 튜플 목록
        """
        if not query:
            logger.warning("빈 쿼리로 검색 시도")
            return []
        
        # 쿼리 인코딩
        query_vector = self.encoder.encode(query)
        
        # 결과 저장 리스트
        results = []
        
        # 모든 문서에 대해 유사도 계산
        for doc_id in self.index["documents"]:
            try:
                # 문서 벡터 로드
                vector_path = self.index["documents"][doc_id]["vector_path"]
                doc_vector = np.load(vector_path)
                
                # 유사도 계산 (코사인 유사도)
                similarity = np.dot(query_vector, doc_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(doc_vector)
                )
                
                # 임계값 확인
                if threshold is not None and similarity < threshold:
                    continue
                
                # 문서 로드
                doc = self.get(doc_id)
                if not doc:
                    continue
                
                # 메타데이터 필터링
                if filter_metadata:
                    match = True
                    for key, value in filter_metadata.items():
                        if key not in doc.metadata or doc.metadata[key] != value:
                            match = False
                            break
                    
                    if not match:
                        continue
                
                # 결과 추가
                results.append((doc, float(similarity)))
            
            except Exception as e:
                logger.error(f"문서 {doc_id} 처리 중 오류 발생: {str(e)}")
        
        # 유사도 기준으로 정렬
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 k개 반환
        return results[:k]
    
    def clear(self) -> bool:
        """
        모든 문서 삭제
        
        Returns:
            성공 여부
        """
        try:
            # 모든 문서 ID 복사
            doc_ids = list(self.index["documents"].keys())
            
            # 각 문서 삭제
            for doc_id in doc_ids:
                self.delete(doc_id)
            
            # 이벤트 발행
            publish("vector_db.cleared")
            
            logger.info("벡터 DB 초기화됨")
            return True
        
        except Exception as e:
            logger.error(f"벡터 DB 초기화 중 오류 발생: {str(e)}")
            return False
