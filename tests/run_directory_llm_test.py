"""
MCP 디렉토리 조회 및 LLM 통합 테스트

LLM이 MCP를 통해 파일 시스템 정보를 얻고 이를 활용할 수 있는지 테스트합니다.
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime

# 프로젝트 루트 디렉토리 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

from mcp.handler import MCPHandler
from mcp.protocol import MCPMessage, MCPMessageType, MCPFunctionCall
from local_llm.api import LocalLLMChatRequest, Message, chat

# 로깅 설정
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('directory_llm_test')

class DirectoryLLMTest:
    """디렉토리 정보를 LLM과 통합 테스트하는 클래스"""
    
    def __init__(self):
        """초기화"""
        # MCP 핸들러 생성
        self.mcp_handler = MCPHandler()
        
        # LLM 채팅 함수 등록
        self.mcp_handler.register_function("llm_chat", self._llm_chat_function)
        
        logger.info(f"MCP 핸들러 초기화 완료. 등록된 함수: {list(self.mcp_handler.registered_functions.keys())}")
    
    async def _llm_chat_function(self, prompt, system_message=None, temperature=0.7, max_tokens=1000):
        """
        Local LLM 채팅 처리 함수
        """
        logger.info(f"Local LLM 호출 시작: prompt='{prompt[:50]}...'")
        
        try:
            # LocalLLMChatRequest 생성
            request = LocalLLMChatRequest(
                messages=[Message(role="user", content=prompt)],
                system_message=system_message,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 실제 API 호출
            response = await chat(request)
            
            # 결과 반환
            if response and hasattr(response, 'content'):
                logger.info(f"Local LLM 호출 성공: {len(response.content)} 문자")
                return {
                    "success": True,
                    "content": response.content,
                    "model_id": response.model_id
                }
            else:
                logger.error(f"Local LLM 호출 실패: 응답 형식 {type(response)}")
                return {
                    "success": False,
                    "error": f"올바르지 않은 응답 형식: {type(response)}"
                }
        except Exception as e:
            logger.error(f"Local LLM 호출 오류: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_directory_listing_with_llm(self, directory_path):
        """
        디렉토리 목록을 조회하고 LLM에게 해석하도록 요청
        """
        logger.info(f"===== 디렉토리 목록 및 LLM 해석 테스트 시작: {directory_path} =====")
        
        # 1. 디렉토리 목록 조회
        logger.info(f"1. 디렉토리 목록 조회: {directory_path}")
        list_message = MCPMessage(
            type=MCPMessageType.FUNCTION_CALL,
            content=MCPFunctionCall(
                name="list_directory",
                arguments={"path": directory_path},
                call_id="dir-list-1"
            ),
            request_id="req-dir-1"
        )
        
        # 디렉토리 목록 가져오기
        try:
            list_result = await asyncio.wait_for(
                self.mcp_handler.handle_message(list_message.model_dump()),
                timeout=10.0
            )
            
            # 결과 확인
            if (list_result["type"] != "function_response" or 
                not list_result["content"]["result"]["success"]):
                logger.error(f"디렉토리 목록 조회 실패: {list_result.get('content', {}).get('result', {}).get('error', '알 수 없는 오류')}")
                return False
            
            dir_content = list_result["content"]["result"]
            logger.info(f"디렉토리 목록 조회 성공: {dir_content['total_items']} 항목")
            
            # 2. 목록을 LLM에게 보내기
            logger.info("2. 디렉토리 목록 정보를 LLM에게 보내는 중...")
            
            # 목록 정보를 텍스트로 정리
            dir_info = f"Directory: {dir_content['path']}\n\n"
            dir_info += "Folders:\n"
            for d in dir_content['directories']:
                dir_info += f"- {d['name']}\n"
            
            dir_info += "\nFiles:\n"
            for f in dir_content['files']:
                size_kb = f['size'] / 1024
                dir_info += f"- {f['name']} ({size_kb:.1f} KB)\n"
            
            # LLM에게 디렉토리 내용 설명 요청
            prompt = f"""Please analyze this directory listing and provide the following information:
