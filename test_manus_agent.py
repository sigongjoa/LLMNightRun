"""
Manus 에이전트 MCP 통합 테스트 스크립트

LM Studio를 사용한 로컬 LLM 기반 Manus 에이전트와 MCP 통합 기능을 테스트합니다.
"""

import asyncio
import argparse
import json
import logging
import sys
import os

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("manus_test")

# 프로젝트 루트 디렉토리를 Python 경로에 추가
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 필요한 모듈 임포트 (프로젝트 루트 경로 추가 후)
from backend.manus.mcp_agent_integration import ManusAgentMCPIntegration
from backend.models.enums import LLMType

async def test_manus_agent(query: str, model_id: str = None, with_tools: bool = True):
    """
    Manus 에이전트를 테스트합니다.
    
    Args:
        query: 사용자 질의
        model_id: 사용할 모델 ID (기본값: None, 설정에서 가져옴)
        with_tools: 도구 사용 여부 (기본값: True)
    """
    try:
        logger.info(f"Manus 에이전트 테스트 시작 - 쿼리: '{query}', 모델: {model_id}, 도구 사용: {with_tools}")
        
        # MCP-에이전트 통합 객체 생성
        integration = ManusAgentMCPIntegration(
            llm_type=LLMType.LOCAL_LLM,
            llm_base_url="http://127.0.0.1:1234",  # LM Studio 기본 주소 (필요시 변경)
            model_id=model_id
        )
        
        # 에이전트에 쿼리 보내기
        result = await integration.process_query(query, with_tools=with_tools)
        
        # 결과 출력
        logger.info(f"응답: {result['response']}")
        
        if 'tool_calls' in result and result['tool_calls']:
            logger.info(f"도구 호출 ({len(result['tool_calls'])}개):")
            for i, tc in enumerate(result['tool_calls']):
                logger.info(f"\n도구 호출 #{i+1}:")
                logger.info(f"이름: {tc['name']}")
                logger.info(f"인자: {json.dumps(tc['arguments'], indent=2)}")
                logger.info(f"결과: {tc['result']}")
                logger.info(f"성공: {tc.get('success', False)}")
        else:
            logger.info("도구 호출 없음")
        
        return result
    
    except Exception as e:
        logger.error(f"테스트 오류: {str(e)}")
        raise e

async def test_mcp_tools():
    """MCP 도구 테스트"""
    
    try:
        integration = ManusAgentMCPIntegration(
            llm_type=LLMType.LOCAL_LLM,
            llm_base_url="http://127.0.0.1:1234",
        )
        
        # MCP 서버 인스턴스 가져오기
        mcp_server = integration.mcp_server
        
        # 도구 목록 가져오기
        tools = mcp_server.list_tools()
        logger.info(f"사용 가능한 도구 목록 ({len(tools['tools'])}개):")
        for tool in tools['tools']:
            logger.info(f"- {tool.name}: {tool.description}")
        
        # 리소스 목록 가져오기
        resources = mcp_server.list_resources()
        logger.info(f"사용 가능한 리소스 목록 ({len(resources['resources'])}개):")
        for resource in resources['resources']:
            logger.info(f"- {resource.uri}: {resource.name}")
        
        # 특정 도구 호출 테스트
        if any(tool.name == "list_directory" for tool in tools['tools']):
            logger.info("\n디렉토리 목록 도구 테스트:")
            result = mcp_server.call_tool("list_directory", {"path": "."})
            logger.info(f"결과: {json.dumps(result, indent=2)}")
        
        # 특정 리소스 읽기 테스트
        if any(resource.uri == "file://project" for resource in resources['resources']):
            logger.info("\n프로젝트 리소스 읽기 테스트:")
            result = mcp_server.read_resource("file://project")
            logger.info(f"결과: {json.dumps(result, indent=2)}")
        
        return {
            "tools": tools,
            "resources": resources
        }
    
    except Exception as e:
        logger.error(f"MCP 도구 테스트 오류: {str(e)}")
        raise e

async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Manus 에이전트 MCP 통합 테스트")
    parser.add_argument("--query", "-q", type=str, default="이 프로젝트의 구조를 분석해줘",
                      help="테스트할 쿼리")
    parser.add_argument("--model", "-m", type=str, default=None,
                      help="사용할 모델 ID")
    parser.add_argument("--no-tools", "-n", action="store_true",
                      help="도구 사용 비활성화")
    parser.add_argument("--tools-only", "-t", action="store_true",
                      help="도구만 테스트 (쿼리 없음)")
    
    args = parser.parse_args()
    
    if args.tools_only:
        await test_mcp_tools()
    else:
        await test_manus_agent(args.query, args.model, not args.no_tools)

if __name__ == "__main__":
    asyncio.run(main())
