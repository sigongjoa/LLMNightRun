"""
프로젝트 관련 데이터베이스 작업 모듈
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models import Project


def get_project(db: Session, project_id: int) -> Optional[Project]:
    """
    단일 프로젝트를 가져옵니다.
    
    Args:
        db: 데이터베이스 세션
        project_id: 프로젝트 ID
        
    Returns:
        프로젝트 또는 None
    """
    return db.query(Project).filter(Project.id == project_id).first()


def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
    """
    프로젝트 목록을 가져옵니다.
    
    Args:
        db: 데이터베이스 세션
        skip: 건너뛸 결과 수
        limit: 최대 결과 수
        
    Returns:
        프로젝트 목록
    """
    return db.query(Project).offset(skip).limit(limit).all()


def create_project(db: Session, name: str, description: Optional[str] = None, tags: Optional[List[str]] = None) -> Project:
    """
    새 프로젝트를 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        name: 프로젝트 이름
        description: 프로젝트 설명 (선택 사항)
        tags: 태그 목록 (선택 사항)
        
    Returns:
        생성된 프로젝트
    """
    tags = tags or []
    
    project = Project(
        name=name,
        description=description,
        tags=tags,
        is_active=True,
        project_data={}
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project


def update_project(db: Session, project_id: int, project_data: Dict[str, Any]) -> Optional[Project]:
    """
    프로젝트를 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        project_id: 프로젝트 ID
        project_data: 업데이트할 프로젝트 데이터
        
    Returns:
        업데이트된 프로젝트 또는 None
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        return None
    
    for key, value in project_data.items():
        if hasattr(project, key) and value is not None:
            setattr(project, key, value)
    
    db.commit()
    db.refresh(project)
    
    return project


def delete_project(db: Session, project_id: int) -> bool:
    """
    프로젝트를 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        project_id: 프로젝트 ID
        
    Returns:
        삭제 성공 여부
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        return False
    
    db.delete(project)
    db.commit()
    
    return True
