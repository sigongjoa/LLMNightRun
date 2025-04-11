# TEMP: 임시 구현 코드입니다. 정상 작동하지만 추후 데이터베이스 연동 및 실제 실험 실행 로직 구현 예정입니다.
from fastapi import APIRouter, HTTPException, Depends, Path, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import json

# 모델과 데이터베이스 관련 임포트는 실제 프로젝트 구조에 맞게 수정 필요

# AB 테스트 모델 정의
class ExperimentTemplate(BaseModel):
    id: str = None
    name: str
    description: Optional[str] = None
    defaultConfig: str  # JSON 문자열
    created_at: datetime = None

class ExperimentSet(BaseModel):
    id: str = None
    name: str
    description: Optional[str] = None
    models: List[str]
    prompts: List[str]
    metrics: List[str]
    templateId: Optional[str] = None
    status: str = "pending"
    created_at: datetime = None
    experiment_count: int = 0

class ExperimentResult(BaseModel):
    id: str = None
    experiment_set_id: str
    experiment_set_name: str
    status: str = "completed"
    run_at: datetime = None
    total_experiments: int = 0
    model_comparison: Dict[str, Any] = None
    prompt_comparison: Dict[str, Any] = None
    detailed_results: List[Dict[str, Any]] = None

# CAUTION: 다른 기능과 연결된 코드입니다. 수정 시 연관 기능(예: 프론트엔드 AB 테스트 페이지)에 영향이 있을 수 있습니다.
# 라우터 생성
router = APIRouter(prefix="/ab-testing", tags=["AB Testing"])

# 메모리 내 데이터 저장소 (실제 구현에서는 데이터베이스로 대체)
templates_db = {}
experiment_sets_db = {}
results_db = {}

# 템플릿 관련 엔드포인트
@router.get("/templates", response_model=List[ExperimentTemplate])
async def get_templates():
    return list(templates_db.values())

@router.post("/templates", response_model=ExperimentTemplate, status_code=201)
async def create_template(template: ExperimentTemplate):
    template_id = str(uuid.uuid4())
    template.id = template_id
    template.created_at = datetime.now()
    
    # JSON 형식 검증
    try:
        json.loads(template.defaultConfig)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in defaultConfig")
    
    templates_db[template_id] = template
    return template

@router.get("/templates/{template_id}", response_model=ExperimentTemplate)
async def get_template(template_id: str = Path(..., description="템플릿 ID")):
    if template_id not in templates_db:
        raise HTTPException(status_code=404, detail="Template not found")
    return templates_db[template_id]

@router.put("/templates/{template_id}", response_model=ExperimentTemplate)
async def update_template(
    updated_template: ExperimentTemplate,
    template_id: str = Path(..., description="템플릿 ID")
):
    if template_id not in templates_db:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # JSON 형식 검증
    try:
        json.loads(updated_template.defaultConfig)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in defaultConfig")
    
    # 기존 필드 유지
    updated_template.id = template_id
    updated_template.created_at = templates_db[template_id].created_at
    
    templates_db[template_id] = updated_template
    return updated_template

@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(template_id: str = Path(..., description="템플릿 ID")):
    if template_id not in templates_db:
        raise HTTPException(status_code=404, detail="Template not found")
    del templates_db[template_id]
    return None

# 실험 세트 관련 엔드포인트
@router.get("/experiment-sets", response_model=List[ExperimentSet])
async def get_experiment_sets():
    return list(experiment_sets_db.values())

@router.post("/experiment-sets", response_model=ExperimentSet, status_code=201)
async def create_experiment_set(experiment_set: ExperimentSet):
    experiment_set_id = str(uuid.uuid4())
    experiment_set.id = experiment_set_id
    experiment_set.created_at = datetime.now()
    experiment_set.experiment_count = len(experiment_set.models) * len(experiment_set.prompts)
    
    # 템플릿 ID가 제공된 경우 존재 여부 확인
    if experiment_set.templateId and experiment_set.templateId not in templates_db:
        raise HTTPException(status_code=404, detail="Template not found")
    
    experiment_sets_db[experiment_set_id] = experiment_set
    return experiment_set

@router.get("/experiment-sets/{experiment_set_id}", response_model=ExperimentSet)
async def get_experiment_set(experiment_set_id: str = Path(..., description="실험 세트 ID")):
    if experiment_set_id not in experiment_sets_db:
        raise HTTPException(status_code=404, detail="Experiment set not found")
    return experiment_sets_db[experiment_set_id]

@router.put("/experiment-sets/{experiment_set_id}", response_model=ExperimentSet)
async def update_experiment_set(
    updated_set: ExperimentSet,
    experiment_set_id: str = Path(..., description="실험 세트 ID")
):
    if experiment_set_id not in experiment_sets_db:
        raise HTTPException(status_code=404, detail="Experiment set not found")
    
    # 기존 필드 유지
    updated_set.id = experiment_set_id
    updated_set.created_at = experiment_sets_db[experiment_set_id].created_at
    updated_set.experiment_count = len(updated_set.models) * len(updated_set.prompts)
    
    experiment_sets_db[experiment_set_id] = updated_set
    return updated_set

