from fastapi import APIRouter, Body, Depends, Path
from typing import Dict, Any, List
from urllib.parse import unquote

from backend.services.manus_service import ManusAgentService

router = APIRouter(prefix="/api/manus", tags=["Manus Agent"])

# 싱글톤 서비스 제공
_manus_service = None

def get_manus_service():
    global _manus_service
    if _manus_service is None:
        _manus_service = ManusAgentService()
    return _manus_service

@router.get("/resources")
async def get_resources(service: ManusAgentService = Depends(get_manus_service)):
    """사용 가능한 리소스 목록 조회"""
    return await service.list_resources()

@router.get("/resource/{uri:path}")
async def get_resource(uri: str, service: ManusAgentService = Depends(get_manus_service)):
    """특정 리소스 읽기"""
    uri = unquote(uri)
    return await service.read_resource(uri)

@router.get("/tools")
async def get_tools(service: ManusAgentService = Depends(get_manus_service)):
    """사용 가능한 도구 목록 조회"""
    return await service.list_tools()

@router.post("/tools/{name}")
async def call_tool(name: str, arguments: Dict[str, Any] = Body(...), service: ManusAgentService = Depends(get_manus_service)):
    """도구 호출"""
    return await service.call_tool(name, arguments)

@router.get("/prompts")
async def get_prompts(service: ManusAgentService = Depends(get_manus_service)):
    """사용 가능한 프롬프트 목록 조회"""
    return await service.list_prompts()

@router.post("/prompts/{name}")
async def execute_prompt(name: str, arguments: Dict[str, Any] = Body(...), service: ManusAgentService = Depends(get_manus_service)):
    """프롬프트 실행"""
    return await service.get_prompt(name, arguments)
