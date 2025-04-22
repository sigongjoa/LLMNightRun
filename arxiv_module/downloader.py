"""
Arxiv 논문 다운로드 모듈

Arxiv에서 논문 PDF를 다운로드하는 기능을 제공합니다.
"""

import os
import urllib.request
import urllib.error
import time
import random
from typing import List, Dict, Any, Optional, Tuple

from core.logging import get_logger
from core.events import publish

logger = get_logger("arxiv_module.downloader")

def download_paper(
    paper_info: Dict[str, Any],
    output_dir: str,
    timeout: int = 30,
    overwrite: bool = False
) -> Optional[str]:
    """
    논문 PDF 다운로드
    
    Args:
        paper_info: 논문 정보 딕셔너리
        output_dir: 출력 디렉토리
        timeout: 다운로드 타임아웃(초)
        overwrite: 기존 파일 덮어쓰기 여부
    
    Returns:
        다운로드된 파일 경로 또는 None (실패 시)
    """
    # 출력 디렉토리 확인
    os.makedirs(output_dir, exist_ok=True)
    
    # 논문 ID 및 PDF 링크 확인
    paper_id = paper_info.get('id')
    pdf_link = paper_info.get('pdf_link')
    
    if not paper_id or not pdf_link:
        logger.error("논문 ID 또는 PDF 링크 없음")
        return None
    
    # 파일명 생성
    file_name = f"arxiv_{paper_id.replace('/', '_')}.pdf"
    file_path = os.path.join(output_dir, file_name)
    
    # 파일이 이미 있는지 확인
    if os.path.exists(file_path) and not overwrite:
        logger.info(f"파일이 이미 존재함: {file_path}")
        return file_path
    
    # 다운로드 시도
    try:
        logger.info(f"논문 다운로드 중: {paper_id} -> {file_path}")
        
        # 이벤트 발행
        publish("arxiv.download.start", paper_id=paper_id, file_path=file_path)
        
        # PDF 다운로드
        urllib.request.urlretrieve(pdf_link, file_path)
        
        # 성공 이벤트 발행
        publish("arxiv.download.complete", paper_id=paper_id, file_path=file_path)
        
        logger.info(f"다운로드 완료: {file_path}")
        return file_path
    
    except urllib.error.URLError as e:
        logger.error(f"다운로드 중 URL 오류 발생: {str(e)}")
        
        # 실패 이벤트 발행
        publish("arxiv.download.error", paper_id=paper_id, error=str(e))
        
        return None
    
    except Exception as e:
        logger.error(f"다운로드 중 오류 발생: {str(e)}")
        
        # 실패 이벤트 발행
        publish("arxiv.download.error", paper_id=paper_id, error=str(e))
        
        return None