1. Briefly summarize what types of files and folders are present
2. Identify any patterns in the file/folder naming
3. Suggest what this directory might be used for based on its contents

Directory information:
{dir_info}

Please keep your response concise but informative.
"""
            
            llm_message = MCPMessage(
                type=MCPMessageType.FUNCTION_CALL,
                content=MCPFunctionCall(
                    name="llm_chat",
                    arguments={
                        "prompt": prompt,
                        "system_message": "You are a helpful AI assistant with expertise in file systems and software development.",
                        "temperature": 0.3
                    },
                    call_id="llm-dir-1"
                ),
                request_id="req-llm-1"
            )
            
            # LLM 호출
            logger.info("LLM 호출 중... (최대 120초 대기)")
            start_time = datetime.now()
            
            try:
                llm_result = await asyncio.wait_for(
                    self.mcp_handler.handle_message(llm_message.model_dump()),
                    timeout=120.0  # 2분
                )
                
                end_time = datetime.now()
                elapsed = (end_time - start_time).total_seconds()
                logger.info(f"LLM 응답 완료. 소요 시간: {elapsed:.2f}초")
                
                # 응답 확인
                if llm_result["type"] != "function_response" or not llm_result["content"]["result"]["success"]:
                    logger.error("LLM 응답 실패")
                    return False
                
                # 응답 내용 출력
                llm_content = llm_result["content"]["result"]["content"]
                logger.info(f"\nLLM 디렉토리 분석 결과:\n{'-'*50}\n{llm_content}\n{'-'*50}")
                
                return {
                    "success": True,
                    "directory_info": dir_content,
                    "llm_analysis": llm_content,
                    "elapsed_seconds": elapsed
                }
                
            except asyncio.TimeoutError:
                logger.error("LLM 응답 타임아웃 (120초 초과)")
                return False
                
        except Exception as e:
            logger.error(f"테스트 중 오류 발생: {str(e)}")
            return False
    
    async def test_file_search_with_llm(self, directory_path, search_pattern):
        """
        파일 검색 후 결과를 LLM에게 분석 요청
        """
        logger.info(f"===== 파일 검색 및 LLM 분석 테스트 시작: {directory_path}, 패턴: {search_pattern} =====")
        
        # 1. 파일 검색
        logger.info(f"1. 파일 검색: {directory_path}, 패턴: {search_pattern}")
        search_message = MCPMessage(
            type=MCPMessageType.FUNCTION_CALL,
            content=MCPFunctionCall(
                name="search_files",
                arguments={
                    "path": directory_path,
                    "pattern": search_pattern,
                    "recursive": True
                },
                call_id="search-1"
            ),
            request_id="req-search-1"
        )
        
        # 검색 실행
        try:
            search_result = await asyncio.wait_for(
                self.mcp_handler.handle_message(search_message.model_dump()),
                timeout=30.0
            )
            
            # 결과 확인
            if (search_result["type"] != "function_response" or 
                not search_result["content"]["result"]["success"]):
                logger.error(f"파일 검색 실패: {search_result.get('content', {}).get('result', {}).get('error', '알 수 없는 오류')}")
                return False
            
            search_content = search_result["content"]["result"]
            logger.info(f"검색 성공: {search_content['total_matches']} 항목 찾음")
            
            # 검색 결과가 없으면
            if search_content['total_matches'] == 0:
                logger.info(f"패턴 '{search_pattern}'에 일치하는 항목이.없습니다.")
                return {
                    "success": True,
                    "search_pattern": search_pattern,
                    "matches": 0,
                    "message": "No matches found"
                }
            
            # 2. 검색 결과를 LLM에게 보내기
            logger.info("2. 검색 결과를 LLM에게 분석 요청...")
            
            # 검색 결과를 텍스트로 정리
            search_info = f"Search in: {search_content['path']}\n"
            search_info += f"Pattern: '{search_content['pattern']}'\n"
            search_info += f"Matches: {search_content['total_matches']}\n\n"
            
            search_info += "Results:\n"
            # 최대 20개만 표시
            for i, item in enumerate(search_content['results'][:20]):
                if item['type'] == 'directory':
                    search_info += f"{i+1}. [DIR] {item['name']} - {item['path']}\n"
                else:
                    size_kb = item.get('size', 0) / 1024
                    search_info += f"{i+1}. [FILE] {item['name']} - {item['path']} ({size_kb:.1f} KB)\n"
            
            if search_content['total_matches'] > 20:
                search_info += f"\n... and {search_content['total_matches'] - 20} more items"
            
            # LLM에게 검색 결과 분석 요청
            prompt = f"""Please analyze these search results and provide insights:
