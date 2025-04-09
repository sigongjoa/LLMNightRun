"""
A/B 테스트 템플릿 컨트롤러

템플릿 관련 비즈니스 로직을 구현합니다.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.logger import get_logger
from backend.ab_testing import models, schemas

# 로거 설정
logger = get_logger(__name__)


async def create_template(db: Session, template: schemas.ExperimentTemplate) -> models.ExperimentTemplate:
    """새 실험 템플릿을 생성합니다."""
    try:
        # 템플릿 생성
        db_template = models.ExperimentTemplate(
            name=template.name,
            description=template.description,
            prompt_template=template.prompt_template,
            model_suggestions=template.model_suggestions,
            default_params=template.default_params,
            tags=template.tags,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
        
    except Exception as e:
        db.rollback()
        logger.error(f"템플릿 생성 실패: {str(e)}")
        raise


async def get_templates(
    db: Session, skip: int = 0, limit: int = 20, 
    search: Optional[str] = None, tag: Optional[str] = None
) -> List[models.ExperimentTemplate]:
    """템플릿 목록을 조회합니다."""
    query = db.query(models.ExperimentTemplate)
    
    # 검색어 필터링
    if search:
        query = query.filter(models.ExperimentTemplate.name.ilike(f"%{search}%") | 
                           models.ExperimentTemplate.description.ilike(f"%{search}%"))
    
    # 태그 필터링 (JSON 배열에서 검색)
    if tag:
        # SQLite에서는 JSON 배열 검색이 제한적이므로 간단하게 구현
        # 실제 프로덕션에서는 데이터베이스에 맞게 쿼리 최적화 필요
        templates = query.all()
        filtered_templates = []
        for template in templates:
            if template.tags and tag in template.tags:
                filtered_templates.append(template)
        return filtered_templates[skip:skip+limit]
    
    return query.offset(skip).limit(limit).all()


async def get_template(db: Session, template_id: int) -> Optional[models.ExperimentTemplate]:
    """템플릿을 ID로 조회합니다."""
    return db.query(models.ExperimentTemplate).filter(models.ExperimentTemplate.id == template_id).first()


async def update_template(
    db: Session, template_id: int, template_data: schemas.ExperimentTemplate
) -> Optional[models.ExperimentTemplate]:
    """템플릿을 업데이트합니다."""
    db_template = await get_template(db, template_id)
    if not db_template:
        return None
    
    # 업데이트할 필드 설정
    db_template.name = template_data.name
    db_template.description = template_data.description
    db_template.prompt_template = template_data.prompt_template
    db_template.model_suggestions = template_data.model_suggestions
    db_template.default_params = template_data.default_params
    db_template.tags = template_data.tags
    db_template.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_template)
    return db_template


async def delete_template(db: Session, template_id: int) -> Dict[str, Any]:
    """템플릿을 삭제합니다."""
    db_template = await get_template(db, template_id)
    if not db_template:
        return {"success": False, "message": f"ID {template_id}에 해당하는 템플릿을 찾을 수 없습니다"}
    
    # 템플릿 삭제
    db.delete(db_template)
    db.commit()
    
    return {"success": True, "message": f"템플릿 '{db_template.name}'이(가) 삭제되었습니다"}


async def create_experiment_set_from_template(
    db: Session, template_id: int, params: Dict[str, Any]
) -> models.ExperimentSet:
    """템플릿으로부터 실험 세트를 생성합니다."""
    # 템플릿 조회
    db_template = await get_template(db, template_id)
    if not db_template:
        raise ValueError(f"ID {template_id}에 해당하는 템플릿을 찾을 수 없습니다")
    
    # 템플릿 파라미터 처리
    experiment_name = params.get("name", f"From Template: {db_template.name}")
    description = params.get("description", f"Generated from template: {db_template.name}")
    
    # 템플릿의 프롬프트에 파라미터 적용
    prompt_template = db_template.prompt_template
    prompt_vars = params.get("prompt_vars", {})
    processed_prompt = prompt_template
    for key, value in prompt_vars.items():
        placeholder = f"{{{key}}}"
        processed_prompt = processed_prompt.replace(placeholder, str(value))
    
    # 모델 선택
    model = params.get("model", db_template.model_suggestions[0] if db_template.model_suggestions else "gpt-3.5-turbo")
    
    # 파라미터 설정
    model_params = db_template.default_params.copy() if db_template.default_params else {}
    custom_params = params.get("params", {})
    model_params.update(custom_params)
    
    # 실험 세트 생성
    experiment_set = models.ExperimentSet(
        name=experiment_name,
        description=description,
        config={"from_template_id": template_id},
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(experiment_set)
    db.flush()  # ID 할당
    
    # 실험 생성
    experiment = models.Experiment(
        experiment_set_id=experiment_set.id,
        name=experiment_name,
        prompt=processed_prompt,
        model=model,
        params=model_params,
        template_id=template_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(experiment)
    
    # 변형 실험 생성 (템플릿에서 지정된 경우)
    variations = params.get("variations", [])
    for idx, variation in enumerate(variations):
        variation_name = variation.get("name", f"Variation {idx+1}")
        variation_prompt = processed_prompt
        
        # 변형 프롬프트 처리
        variation_prompt_vars = variation.get("prompt_vars", {})
        for key, value in variation_prompt_vars.items():
            placeholder = f"{{{key}}}"
            variation_prompt = variation_prompt.replace(placeholder, str(value))
        
        # 변형 모델 및 파라미터
        variation_model = variation.get("model", model)
        variation_params = model_params.copy()
        variation_params.update(variation.get("params", {}))
        
        # 변형 실험 추가
        variation_experiment = models.Experiment(
            experiment_set_id=experiment_set.id,
            name=variation_name,
            prompt=variation_prompt,
            model=variation_model,
            params=variation_params,
            is_control=False,
            template_id=template_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(variation_experiment)
    
    # 변경사항 저장
    db.commit()
    db.refresh(experiment_set)
    return experiment_set
