"""
인덱싱 관련 데이터베이스 작업 모듈

코드베이스 인덱싱 관련 CRUD 작업을 제공합니다.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any
from datetime import datetime

from ..models import (
    CodebaseIndexingSettings as DBCodebaseIndexingSettings,
    CodebaseIndexingRun as DBCodebaseIndexingRun,
    CodeEmbedding as DBCodeEmbedding,
    Codebase, CodebaseFile,
    IndexingStatusEnum, IndexingFrequencyEnum
)
from ...models.indexing import (
    CodebaseIndexingSettings, CodebaseIndexingRun, CodeEmbedding,
    IndexingStatus, IndexingFrequency
)


def get_indexing_settings(
    db: Session,
    codebase_id: int
) -> Optional[DBCodebaseIndexingSettings]:
    """
    코드베이스의 인덱싱 설정을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        
    Returns:
        인덱싱 설정 또는 None (없는 경우)
    """
    return db.query(DBCodebaseIndexingSettings)\
        .filter(DBCodebaseIndexingSettings.codebase_id == codebase_id)\
        .first()


def create_or_update_indexing_settings(
    db: Session,
    codebase_id: int,
    settings: Union[Dict[str, Any], CodebaseIndexingSettings]
) -> DBCodebaseIndexingSettings:
    """
    코드베이스의 인덱싱 설정을 생성하거나 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        settings: 설정 데이터
        
    Returns:
        생성 또는 업데이트된 인덱싱 설정
    """
    # 딕셔너리로 변환
    if not isinstance(settings, dict):
        settings_data = settings.dict(exclude_unset=True)
    else:
        settings_data = settings
    
    # 설정 데이터에 codebase_id 추가
    settings_data["codebase_id"] = codebase_id
    
    # 기존 설정 확인
    existing_settings = get_indexing_settings(db, codebase_id)
    
    if existing_settings:
        # frequency 처리
        if "frequency" in settings_data and not isinstance(settings_data["frequency"], IndexingFrequencyEnum):
            frequency = settings_data["frequency"]
            if isinstance(frequency, IndexingFrequency):
                settings_data["frequency"] = IndexingFrequencyEnum[frequency.value]
            else:
                settings_data["frequency"] = IndexingFrequencyEnum[frequency]
        
        # 기존 설정 업데이트
        for key, value in settings_data.items():
            if hasattr(existing_settings, key) and value is not None:
                setattr(existing_settings, key, value)
        
        # 수정 시간 갱신
        existing_settings.updated_at = datetime.utcnow()
        
        # 변경사항 저장
        db.commit()
        db.refresh(existing_settings)
        
        return existing_settings
    else:
        # frequency 처리
        if "frequency" in settings_data and not isinstance(settings_data["frequency"], IndexingFrequencyEnum):
            frequency = settings_data["frequency"]
            if isinstance(frequency, IndexingFrequency):
                settings_data["frequency"] = IndexingFrequencyEnum[frequency.value]
            else:
                settings_data["frequency"] = IndexingFrequencyEnum[frequency]
        
        # 새 설정 생성
        new_settings = DBCodebaseIndexingSettings(**settings_data)
        
        # 데이터베이스에 저장
        db.add(new_settings)
        db.commit()
        db.refresh(new_settings)
        
        return new_settings


def create_indexing_run(
    db: Session,
    codebase_id: int,
    is_full_index: bool = False,
    triggered_by: str = "manual"
) -> DBCodebaseIndexingRun:
    """
    새 인덱싱 실행을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        is_full_index: 전체 인덱싱 여부
        triggered_by: 트리거 소스
        
    Returns:
        생성된 인덱싱 실행 객체
    """
    # 설정 ID 조회
    settings = get_indexing_settings(db, codebase_id)
    settings_id = settings.id if settings else None
    
    # 인덱싱 실행 생성
    indexing_run = DBCodebaseIndexingRun(
        codebase_id=codebase_id,
        settings_id=settings_id,
        status=IndexingStatusEnum.pending,
        is_full_index=is_full_index,
        triggered_by=triggered_by
    )
    
    # 데이터베이스에 저장
    db.add(indexing_run)
    db.commit()
    db.refresh(indexing_run)
    
    return indexing_run


def update_indexing_run(
    db: Session,
    run_id: int,
    update_data: Dict[str, Any]
) -> Optional[DBCodebaseIndexingRun]:
    """
    인덱싱 실행 정보를 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        run_id: 인덱싱 실행 ID
        update_data: 업데이트할 데이터
        
    Returns:
        업데이트된 인덱싱 실행 객체 또는 None (없는 경우)
    """
    # 인덱싱 실행 조회
    indexing_run = db.query(DBCodebaseIndexingRun)\
        .filter(DBCodebaseIndexingRun.id == run_id)\
        .first()
    
    if not indexing_run:
        return None
    
    # status 처리
    if "status" in update_data and not isinstance(update_data["status"], IndexingStatusEnum):
        status = update_data["status"]
        if isinstance(status, IndexingStatus):
            update_data["status"] = IndexingStatusEnum[status.value]
        else:
            update_data["status"] = IndexingStatusEnum[status]
    
    # 업데이트할 필드 설정
    for key, value in update_data.items():
        if hasattr(indexing_run, key):
            setattr(indexing_run, key, value)
    
    # 변경사항 저장
    db.commit()
    db.refresh(indexing_run)
    
    return indexing_run


def get_indexing_runs(
    db: Session,
    codebase_id: int,
    status: Optional[Union[str, IndexingStatus]] = None,
    limit: int = 10
) -> List[DBCodebaseIndexingRun]:
    """
    코드베이스의 인덱싱 실행 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        status: 상태 필터
        limit: 최대 조회 개수
        
    Returns:
        인덱싱 실행 목록
    """
    query = db.query(DBCodebaseIndexingRun)\
        .filter(DBCodebaseIndexingRun.codebase_id == codebase_id)
    
    if status:
        # Enum 변환
        if isinstance(status, str):
            db_status = IndexingStatusEnum[status]
        elif isinstance(status, IndexingStatus):
            db_status = IndexingStatusEnum[status.value]
        else:
            db_status = status
            
        query = query.filter(DBCodebaseIndexingRun.status == db_status)
    
    # 최신 실행부터 조회
    return query.order_by(DBCodebaseIndexingRun.id.desc())\
        .limit(limit)\
        .all()


def get_latest_indexing_run(
    db: Session,
    codebase_id: int
) -> Optional[DBCodebaseIndexingRun]:
    """
    코드베이스의 최신 인덱싱 실행을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        
    Returns:
        최신 인덱싱 실행 또는 None (없는 경우)
    """
    return db.query(DBCodebaseIndexingRun)\
        .filter(DBCodebaseIndexingRun.codebase_id == codebase_id)\
        .order_by(DBCodebaseIndexingRun.id.desc())\
        .first()


def create_code_embedding(
    db: Session,
    codebase_id: int,
    file_id: int,
    chunk_id: str,
    content: str,
    embedding: Optional[List[float]] = None,
    embedding_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    run_id: Optional[int] = None
) -> DBCodeEmbedding:
    """
    새 코드 임베딩을 생성합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        file_id: 파일 ID
        chunk_id: 청크 ID
        content: 원본 코드 내용
        embedding: 임베딩 벡터
        embedding_key: 외부 벡터 DB에서의 키
        metadata: 추가 메타데이터
        run_id: 인덱싱 실행 ID
        
    Returns:
        생성된 코드 임베딩 객체
    """
    # 기본값 설정
    if metadata is None:
        metadata = {}
    
    # 코드 임베딩 생성
    code_embedding = DBCodeEmbedding(
        codebase_id=codebase_id,
        file_id=file_id,
        run_id=run_id,
        chunk_id=chunk_id,
        content=content,
        embedding=embedding,
        embedding_key=embedding_key,
        metadata=metadata
    )
    
    # 데이터베이스에 저장
    db.add(code_embedding)
    db.commit()
    db.refresh(code_embedding)
    
    return code_embedding


def update_code_embedding(
    db: Session,
    embedding_id: int,
    update_data: Dict[str, Any]
) -> Optional[DBCodeEmbedding]:
    """
    코드 임베딩을 업데이트합니다.
    
    Args:
        db: 데이터베이스 세션
        embedding_id: 임베딩 ID
        update_data: 업데이트할 데이터
        
    Returns:
        업데이트된 코드 임베딩 객체 또는 None (없는 경우)
    """
    # 코드 임베딩 조회
    code_embedding = db.query(DBCodeEmbedding)\
        .filter(DBCodeEmbedding.id == embedding_id)\
        .first()
    
    if not code_embedding:
        return None
    
    # 업데이트할 필드 설정
    for key, value in update_data.items():
        if hasattr(code_embedding, key):
            setattr(code_embedding, key, value)
    
    # 수정 시간 갱신
    code_embedding.updated_at = datetime.utcnow()
    
    # 변경사항 저장
    db.commit()
    db.refresh(code_embedding)
    
    return code_embedding


def get_file_embeddings(
    db: Session,
    file_id: int
) -> List[DBCodeEmbedding]:
    """
    파일의 모든 임베딩을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        file_id: 파일 ID
        
    Returns:
        코드 임베딩 목록
    """
    return db.query(DBCodeEmbedding)\
        .filter(DBCodeEmbedding.file_id == file_id)\
        .all()


def delete_file_embeddings(
    db: Session,
    file_id: int
) -> int:
    """
    파일의 모든 임베딩을 삭제합니다.
    
    Args:
        db: 데이터베이스 세션
        file_id: 파일 ID
        
    Returns:
        삭제된 임베딩 수
    """
    result = db.query(DBCodeEmbedding)\
        .filter(DBCodeEmbedding.file_id == file_id)\
        .delete()
    
    db.commit()
    return result


def get_codebase_embeddings_stats(
    db: Session,
    codebase_id: int
) -> Dict[str, Any]:
    """
    코드베이스의 임베딩 통계를 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        
    Returns:
        통계 정보
    """
    # 총 임베딩 수
    total_embeddings = db.query(DBCodeEmbedding)\
        .filter(DBCodeEmbedding.codebase_id == codebase_id)\
        .count()
    
    # 임베딩된 파일 수
    indexed_files = db.query(DBCodeEmbedding.file_id)\
        .filter(DBCodeEmbedding.codebase_id == codebase_id)\
        .distinct()\
        .count()
    
    # 최근 인덱싱 실행
    latest_run = get_latest_indexing_run(db, codebase_id)
    
    return {
        "total_embeddings": total_embeddings,
        "indexed_files": indexed_files,
        "last_indexed_at": latest_run.end_time if latest_run and latest_run.end_time else None,
        "last_index_status": latest_run.status.value if latest_run else None
    }


def get_codebase_files(
    db: Session, 
    codebase_id: int, 
    is_directory: Optional[bool] = None,
    path_pattern: Optional[str] = None
) -> List[CodebaseFile]:
    """
    코드베이스의 파일 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 코드베이스 ID
        is_directory: 디렉토리 여부 필터
        path_pattern: 경로 패턴 필터
        
    Returns:
        파일 목록
    """
    query = db.query(CodebaseFile)\
        .filter(CodebaseFile.codebase_id == codebase_id)
    
    if is_directory is not None:
        query = query.filter(CodebaseFile.is_directory == is_directory)
    
    if path_pattern:
        query = query.filter(CodebaseFile.path.like(f"%{path_pattern}%"))
    
    return query.all()


def get_codebases(
    db: Session, 
    codebase_id: Optional[int] = None,
    single: bool = False
) -> Union[List[Codebase], Optional[Codebase]]:
    """
    코드베이스 목록을 조회합니다.
    
    Args:
        db: 데이터베이스 세션
        codebase_id: 조회할 코드베이스 ID
        single: 단일 결과 반환 여부
        
    Returns:
        코드베이스 목록 또는 단일 코드베이스
    """
    query = db.query(Codebase)
    
    if codebase_id:
        query = query.filter(Codebase.id == codebase_id)
        if single:
            return query.first()
    
    return query.all()