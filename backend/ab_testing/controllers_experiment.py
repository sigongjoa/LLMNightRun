"""
A/B 테스트 실험 관리 컨트롤러

실험 관리 관련 비즈니스 로직을 구현합니다.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.logger import get_logger
from . import models, schemas

# 로거 설정
logger = get_logger(__name__)


async def create_experiment_set(
    db: Session, experiment_set: schemas.ExperimentSetCreate
) -> models.ExperimentSet:
    """새 실험 세트를 생성합니다."""
    # 실험 세트 생성
    db_experiment_set = models.ExperimentSet(
        name=experiment_set.name,
        description=experiment_set.description,
        config=experiment_set.config,
        is_active=True
    )
    
    # 변경사항 저장 (실험 세트만)
    db.add(db_experiment_set)
    db.commit()
    db.refresh(db_experiment_set)
    
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
    
    # 변경사항 저장 (실험 포함)
    db.commit()
    db.refresh(db_experiment_set)
    return db_experiment_set


async def get_experiment_sets(
    db: Session, skip: int = 0, limit: int = 100, active_only: bool = False
) -> List[models.ExperimentSet]:
    """모든 실험 세트를 조회합니다."""
    query = db.query(models.ExperimentSet)
    
    if active_only:
        query = query.filter(models.ExperimentSet.is_active == True)
    
    return query.offset(skip).limit(limit).all()


async def get_experiment_set(
    db: Session, experiment_set_id: int
) -> Optional[models.ExperimentSet]:
    """실험 세트를 ID로 조회합니다."""
    return db.query(models.ExperimentSet).filter(
        models.ExperimentSet.id == experiment_set_id
    ).first()


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
    
    db_experiment_set.updated_at = models.datetime.utcnow()
    
    # 변경사항 저장
    db.commit()
    db.refresh(db_experiment_set)
    return db_experiment_set


async def delete_experiment_set(
    db: Session, experiment_set_id: int
) -> Dict[str, Any]:
    """실험 세트를 삭제합니다."""
    db_experiment_set = await get_experiment_set(db, experiment_set_id)
    if not db_experiment_set:
        return {"success": False, "message": f"ID {experiment_set_id}에 해당하는 실험 세트를 찾을 수 없습니다"}
    
    # 실험 세트 삭제
    db.delete(db_experiment_set)
    db.commit()
    return {"success": True, "message": f"실험 세트 '{db_experiment_set.name}'이(가) 삭제되었습니다"}


async def add_experiment(
    db: Session, experiment_set_id: int, experiment: schemas.ExperimentCreate
) -> models.Experiment:
    """실험 세트에 새 실험을 추가합니다."""
    # 실험 세트 조회
    db_experiment_set = db.query(models.ExperimentSet).filter(
        models.ExperimentSet.id == experiment_set_id
    ).first()
    
    if not db_experiment_set:
        raise HTTPException(status_code=404, detail=f"ID {experiment_set_id}에 해당하는 실험 세트를 찾을 수 없습니다")
    
    # 실험 생성
    db_experiment = models.Experiment(
        experiment_set_id=experiment_set_id,
        name=experiment.name,
        prompt=experiment.prompt,
        model=experiment.model,
        params=experiment.params,
        weight=experiment.weight,
        is_control=experiment.is_control
    )
    
    # 변경사항 저장
    db.add(db_experiment)
    db.commit()
    db.refresh(db_experiment)
    return db_experiment


async def get_experiment(db: Session, experiment_id: int) -> Optional[models.Experiment]:
    """실험을 ID로 조회합니다."""
    return db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()


async def update_experiment(
    db: Session, experiment_id: int, experiment: schemas.ExperimentBase
) -> Optional[models.Experiment]:
    """실험을 업데이트합니다."""
    db_experiment = await get_experiment(db, experiment_id)
    if not db_experiment:
        return None
    
    # 업데이트할 필드 설정
    if experiment.name is not None:
        db_experiment.name = experiment.name
    if experiment.prompt is not None:
        db_experiment.prompt = experiment.prompt
    if experiment.model is not None:
        db_experiment.model = experiment.model
    if experiment.params is not None:
        db_experiment.params = experiment.params
    if experiment.weight is not None:
        db_experiment.weight = experiment.weight
    if experiment.is_control is not None:
        db_experiment.is_control = experiment.is_control
    
    db_experiment.updated_at = models.datetime.utcnow()
    
    # 변경사항 저장
    db.commit()
    db.refresh(db_experiment)
    return db_experiment


async def delete_experiment(db: Session, experiment_id: int) -> Dict[str, Any]:
    """실험을 삭제합니다."""
    db_experiment = await get_experiment(db, experiment_id)
    if not db_experiment:
        return {"success": False, "message": f"ID {experiment_id}에 해당하는 실험을 찾을 수 없습니다"}
    
    # 실험 삭제
    db.delete(db_experiment)
    db.commit()
    return {"success": True, "message": f"실험 '{db_experiment.name}'이(가) 삭제되었습니다"}
