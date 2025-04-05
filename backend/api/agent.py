"""
에이전트 API 라우터 모듈

에이전트 관련 엔드포인트를 정의합니다.
"""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Optional

from ..database.connection import get_db
from ..models.agent import AgentRequest, AgentResponse
from ..schema import AgentState, Message
from ..agent.toolcall import ToolCallAgent
from ..tool.base import ToolCollection
from ..tool.github_tool import GitHubTool
from ..tool.python_execute import PythonExecute
from ..tool.str_replace_editor import StrReplaceEditor
from ..tool.terminate import Terminate
from ..database.operations.agent import (
    create_agent_session, update_agent_session, 
    finish_agent_session, create_agent_log, get_agent_logs
)

# 로거 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/agent",
    tags=["agent"],
    responses={404: {"description": "에이전트를 찾을 수 없음"}},
)

# 에이전트 인스턴스 저장소
agent_instances: Dict[str, ToolCallAgent] = {}


@router.post("/create")
async def create_agent():
    """
    새 에이전트를 생성합니다.
    
    Returns:
        생성된 에이전트 정보
    """
    try:
        # 고유 ID 생성
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        # 에이전트 생성 (아직 초기화만 하고 실행은 하지 않음)
        agent = ToolCallAgent(
            name="toolcall",
            description="도구 호출을 실행할 수 있는 에이전트.",
            system_prompt="당신은 도구를 사용하여 작업을 수행하는 도우미입니다.",
            next_step_prompt="어떤 도구를 사용할지 결정하세요. 가능한 도구 목록에서 선택하거나, 도구가 필요하지 않으면 텍스트로 응답하세요."
        )
        
        # 에이전트 저장
        agent_instances[agent_id] = agent
        
        return {
            "agent_id": agent_id,
            "state": AgentState.IDLE,
            "messages": [],
            "result": ""
        }
    except Exception as e:
        logger.error(f"에이전트 생성 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"에이전트 생성 실패: {str(e)}")


@router.post("/{agent_id}/run", response_model=AgentResponse)
async def run_agent(
    agent_id: str,
    request: AgentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    에이전트를 실행합니다.
    
    Args:
        agent_id: 에이전트 ID
        request: 에이전트 실행 요청 정보
        background_tasks: 백그라운드 작업 객체
        db: 데이터베이스 세션
        
    Returns:
        에이전트 실행 결과
        
    Raises:
        HTTPException: 에이전트를 찾을 수 없는 경우
    """
    # 에이전트 확인
    if agent_id not in agent_instances:
        raise HTTPException(status_code=404, detail=f"에이전트 ID {agent_id}를 찾을 수 없습니다.")
    
    agent = agent_instances[agent_id]
    
    try:
        # 도구 설정
        tools = ToolCollection(
            GitHubTool(),
            PythonExecute(),
            StrReplaceEditor(workspace_root=request.workspace),
            Terminate()
        )
        
        agent.available_tools = tools
        agent.special_tool_names = ["terminate"]  # terminate 도구가 호출되면 에이전트 종료
        
        if request.max_steps and request.max_steps > 0:
            agent.max_steps = request.max_steps
        
        # 데이터베이스에 에이전트 세션 생성
        session = create_agent_session(
            db,
            {
                "session_id": agent_id,
                "agent_type": agent.name,
                "status": "running",
                "parameters": {
                    "prompt": request.prompt,
                    "workspace": request.workspace,
                    "max_steps": agent.max_steps
                }
            }
        )
        
        # 사용자 메시지 추가
        user_msg = Message.user_message(request.prompt)
        agent.messages.append(user_msg)
        
        # 백그라운드에서 에이전트 실행
        background_tasks.add_task(
            run_agent_background,
            agent_id=agent_id,
            agent=agent,
            db=db
        )
        
        # 상태 반환
        return {
            "agent_id": agent_id,
            "state": agent.state,
            "messages": [msg.dict() for msg in agent.messages],
            "result": ""
        }
    except Exception as e:
        logger.error(f"에이전트 실행 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"에이전트 실행 실패: {str(e)}")


async def run_agent_background(agent_id: str, agent: ToolCallAgent, db: Session):
    """
    백그라운드에서 에이전트를 실행하는 함수
    
    Args:
        agent_id: 에이전트 ID
        agent: 에이전트 인스턴스
        db: 데이터베이스 세션
    """
    try:
        # 실행 단계 로깅 함수
        async def log_step(phase: str, step: int, input_data=None, output_data=None, tool_calls=None, error=None):
            await create_agent_log(
                db,
                {
                    "session_id": agent_id,
                    "step": step,
                    "phase": phase,
                    "input_data": input_data,
                    "output_data": output_data,
                    "tool_calls": tool_calls,
                    "error": error
                }
            )
        
        # 에이전트 실행
        current_step = 0
        result = ""
        
        # 초기화 단계 로깅
        await log_step("initialize", current_step, input_data={"agent_id": agent_id})
        
        try:
            # 에이전트 실행
            result = await agent.run()
            
            # 종료 단계 로깅
            await log_step(
                "finish", 
                agent.current_step,
                output_data={"result": result, "state": agent.state}
            )
            
            # 세션 완료
            await finish_agent_session(db, agent_id, "completed")
            
        except Exception as run_error:
            logger.error(f"에이전트 실행 오류: {str(run_error)}")
            
            # 오류 단계 로깅
            await log_step(
                "error",
                agent.current_step,
                error=str(run_error)
            )
            
            # 세션 오류 상태로 표시
            await finish_agent_session(db, agent_id, "error")
    
    except Exception as e:
        logger.error(f"백그라운드 에이전트 실행 오류: {str(e)}")
        try:
            # 세션 오류 상태로 표시 (최종 시도)
            await finish_agent_session(db, agent_id, "error")
        except:
            pass


@router.get("/{agent_id}/status", response_model=AgentResponse)
async def get_agent_status(agent_id: str):
    """
    에이전트의 현재 상태를 조회합니다.
    
    Args:
        agent_id: 에이전트 ID
        
    Returns:
        에이전트 상태 정보
        
    Raises:
        HTTPException: 에이전트를 찾을 수 없는 경우
    """
    # 에이전트 확인
    if agent_id not in agent_instances:
        raise HTTPException(status_code=404, detail=f"에이전트 ID {agent_id}를 찾을 수 없습니다.")
    
    agent = agent_instances[agent_id]
    
    # 상태 반환
    return {
        "agent_id": agent_id,
        "state": agent.state,
        "messages": [msg.dict() for msg in agent.messages],
        "result": ""
    }


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """
    에이전트를 삭제합니다.
    
    Args:
        agent_id: 에이전트 ID
        
    Returns:
        삭제 결과
        
    Raises:
        HTTPException: 에이전트를 찾을 수 없는 경우
    """
    # 에이전트 확인
    if agent_id not in agent_instances:
        raise HTTPException(status_code=404, detail=f"에이전트 ID {agent_id}를 찾을 수 없습니다.")
    
    # 에이전트 종료 및 자원 정리
    agent = agent_instances[agent_id]
    await agent.cleanup()
    
    # 저장소에서 삭제
    del agent_instances[agent_id]
    
    return {"message": f"에이전트 {agent_id}가 삭제되었습니다."}