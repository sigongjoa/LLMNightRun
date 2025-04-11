from fastapi import FastAPI, APIRouter, Body, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import httpx
import logging
from datetime import datetime, timezone
import uuid

# 로그 설정
logger = logging.getLogger(__name__)

# Pydantic 모델
class PromptPreviewRequest(BaseModel):
    template: str
    system_prompt: Optional[str] = None  # 시스템 프롬프트 추가
    variables: Dict[str, str] = {}

class PromptPreviewResponse(BaseModel):
    result: str
    
class PromptExecuteRequest(BaseModel):
    template_id: Optional[int] = None
    template: str
    system_prompt: Optional[str] = None
    variables: Dict[str, str] = {}
    llm_type: str = "LOCAL_LLM"
    
class PromptExecuteResponse(BaseModel):
    content: str
    model_id: str

# 라우터 생성
router = APIRouter()

# LM Studio 서버 URL
LM_STUDIO_URL = "http://127.0.0.1:1234"

# 임시 프롬프트 템플릿 저장소 (메모리 기반)
_templates_db = []

# 프롬프트 미리보기 엔드포인트
@router.post("/prompt-engineering/preview", response_model=PromptPreviewResponse)
async def preview_prompt(request: PromptPreviewRequest):
    """프롬프트 미리보기 - 변수를 실제 값으로 대체"""
    template = request.template
    system_prompt = request.system_prompt or ""
    
    # 템플릿 변수 처리
    for var_name, var_value in request.variables.items():
        placeholder = f"{{{{{var_name}}}}}"
        template = template.replace(placeholder, var_value)
        # 시스템 프롬프트에도 변수 대체 적용
        if system_prompt:
            system_prompt = system_prompt.replace(placeholder, var_value)
    
    # 시스템 프롬프트가 있는 경우 힘께 반환
    result = template
    if system_prompt:
        result = f"[System Prompt]\n{system_prompt}\n\n[User Prompt]\n{template}"
    
    return {"result": result}

# 프롬프트 템플릿 생성 엔드포인트
@router.post("/prompt-templates/")
async def create_prompt_template(data: Dict[str, Any] = Body(...)):
    """프롬프트 템플릿 생성 엔드포인트"""
    now = datetime.now(timezone.utc).isoformat()
    
    # 새 템플릿 생성
    new_template = {
        "id": len(_templates_db) + 1,
        "name": data.get("name", ""),
        "content": data.get("content", ""),
        "system_prompt": data.get("system_prompt", ""),
        "description": data.get("description", ""),
        "category": data.get("category", "일반"),
        "tags": data.get("tags", []),
        "template_variables": data.get("template_variables", []),
        "user_id": 1,
        "created_at": now,
        "updated_at": now
    }
    
    # 메모리 DB에 추가
    _templates_db.append(new_template)
    
    return new_template

