"""
프로젝트 관련 데이터베이스 작업 모듈

이 모듈은 프로젝트 관련 데이터베이스 쿼리 및 작업을 제공합니다.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from ..models import Project
from ..connection import get_db_context

# 로거 설정
logger = logging.getLogger(__name__)

def get_project(project_id: int) -> Optional[Project]:
    """
    프로젝트 조회
    
    Args:
        project_id: 프로젝트 ID
        
    Returns:
        프로젝트 객체 또는 None
    """
    try:
        with get_db_context() as db:
            return db.query(Project).filter(Project.id == project_id).first()
    except Exception as e:
        logger.error(f"프로젝트 조회 중 오류 발생: {str(e)}")
        return None


def list_projects(
    filters: Dict[str, Any] = None,
    offset: int = 0,
    limit: int = 10
) -> Tuple[List[Project], int]:
    """
    프로젝트 목록 조회
    
    Args:
        filters: 필터 조건
        offset: 페이지 오프셋
        limit: 페이지 크기
        
    Returns:
        프로젝트 목록과 총 프로젝트 수 튜플
    """
    filters = filters or {}
    
    try:
        with get_db_context() as db:
            # 기본 쿼리
            query = db.query(Project)
            
            # 필터 적용
            if 'name' in filters:
                query = query.filter(Project.name.ilike(f"%{filters['name']}%"))
            
            if 'is_active' in filters:
                query = query.filter(Project.is_active == filters['is_active'])
            
            # 총 개수 계산
            total = query.count()
            
            # 페이지네이션 적용
            projects = query.offset(offset).limit(limit).all()
            
            return projects, total
    except Exception as e:
        logger.error(f"프로젝트 목록 조회 중 오류 발생: {str(e)}")
        return [], 0


def create_project(project_data: Dict[str, Any]) -> Optional[Project]:
    """
    프로젝트 생성
    
    Args:
        project_data: 프로젝트 데이터
        
    Returns:
        생성된 프로젝트 객체 또는 None
    """
    try:
        with get_db_context() as db:
            # 프로젝트 객체 생성
            project = Project(**project_data)
            
            # 데이터베이스에 추가
            db.add(project)
            db.commit()
            db.refresh(project)
            
            return project
    except Exception as e:
        logger.error(f"프로젝트 생성 중 오류 발생: {str(e)}")
        return None


def update_project(project_id: int, update_data: Dict[str, Any]) -> Optional[Project]:
    """
    프로젝트 업데이트
    
    Args:
        project_id: 프로젝트 ID
        update_data: 업데이트할 데이터
        
    Returns:
        업데이트된 프로젝트 객체 또는 None
    """
    try:
        with get_db_context() as db:
            # 프로젝트 조회
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return None
            
            # 필드 업데이트
            for key, value in update_data.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            # 변경사항 저장
            db.commit()
            db.refresh(project)
            
            return project
    except Exception as e:
        logger.error(f"프로젝트 업데이트 중 오류 발생: {str(e)}")
        return None


def delete_project(project_id: int) -> bool:
    """
    프로젝트 삭제
    
    Args:
        project_id: 프로젝트 ID
        
    Returns:
        성공 여부
    """
    try:
        with get_db_context() as db:
            # 프로젝트 조회
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return False
            
            # 프로젝트 삭제
            db.delete(project)
            db.commit()
            
            return True
    except Exception as e:
        logger.error(f"프로젝트 삭제 중 오류 발생: {str(e)}")
        return False


def get_project_by_name(name: str) -> Optional[Project]:
    """
    이름으로 프로젝트 조회
    
    Args:
        name: 프로젝트 이름
        
    Returns:
        프로젝트 객체 또는 None
    """
    try:
        with get_db_context() as db:
            return db.query(Project).filter(Project.name == name).first()
    except Exception as e:
        logger.error(f"이름으로 프로젝트 조회 중 오류 발생: {str(e)}")
        return None
