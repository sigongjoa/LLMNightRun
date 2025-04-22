"""
Arxiv 논문 검색 모듈

Arxiv API를 통해 논문을 검색하고 메타데이터를 가져오는 기능을 제공합니다.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import time
from typing import List, Dict, Any, Optional, Tuple

from core.logging import get_logger

logger = get_logger("arxiv_module.search")

# Arxiv API 기본 URL
ARXIV_API_URL = "http://export.arxiv.org/api/query"

def search_papers(
    query: str,
    max_results: int = 10,
    start: int = 0,
    sort_by: str = "relevance",
    sort_order: str = "descending",
    categories: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Arxiv에서 논문 검색
    
    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수
        start: 시작 인덱스
        sort_by: 정렬 기준 ('relevance', 'lastUpdatedDate', 'submittedDate')
        sort_order: 정렬 순서 ('ascending', 'descending')
        categories: 검색할 카테고리 목록 (예: ['cs.AI', 'cs.LG'])
    
    Returns:
        검색 결과 논문 목록 (딕셔너리 리스트)
    """
    # 검색 쿼리 구성
    search_query = query
    
    # 카테고리 필터 추가
    if categories:
        cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
        if query:
            search_query = f"({search_query}) AND ({cat_query})"
        else:
            search_query = cat_query
    
    # 쿼리 파라미터 구성
    params = {
        'search_query': search_query,
        'start': start,
        'max_results': max_results,
        'sortBy': sort_by,
        'sortOrder': sort_order
    }
    
    # URL 인코딩
    url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"
    
    try:
        logger.info(f"Arxiv API 요청: {url}")
        
        # API 요청
        with urllib.request.urlopen(url) as response:
            response_text = response.read().decode('utf-8')
        
        # XML 응답 파싱
        return _parse_arxiv_response(response_text)
    
    except Exception as e:
        logger.error(f"Arxiv 검색 중 오류 발생: {str(e)}")
        return []

def get_paper_details(paper_id: str) -> Optional[Dict[str, Any]]:
    """
    논문 ID로 상세 정보 가져오기
    
    Args:
        paper_id: 논문 ID (예: '2103.13630' 또는 전체 URL)
    
    Returns:
        논문 상세 정보 (딕셔너리) 또는 None (오류 시)
    """
    # ID 형식 처리
    if '/' in paper_id:
        # URL에서 ID 추출
        paper_id = paper_id.split('/')[-1]
        
        # 버전 정보 제거 (있는 경우)
        if 'v' in paper_id:
            paper_id = paper_id.split('v')[0]
    
    # 쿼리 URL
    url = f"{ARXIV_API_URL}?id_list={paper_id}"
    
    try:
        logger.info(f"Arxiv API 요청: {url}")
        
        # API 요청
        with urllib.request.urlopen(url) as response:
            response_text = response.read().decode('utf-8')
        
        # XML 응답 파싱
        results = _parse_arxiv_response(response_text)
        
        # 결과 반환
        if results:
            return results[0]
        else:
            logger.warning(f"논문을 찾을 수 없음: {paper_id}")
            return None
    
    except Exception as e:
        logger.error(f"논문 상세 정보 가져오는 중 오류 발생: {str(e)}")
        return None

def _parse_arxiv_response(response_text: str) -> List[Dict[str, Any]]:
    """
    Arxiv API 응답 XML 파싱
    
    Args:
        response_text: API 응답 텍스트 (XML)
    
    Returns:
        파싱된 논문 목록
    """
    # XML 네임스페이스
    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    
    # XML 파싱
    root = ET.fromstring(response_text)
    
    # 결과 저장 리스트
    results = []
    
    # 각 논문 엔트리 처리
    for entry in root.findall('.//atom:entry', namespaces):
        # 기본 정보 추출
        try:
            paper_id = entry.find('.//atom:id', namespaces).text.split('/abs/')[-1]
            title = entry.find('.//atom:title', namespaces).text.strip()
            abstract = entry.find('.//atom:summary', namespaces).text.strip()
            published = entry.find('.//atom:published', namespaces).text
            updated = entry.find('.//atom:updated', namespaces).text
            
            # 저자 정보 추출
            authors = []
            for author in entry.findall('.//atom:author', namespaces):
                name = author.find('.//atom:name', namespaces).text
                authors.append(name)
            
            # 카테고리 추출
            categories = []
            for category in entry.findall('.//atom:category', namespaces):
                term = category.get('term')
                if term:
                    categories.append(term)
            
            # PDF 링크 추출
            pdf_link = None
            for link in entry.findall('.//atom:link', namespaces):
                if link.get('title') == 'pdf':
                    pdf_link = link.get('href')
                    break
            
            # 논문 정보 딕셔너리 생성
            paper_info = {
                'id': paper_id,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'categories': categories,
                'published': published,
                'updated': updated,
                'pdf_link': pdf_link,
                'arxiv_url': f"https://arxiv.org/abs/{paper_id}"
            }
            
            results.append(paper_info)
        
        except Exception as e:
            logger.warning(f"논문 엔트리 파싱 중 오류 발생: {str(e)}")
            continue
    
    return results

def get_category_taxonomy() -> Dict[str, List[Dict[str, str]]]:
    """
    Arxiv 카테고리 분류체계 가져오기
    
    Returns:
        카테고리 분류체계 딕셔너리
    """
    # 카테고리 분류체계 (하드코딩)
    # 실제 구현에서는 Arxiv 웹사이트에서 가져오거나 주기적으로 업데이트할 수 있음
    taxonomy = {
        "Computer Science": [
            {"code": "cs.AI", "name": "Artificial Intelligence"},
            {"code": "cs.CL", "name": "Computation and Language"},
            {"code": "cs.CV", "name": "Computer Vision and Pattern Recognition"},
            {"code": "cs.LG", "name": "Machine Learning"},
            {"code": "cs.NE", "name": "Neural and Evolutionary Computing"},
            # 더 많은 CS 카테고리...
        ],
        "Mathematics": [
            {"code": "math.ST", "name": "Statistics Theory"},
            {"code": "math.PR", "name": "Probability"},
            # 더 많은 수학 카테고리...
        ],
        "Physics": [
            {"code": "physics.comp-ph", "name": "Computational Physics"},
            # 더 많은 물리학 카테고리...
        ],
        # 더 많은 분야...
    }
    
    return taxonomy

def search_with_rate_limit(
    queries: List[str],
    max_results_per_query: int = 10,
    delay_seconds: float = 3.0
) -> Dict[str, List[Dict[str, Any]]]:
    """
    여러 쿼리에 대해 속도 제한을 고려하여 검색
    
    Args:
        queries: 검색 쿼리 목록
        max_results_per_query: 쿼리당 최대 결과 수
        delay_seconds: 쿼리 간 지연 시간(초)
    
    Returns:
        쿼리별 검색 결과 딕셔너리
    """
    results = {}
    
    for query in queries:
        # 검색 실행
        query_results = search_papers(query, max_results=max_results_per_query)
        results[query] = query_results
        
        # 속도 제한을 위한 지연
        if query != queries[-1]:  # 마지막 쿼리가 아니면 지연
            time.sleep(delay_seconds)
    
    return results
