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
from ..models.enums import AgentState, AgentPhase
from ..models.agent import Message
from ..agent.toolcall import ToolCallAgent
from ..tool.base import ToolCollection
from ..tool.github_tool import GitHubTool
from ..tool.python_execute import PythonExecute
from ..tool.str_replace_editor import StrReplaceEditor
from ..tool.terminate import Terminate

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
        
        # 기존 에이전트 정리 (동일 클라이언트를 위한 중복 생성 방지)
        if len(agent_instances) > 10:  # 최대 에이전트 수 제한
            # 가장 오래된 에이전트 5개 삭제
            old_agents = list(agent_instances.keys())[:5]
            for old_id in old_agents:
                try:
                    await agent_instances[old_id].cleanup()
                    del agent_instances[old_id]
                except Exception as e:
                    logger.warning(f"오래된 에이전트 {old_id} 정리 실패: {str(e)}")
        
        # 에이전트 생성 (아직 초기화만 하고 실행은 하지 않음)
        agent = ToolCallAgent(
            name="mcp",  # manus에서 mcp로 변경
            description="MCP 도구 호출을 실행할 수 있는 에이전트.",
            system_prompt="당신은 MCP 도구를 사용하여 작업을 수행하는 도우미입니다.",
            next_step_prompt="어떤 도구를 사용할지 결정하세요. 가능한 도구 목록에서 선택하거나, 도구가 필요하지 않으면 텍스트로 응답하세요."
        )
        
        # 초기 시스템 메시지 추가 (ID 자동 생성)
        system_msg = Message.system_message("당신은 MCP 도구를 사용하여 작업을 수행하는 도우미입니다.")
        agent.messages.append(system_msg)
        
        # 에이전트 저장
        agent_instances[agent_id] = agent
        
        return {
            "agent_id": agent_id,
            "state": AgentState.IDLE,
            "messages": [msg.dict() for msg in agent.messages],
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
        
        # 데이터베이스 작업 완전히 비활성화
        # 사용자 메시지 추가
        user_msg = Message.user_message(request.prompt)
        agent.messages.append(user_msg)
        
        # 백그라운드에서 에이전트 실행
        background_tasks.add_task(
            run_agent_background,
            agent_id=agent_id,
            agent=agent
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


async def run_agent_background(agent_id: str, agent: ToolCallAgent):
    """
    백그라운드에서 에이전트를 실행하는 함수
    
    Args:
        agent_id: 에이전트 ID
        agent: 에이전트 인스턴스
    """
    try:
        # 에이전트 실행
        result = ""
        
        try:
            # 에이전트 실행
            result = await agent.run()
            logger.info(f"에이전트 {agent_id} 실행 완료: {result[:100]}...")
            
        except Exception as run_error:
            logger.error(f"에이전트 실행 오류: {str(run_error)}")
    
    except Exception as e:
        logger.error(f"백그라운드 에이전트 실행 오류: {str(e)}")


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
    
    try:
        # 상태 반환
        formatted_messages = []
        
        # 중복 ID 및 중복 내용 방지
        unique_ids = set()
        seen_contents = {}  # role + content -> count
        
        # 메시지 계수
        role_counters = {'user': 0, 'assistant': 0, 'system': 0, 'tool': 0}
        
        for msg in agent.messages:
            try:
                msg_dict = msg.dict()
                
                # id 필드 확인하고 없으면 추가
                if 'id' not in msg_dict or not msg_dict['id']:
                    msg_dict['id'] = f"{msg.role}-{uuid.uuid4().hex}"
                
                # 중복 ID 확인
                if msg_dict['id'] in unique_ids:
                    # ID가 중복인 경우 새 ID 생성
                    msg_dict['id'] = f"{msg.role}-{uuid.uuid4().hex}"
                
                # 중복 내용 확인 (동일 역할 + 내용 조합)
                content_key = f"{msg.role}:{msg.content or ''}"
                if content_key in seen_contents:
                    # 이미 동일한 내용이 있으면 ID만 기록하고 건너뛰기
                    unique_ids.add(msg_dict['id'])
                    continue
                
                # 현재 메시지 추적
                seen_contents[content_key] = True
                unique_ids.add(msg_dict['id'])
                
                # 역할별 카운터 증가
                role_counters[msg.role] += 1
                
                # 메시지에 메타데이터 추가
                msg_dict['sequence'] = role_counters[msg.role]
                
                formatted_messages.append(msg_dict)
            except Exception as e:
                logger.error(f"메시지 변환 오류: {e}", exc_info=True)
                # 오류 발생 시 오류 대신 가짜 메시지 추가
                formatted_messages.append({
                    "role": "system",
                    "content": "메시지 로딩 중 오류가 발생했습니다.",
                    "id": f"error-{uuid.uuid4().hex}"
                })
        
        # 로그 추가
        if len(formatted_messages) < len(agent.messages):
            logger.info(f"메시지 중복 필터링: {len(agent.messages)}개 -> {len(formatted_messages)}개")
        
        return {
            "agent_id": agent_id,
            "state": agent.state,
            "messages": formatted_messages,
            "result": ""
        }
    except Exception as e:
        # 404를 발생시키지 않도록, 해당 에이전트가 없는 경우 빈 메시지를 반환
        # 이는 오래된 클라이언트 코드가 여전히 기존 에이전트 상태를 폴링하는 경우를 처리하기 위함
        logger.warning(f"에이전트 {agent_id} 없음, 빈 상태 반환")
        
        # 빈 상태 반환
        return {
            "agent_id": agent_id,
            "state": AgentState.IDLE,
            "messages": [],
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