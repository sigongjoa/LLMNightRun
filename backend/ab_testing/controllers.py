"""
A/B 테스트 컨트롤러

API 라우트에서 호출되는 비즈니스 로직을 구현합니다.
"""

import asyncio
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fastapi import HTTPException

from backend.logger import get_logger
from . import models, schemas
from .config import ab_testing_settings
from .services.experiment import ExperimentRunner
from .services.evaluator import Evaluator
from .services.model_wrapper import get_model_wrapper
from .services.reporter import Reporter


# 로거 설정
logger = get_logger(__name__)


# 실험 세트 관리 함수
async def create_experiment_set(db: Session, experiment_set: schemas.ExperimentSetCreate) -> models.ExperimentSet:
    """새 실험 세트를 생성합니다."""
    try:
        # 실험 세트 생성
        db_experiment_set = models.ExperimentSet(
            name=experiment_set.name,
            description=experiment_set.description,
            config=experiment_set.config,
            is_active=True
        )
        db.add(db_experiment_set)
        db.flush()  # ID 할당을 위해 flush
        
        # 실험 추가
        for experiment in experiment_set.experiments:
            db_experiment = models.Experiment(
                experiment_set_id=db_experiment_set.id,
                name=experiment.name,
                prompt=experiment.prompt,
                model=experiment.model,
                params=experiment.params,
                weight=experiment.weight,
                is_control=experiment.is_control
            )
            db.add(db_experiment)
        
        # 변경사항 저장
        db.commit()
        db.refresh(db_experiment_set)
        return db_experiment_set
        
    except Exception as e:
        db.rollback()
        logger.error(f"실험 세트 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"실험 세트 생성 중 오류가 발생했습니다: {str(e)}")


async def get_experiment_sets(
    db: Session, skip: int = 0, limit: int = 100, active_only: bool = True
) -> List[models.ExperimentSet]:
    """실험 세트 목록을 조회합니다."""
    query = db.query(models.ExperimentSet)
    
    if active_only:
        query = query.filter(models.ExperimentSet.is_active == True)
        
    return query.order_by(desc(models.ExperimentSet.created_at)).offset(skip).limit(limit).all()


async def get_experiment_set(db: Session, experiment_set_id: int) -> Optional[models.ExperimentSet]:
    """실험 세트를 ID로 조회합니다."""
    return db.query(models.ExperimentSet).filter(models.ExperimentSet.id == experiment_set_id).first()


async def update_experiment_set(
    db: Session, experiment_set_id: int, experiment_set: schemas.ExperimentSetBase
) -> Optional[models.ExperimentSet]:
    """실험 세트를 업데이트합니다."""
    db_experiment_set = await get_experiment_set(db, experiment_set_id)
    if not db_experiment_set:
        return None
    
    # 업데이트할 필드 설정
    if experiment_set.name is not None:
        db_experiment_set.name = experiment_set.name
    if experiment_set.description is not None:
        db_experiment_set.description = experiment_set.description
    if experiment_set.config is not None:
        db_experiment_set.config = experiment_set.config
    
    db_experiment_set.updated_at = datetime.utcnow()
    
    # 변경사항 저장
    db.commit()
    db.refresh(db_experiment_set)
    return db_experiment_set


async def delete_experiment_set(db: Session, experiment_set_id: int) -> Dict[str, Any]:
    """실험 세트를 삭제합니다 (소프트 삭제)."""
    db_experiment_set = await get_experiment_set(db, experiment_set_id)
    if not db_experiment_set:
        return {"success": False, "message": f"ID {experiment_set_id}에 해당하는 실험 세트를 찾을 수 없습니다"}
    
    # 소프트 삭제 (is_active = False)
    db_experiment_set.is_active = False
    db_experiment_set.updated_at = datetime.utcnow()
    
    # 변경사항 저장
    db.commit()
    return {"success": True, "message": f"실험 세트 '{db_experiment_set.name}'이(가) 삭제되었습니다"}


# 실험 관리 함수
from .controllers_experiment import (
    add_experiment, 
    get_experiment, 
    update_experiment, 
    delete_experiment
)

# 실험 실행 함수
from .controllers_execution import (
    run_experiment_set_background,
    get_experiment_set_status,
    get_experiment_set_results
)

# 평가 함수
from .controllers_evaluation import (
    evaluate_experiment_set_background,
    get_experiment_set_evaluations
)

# 보고서 및 내보내기 함수
from .controllers_report import (
    generate_report_background,
    get_report_path,
    export_experiment_set_background,
    get_export_path
)
