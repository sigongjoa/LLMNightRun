"""
Vector DB 연동 모듈 - 논문 데이터 벡터 저장 및 검색 기능

기존 vectorDB와 연동하여 논문 데이터를 벡터화하고 저장/검색하는 기능 제공
"""

import os
import sys
import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

# 기존 vector_db 모듈 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 기존 vector_db 모듈 import
try:
    from vector_db.vector_store import VectorDB
    from vector_db.encoders import Encoder, DefaultEncoder
    
    # sentence_transformers가 설치되어 있는지 확인
    try:
        from sentence_transformers import SentenceTransformer
        from vector_db.encoders import SentenceTransformerEncoder
        has_sentence_transformer = True
    except ImportError:
        has_sentence_transformer = False
        
except ImportError as e:
    logging.error(f"Error importing vector_db modules: {e}")
    raise ImportError(f"Could not import vector_db modules. Please ensure the path is correct: {parent_dir}")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# EncoderFactory 클래스 정의 (vector_db에 없는 경우)
class EncoderFactory:
    """
    인코더 팩토리 클래스 - 다양한 인코더 생성 관리
    """
    def __init__(self):
        """EncoderFactory 초기화"""
        pass
        
    def get_encoder(self, model_name: str = "all-MiniLM-L6-v2") -> Encoder:
        """
        인코더 가져오기
        
        Args:
            model_name (str): 모델 이름
            
        Returns:
            Encoder: 인코더 인스턴스
        """
        # SentenceTransformer 인코더 사용 가능한 경우
        if has_sentence_transformer:
            try:
                return SentenceTransformerEncoder(model_name=model_name)
            except Exception as e:
                logger.warning(f"Error creating SentenceTransformerEncoder: {e}")
                logger.warning("Falling back to DefaultEncoder")
        
        # 기본 인코더
        return DefaultEncoder()

