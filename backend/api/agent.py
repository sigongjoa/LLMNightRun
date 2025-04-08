"""
에이전트 API 라우터 모듈

Tool Calling 기능을 갖춘 자동화 에이전트 관련 엔드포인트를 정의합니다.
"""

import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List

from ..database.connection import get_db
from ..models.agent import AgentRequest, AgentResponse, Message
from ..models.enums import AgentState
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

# 최대 동시 에이전트 수 설정
MAX_AGENTS = 10
CLEANUP_COUNT = 5

@router.post("/create", response_model=AgentResponse)
async def create_agent():
    """
    새 에이전트를 생성합니다.
    
    Returns:
        AgentResponse: 생성된 에이전트 정보
    """
    try:
        # 저장소 청소 로직 실행
        await cleanup_old_agents()
        
        # 고유 ID 생성
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        
        # 에이전트 생성 및 초기화
        agent = create_tool_call_agent()
        
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


async def cleanup_old_agents():
    """오래된 에이전트를 정리하는 유틸리티 함수"""
    if len(agent_instances) > MAX_AGENTS:
        old_agents = list(agent_instances.keys())[:CLEANUP_COUNT]
        for old_id in old_agents:
            try:
                await agent_instances[old_id].cleanup()
                del agent_instances[old_id]
                logger.info(f"오래된 에이전트 {old_id} 정리 완료")
            except Exception as e:
                logger.warning(f"오래된 에이전트 {old_id} 정리 실패: {str(e)}")


