"""
에이전트 관련 데이터베이스 작업 모듈

에이전트 세션 및 로그에 대한 CRUD 작업을 제공합니다.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Union, Dict, Any
from datetime import datetime

from ..models import AgentSession as DBAgentSession, AgentLog as DBAgentLog, AgentPhaseEnum
from ...models.agent import AgentSession, AgentLog
from ...models.enums import AgentPhase


def get_agent_sessions(
    db: Session, 
    session_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[AgentSession]:
    """
    Agent 세션 목록 조회
    
    Args:
        db: 데이터베이스 세션
        session_id: 특정 세션 ID로 필터링
        agent_type: Agent 유형으로 필터링
        status: 상태로 필터링
        skip: 건너뛸 항목 수
        limit: 최대 반환 항목 수
    
    Returns:
        Agent 세션 목록
    """
    query = db.query(DBAgentSession)
    
    if session_id:
        query = query.filter(DBAgentSession.session_id == session_id)
    
    if agent_type:
        query = query.filter(DBAgentSession.agent_type == agent_type)
    
    if status:
        query = query.filter(DBAgentSession.status == status)
    
    # 최신 세션부터 조회
    query = query.order_by(DBAgentSession.start_time.desc())
    
    return query.offset(skip).limit(limit).all()


def get_agent_session(
    db: Session, 
    session_id: str
) -> Optional[AgentSession]:
    """
    특정 Agent 세션 조회
    
    Args:
        db: 데이터베이스 세션
        session_id: 세션 ID
    
    Returns:
        Agent 세션 또는 None
    """
    return db.query(DBAgentSession).filter(DBAgentSession.session_id == session_id).first()


def create_agent_session(
    db: Session,
    session: Union[AgentSession, Dict[str, Any]]
) -> AgentSession:
    """
    새 Agent 세션 생성
    
    Args:
        db: 데이터베이스 세션
        session: 생성할 세션 정보
    
    Returns:
        생성된 Agent 세션
    """
    # 딕셔너리로 변환
    if not isinstance(session, dict):
        session_data = session.dict(exclude_unset=True)
    else:
        session_data = session
    
    # ID 제거 (자동 생성)
    if "id" in session_data:
        del session_data["id"]
    
    # 시작 시간이 지정되지 않은 경우 현재 시간 사용
    if "start_time" not in session_data or not session_data["start_time"]:
        session_data["start_time"] = datetime.utcnow()
    
    # 데이터베이스 모델 생성
    db_session = DBAgentSession(**session_data)
    
    # 데이터베이스에 저장
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session


def update_agent_session(
    db: Session,
    session_id: str,
    update_data: Dict[str, Any]
) -> Optional[AgentSession]:
    """
    Agent 세션 업데이트
    
    Args:
        db: 데이터베이스 세션
        session_id: 세션 ID
        update_data: 업데이트할 데이터 필드
    
    Returns:
        업데이트된 Agent 세션 또는 None
    """
    db_session = db.query(DBAgentSession).filter(DBAgentSession.session_id == session_id).first()
    
    if not db_session:
        return None
    
    for key, value in update_data.items():
        if hasattr(db_session, key):
            setattr(db_session, key, value)
    
    db.commit()
    db.refresh(db_session)
    
    return db_session


def finish_agent_session(
    db: Session,
    session_id: str,
    status: str = "completed"
) -> Optional[AgentSession]:
    """
    Agent 세션 종료 처리
    
    Args:
        db: 데이터베이스 세션
        session_id: 세션 ID
        status: 종료 상태 (completed, error 등)
    
    Returns:
        업데이트된 Agent 세션 또는 None
    """
    return update_agent_session(
        db,
        session_id,
        {
            "status": status,
            "end_time": datetime.utcnow()
        }
    )


def get_agent_logs(
    db: Session,
    session_id: Optional[str] = None,
    phase: Optional[Union[AgentPhase, str]] = None,
    step: Optional[int] = None,
    has_error: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AgentLog]:
    """
    Agent 로그 목록 조회
    
    Args:
        db: 데이터베이스 세션
        session_id: 세션 ID로 필터링
        phase: 특정 단계로 필터링
        step: 특정 스텝으로 필터링
        has_error: 오류 발생 여부로 필터링
        skip: 건너뛸 항목 수
        limit: 최대 반환 항목 수
    
    Returns:
        Agent 로그 목록
    """
    query = db.query(DBAgentLog)
    
    if session_id:
        query = query.filter(DBAgentLog.session_id == session_id)
    
    if phase:
        # Enum 변환
        if isinstance(phase, str):
            db_phase = AgentPhaseEnum[phase]
        elif isinstance(phase, AgentPhase):
            db_phase = AgentPhaseEnum[phase.value]
        else:
            db_phase = phase
            
        query = query.filter(DBAgentLog.phase == db_phase)
    
    if step is not None:
        query = query.filter(DBAgentLog.step == step)
    
    if has_error is not None:
        if has_error:
            query = query.filter(DBAgentLog.error.isnot(None))
        else:
            query = query.filter(DBAgentLog.error.is_(None))
    
    # 타임스탬프 순으로 정렬
    query = query.order_by(DBAgentLog.timestamp.asc())
    
    return query.offset(skip).limit(limit).all()


def create_agent_log(
    db: Session,
    log: Union[AgentLog, Dict[str, Any]]
) -> AgentLog:
    """
    새 Agent 로그 생성
    
    Args:
        db: 데이터베이스 세션
        log: 생성할 로그 정보
    
    Returns:
        생성된 Agent 로그
    """
    # 딕셔너리로 변환
    if not isinstance(log, dict):
        log_data = log.dict(exclude_unset=True)
    else:
        log_data = log
    
    # ID 제거 (자동 생성)
    if "id" in log_data:
        del log_data["id"]
    
    # 타임스탬프가 지정되지 않은 경우 현재 시간 사용
    if "timestamp" not in log_data or not log_data["timestamp"]:
        log_data["timestamp"] = datetime.utcnow()
    
    # phase 처리 (문자열/Enum -> DB Enum)
    if "phase" in log_data and not isinstance(log_data["phase"], AgentPhaseEnum):
        phase = log_data["phase"]
        if isinstance(phase, AgentPhase):
            log_data["phase"] = AgentPhaseEnum[phase.value]
        else:
            log_data["phase"] = AgentPhaseEnum[phase]
    
    # 세션 확인 및 업데이트
    session_id = log_data.get("session_id")
    if session_id:
        db_session = db.query(DBAgentSession).filter(DBAgentSession.session_id == session_id).first()
        
        if db_session:
            # 총 스텝 수 업데이트
            step = log_data.get("step", 0)
            if step > db_session.total_steps:
                db_session.total_steps = step
        else:
            # 세션이 없으면 자동으로 생성
            agent_type = log_data.get("agent_type", "unknown")
            db_session = DBAgentSession(
                session_id=session_id,
                agent_type=agent_type,
                start_time=datetime.utcnow(),
                status="running"
            )
            db.add(db_session)
    
    # 데이터베이스 모델 생성
    db_log = DBAgentLog(**log_data)
    
    # 데이터베이스에 저장
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    
    return db_log