class ArxivVectorDBHandler:
    """arXiv 논문 데이터 vectorDB 연동 클래스"""
    
    def __init__(self, 
                collection_name: str = "arxiv_papers",
                db_path: Optional[str] = None,
                encoder_name: str = "all-MiniLM-L6-v2"):
        """
        ArxivVectorDBHandler 초기화
        
        Args:
            collection_name (str): 벡터 컬렉션 이름
            db_path (str, optional): 벡터 DB 경로 (기본값: vector_db_data)
            encoder_name (str): 임베딩 인코더 이름
        """
        # DB 경로 설정
        if db_path is None:
            db_path = os.path.join(parent_dir, "vector_db_data")
            
        self.collection_name = collection_name
        self.db_path = db_path
        
        # 디렉토리 생성
        os.makedirs(db_path, exist_ok=True)
        
        try:
            # 인코더 및 벡터 스토어 초기화
            self.encoder_factory = EncoderFactory()
            self.encoder = self.encoder_factory.get_encoder(encoder_name)
            
            # VectorDB 초기화
            collection_path = os.path.join(db_path, collection_name)
            os.makedirs(collection_path, exist_ok=True)
            self.vector_db = VectorDB(encoder=self.encoder, storage_dir=collection_path)
                
            logger.info(f"Initialized ArxivVectorDBHandler with collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing ArxivVectorDBHandler: {e}")
            raise
    
    def add_paper(self, paper_data: Dict[str, Any]) -> str:
        """
        논문 데이터 추가
        
        Args:
            paper_data (Dict[str, Any]): 논문 데이터
            
        Returns:
            str: 저장된 문서 ID
        """
        try:
            # 필수 필드 확인
            required_fields = ['id', 'title', 'summary']
            for field in required_fields:
                if field not in paper_data:
                    raise ValueError(f"Missing required field: {field}")
                    
            # datetime 객체를 문자열로 변환
            paper_data_serializable = self._ensure_json_serializable(paper_data)
            
            # 임베딩 텍스트 생성
            embed_text = f"{paper_data_serializable['title']} {paper_data_serializable['summary']}"
            if 'keywords' in paper_data_serializable and paper_data_serializable['keywords']:
                keyword_str = " ".join([kw['keyword'] for kw in paper_data_serializable['keywords']])
                embed_text += f" {keyword_str}"
            
            # VectorDB에 추가
            doc_id = self.vector_db.add(
                document=embed_text,
                metadata=paper_data_serializable
            )
            
            logger.info(f"Added paper to vector DB: {paper_data_serializable['title']} (ID: {doc_id})")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding paper to vector DB: {e}")
            raise
    
    def get_paper(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        논문 데이터 조회
        
        Args:
            doc_id (str): 문서 ID
            
        Returns:
            Dict[str, Any]: 논문 데이터
        """
        try:
            doc = self.vector_db.get(doc_id)
            if doc:
                return doc.metadata
            return None
        except Exception as e:
            logger.error(f"Error getting paper from vector DB: {e}")
            return None
    
    def update_paper(self, doc_id: str, paper_data: Dict[str, Any]) -> bool:
        """
        논문 데이터 업데이트
        
        Args:
            doc_id (str): 문서 ID
            paper_data (Dict[str, Any]): 업데이트할 논문 데이터
            
        Returns:
            bool: 성공 여부
        """
        try:
            # datetime 객체를 문자열로 변환
            paper_data_serializable = self._ensure_json_serializable(paper_data)
            
            # 임베딩 텍스트 업데이트
            embed_text = f"{paper_data_serializable.get('title', '')} {paper_data_serializable.get('summary', '')}"
            if 'keywords' in paper_data_serializable and paper_data_serializable['keywords']:
                keyword_str = " ".join([kw['keyword'] for kw in paper_data_serializable['keywords']])
                embed_text += f" {keyword_str}"
            
            # 업데이트
            result = self.vector_db.update(
                doc_id=doc_id,
                text=embed_text,
                metadata=paper_data_serializable
            )
            
            if result:
                logger.info(f"Updated paper in vector DB: {doc_id}")
            else:
                logger.warning(f"Paper not found for update: {doc_id}")
                
            return result
            
        except Exception as e:
            logger.error(f"Error updating paper in vector DB: {e}")
            return False
    
    def delete_paper(self, doc_id: str) -> bool:
        """
        논문 데이터 삭제
        
        Args:
            doc_id (str): 문서 ID
            
        Returns:
            bool: 성공 여부
        """
        try:
            result = self.vector_db.delete(doc_id)
            if result:
                logger.info(f"Deleted paper from vector DB: {doc_id}")
            else:
                logger.warning(f"Paper not found for deletion: {doc_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting paper from vector DB: {e}")
            return False
    
    def search_papers(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        논문 검색
        
        Args:
            query (str): 검색 쿼리
            limit (int): 결과 제한 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 목록
        """
        try:
            # 벡터 검색
            results = self.vector_db.search(
                query=query,
                k=limit
            )
            
            # 결과 처리
            search_results = []
            for doc, score in results:
                item = {
                    'id': doc.id,
                    'score': score,
                    **doc.metadata
                }
                search_results.append(item)
                
            logger.info(f"Search for '{query}' returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching papers in vector DB: {e}")
            return []
    
    def list_papers(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        논문 목록 조회
        
        Args:
            limit (int): 결과 제한 수
            offset (int): 시작 오프셋
            
        Returns:
            List[Dict[str, Any]]: 논문 목록
        """
        try:
            logger.info(f"Listing papers from vector DB (limit={limit}, offset={offset})")
            docs = self.vector_db.list_documents(limit=limit, offset=offset)
            
            # 결과 처리
            papers = []
            
            if not docs:
                logger.warning("list_documents returned None or empty list")
                return []
                
            logger.info(f"Retrieved {len(docs)} documents from vector DB")
            
            for i, doc in enumerate(docs):
                try:
                    # 기본 ID 확인 (metadata에 id가 없는 경우 doc.id 사용)
                    paper = {
                        'id': doc.id,
                    }
                    
                    # Metadata가 None인지 확인
                    if doc.metadata is not None:
                        paper.update(doc.metadata)
                    else:
                        logger.warning(f"Document {i} (ID: {doc.id}) has None metadata")
                    
                    papers.append(paper)
                except Exception as doc_err:
                    logger.error(f"Error processing document {i}: {doc_err}")
                
            logger.info(f"Successfully listed {len(papers)} papers from vector DB")
            return papers
            
        except Exception as e:
            logger.error(f"Error listing papers from vector DB: {e}", exc_info=True)
            return []
    
    def get_paper_count(self) -> int:
        """
        논문 수 조회
        
        Returns:
            int: 저장된 논문 수
        """
        try:
            count = self.vector_db.count()
            return count
        except Exception as e:
            logger.error(f"Error getting paper count from vector DB: {e}")
            return 0
            
    def paper_exists(self, paper_id: str) -> bool:
        """
        논문 존재 여부 확인
        
        Args:
            paper_id (str): arXiv 논문 ID
            
        Returns:
            bool: 존재 여부
        """
        try:
            # 검색해서 확인
            docs = self.vector_db.list_documents()
            for doc in docs:
                metadata = doc.metadata
                if metadata.get('id') == paper_id or metadata.get('entry_id') == paper_id:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking paper existence in vector DB: {e}")
            return False
            
    def _ensure_json_serializable(self, data):
        """
        JSON 직렬화 가능한 객체로 변환
        
        Args:
            data: 변환할 데이터 (dict, list, datetime 등)
            
        Returns:
            JSON 직렬화 가능한 데이터
        """
        import datetime
        
        if isinstance(data, dict):
            return {k: self._ensure_json_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._ensure_json_serializable(item) for item in data]
        elif isinstance(data, datetime.datetime):
            return data.isoformat()
        elif isinstance(data, datetime.date):
            return data.isoformat()
        else:
            return data

# 사용 예시
if __name__ == "__main__":
    # 핸들러 초기화
    handler = ArxivVectorDBHandler()
    
    # 예시 논문 데이터
    sample_paper = {
        'id': 'arxiv:2004.14546',
        'entry_id': '2004.14546',
        'title': 'Pretrained Transformers for Text Ranking: BERT and Beyond',
        'authors': ['Andrew Yates', 'Rodrigo Nogueira', 'Jimmy Lin'],
        'summary': 'The goal of text ranking is to generate an ordered list of texts...',
        'published': '2020-04-30',
        'categories': ['cs.IR', 'cs.CL'],
        'keywords': [
            {'keyword': 'transformers', 'score': 0.95},
            {'keyword': 'bert', 'score': 0.92},
            {'keyword': 'text ranking', 'score': 0.88}
        ]
    }
    
    try:
        # 논문 추가
        doc_id = handler.add_paper(sample_paper)
        print(f"Added paper with ID: {doc_id}")
        
        # 검색 테스트
        search_results = handler.search_papers("transformers bert")
        print(f"Search results: {len(search_results)} papers found")
        for result in search_results:
            print(f"- {result['title']} (Score: {result['score']:.4f})")
        
        # 논문 수 확인
        count = handler.get_paper_count()
        print(f"Total papers in DB: {count}")
        
        # 추가한 논문 삭제
        if handler.delete_paper(doc_id):
            print(f"Successfully deleted paper: {doc_id}")
            
    except Exception as e:
        print(f"Error in vector DB example: {e}")
