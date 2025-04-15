"""
ReAct (추론 및 행동) 에이전트

ReAct 패러다임을 구현한 에이전트입니다.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import BaseAgent

# 로깅 설정
logger = logging.getLogger("agent.react")


class ReActAgent(BaseAgent):
    """
    ReAct 에이전트 클래스
    
    추론(Reasoning)과 행동(Action)을 반복하는 에이전트입니다.
    """
    
    def __init__(self, agent_id: str = None, name: str = "ReAct Agent", config: Dict[str, Any] = None):
        """
        ReAct 에이전트 초기화
        
        Args:
            agent_id: 에이전트 ID (없으면 자동 생성)
            name: 에이전트 이름
            config: 에이전트 구성
        """
        super().__init__(agent_id, name, config)
        
        # ReAct 관련 설정
        self.max_iterations = self.config.get("max_iterations", 10)
        self.model_name = self.config.get("model", "gpt-4")
        
        logger.info(f"ReAct 에이전트 초기화: {self.agent_id} ({self.name})")
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        ReAct 방식으로 작업 실행
        
        Args:
            task_id: 작업 ID
            
        Returns:
            작업 실행 결과
        """
        # 현재 작업 가져오기
        if not self.current_task or self.current_task["id"] != task_id:
            logger.error(f"작업 ID {task_id}가 현재 작업과 일치하지 않습니다.")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": "작업을 찾을 수 없습니다.",
                "agent_id": self.agent_id
            }
        
        # 작업 시작
        logger.info(f"ReAct 작업 실행: {task_id}")
        self.status = "working"
        
        # 단계 기록
        steps = []
        
        # 작업 설명
        task_description = self.current_task["description"]
        
        # ReAct 반복
        iteration = 0
        final_answer = None
        
        while iteration < self.max_iterations and not final_answer:
            iteration += 1
            logger.info(f"ReAct 반복 {iteration}/{self.max_iterations}")
            
            # 1. 추론 단계 (Reasoning)
            thought = await self._think(task_description, steps)
            steps.append({"type": "thought", "content": thought})
            self.last_action = f"Thinking: {thought[:50]}..."
            
            # 2. 행동 단계 (Action)
            action, action_params = await self._decide_action(thought, steps)
            steps.append({"type": "action", "content": action, "parameters": action_params})
            self.last_action = f"Action: {action}"
            
            # 최종 답변인 경우
            if action == "final_answer":
                final_answer = action_params.get("answer", "No answer provided")
                break
            
            # 3. 도구 실행 및 결과 획득
            if action in self.tools:
                try:
                    result = await self.tools[action](**action_params)
                    steps.append({"type": "result", "content": result})
                    self.last_action = f"Got result from {action}"
                except Exception as e:
                    error_msg = f"도구 실행 오류 ({action}): {str(e)}"
                    logger.error(error_msg)
                    steps.append({"type": "error", "content": error_msg})
                    self.last_action = f"Error in {action}"
            else:
                error_msg = f"알 수 없는 도구: {action}"
                logger.error(error_msg)
                steps.append({"type": "error", "content": error_msg})
                self.last_action = "Unknown tool error"
        
        # 작업 완료
        self.status = "idle"
        self.current_task["status"] = "completed"
        
        # 결과 반환
        return {
            "task_id": task_id,
            "status": "completed" if final_answer else "incomplete",
            "steps": steps,
            "final_answer": final_answer,
            "agent_id": self.agent_id,
            "iterations": iteration
        }
    
    async def _think(self, task_description: str, steps: List[Dict[str, Any]]) -> str:
        """
        추론 단계
        
        Args:
            task_description: 작업 설명
            steps: 지금까지의 단계
            
        Returns:
            사고 내용
        """
        # 실제 구현에서는 LLM API 호출
        logger.info("추론 단계 실행")
        
        # 샘플 응답
        if not steps:
            return f"작업을 이해해보자. 작업은 '{task_description}'이다. 먼저 무엇을 해야할지 파악해야 한다."
        
        last_step = steps[-1]
        if last_step["type"] == "result":
            return f"결과를 분석해보자. {last_step['content']}. 다음 단계를 결정해야 한다."
        
        return "지금까지의 정보를 바탕으로, 다음 단계로 최종 답변을 제시해야 겠다."
    
    async def _decide_action(self, thought: str, steps: List[Dict[str, Any]]) -> tuple:
        """
        행동 결정 단계
        
        Args:
            thought: 사고 내용
            steps: 지금까지의 단계
            
        Returns:
            (행동, 매개변수) 튜플
        """
        # 실제 구현에서는 LLM API 호출
        logger.info("행동 결정 단계 실행")
        
        # 샘플 응답
        if len(steps) < 2:
            return "web_search", {"query": "테스트 검색어"}
        
        if len(steps) < 4:
            return "code_execution", {"code": "print('Hello, world!')", "language": "python"}
        
        # 최종 답변
        return "final_answer", {"answer": "이것이 ReAct 에이전트의 샘플 최종 답변입니다."}


async def execute_task(task_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    ReAct 에이전트로 작업 실행
    
    Args:
        task_id: 작업 ID
        config: 에이전트 구성
        
    Returns:
        작업 실행 결과
    """
    # 샘플 작업 데이터
    task_data = {
        "id": task_id,
        "description": "샘플 작업 설명입니다.",
        "parameters": {},
        "status": "assigned",
        "created_at": datetime.utcnow().isoformat()
    }
    
    # ReAct 에이전트 생성
    agent = ReActAgent(config=config)
    
    # 작업 할당
    agent.current_task = task_data
    
    # 작업 실행
    result = await agent.execute_task(task_id)
    
    return result
