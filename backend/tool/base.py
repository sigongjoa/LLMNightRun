"""
LLMNightRun 도구 기본 모듈

에이전트가 사용하는 도구의 기본 클래스와 도구 컬렉션을 정의합니다.
"""

import asyncio
import inspect
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field, create_model

from backend.logger import get_logger
from backend.schema import FunctionDefinition, ToolResult


logger = get_logger(__name__)


class BaseTool(ABC):
    """도구 기본 추상 클래스
    
    모든 도구의 기본 인터페이스를 정의합니다.
    """
    
    name: str = "base_tool"
    description: str = "기본 도구 클래스"
    
    @abstractmethod
    async def execute(self, **kwargs) -> Union[ToolResult, str]:
        """도구 실행
        
        Args:
            **kwargs: 도구 호출 인자
            
        Returns:
            ToolResult 또는 str: 실행 결과
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """도구 스키마 정의
        
        Returns:
            Dict[str, Any]: 도구 스키마 정보
        """
        schema = {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema(),
        }
        return schema
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """도구 인자 스키마 생성
        
        Returns:
            Dict[str, Any]: 인자 스키마
        """
        try:
            # 실행 메서드 시그니처 분석
            sig = inspect.signature(self.execute)
            
            # 기본 스키마
            schema = {
                "type": "object",
                "properties": {},
                "required": [],
            }
            
            # 인자 반복 처리
            for name, param in sig.parameters.items():
                # self 또는 **kwargs 무시
                if name == "self" or param.kind == param.VAR_KEYWORD:
                    continue
                
                # 인자 타입 추정 (어노테이션이 있는 경우)
                param_type = "string"  # 기본값
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == str:
                        param_type = "string"
                    elif param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == list or param.annotation == List:
                        param_type = "array"
                    elif param.annotation == dict or param.annotation == Dict:
                        param_type = "object"
                
                # 인자 정보 추가
                schema["properties"][name] = {"type": param_type}
                
                # 필수 인자 여부
                if param.default == inspect.Parameter.empty:
                    schema["required"].append(name)
            
            return schema
        
        except Exception as e:
            logger.error(f"인자 스키마 생성 중 오류 발생: {e}")
            return {"type": "object", "properties": {}}
    
    async def cleanup(self) -> None:
        """도구 사용 후 정리 작업
        
        일부 도구는 이 메서드를 오버라이드하여 자원을 정리할 수 있습니다.
        """
        pass


class ToolCollection:
    """도구 컬렉션
    
    여러 도구를 관리하고 실행하는 컬렉션 클래스입니다.
    """
    
    def __init__(self, *tools: BaseTool):
        """도구 컬렉션 초기화
        
        Args:
            *tools: 도구 인스턴스들
        """
        self.tool_map: Dict[str, BaseTool] = {}
        
        # 도구 추가
        for tool in tools:
            self.add_tool(tool)
    
    def add_tool(self, tool: BaseTool) -> None:
        """도구 추가
        
        Args:
            tool: 추가할 도구 인스턴스
        """
        self.tool_map[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """이름으로 도구 검색
        
        Args:
            name: 도구 이름
            
        Returns:
            BaseTool 또는 None: 찾은 도구 또는 None (없는 경우)
        """
        return self.tool_map.get(name)
    
    def to_params(self) -> List[Dict[str, Any]]:
        """LLM API 호출용 도구 파라미터 목록
        
        Returns:
            List[Dict[str, Any]]: 도구 파라미터 목록
        """
        tools = []
        for name, tool in self.tool_map.items():
            try:
                schema = tool.get_schema()
                tools.append({
                    "type": "function",
                    "function": {
                        "name": schema["name"],
                        "description": schema["description"],
                        "parameters": schema["parameters"],
                    }
                })
            except Exception as e:
                logger.error(f"도구 '{name}' 스키마 생성 중 오류: {e}")
        return tools
    
    async def execute(self, name: str, tool_input: Dict[str, Any]) -> Any:
        """도구 실행
        
        Args:
            name: 도구 이름
            tool_input: 도구 입력 인자
            
        Returns:
            Any: 실행 결과
            
        Raises:
            ValueError: 알 수 없는 도구나 잘못된 인자인 경우
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"알 수 없는 도구: {name}")
        
        try:
            result = await tool.execute(**tool_input)
            return result
        except Exception as e:
            logger.error(f"도구 '{name}' 실행 중 오류: {e}")
            return ToolResult(output="", error=f"실행 오류: {str(e)}")
    
    async def cleanup(self) -> None:
        """모든 도구 정리
        
        모든 도구의 cleanup 메서드를 호출합니다.
        """
        for name, tool in self.tool_map.items():
            try:
                if hasattr(tool, "cleanup") and callable(tool.cleanup):
                    await tool.cleanup()
            except Exception as e:
                logger.error(f"도구 '{name}' 정리 중 오류: {e}")