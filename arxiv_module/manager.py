"""
Arxiv 논문 관리 모듈

검색된 논문을 관리하고 벡터 DB와 연동하는 기능을 제공합니다.
"""

import os
import json
import datetime
from typing import List, Dict, Any, Optional, Tuple, Set

from core.logging import get_logger
from core.config import get_config
from core.events import publish

from .search import search_papers, get_paper_details
from .downloader import download_paper, download_multiple_papers

# 벡터 DB 연동을 위한 임포트
try:
    from vector_db import VectorDB, Document
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False

logger = get_logger("arxiv_module.manager")

class ArxivManager:
    """Arxiv 논문 관리자 클래스"""
    
    def __init__(self, data_dir: Optional[str] = None, use_vector_db: bool = True):
        """
        Arxiv 논문 관리자 초기화
        
        Args:
            data_dir: 데이터 저장 디렉토리 (기본값: 설정에서 가져옴)
            use_vector_db: 벡터 DB 사용 여부
        """
        config = get_config()
        
        # 데이터 디렉토리 설정
        self.data_dir = data_dir or os.path.join(
            config.get("core", "data_dir", "data"),
            "arxiv"
        )
        
        # 하위 디렉토리 설정
        self.papers_dir = os.path.join(self.data_dir, "papers")
        self.pdfs_dir = os.path.join(self.data_dir, "pdfs")
        self.collections_dir = os.path.join(self.data_dir, "collections")
        
        # 디렉토리 생성
        for directory in [self.data_dir, self.papers_dir, self.pdfs_dir, self.collections_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # 벡터 DB 설정
        self.use_vector_db = use_vector_db and VECTOR_DB_AVAILABLE
        self.vector_db = None
        
        if self.use_vector_db:
            try:
                self.vector_db = VectorDB()
                logger.info("벡터 DB 연결 성공")
            except Exception as e:
                logger.error(f"벡터 DB 연결 실패: {str(e)}")
                self.use_vector_db = False
        
        # 검색 기록 파일
        self.search_history_file = os.path.join(self.data_dir, "search_history.json")
        self.search_history = self._load_search_history()
        
        logger.info(f"Arxiv 관리자 초기화됨 (벡터 DB 사용: {self.use_vector_db})")
    
    def _load_search_history(self) -> List[Dict[str, Any]]:
        """
        검색 기록 로드
        
        Returns:
            검색 기록 목록
        """
        if os.path.exists(self.search_history_file):
            try:
                with open(self.search_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"검색 기록 로드 실패: {str(e)}")
        
        return []
    
    def _save_search_history(self) -> None:
        """검색 기록 저장"""
        try:
            with open(self.search_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"검색 기록 저장 실패: {str(e)}")
    
    def search(self, query: str, max_results: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        논문 검색 및 결과 저장
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            **kwargs: 추가 검색 옵션
        
        Returns:
            검색 결과 논문 목록
        """
        # 검색 실행
        results = search_papers(query, max_results=max_results, **kwargs)
        
        # 검색 기록 추가
        search_entry = {
            "query": query,
            "timestamp": datetime.datetime.now().isoformat(),
            "max_results": max_results,
            "options": kwargs,
            "result_count": len(results),
            "result_ids": [paper["id"] for paper in results]
        }
        
        self.search_history.append(search_entry)
        self._save_search_history()
        
        # 검색 결과 저장
        for paper in results:
            self.save_paper(paper)
        
        # 이벤트 발행
        publish("arxiv.search.complete", query=query, result_count=len(results))
        
        return results
    
    def save_paper(self, paper: Dict[str, Any]) -> str:
        """
        논문 정보 저장
        
        Args:
            paper: 논문 정보 딕셔너리
        
        Returns:
            저장된 파일 경로
        """
        paper_id = paper['id']
        file_path = os.path.join(self.papers_dir, f"{paper_id}.json")
        
        # 타임스탬프 추가
        if 'saved_at' not in paper:
            paper['saved_at'] = datetime.datetime.now().isoformat()
        
        # 파일 저장
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(paper, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"논문 정보 저장됨: {file_path}")
            
            # 벡터 DB에 추가 (활성화된 경우)
            if self.use_vector_db and self.vector_db:
                self._add_to_vector_db(paper)
            
            return file_path
        
        except Exception as e:
            logger.error(f"논문 정보 저장 실패: {str(e)}")
            return ""
    
    def _add_to_vector_db(self, paper: Dict[str, Any]) -> Optional[str]:
        """
        논문을 벡터 DB에 추가
        
        Args:
            paper: 논문 정보 딕셔너리
        
        Returns:
            추가된 문서 ID 또는 None (실패 시)
        """
        if not self.use_vector_db or not self.vector_db:
            return None
        
        try:
            # 텍스트 준비 (제목 + 초록)
            text = f"{paper['title']}\n\n{paper['abstract']}"
            
            # 메타데이터 준비
            metadata = {
                "source": "arxiv",
                "paper_id": paper['id'],
                "authors": paper['authors'],
                "categories": paper['categories'],
                "published": paper['published'],
                "updated": paper['updated'],
            }
            
            # 벡터 DB에 추가
            doc_id = self.vector_db.add(text, metadata=metadata)
            logger.debug(f"논문을 벡터 DB에 추가함: {doc_id}")
            
            return doc_id
        
        except Exception as e:
            logger.error(f"벡터 DB 추가 실패: {str(e)}")
            return None
    
    def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        저장된 논문 정보 가져오기
        
        Args:
            paper_id: 논문 ID
        
        Returns:
            논문 정보 또는 None (없는 경우)
        """
        file_path = os.path.join(self.papers_dir, f"{paper_id}.json")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"논문 정보 로드 실패: {str(e)}")
                return None
        else:
            # 로컬에 없으면 Arxiv에서 가져오기
            logger.info(f"로컬에 논문이 없음, Arxiv에서 가져오기: {paper_id}")
            paper = get_paper_details(paper_id)
            
            if paper:
                self.save_paper(paper)
            
            return paper
    
    def download_paper_pdf(self, paper_id: str, overwrite: bool = False) -> Optional[str]:
        """
        논문 PDF 다운로드
        
        Args:
            paper_id: 논문 ID
            overwrite: 기존 파일 덮어쓰기 여부
        
        Returns:
            다운로드된 파일 경로 또는 None (실패 시)
        """
        # 논문 정보 가져오기
        paper = self.get_paper(paper_id)
        
        if not paper:
            logger.error(f"다운로드할 논문 정보를 찾을 수 없음: {paper_id}")
            return None
        
        # PDF 다운로드
        return download_paper(paper, self.pdfs_dir, overwrite=overwrite)
    
    def create_collection(self, name: str, description: str = "", papers: List[str] = None) -> str:
        """
        논문 컬렉션 생성
        
        Args:
            name: 컬렉션 이름
            description: 컬렉션 설명
            papers: 논문 ID 목록 (기본값: 빈 목록)
        
        Returns:
            컬렉션 파일 경로
        """
        # 컬렉션 ID 생성 (이름 기반)
        collection_id = name.lower().replace(" ", "_")
        file_path = os.path.join(self.collections_dir, f"{collection_id}.json")
        
        # 컬렉션 데이터 구성
        collection = {
            "id": collection_id,
            "name": name,
            "description": description,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "papers": papers or []
        }
        
        # 파일 저장
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(collection, f, ensure_ascii=False, indent=2)
            
            logger.info(f"컬렉션 생성됨: {name} ({len(papers or [])}개 논문)")
            return file_path
        
        except Exception as e:
            logger.error(f"컬렉션 생성 실패: {str(e)}")
            return ""
    
    def get_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """
        컬렉션 정보 가져오기
        
        Args:
            collection_id: 컬렉션 ID
        
        Returns:
            컬렉션 정보 또는 None (없는 경우)
        """
        file_path = os.path.join(self.collections_dir, f"{collection_id}.json")
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"컬렉션 로드 실패: {str(e)}")
        
        return None
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """
        모든 컬렉션 목록 가져오기
        
        Returns:
            컬렉션 목록
        """
        collections = []
        
        for filename in os.listdir(self.collections_dir):
            if filename.endswith(".json"):
                try:
                    file_path = os.path.join(self.collections_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        collection = json.load(f)
                    
                    # 기본 정보만 포함
                    collections.append({
                        "id": collection["id"],
                        "name": collection["name"],
                        "description": collection["description"],
                        "created_at": collection["created_at"],
                        "updated_at": collection["updated_at"],
                        "paper_count": len(collection["papers"])
                    })
                
                except Exception as e:
                    logger.error(f"컬렉션 파일 로드 실패: {filename} - {str(e)}")
        
        # 업데이트 날짜 기준 정렬
        collections.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return collections
    
    def update_collection(self, collection_id: str, **updates) -> bool:
        """
        컬렉션 업데이트
        
        Args:
            collection_id: 컬렉션 ID
            **updates: 업데이트할 필드 (name, description, papers 등)
        
        Returns:
            성공 여부
        """
        # 컬렉션 가져오기
        collection = self.get_collection(collection_id)
        
        if not collection:
            logger.error(f"업데이트할 컬렉션을 찾을 수 없음: {collection_id}")
            return False
        
        # 필드 업데이트
        for key, value in updates.items():
            if key in collection:
                collection[key] = value
        
        # 업데이트 시간 변경
        collection["updated_at"] = datetime.datetime.now().isoformat()
        
        # 저장
        file_path = os.path.join(self.collections_dir, f"{collection_id}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(collection, f, ensure_ascii=False, indent=2)
            
            logger.info(f"컬렉션 업데이트됨: {collection_id}")
            return True
        
        except Exception as e:
            logger.error(f"컬렉션 업데이트 실패: {str(e)}")
            return False
    
    def add_to_collection(self, collection_id: str, paper_ids: List[str]) -> bool:
        """
        컬렉션에 논문 추가
        
        Args:
            collection_id: 컬렉션 ID
            paper_ids: 추가할 논문 ID 목록
        
        Returns:
            성공 여부
        """
        # 컬렉션 가져오기
        collection = self.get_collection(collection_id)
        
        if not collection:
            logger.error(f"컬렉션을 찾을 수 없음: {collection_id}")
            return False
        
        # 기존 논문 목록
        existing_papers = set(collection["papers"])
        
        # 새 논문 추가
        new_papers = [pid for pid in paper_ids if pid not in existing_papers]
        collection["papers"].extend(new_papers)
        
        # 컬렉션 업데이트
        return self.update_collection(
            collection_id, 
            papers=collection["papers"],
            updated_at=datetime.datetime.now().isoformat()
        )
    
    def remove_from_collection(self, collection_id: str, paper_ids: List[str]) -> bool:
        """
        컬렉션에서 논문 제거
        
        Args:
            collection_id: 컬렉션 ID
            paper_ids: 제거할 논문 ID 목록
        
        Returns:
            성공 여부
        """
        # 컬렉션 가져오기
        collection = self.get_collection(collection_id)
        
        if not collection:
            logger.error(f"컬렉션을 찾을 수 없음: {collection_id}")
            return False
        
        # 제거할 논문 ID 세트
        remove_set = set(paper_ids)
        
        # 논문 제거
        collection["papers"] = [pid for pid in collection["papers"] if pid not in remove_set]
        
        # 컬렉션 업데이트
        return self.update_collection(
            collection_id, 
            papers=collection["papers"],
            updated_at=datetime.datetime.now().isoformat()
        )
    
    def delete_collection(self, collection_id: str) -> bool:
        """
        컬렉션 삭제
        
        Args:
            collection_id: 컬렉션 ID
        
        Returns:
            성공 여부
        """
        file_path = os.path.join(self.collections_dir, f"{collection_id}.json")
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"컬렉션 삭제됨: {collection_id}")
                return True
            except Exception as e:
                logger.error(f"컬렉션 삭제 실패: {str(e)}")
        else:
            logger.warning(f"삭제할 컬렉션을 찾을 수 없음: {collection_id}")
        
        return False
    
    def search_in_vector_db(self, query: str, limit: int = 10, threshold: Optional[float] = 0.5) -> List[Dict[str, Any]]:
        """
        벡터 DB에서 의미 기반 검색
        
        Args:
            query: 검색 쿼리
            limit: 최대 결과 수
            threshold: 유사도 임계값
        
        Returns:
            검색 결과 목록
        """
        if not self.use_vector_db or not self.vector_db:
            logger.warning("벡터 DB가 활성화되지 않음")
            return []
        
        try:
            # 벡터 DB에서 검색
            filter_metadata = {"source": "arxiv"}
            results = self.vector_db.search(
                query=query,
                k=limit,
                threshold=threshold,
                filter_metadata=filter_metadata
            )
            
            # 결과 변환
            formatted_results = []
            for doc, score in results:
                paper_id = doc.metadata.get("paper_id")
                
                # 변환된 결과 추가
                formatted_results.append({
                    "document_id": doc.id,
                    "paper_id": paper_id,
                    "title": doc.text.split("\n\n")[0] if "\n\n" in doc.text else doc.text.split("\n")[0],
                    "abstract": doc.text.split("\n\n")[1] if "\n\n" in doc.text else "",
                    "score": score,
                    "metadata": doc.metadata
                })
            
            return formatted_results
        
        except Exception as e:
            logger.error(f"벡터 DB 검색 중 오류 발생: {str(e)}")
            return []
    
    def get_recent_papers(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        최근에 저장된 논문 목록 가져오기
        
        Args:
            limit: 최대 결과 수
        
        Returns:
            논문 목록
        """
        papers = []
        
        try:
            # 모든 논문 파일 가져오기
            for filename in os.listdir(self.papers_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(self.papers_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        paper = json.load(f)
                    
                    papers.append(paper)
                    
                    # 충분한 결과를 얻으면 중단
                    if len(papers) >= limit:
                        break
            
            # 저장 날짜 기준 정렬
            papers.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
            
            return papers[:limit]
        
        except Exception as e:
            logger.error(f"최근 논문 목록 가져오기 실패: {str(e)}")
            return []