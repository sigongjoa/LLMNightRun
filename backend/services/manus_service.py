from typing import Dict, Any, List, Optional
import httpx
import os
import json
from fastapi import HTTPException
from urllib.parse import quote

class ManusAgentService:
    def __init__(self):
        self.base_url = os.getenv("MANUS_API_URL", "http://localhost:8000/manus/mcp")
    
    async def initialize(self, version: str, capabilities: Dict[str, Any]):
        """Manus MCP 서버 초기화"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/initialize",
                json={"version": version, "capabilities": capabilities}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """사용 가능한 리소스 목록 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/resources/list")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            result = response.json()
            return result.get("resources", [])
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """특정 리소스 읽기"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/resources/read",
                json={"uri": uri}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/tools/list")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            result = response.json()
            return result.get("tools", [])
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """도구 호출"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tools/call",
                json={"name": name, "arguments": arguments}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
    
    async def list_prompts(self) -> List[Dict[str, Any]]:
        """사용 가능한 프롬프트 목록 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/prompts/list")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            result = response.json()
            return result.get("prompts", [])
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """프롬프트 가져오기"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/prompts/get",
                json={"name": name, "arguments": arguments}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            return response.json()