def create_tool_call_agent() -> ToolCallAgent:
    """에이전트 인스턴스를 생성하는 유틸리티 함수"""
    # 기본 시스템 프롬프트
    system_prompt = "당신은 MCP 도구를 사용하여 작업을 수행하는 도우미입니다."
    
    # 에이전트 생성
    agent = ToolCallAgent(
        name="mcp",
        description="MCP 도구 호출을 실행할 수 있는 에이전트.",
        system_prompt=system_prompt,
        next_step_prompt="어떤 도구를 사용할지 결정하세요. 가능한 도구 목록에서 선택하거나, 도구가 필요하지 않으면 텍스트로 응답하세요."
    )
    
    # 초기 시스템 메시지 추가
    system_msg = Message.system_message(system_prompt)
    agent.messages.append(system_msg)
    
    return agent


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
        AgentResponse: 에이전트 실행 상태
        
    Raises:
        HTTPException: 에이전트를 찾을 수 없는 경우
    """
    # 에이전트 존재 확인
    agent = get_agent_or_404(agent_id)
    
    try:
        # 에이전트 도구 설정
        configure_agent_tools(agent, request.workspace)
        
        # 실행 단계 설정
        if request.max_steps and request.max_steps > 0:
            agent.max_steps = request.max_steps
        
        # 사용자 메시지 추가
        user_msg = Message.user_message(request.prompt)
        agent.messages.append(user_msg)
        
        # 백그라운드에서 에이전트 실행
        background_tasks.add_task(
            run_agent_background,
            agent_id=agent_id,
            agent=agent
        )
        
        # 현재 상태 반환
        return {
            "agent_id": agent_id,
            "state": agent.state,
            "messages": [msg.dict() for msg in agent.messages],
            "result": ""
        }
    except Exception as e:
        logger.error(f"에이전트 실행 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"에이전트 실행 실패: {str(e)}")


def configure_agent_tools(agent: ToolCallAgent, workspace: str):
    """에이전트 도구를 설정하는 유틸리티 함수"""
    # 도구 컬렉션 생성
    tools = ToolCollection(
        GitHubTool(),
        PythonExecute(),
        StrReplaceEditor(workspace_root=workspace),
        Terminate()
    )
    
    # 도구 설정
    agent.available_tools = tools
    agent.special_tool_names = ["terminate"]  # terminate 도구가 호출되면 에이전트 종료


async def run_agent_background(agent_id: str, agent: ToolCallAgent):
    """
    백그라운드에서 에이전트를 실행하는 함수
    
    Args:
        agent_id: 에이전트 ID
        agent: 에이전트 인스턴스
    """
    try:
        # 에이전트 실행
        result = await agent.run()
        logger.info(f"에이전트 {agent_id} 실행 완료: {result[:100] if result else '결과 없음'}...")
    except Exception as e:
        logger.error(f"에이전트 {agent_id} 백그라운드 실행 오류: {str(e)}", exc_info=True)


def get_agent_or_404(agent_id: str) -> ToolCallAgent:
    """
    에이전트 ID로 에이전트를 조회하거나 404 에러를 발생시키는 유틸리티 함수
    
    Args:
        agent_id: 에이전트 ID
        
    Returns:
        ToolCallAgent: 조회된 에이전트 인스턴스
        
    Raises:
        HTTPException: 에이전트를 찾을 수 없는 경우
    """
    if agent_id not in agent_instances:
        raise HTTPException(status_code=404, detail=f"에이전트 ID {agent_id}를 찾을 수 없습니다.")
    
    return agent_instances[agent_id]


@router.get("/{agent_id}/status", response_model=AgentResponse)
async def get_agent_status(agent_id: str):
    """
    에이전트의 현재 상태를 조회합니다.
    
    Args:
        agent_id: 에이전트 ID
        
    Returns:
        AgentResponse: 에이전트 상태 정보
    """
    try:
        # 에이전트 조회 시도
        agent = get_agent_or_404(agent_id)
        
        # 메시지 형식화
        formatted_messages = format_agent_messages(agent.messages)
        
        return {
            "agent_id": agent_id,
            "state": agent.state,
            "messages": formatted_messages,
            "result": ""
        }
    except HTTPException as http_ex:
        # 404 에러를 캡처하고 빈 상태 반환 (클라이언트 호환성)
        if http_ex.status_code == 404:
            logger.warning(f"에이전트 {agent_id} 없음, 빈 상태 반환")
            return {
                "agent_id": agent_id,
                "state": AgentState.IDLE,
                "messages": [],
                "result": ""
            }
        raise
    except Exception as e:
        logger.error(f"에이전트 상태 조회 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"에이전트 상태 조회 실패: {str(e)}")


def format_agent_messages(messages: List[Message]) -> List[dict]:
    """
    에이전트 메시지를 형식화하는 유틸리티 함수
    
    Args:
        messages: 메시지 목록
        
    Returns:
        List[dict]: 형식화된 메시지 목록
    """
    formatted_messages = []
    
    # 중복 ID 및 중복 내용 방지
    unique_ids = set()
    seen_contents = {}
    
    # 메시지 계수
    role_counters = {'user': 0, 'assistant': 0, 'system': 0, 'tool': 0}
    
    for msg in messages:
        try:
            msg_dict = msg.dict()
            
            # ID 필드 검증 및 생성
            if 'id' not in msg_dict or not msg_dict['id']:
                msg_dict['id'] = f"{msg.role}-{uuid.uuid4().hex}"
            
            # 중복 ID 검사
            if msg_dict['id'] in unique_ids:
                msg_dict['id'] = f"{msg.role}-{uuid.uuid4().hex}"
            
            # 중복 내용 검사 (동일 역할 + 내용 조합)
            content_key = f"{msg.role}:{msg.content or ''}"
            if content_key in seen_contents:
                unique_ids.add(msg_dict['id'])
                continue
            
            # 현재 메시지 추적
            seen_contents[content_key] = True
            unique_ids.add(msg_dict['id'])
            
            # 역할별 카운터 증가 및 메타데이터 추가
            role_counters[msg.role] += 1
            msg_dict['sequence'] = role_counters[msg.role]
            
            formatted_messages.append(msg_dict)
        except Exception as e:
            logger.error(f"메시지 변환 오류: {e}", exc_info=True)
            formatted_messages.append({
                "role": "system",
                "content": "메시지 로딩 중 오류가 발생했습니다.",
                "id": f"error-{uuid.uuid4().hex}"
            })
    
    # 중복 필터링 로그
    if len(formatted_messages) < len(messages):
        logger.info(f"메시지 중복 필터링: {len(messages)}개 -> {len(formatted_messages)}개")
    
    return formatted_messages


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """
    에이전트를 삭제합니다.
    
    Args:
        agent_id: 에이전트 ID
        
    Returns:
        dict: 삭제 결과 메시지
    """
    try:
        # 에이전트 조회
        agent = get_agent_or_404(agent_id)
        
        # 에이전트 정리 및 삭제
        await agent.cleanup()
        del agent_instances[agent_id]
        
        return {"message": f"에이전트 {agent_id}가 삭제되었습니다."}
    except HTTPException:
        # 404 에러는 그대로 전달
        raise
    except Exception as e:
        logger.error(f"에이전트 삭제 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"에이전트 삭제 실패: {str(e)}")