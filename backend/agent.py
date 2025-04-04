"""
LLMNightRun 에이전트 라우터 모듈

에이전트 기능을 위한 API 엔드포인트를 정의합니다.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.agent import Manus
from backend.database.connection import get_db
from backend.logger import get_logger
from backend.schema import AgentState, Message


logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


# 전역 에이전트 저장소 (실제 구현에서는 데이터베이스나 Redis 등에 저장하는 것이 좋습니다)
agent_instances = {}


class AgentRequest(BaseModel):
    """에이전트 요청 모델"""
    prompt: str
    workspace: Optional[str] = None
    max_steps: Optional[int] = None


class AgentResponse(BaseModel):
    """에이전트 응답 모델"""
    agent_id: str
    state: AgentState
    messages: List[Dict] = []
    result: str = ""


@router.post("/create", response_model=AgentResponse)
async def create_agent(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """새 에이전트 인스턴스 생성
    
    Args:
        background_tasks: 백그라운드 작업 관리자
        db: 데이터베이스 세션
        
    Returns:
        AgentResponse: 생성된 에이전트 정보
    """
    try:
        # Manus 에이전트 생성
        agent = Manus()
        agent_id = f"agent_{len(agent_instances) + 1}"
        
        # 에이전트 저장
        agent_instances[agent_id] = agent
        
        return AgentResponse(
            agent_id=agent_id,
            state=agent.state,
            messages=[],
            result=""
        )
    except Exception as e:
        logger.error(f"에이전트 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{agent_id}/run", response_model=AgentResponse)
async def run_agent(
    agent_id: str,
    request: AgentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """에이전트 실행
    
    Args:
        agent_id: 에이전트 ID
        request: 실행 요청 정보
        background_tasks: 백그라운드 작업 관리자
        db: 데이터베이스 세션
        
    Returns:
        AgentResponse: 실행 결과
        
    Raises:
        HTTPException: 에이전트를 찾을 수 없거나 실행 중 오류 발생 시
    """
    # 에이전트 찾기
    agent = agent_instances.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"에이전트를 찾을 수 없습니다: {agent_id}")
    
    try:
        # 설정 조정
        if request.max_steps:
            agent.max_steps = request.max_steps
        
        # 에이전트 실행
        result = await agent.run(request.prompt)
        
        # 메시지 변환
        messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "base64_image": msg.base64_image,
                "tool_call_id": msg.tool_call_id,
                "name": msg.name,
                "tool_calls": [tc.dict() for tc in (msg.tool_calls or [])]
            }
            for msg in agent.messages
        ]
        
        return AgentResponse(
            agent_id=agent_id,
            state=agent.state,
            messages=messages,
            result=result
        )
    except Exception as e:
        logger.error(f"에이전트 실행 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/status", response_model=AgentResponse)
async def get_agent_status(agent_id: str, db: Session = Depends(get_db)):
    """에이전트 상태 조회
    
    Args:
        agent_id: 에이전트 ID
        db: 데이터베이스 세션
        
    Returns:
        AgentResponse: 에이전트 상태 정보
        
    Raises:
        HTTPException: 에이전트를 찾을 수 없는 경우
    """
    # 에이전트 찾기
    agent = agent_instances.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"에이전트를 찾을 수 없습니다: {agent_id}")
    
    # 메시지 변환
    messages = [
        {
            "role": msg.role,
            "content": msg.content,
            "base64_image": msg.base64_image,
            "tool_call_id": msg.tool_call_id,
            "name": msg.name,
            "tool_calls": [tc.dict() for tc in (msg.tool_calls or [])]
        }
        for msg in agent.messages
    ]
    
    return AgentResponse(
        agent_id=agent_id,
        state=agent.state,
        messages=messages,
        result=""
    )


@router.delete("/{agent_id}", response_model=dict)
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """에이전트 삭제
    
    Args:
        agent_id: 에이전트 ID
        db: 데이터베이스 세션
        
    Returns:
        dict: 삭제 결과
        
    Raises:
        HTTPException: 에이전트를 찾을 수 없는 경우
    """
    # 에이전트 찾기
    agent = agent_instances.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"에이전트를 찾을 수 없습니다: {agent_id}")
    
    try:
        # 에이전트 자원 정리
        await agent.cleanup()
        
        # 에이전트 삭제
        del agent_instances[agent_id]
        
        return {"message": f"에이전트 {agent_id}가 삭제되었습니다."}
    except Exception as e:
        logger.error(f"에이전트 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))