def download_multiple_papers(
    papers: List[Dict[str, Any]],
    output_dir: str,
    delay_range: Tuple[float, float] = (1.0, 3.0),
    timeout: int = 30,
    max_retries: int = 3,
    overwrite: bool = False
) -> List[Tuple[Dict[str, Any], Optional[str]]]:
    """
    여러 논문 PDF 다운로드
    
    Args:
        papers: 논문 정보 리스트
        output_dir: 출력 디렉토리
        delay_range: 다운로드 간 지연 시간 범위(초)
        timeout: 다운로드 타임아웃(초)
        max_retries: 최대 재시도 횟수
        overwrite: 기존 파일 덮어쓰기 여부
    
    Returns:
        (논문 정보, 다운로드 경로) 튜플 리스트
    """
    # 출력 디렉토리 확인
    os.makedirs(output_dir, exist_ok=True)
    
    # 결과 저장 리스트
    results = []
    
    # 총 다운로드 수 추적
    total_papers = len(papers)
    successful_downloads = 0
    
    # 이벤트 발행
    publish("arxiv.batch_download.start", total_papers=total_papers)
    
    for i, paper in enumerate(papers):
        retry_count = 0
        download_path = None
        
        # 최대 재시도 횟수만큼 시도
        while retry_count < max_retries and download_path is None:
            if retry_count > 0:
                # 재시도 시 더 긴 지연
                retry_delay = random.uniform(delay_range[1], delay_range[1] * 2)
                logger.info(f"다운로드 재시도 {retry_count}/{max_retries}, {retry_delay:.1f}초 대기 중...")
                time.sleep(retry_delay)
            
            # 다운로드 시도
            download_path = download_paper(
                paper, output_dir, timeout=timeout, overwrite=overwrite
            )
            
            retry_count += 1
        
        # 결과 추가
        results.append((paper, download_path))
        
        # 성공 여부 추적
        if download_path:
            successful_downloads += 1
        
        # 진행 상황 이벤트 발행
        publish("arxiv.batch_download.progress", 
               current=i+1, total=total_papers, successful=successful_downloads)
        
        # 마지막 논문이 아닌 경우 지연
        if i < total_papers - 1:
            delay = random.uniform(delay_range[0], delay_range[1])
            time.sleep(delay)
    
    # 완료 이벤트 발행
    publish("arxiv.batch_download.complete", 
           total=total_papers, successful=successful_downloads)
    
    logger.info(f"다운로드 완료: {successful_downloads}/{total_papers} 성공")
    return results

def get_download_progress(file_path: str, total_size: Optional[int] = None) -> Tuple[int, Optional[int]]:
    """
    다운로드 진행 상황 가져오기
    
    Args:
        file_path: 다운로드 중인 파일 경로
        total_size: 총 파일 크기 (바이트)
    
    Returns:
        (현재 크기, 총 크기) 튜플
    """
    if not os.path.exists(file_path):
        return 0, total_size
    
    current_size = os.path.getsize(file_path)
    return current_size, total_size

class DownloadProgressTracker:
    """다운로드 진행 상황 추적기"""
    
    def __init__(self, total_papers: int):
        """
        진행 상황 추적기 초기화
        
        Args:
            total_papers: 총 논문 수
        """
        self.total_papers = total_papers
        self.completed_papers = 0
        self.failed_papers = 0
        self.in_progress_papers = 0
        self.current_paper_id = None
        self.current_paper_progress = 0
    
    def update(self, completed: int, failed: int, in_progress: int = 0, 
              current_id: Optional[str] = None, current_progress: float = 0):
        """
        진행 상황 업데이트
        
        Args:
            completed: 완료된 논문 수
            failed: 실패한 논문 수
            in_progress: 진행 중인 논문 수
            current_id: 현재 다운로드 중인 논문 ID
            current_progress: 현재 논문 다운로드 진행률 (0-1)
        """
        self.completed_papers = completed
        self.failed_papers = failed
        self.in_progress_papers = in_progress
        self.current_paper_id = current_id
        self.current_paper_progress = current_progress
    
    def get_overall_progress(self) -> float:
        """
        전체 진행률 계산
        
        Returns:
            전체 진행률 (0-1)
        """
        if self.total_papers == 0:
            return 0
        
        # 완료된 논문 + 현재 진행 중인 논문의 부분 진행
        completed_progress = self.completed_papers
        if self.current_paper_id and self.in_progress_papers > 0:
            completed_progress += self.current_paper_progress
        
        return completed_progress / self.total_papers
    
    def get_status_text(self) -> str:
        """
        상태 텍스트 가져오기
        
        Returns:
            현재 상태 텍스트
        """
        progress_percent = self.get_overall_progress() * 100
        
        if self.current_paper_id:
            current_paper_percent = self.current_paper_progress * 100
            return (f"다운로드 중: {self.completed_papers}/{self.total_papers} 완료 "
                   f"({progress_percent:.1f}%) - 현재: {self.current_paper_id} "
                   f"({current_paper_percent:.1f}%)")
        else:
            return f"다운로드 중: {self.completed_papers}/{self.total_papers} 완료 ({progress_percent:.1f}%)"