# 프롬프트 템플릿 목록 조회 엔드포인트
@router.get("/prompt-templates/")
async def get_prompt_templates(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """프롬프트 템플릿 목록 조회"""
    logger.info(f"프롬프트 템플릿 목록 조회 - 카테고리: {category}, 태그: {tag}, skip: {skip}, limit: {limit}")
    
    # 필터링 적용
    filtered_templates = _templates_db
    
    # 카테고리 필터
    if category:
        filtered_templates = [t for t in filtered_templates if t.get("category") == category]
    
    # 태그 필터
    if tag:
        filtered_templates = [t for t in filtered_templates if tag in t.get("tags", [])]
    
    # 페이지네이션 적용
    paginated_templates = filtered_templates[skip:skip+limit]
    
    return paginated_templates

# 프롬프트 템플릿 상세 조회 엔드포인트
@router.get("/prompt-templates/{template_id}")
async def get_prompt_template(template_id: int):
    """프롬프트 템플릿 상세 조회"""
    logger.info(f"프롬프트 템플릿 상세 조회 - ID: {template_id}")
    
    # ID로 템플릿 찾기
    for template in _templates_db:
        if template.get("id") == template_id:
            return template
    
    # 템플릿을 찾지 못한 경우
    raise HTTPException(status_code=404, detail=f"템플릿 ID {template_id}를 찾을 수 없습니다")

# 프롬프트 템플릿 업데이트 엔드포인트
@router.put("/prompt-templates/{template_id}")
async def update_prompt_template(template_id: int, data: Dict[str, Any] = Body(...)):
    """프롬프트 템플릿 업데이트"""
    logger.info(f"프롬프트 템플릿 업데이트 - ID: {template_id}")
    
    # ID로 템플릿 찾기
    for i, template in enumerate(_templates_db):
        if template.get("id") == template_id:
            # 업데이트할 필드
            _templates_db[i].update({
                "name": data.get("name", template.get("name")),
                "content": data.get("content", template.get("content")),
                "system_prompt": data.get("system_prompt", template.get("system_prompt")),
                "description": data.get("description", template.get("description")),
                "category": data.get("category", template.get("category")),
                "tags": data.get("tags", template.get("tags")),
                "template_variables": data.get("template_variables", template.get("template_variables")),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            return _templates_db[i]
    
    # 템플릿을 찾지 못한 경우
    raise HTTPException(status_code=404, detail=f"템플릿 ID {template_id}를 찾을 수 없습니다")

# 프롬프트 템플릿 삭제 엔드포인트
@router.delete("/prompt-templates/{template_id}")
async def delete_prompt_template(template_id: int):
    """프롬프트 템플릿 삭제"""
    logger.info(f"프롬프트 템플릿 삭제 - ID: {template_id}")
    
    # ID로 템플릿 찾기
    for i, template in enumerate(_templates_db):
        if template.get("id") == template_id:
            # 템플릿 삭제
            del _templates_db[i]
            return {"success": True, "message": f"템플릿 ID {template_id}가 삭제되었습니다"}
    
    # 템플릿을 찾지 못한 경우
    raise HTTPException(status_code=404, detail=f"템플릿 ID {template_id}를 찾을 수 없습니다")

# 프롬프트 실행 엔드포인트 (LM Studio로 전송)
@router.post("/prompt-engineering/execute", response_model=PromptExecuteResponse)
async def execute_prompt(request: PromptExecuteRequest):
    """프롬프트 실행 - LM Studio로 전송"""
    try:
        # 템플릿 처리
        template = request.template
        system_prompt = request.system_prompt or ""
        
        # 변수 치환
        for var_name, var_value in request.variables.items():
            placeholder = f"{{{{{var_name}}}}}"
            template = template.replace(placeholder, var_value)
            if system_prompt:
                system_prompt = system_prompt.replace(placeholder, var_value)
        
        # 메시지 구성
        messages = []
        
        # 시스템 프롬프트가 있는 경우 추가
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        # 사용자 프롬프트 추가
        messages.append({"role": "user", "content": template})
        
        # LM Studio API 호출
        logger.info(f"LM Studio API 호출: {LM_STUDIO_URL}/v1/chat/completions")
        logger.info(f"Messages: {messages}")
        
        async with httpx.AsyncClient(timeout=90.0) as client:  # 타임아웃을 90초로 증가
            response = await client.post(
                f"{LM_STUDIO_URL}/v1/chat/completions",
                json={
                    "model": "deepseek-r1-distill-qwen-7b",  # 기본 모델
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return {
                    "content": content,
                    "model_id": "deepseek-r1-distill-qwen-7b"
                }
            else:
                logger.error(f"LM Studio API 오류: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail="LM Studio API 호출 중 오류가 발생했습니다")
                
    except Exception as e:
        logger.error(f"LM Studio 호출 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LM Studio 호출 오류: {str(e)}")
        
# LM Studio 상태 확인 엔드포인트
@router.get("/prompt-engineering/lm-studio-status")
async def lm_studio_status():
    """연결된 LM Studio 서버 상태 확인"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LM_STUDIO_URL}/v1/models")
            
            if response.status_code == 200:
                models = response.json()
                return {
                    "connected": True,
                    "url": LM_STUDIO_URL,
                    "models": models
                }
            else:
                return {
                    "connected": False,
                    "url": LM_STUDIO_URL,
                    "error": f"Status code: {response.status_code}"
                }
    except Exception as e:
        return {
            "connected": False,
            "url": LM_STUDIO_URL,
            "error": str(e)
        }
