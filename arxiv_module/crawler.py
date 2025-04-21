"""
arXiv Crawler Module - CS/AI 논문 크롤링 기능

arXiv API를 사용해 CS/AI 카테고리의 논문을 검색하고 다운로드하는 기능 제공
"""

import os
import time
import arxiv
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional, Union

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CS/AI 관련 arXiv 카테고리
CS_CATEGORIES = [
    'cs.AI',    # 인공지능
    'cs.CL',    # 컴퓨터 언어학
    'cs.CV',    # 컴퓨터 비전
    'cs.LG',    # 기계학습
    'cs.NE',    # 신경 및 진화적 컴퓨팅
    'cs.RO',    # 로보틱스
    'cs.IR',    # 정보 검색
    'cs.HC',    # 인간-컴퓨터 상호작용
]

class ArxivCrawler:
    """arXiv 논문 크롤링 클래스"""
    
    def __init__(self, download_dir: str = 'papers'):
        """
        ArxivCrawler 초기화
        
        Args:
            download_dir (str): PDF 다운로드 디렉토리 경로
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.client = arxiv.Client()
        
    def search(self, 
               query: str = "",
               categories: List[str] = None,
               date_from: Optional[datetime] = None, 
               date_to: Optional[datetime] = None,
               max_results: int = 50) -> List[Dict[str, Any]]:
        """
        arXiv에서 논문 검색
        
        Args:
            query (str): 검색 쿼리
            categories (List[str]): 검색할 카테고리 목록
            date_from (datetime): 시작 날짜
            date_to (datetime): 종료 날짜
            max_results (int): 최대 검색 결과 수
            
        Returns:
            List[Dict[str, Any]]: 검색 결과 논문 메타데이터 목록
        """
        logger.info(f"Searching arXiv with query: {query}, categories: {categories}")
        
        # 카테고리 필터링
        if not categories:
            categories = CS_CATEGORIES
            
        category_filter = " OR ".join([f"cat:{cat}" for cat in categories])
        
        # 날짜 필터링
        date_filter = ""
        if date_from or date_to:
            if date_from:
                date_filter += f" AND submittedDate:[{date_from.strftime('%Y%m%d')}000000 TO "
            else:
                date_filter += f" AND submittedDate:[00000000000000 TO "
                
            if date_to:
                date_filter += f"{date_to.strftime('%Y%m%d')}235959]"
            else:
                date_filter += f"{datetime.now().strftime('%Y%m%d')}235959]"
        
        # 최종 검색 쿼리 구성
        search_query = query
        if category_filter:
            search_query = f"({search_query}) AND ({category_filter})" if search_query else category_filter
        if date_filter:
            search_query += date_filter
            
        logger.info(f"Final search query: {search_query}")
        
        # arXiv API 검색
        search = arxiv.Search(
            query=search_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        # 검색 요청 및 결과 처리
        try:
            results = list(self.client.results(search))
            papers = []
            
            for paper in results:
                paper_data = {
                    'id': paper.entry_id,
                    'title': paper.title,
                    'authors': [author.name for author in paper.authors],
                    'summary': paper.summary,
                    'published': paper.published,
                    'updated': paper.updated,
                    'categories': paper.categories,
                    'pdf_url': paper.pdf_url,
                    'entry_id': paper.entry_id.split('/')[-1]  # arXiv ID 추출
                }
                papers.append(paper_data)
                
            logger.info(f"Found {len(papers)} papers")
            return papers
            
        except Exception as e:
            logger.error(f"Error during arXiv search: {e}")
            return []
        
    def download_paper(self, paper_id: str, filename: Optional[str] = None) -> Optional[str]:
        """
        논문 ID로 PDF 다운로드
        
        Args:
            paper_id (str): 논문 ID (arXiv ID)
            filename (str, optional): 저장할 파일명
            
        Returns:
            str: 다운로드된 PDF 파일 경로 또는 None (실패시)
        """
        try:
            # ID에서 arXiv 식별자 추출
            if '/' in paper_id:
                paper_id = paper_id.split('/')[-1]
                
            search = arxiv.Search(id_list=[paper_id])
            paper = next(self.client.results(search))
            
            if not filename:
                # 파일명 생성 (slugify 활용)
                filename = f"{paper_id}_{paper.title.replace(' ', '_')[:50]}.pdf"
                filename = "".join(c if c.isalnum() or c in "._- " else "_" for c in filename)
            
            file_path = os.path.join(self.download_dir, filename)
            
            # 이미 다운로드된 파일인지 확인
            if os.path.exists(file_path):
                logger.info(f"Paper already downloaded: {file_path}")
                return file_path
            
            # PDF 다운로드
            logger.info(f"Downloading paper: {paper.title} to {file_path}")
            paper.download_pdf(filename=file_path)
            
            # API 제한을 위한 대기
            time.sleep(3)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error downloading paper {paper_id}: {e}")
            return None
            
    def download_papers(self, paper_ids: List[str]) -> Dict[str, Union[str, None]]:
        """
        여러 논문 ID로 PDF 다운로드
        
        Args:
            paper_ids (List[str]): 논문 ID 목록
            
        Returns:
            Dict[str, Union[str, None]]: 논문 ID를 키로, 파일 경로를 값으로 하는 사전
        """
        results = {}
        for paper_id in paper_ids:
            file_path = self.download_paper(paper_id)
            results[paper_id] = file_path
            
        return results

# 사용 예시
if __name__ == "__main__":
    crawler = ArxivCrawler(download_dir="papers")
    
    # 최근 7일간의 AI 논문 검색
    date_from = datetime.now() - timedelta(days=7)
    papers = crawler.search(
        query="transformer",
        categories=["cs.AI", "cs.LG"],
        date_from=date_from,
        max_results=5
    )
    
    for i, paper in enumerate(papers):
        print(f"{i+1}. {paper['title']} by {', '.join(paper['authors'])}")
    
    # 첫 번째 논문 다운로드
    if papers:
        file_path = crawler.download_paper(papers[0]['entry_id'])
        print(f"Downloaded to {file_path}")