@router.delete("/experiment-sets/{experiment_set_id}", status_code=204)
async def delete_experiment_set(experiment_set_id: str = Path(..., description="실험 세트 ID")):
    if experiment_set_id not in experiment_sets_db:
        raise HTTPException(status_code=404, detail="Experiment set not found")
    del experiment_sets_db[experiment_set_id]
    return None

# 실험 실행 및 결과 관련 엔드포인트
@router.post("/experiment-sets/{experiment_set_id}/run", response_model=dict)
async def run_experiment_set(experiment_set_id: str = Path(..., description="실험 세트 ID")):
    if experiment_set_id not in experiment_sets_db:
        raise HTTPException(status_code=404, detail="Experiment set not found")
    
    experiment_set = experiment_sets_db[experiment_set_id]
    
    # 실행 중으로 상태 변경
    experiment_set.status = "running"
    
    # 여기서 실제 실험 실행 로직을 구현
    # 실제 구현에서는 비동기 작업으로 처리하고 결과를 DB에 저장
    
    # 임시 결과 생성 (실제 구현에서는 실제 데이터로 대체)
    result_id = str(uuid.uuid4())
    result = ExperimentResult(
        id=result_id,
        experiment_set_id=experiment_set_id,
        experiment_set_name=experiment_set.name,
        status="completed",
        run_at=datetime.now(),
        total_experiments=experiment_set.experiment_count,
        model_comparison={
            "models": [{"id": model_id, "name": f"Model {model_id}"} for model_id in experiment_set.models],
            "metrics": [{"id": metric_id, "name": f"Metric {metric_id}"} for metric_id in experiment_set.metrics],
            "scores": {
                model_id: {
                    metric_id: round(0.5 + 0.5 * hash(model_id + metric_id) % 100 / 100, 2)  # 랜덤 점수
                    for metric_id in experiment_set.metrics
                }
                for model_id in experiment_set.models
            }
        },
        prompt_comparison={
            "prompts": [{"id": prompt_id, "name": f"Prompt {prompt_id}"} for prompt_id in experiment_set.prompts],
            "metrics": [{"id": metric_id, "name": f"Metric {metric_id}"} for metric_id in experiment_set.metrics],
            "scores": {
                prompt_id: {
                    metric_id: round(0.5 + 0.5 * hash(prompt_id + metric_id) % 100 / 100, 2)  # 랜덤 점수
                    for metric_id in experiment_set.metrics
                }
                for prompt_id in experiment_set.prompts
            }
        },
        detailed_results=[
            {
                "id": str(uuid.uuid4()),
                "experiment_id": f"exp-{i}",
                "model_id": model_id,
                "model_name": f"Model {model_id}",
                "prompt_id": prompt_id,
                "prompt_name": f"Prompt {prompt_id}",
                "metric_id": metric_id,
                "metric_name": f"Metric {metric_id}",
                "score": round(0.5 + 0.5 * hash(model_id + prompt_id + metric_id) % 100 / 100, 2)  # 랜덤 점수
            }
            for i, (model_id, prompt_id, metric_id) in enumerate(
                [(m, p, mt) for m in experiment_set.models for p in experiment_set.prompts for mt in experiment_set.metrics]
            )
        ]
    )
    
    results_db[result_id] = result
    
    # 완료 상태로 변경
    experiment_set.status = "completed"
    
    return {"message": "실험이 성공적으로 실행되었습니다.", "result_id": result_id}

@router.get("/results/{result_id}", response_model=ExperimentResult)
async def get_result(result_id: str = Path(..., description="결과 ID")):
    if result_id not in results_db:
        raise HTTPException(status_code=404, detail="Result not found")
    return results_db[result_id]

@router.get("/results/{result_id}/export")
async def export_result(result_id: str = Path(..., description="결과 ID")):
    if result_id not in results_db:
        raise HTTPException(status_code=404, detail="Result not found")
    
    # 실제 구현에서는 CSV 파일 생성 및 응답 반환
    result = results_db[result_id]
    
    # 임시 CSV 데이터 생성
    csv_data = "model_id,model_name,prompt_id,prompt_name,metric_id,metric_name,score\n"
    for detail in result.detailed_results:
        csv_data += f"{detail['model_id']},{detail['model_name']},{detail['prompt_id']},{detail['prompt_name']},{detail['metric_id']},{detail['metric_name']},{detail['score']}\n"
    
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=ab_test_result_{result_id}.csv"}
    )

# 기타 필요한 엔드포인트
@router.get("/models", response_model=List[dict])
async def get_models():
    # 임시 모델 데이터 반환
    return [
        {"id": f"model-{i}", "name": f"모델 {i}", "description": f"모델 {i}에 대한 설명입니다."}
        for i in range(1, 6)
    ]

@router.get("/prompts", response_model=List[dict])
async def get_prompts():
    # 임시 프롬프트 데이터 반환
    return [
        {"id": f"prompt-{i}", "name": f"프롬프트 {i}", "description": f"프롬프트 {i}에 대한 설명입니다."}
        for i in range(1, 6)
    ]

@router.get("/metrics", response_model=List[dict])
async def get_metrics():
    # 임시 평가 지표 데이터 반환
    return [
        {"id": f"metric-{i}", "name": f"평가 지표 {i}", "description": f"평가 지표 {i}에 대한 설명입니다."}
        for i in range(1, 4)
    ]
