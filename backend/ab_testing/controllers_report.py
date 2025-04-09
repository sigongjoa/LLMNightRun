"""
A/B 테스트 보고서 컨트롤러

보고서 생성 및 내보내기 관련 비즈니스 로직을 구현합니다.
"""

import os
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.logger import get_logger
from backend.database.connection import Session as DBSession
from . import models
from .config import ab_testing_settings
from .services.reporter import Reporter

# 로거 설정
logger = get_logger(__name__)


async def generate_report_background(
    db: Session, 
    experiment_set_id: int, 
    format: str,
    run_id: Optional[str],
    task_id: str
):
    """백그라운드에서 실험 세트 보고서를 생성합니다."""
    logger.info(f"실험 세트 보고서 생성 시작: id={experiment_set_id}, format={format}, run_id={run_id}, task_id={task_id}")
    
    try:
        # 세션 복제 (백그라운드 작업용)
        db_copy = DBSession(bind=db.get_bind())
        
        # 리포터 생성
        reporter = Reporter(db_copy)
        
        # 보고서 생성
        report_path = await reporter.generate_report(
            experiment_set_id,
            format=format,
            run_id=run_id,
            report_id=task_id
        )
        
        logger.info(f"실험 세트 보고서 생성 완료: id={experiment_set_id}, format={format}, path={report_path}, task_id={task_id}")
        
    except Exception as e:
        logger.error(f"실험 세트 보고서 생성 실패: id={experiment_set_id}, format={format}, task_id={task_id}, error={str(e)}")
    finally:
        if 'db_copy' in locals():
            db_copy.close()


async def get_report_path(report_id: str) -> Optional[str]:
    """보고서 파일 경로를 반환합니다."""
    # 보고서 디렉토리 확인
    reports_dir = ab_testing_settings.reports_dir
    os.makedirs(reports_dir, exist_ok=True)
    
    # 가능한 확장자 검색
    for ext in ["html", "pdf", "json"]:
        path = os.path.join(reports_dir, f"{report_id}.{ext}")
        if os.path.isfile(path):
            return path
    
    return None


async def export_experiment_set_background(
    db: Session,
    experiment_set_id: int,
    format: str,
    run_id: Optional[str],
    include_results: bool,
    include_evaluations: bool,
    task_id: str
):
    """백그라운드에서 실험 세트를 내보냅니다."""
    logger.info(f"실험 세트 내보내기 시작: id={experiment_set_id}, format={format}, run_id={run_id}, task_id={task_id}")
    
    try:
        # 세션 복제 (백그라운드 작업용)
        db_copy = DBSession(bind=db.get_bind())
        
        # 리포터 생성
        reporter = Reporter(db_copy)
        
        # 내보내기 실행
        export_path = await reporter.export_data(
            experiment_set_id,
            format=format,
            run_id=run_id,
            include_results=include_results,
            include_evaluations=include_evaluations,
            export_id=task_id
        )
        
        logger.info(f"실험 세트 내보내기 완료: id={experiment_set_id}, format={format}, path={export_path}, task_id={task_id}")
        
    except Exception as e:
        logger.error(f"실험 세트 내보내기 실패: id={experiment_set_id}, format={format}, task_id={task_id}, error={str(e)}")
    finally:
        if 'db_copy' in locals():
            db_copy.close()


async def get_export_path(export_id: str) -> Optional[str]:
    """내보내기 파일 경로를 반환합니다."""
    # 내보내기 디렉토리 확인
    exports_dir = ab_testing_settings.exports_dir
    os.makedirs(exports_dir, exist_ok=True)
    
    # 가능한 확장자 검색
    for ext in ["json", "csv", "xlsx", "html"]:
        path = os.path.join(exports_dir, f"{export_id}.{ext}")
        if os.path.isfile(path):
            return path
    
    return None
