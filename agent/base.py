"""
에이전트 시스템 기본 모듈

이 모듈은 에이전트 시스템의 기본 클래스와 핵심 기능을 제공합니다.
"""

import json
import uuid
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

# 로깅 설정
logger = logging.getLogger("agent")


class BaseAgent:
    """
    에이전트 기본 클래스
    
    모든 에이전트 유형의 기본이 되는 추상 클래스입니다.
    """
    
    def __init__(self, agent_id: str = None, name: str = "Agent", config: Dict[str, Any] = None):
        """
        에이전트 초기화
        
        Args:
            agent_id: 에이전트 ID (없으면 자동 생성)
            name: 에이전트 이름
            config: 에이전트 구성
        """
        # 기본 속성 설정
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name
        self.config = config or {}
        self.created_at = datetime.utcnow().isoformat()
        self.status = "idle"
        self.current_task = None
        self.last_action = None
        self.memory = {}
        self.tools = {}
        
        # 도구 등록
        self.register_default_tools()
        
        logger.info(f"에이전트 초기화: {self.agent_id} ({self.name})")
    
    def register_default_tools(self):
        """기본 도구 등록"""
        # 웹 검색 도구
        self.register_tool("web_search", self.web_search)
        
        # 코드 실행 도구
        self.register_tool("code_execution", self.execute_code)
        
        # 파일 작업 도구
        self.register_tool("read_file", self.read_file)
        self.register_tool("write_file", self.write_file)
    
    def register_tool(self, name: str, func: Callable):
        """
        도구 등록
        
        Args:
            name: 도구 이름
            func: 도구 함수
        """
        self.tools[name] = func
        logger.debug(f"도구 등록됨: {name}")
    
    async def web_search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        웹 검색 도구
        
        Args:
            query: 검색 쿼리
            num_results: 결과 수
            
        Returns:
            검색 결과
        """
        # 실제 구현에서는 검색 API를 호출
        logger.info(f"웹 검색: {query}")
        
        # 샘플 결과 반환
        return {
            "query": query,
            "results": [
                {
                    "title": f"샘플 검색 결과 {i+1}",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"{query}에 관한 샘플 검색 결과 {i+1}입니다."
                }
                for i in range(num_results)
            ]
        }
    
    async def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        코드 실행 도구
        
        Args:
            code: 실행할 코드
            language: 프로그래밍 언어
            
        Returns:
            실행 결과
        """
        # 실제 구현에서는 안전한 환경에서 코드 실행
        logger.info(f"{language} 코드 실행 ({len(code)} 자)")
        
        # 샘플 결과 반환
        return {
            "language": language,
            "output": f"샘플 {language} 코드 실행 결과입니다.",
            "execution_time": 0.5
        }
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """
        파일 읽기 도구
        
        Args:
            path: 파일 경로
            
        Returns:
            파일 내용
        """
        # 실제 구현에서는 안전하게 파일 읽기
        logger.info(f"파일 읽기: {path}")
        
        # 샘플 결과 반환
        return {
            "path": path,
            "content": f"{path} 파일의 샘플 내용입니다.",
            "size": 42
        }
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        파일 쓰기 도구
        
        Args:
            path: 파일 경로
            content: 파일 내용
            
        Returns:
            성공 여부
        """
        # 실제 구현에서는 안전하게 파일 쓰기
        logger.info(f"파일 쓰기: {path} ({len(content)} 자)")
        
        # 샘플 결과 반환
        return {
            "path": path,
            "success": True,
            "size": len(content)
        }
    
    async def assign_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        작업 할당
        
        Args:
            task: 작업 정보
            
        Returns:
            작업 ID 및 상태
        """
        # 작업 ID 생성
        task_id = task.get("id") or str(uuid.uuid4())
        
        # 작업 정보 설정
        self.current_task = {
            "id": task_id,
            "description": task.get("description", ""),
            "parameters": task.get("parameters", {}),
            "status": "assigned",
            "created_at": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id
        }
        
        # 에이전트 상태 업데이트
        self.status = "working"
        self.last_action = f"Task assigned: {task_id}"
        
        logger.info(f"작업 할당됨: {task_id} (에이전트 {self.agent_id})")
        
        return {
            "task_id": task_id,
            "status": "assigned",
            "agent_id": self.agent_id,
            "estimated_completion": None  # 실제 구현에서는 예상 완료 시간 계산
        }
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        작업 실행
        
        Args:
            task_id: 작업 ID
            
        Returns:
            작업 결과
        """
        # 실제 구현에서는 에이전트 유형별로 재정의
        logger.warning(f"기본 작업 실행 호출됨 (에이전트 {self.agent_id})")
        
        return {
            "task_id": task_id,
            "status": "completed",
            "result": "이 기본 메서드는 구현되지 않았습니다. 재정의가 필요합니다.",
            "agent_id": self.agent_id
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """
        에이전트 상태 조회
        
        Returns:
            상태 정보
        """
        return {
            "id": self.agent_id,
            "name": self.name,
            "status": self.status,
            "current_task": self.current_task["id"] if self.current_task else None,
            "last_action": self.last_action,
            "last_updated": datetime.utcnow().isoformat()
        }


def create_agent(agent_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    에이전트 생성 함수
    
    에이전트 생성을 위한 팩토리 함수입니다.
    
    Args:
        agent_data: 에이전트 생성 정보
        
    Returns:
        생성된 에이전트 정보
    """
    agent_id = str(uuid.uuid4())
    agent_type = agent_data.get("type", "task")
    
    agent = {
        "id": agent_id,
        "name": agent_data.get("name", "New Agent"),
        "type": agent_type,
        "description": agent_data.get("description", ""),
        "config": agent_data.get("config", {}),
        "created_at": datetime.utcnow().isoformat(),
        "status": "idle"
    }
    
    logger.info(f"에이전트 생성됨: {agent_id} ({agent['name']}, 유형: {agent_type})")
    
    return agent


def assign_task(agent_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    작업 할당 함수
    
    Args:
        agent_id: 에이전트 ID
        task_data: 작업 정보
        
    Returns:
        작업 ID 및 상태
    """
    task_id = str(uuid.uuid4())
    
    task = {
        "id": task_id,
        "agent_id": agent_id,
        "description": task_data.get("description", ""),
        "parameters": task_data.get("parameters", {}),
        "status": "assigned",
        "created_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"작업 할당됨: {task_id} (에이전트 {agent_id})")
    
    return {
        "task_id": task_id,
        "status": "assigned",
        "agent_id": agent_id,
        "estimated_completion": None  # 실제 구현에서는 예상 완료 시간 계산
    }
