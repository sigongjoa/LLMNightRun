# DO NOT CHANGE CODE: 이 파일은 프롬프트 엔지니어링 API 라우터입니다.
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import httpx
from pydantic import BaseModel
import logging

from database import get_db
from models import PromptTemplate as DBPromptTemplate, User
from schemas import PromptTemplateCreate, PromptTemplateUpdate, PromptTemplate
from auth.dependencies import get_current_active_user

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(tags=["prompt_engineering"])

# PromptTemplate 모델
class PromptTemplateBase(BaseModel):
    name: str
    content: str
    description: Optional[str] = None
    category: Optional[str] = "일반"
    tags: List[str] = []
    template_variables: List[str] = []

class PromptTemplateCreate(PromptTemplateBase):
    pass

class PromptTemplateResponse(PromptTemplateBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        orm_mode = True

# 프롬프트 미리보기 요청 모델
class PreviewRequest(BaseModel):
    template: str
    variables: Dict[str, str] = {}

# 프롬프트 실행 요청 모델
class ExecuteRequest(BaseModel):
    template_id: int
    variables: Dict[str, str] = {}
    llm_type: str

# 프롬프트 템플릿 CRUD 엔드포인트
@router.post("/prompt-templates/", response_model=PromptTemplateResponse)
async def create_prompt_template(
    template: PromptTemplateBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """새로운 프롬프트 템플릿 생성"""
    logger.info(f"사용자 {current_user.username}가 프롬프트 템플릿 생성 요청: {template.name}")
    
    # DB 모델로 변환
    db_template = DBPromptTemplate(
        name=template.name,
        content=template.content,
        description=template.description,
        category=template.category,
        tags=template.tags,
        template_variables=template.template_variables,
        user_id=current_user.id
    )
    
    # DB에 저장
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    
    logger.info(f"프롬프트 템플릿 생성 완료: ID {db_template.id}")
    return db_template

@router.get("/prompt-templates/", response_model=List[PromptTemplateResponse])
async def get_prompt_templates(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """프롬프트 템플릿 목록 조회"""
    logger.info(f"사용자 {current_user.username}가 프롬프트 템플릿 목록 조회")
    
    # 기본 쿼리
    query = db.query(DBPromptTemplate).filter(DBPromptTemplate.user_id == current_user.id)
    
    # 필터 적용
    if category:
        query = query.filter(DBPromptTemplate.category == category)
    
    # 태그 필터링 (PostgreSQL에서는 @> 연산자 사용)
    if tag:
        query = query.filter(DBPromptTemplate.tags.any(tag))
    
    # 페이지네이션
    templates = query.offset(skip).limit(limit).all()
    
    logger.info(f"프롬프트 템플릿 {len(templates)}개 조회됨")
    return templates

@router.get("/prompt-templates/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """특정 프롬프트 템플릿 조회"""
    template = db.query(DBPromptTemplate).filter(
        DBPromptTemplate.id == template_id,
        DBPromptTemplate.user_id == current_user.id
    ).first()
    
    if not template:
        logger.warning(f"템플릿 ID {template_id} 찾을 수 없음")
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    logger.info(f"템플릿 ID {template_id} 조회 완료")
    return template

@router.put("/prompt-templates/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt_template(
    template_id: int,
    template_update: PromptTemplateBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """프롬프트 템플릿 업데이트"""
    template = db.query(DBPromptTemplate).filter(
        DBPromptTemplate.id == template_id,
        DBPromptTemplate.user_id == current_user.id
    ).first()
    
    if not template:
        logger.warning(f"템플릿 ID {template_id} 찾을 수 없음")
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    # 필드 업데이트
    template.name = template_update.name
    template.content = template_update.content
    template.description = template_update.description
    template.category = template_update.category
    template.tags = template_update.tags
    template.template_variables = template_update.template_variables
    
    # DB에 저장
    db.commit()
    db.refresh(template)
    
    logger.info(f"템플릿 ID {template_id} 업데이트 완료")
    return template

@router.delete("/prompt-templates/{template_id}", status_code=204)
async def delete_prompt_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """프롬프트 템플릿 삭제"""
    template = db.query(DBPromptTemplate).filter(
        DBPromptTemplate.id == template_id,
        DBPromptTemplate.user_id == current_user.id
    ).first()
    
    if not template:
        logger.warning(f"템플릿 ID {template_id} 찾을 수 없음")
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    # DB에서 삭제
    db.delete(template)
    db.commit()
    
    logger.info(f"템플릿 ID {template_id} 삭제 완료")

# 프롬프트 엔지니어링 엔드포인트
@router.post("/prompt-engineering/preview", dependencies=[])
async def preview_prompt(request: PreviewRequest):
    """프롬프트 미리보기"""
    logger.info("프롬프트 미리보기 요청")
    
    # 템플릿 처리 (변수 대체)
    template = request.template
    for var_name, var_value in request.variables.items():
        placeholder = f"{{{{{var_name}}}}}"
        template = template.replace(placeholder, var_value)
    
    return {"result": template}

@router.post("/prompt-engineering/execute")
async def execute_prompt(
    request: ExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """프롬프트 실행"""
    logger.info(f"프롬프트 실행 요청: 템플릿 ID {request.template_id}, LLM 타입: {request.llm_type}")
    
    # 템플릿 조회
    template = db.query(DBPromptTemplate).filter(
        DBPromptTemplate.id == request.template_id,
        DBPromptTemplate.user_id == current_user.id
    ).first()
    
    if not template:
        logger.warning(f"템플릿 ID {request.template_id} 찾을 수 없음")
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    # 템플릿 처리 (변수 대체)
    prompt_content = template.content
    for var_name, var_value in request.variables.items():
        placeholder = f"{{{{{var_name}}}}}"
        prompt_content = prompt_content.replace(placeholder, var_value)
    
    # LLM 타입에 따라 적절한 서비스 호출
    if request.llm_type == "LOCAL_LLM":
        try:
            # LM Studio API 호출
            async with httpx.AsyncClient(timeout=30.0) as client:
                llm_response = await client.post(
                    "http://127.0.0.1:1234/v1/chat/completions",
                    json={
                        "model": "deepseek-r1-distill-qwen-7b",
                        "messages": [{"role": "user", "content": prompt_content}],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                
                if llm_response.status_code == 200:
                    response_data = llm_response.json()
                    content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    # 응답 데이터 생성
                    return {
                        "question": {
                            "id": 0,  # 임시 ID
                            "content": prompt_content,
                            "user_id": current_user.id
                        },
                        "response": {
                            "id": 0,  # 임시 ID
                            "content": content,
                            "question_id": 0,  # 임시 ID
                            "llm_type": request.llm_type,
                            "model_id": "deepseek-r1-distill-qwen-7b"
                        }
                    }
                else:
                    logger.error(f"LLM API 오류: {llm_response.status_code} - {llm_response.text}")
                    raise HTTPException(status_code=500, detail="LLM API 호출 중 오류가 발생했습니다")
                    
        except Exception as e:
            logger.error(f"LLM 호출 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"LLM 호출 오류: {str(e)}")
    else:
        # 다른 LLM 타입 처리
        logger.warning(f"지원되지 않는 LLM 타입: {request.llm_type}")
        raise HTTPException(status_code=400, detail=f"지원되지 않는 LLM 타입: {request.llm_type}")