1. What types of files or directories match the search pattern '{search_pattern}'?
2. Are there any notable patterns in where these files are located?
3. Based on the matches, what might be the purpose or significance of these files?

Search results:
{search_info}

Please keep your response concise and focus on the most insightful observations.
"""
            
            llm_message = MCPMessage(
                type=MCPMessageType.FUNCTION_CALL,
                content=MCPFunctionCall(
                    name="llm_chat",
                    arguments={
                        "prompt": prompt,
                        "system_message": "You are a helpful AI assistant with expertise in file systems and software development.",
                        "temperature": 0.3
                    },
                    call_id="llm-search-1"
                ),
                request_id="req-llm-search-1"
            )
            
            # LLM 호출
            logger.info("LLM 호출 중... (최대 120초 대기)")
            start_time = datetime.now()
            
            try:
                llm_result = await asyncio.wait_for(
                    self.mcp_handler.handle_message(llm_message.model_dump()),
                    timeout=120.0  # 2분
                )
                
                end_time = datetime.now()
                elapsed = (end_time - start_time).total_seconds()
                logger.info(f"LLM 응답 완료. 소요 시간: {elapsed:.2f}초")
                
                # 응답 확인
                if llm_result["type"] != "function_response" or not llm_result["content"]["result"]["success"]:
                    logger.error("LLM 응답 실패")
                    return False
                
                # 응답 내용 출력
                llm_content = llm_result["content"]["result"]["content"]
                logger.info(f"\nLLM 검색 결과 분석:\n{'-'*50}\n{llm_content}\n{'-'*50}")
                
                return {
                    "success": True,
                    "search_pattern": search_pattern,
                    "search_results": search_content,
                    "llm_analysis": llm_content,
                    "elapsed_seconds": elapsed
                }
                
            except asyncio.TimeoutError:
                logger.error("LLM 응답 타임아웃 (120초 초과)")
                return False
                
        except Exception as e:
            logger.error(f"테스트 중 오류 발생: {str(e)}")
            return False


async def run_tests():
    """테스트 실행"""
    logger.info("디렉토리 및 LLM 통합 테스트 시작")
    logger.info("=" * 60)
    
    tester = DirectoryLLMTest()
    
    # D 드라이브 목록 테스트
    logger.info("D 드라이브 목록 테스트 시작")
    d_drive_result = await tester.test_directory_listing_with_llm("D:\\")
    
    # LLMNightRun_feature 디렉토리 검색 테스트
    logger.info("\nLLMNightRun_feature 디렉토리 내 'test' 검색 테스트 시작")
    search_result = await tester.test_file_search_with_llm("D:\\LLMNightRun_feature", "test")
    
    # 테스트 결과 요약
    logger.info("\n" + "=" * 60)
    logger.info("테스트 결과 요약")
    logger.info("=" * 60)
    logger.info(f"1. D 드라이브 목록 분석: {'성공' if d_drive_result else '실패'}")
    logger.info(f"2. 파일 검색 및 분석: {'성공' if search_result else '실패'}")
    
    return d_drive_result and search_result


if __name__ == "__main__":
    # 테스트 실행
    success = asyncio.run(run_tests())
    
    # 종료 코드 설정
    sys.exit(0 if success else 1)
