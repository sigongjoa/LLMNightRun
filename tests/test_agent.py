"""
에이전트 시스템 테스트

에이전트 시스템의 기능을 테스트합니다.
"""

import unittest
import asyncio
import json
from unittest.mock import patch, MagicMock

# 테스트 대상 모듈 임포트
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent.base import BaseAgent, create_agent, assign_task
from agent.react import ReActAgent, execute_task


class TestAgentSystem(unittest.TestCase):
    """에이전트 시스템 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 비동기 이벤트 루프 설정
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # 테스트 데이터 설정
        self.test_agent_data = {
            "name": "테스트 에이전트",
            "type": "task",
            "description": "테스트용 작업 에이전트",
            "config": {
                "model": "gpt-4",
                "max_iterations": 5,
                "tools": ["web_search", "code_execution"]
            }
        }
        
        self.test_task_data = {
            "description": "테스트 작업입니다.",
            "parameters": {
                "priority": "high",
                "deadline": "2023-12-31"
            }
        }
    
    def tearDown(self):
        """테스트 정리"""
        self.loop.close()
    
    def test_create_agent(self):
        """에이전트 생성 테스트"""
        # 함수 호출
        result = create_agent(self.test_agent_data)
        
        # 결과 검증
        self.assertIsNotNone(result["id"])
        self.assertEqual(result["name"], "테스트 에이전트")
        self.assertEqual(result["type"], "task")
        self.assertEqual(result["status"], "idle")
        self.assertIn("config", result)
    
    def test_base_agent_initialization(self):
        """기본 에이전트 초기화 테스트"""
        # 에이전트 생성
        agent = BaseAgent(
            name="테스트 에이전트",
            config={"model": "gpt-4", "max_iterations": 5}
        )
        
        # 검증
        self.assertIsNotNone(agent.agent_id)
        self.assertEqual(agent.name, "테스트 에이전트")
        self.assertEqual(agent.status, "idle")
        self.assertIsNone(agent.current_task)
        
        # 도구 등록 확인
        self.assertIn("web_search", agent.tools)
        self.assertIn("code_execution", agent.tools)
        self.assertIn("read_file", agent.tools)
        self.assertIn("write_file", agent.tools)
    
    def test_assign_task(self):
        """작업 할당 테스트"""
        # 에이전트 생성
        agent_result = create_agent(self.test_agent_data)
        agent_id = agent_result["id"]
        
        # 함수 호출
        result = assign_task(agent_id, self.test_task_data)
        
        # 결과 검증
        self.assertIsNotNone(result["task_id"])
        self.assertEqual(result["status"], "assigned")
        self.assertEqual(result["agent_id"], agent_id)
    
    @patch('agent.base.BaseAgent.assign_task')
    @patch('agent.base.BaseAgent.execute_task')
    async def test_base_agent_task_flow(self, mock_execute, mock_assign):
        """기본 에이전트 작업 흐름 테스트"""
        # 모의 응답 설정
        task_id = "test-task-1"
        mock_assign.return_value = {
            "task_id": task_id,
            "status": "assigned",
            "agent_id": "test-agent-1",
            "estimated_completion": None
        }
        
        mock_execute.return_value = {
            "task_id": task_id,
            "status": "completed",
            "result": "작업이 성공적으로 완료되었습니다.",
            "agent_id": "test-agent-1"
        }
        
        # 에이전트 생성
        agent = BaseAgent(
            agent_id="test-agent-1",
            name="테스트 에이전트",
            config={"model": "gpt-4"}
        )
        
        # 작업 할당
        assign_result = await agent.assign_task(self.test_task_data)
        
        # 작업 실행
        execute_result = await agent.execute_task(task_id)
        
        # 결과 검증
        self.assertEqual(assign_result["task_id"], task_id)
        self.assertEqual(assign_result["status"], "assigned")
        
        self.assertEqual(execute_result["task_id"], task_id)
        self.assertEqual(execute_result["status"], "completed")
        self.assertEqual(execute_result["agent_id"], "test-agent-1")
    
    def test_react_agent_initialization(self):
        """ReAct 에이전트 초기화 테스트"""
        # 에이전트 생성
        agent = ReActAgent(
            name="ReAct 테스트 에이전트",
            config={
                "model": "gpt-4",
                "max_iterations": 3
            }
        )
        
        # 검증
        self.assertIsNotNone(agent.agent_id)
        self.assertEqual(agent.name, "ReAct 테스트 에이전트")
        self.assertEqual(agent.status, "idle")
        self.assertEqual(agent.max_iterations, 3)
        self.assertEqual(agent.model_name, "gpt-4")
    
    @patch('agent.react.execute_task')
    def test_execute_task_function(self, mock_execute):
        """execute_task 함수 테스트"""
        # 모의 응답 설정
        task_result = {
            "task_id": "test-task-1",
            "status": "completed",
            "steps": [
                {"type": "thought", "content": "작업을 이해해봅시다."},
                {"type": "action", "content": "web_search", "parameters": {"query": "테스트 검색어"}},
                {"type": "result", "content": {"results": [{"title": "검색 결과", "url": "https://example.com"}]}},
                {"type": "thought", "content": "정보를 분석합니다."},
                {"type": "action", "content": "final_answer", "parameters": {"answer": "작업 완료했습니다."}}
            ],
            "final_answer": "작업 완료했습니다.",
            "agent_id": "test-agent-1",
            "iterations": 3
        }
        mock_execute.return_value = task_result
        
        # 함수 호출
        config = {"model": "gpt-4", "max_iterations": 3}
        result = self.loop.run_until_complete(
            execute_task("test-task-1", config)
        )
        
        # 결과 검증
        self.assertEqual(result["task_id"], "test-task-1")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["final_answer"], "작업 완료했습니다.")
        self.assertEqual(len(result["steps"]), 5)
        self.assertEqual(result["iterations"], 3)
    
    @patch('agent.react.ReActAgent._think')
    @patch('agent.react.ReActAgent._decide_action')
    @patch('agent.react.ReActAgent.web_search')
    async def test_react_agent_execution(self, mock_web_search, mock_decide_action, mock_think):
        """ReAct 에이전트 실행 테스트"""
        # 모의 함수 설정
        mock_think.side_effect = [
            "작업을 이해해봅시다.",
            "검색 결과를 분석합니다.",
            "최종 답변을 준비합니다."
        ]
        
        mock_decide_action.side_effect = [
            ("web_search", {"query": "테스트 검색어"}),
            ("code_execution", {"code": "print('Hello')", "language": "python"}),
            ("final_answer", {"answer": "테스트 작업 완료했습니다."})
        ]
        
        mock_web_search.return_value = {
            "query": "테스트 검색어",
            "results": [{"title": "테스트 결과", "url": "https://example.com"}]
        }
        
        # 에이전트 생성
        agent = ReActAgent(
            agent_id="test-agent-2",
            name="ReAct 테스트 에이전트",
            config={"model": "gpt-4", "max_iterations": 5}
        )
        
        # 테스트 작업 설정
        agent.current_task = {
            "id": "test-task-2",
            "description": "테스트 작업입니다.",
            "parameters": {},
            "status": "assigned"
        }
        
        # code_execution 도구 모킹
        agent.tools["code_execution"] = MagicMock(return_value={"output": "Hello"})
        
        # 작업 실행
        result = await agent.execute_task("test-task-2")
        
        # 결과 검증
        self.assertEqual(result["task_id"], "test-task-2")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["final_answer"], "테스트 작업 완료했습니다.")
        self.assertEqual(len(result["steps"]), 6)  # 3개의 사고, 2개의 행동, 1개의 최종 답변
        
        # 도구 호출 확인
        mock_web_search.assert_called_once_with(query="테스트 검색어")
        agent.tools["code_execution"].assert_called_once_with(
            code="print('Hello')", language="python"
        )


if __name__ == '__main__':
    unittest.main()
