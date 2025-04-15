"""
MCP와 Local LLM 통합 테스트

MCP와 실제 Local LLM 서버 간의 통합을 테스트합니다.
"""

import os
import sys
import asyncio
import json
import tempfile
import logging
from datetime import datetime

# 프로젝트 루트 디렉토리 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)

# 이제 mcp와 local_llm 모듈을 가져올 수 있습니다
from mcp.handler import MCPHandler
from mcp.protocol import MCPMessage, MCPMessageType, MCPFunctionCall
from local_llm.api import LocalLLMChatRequest, Message

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('integration_test')

class LocalLLMMCPIntegrationTest:
    """MCP와 Local LLM 통합 테스트 클래스"""
    
    def __init__(self):
        """초기화"""
        # 임시 디렉토리 생성 (테스트 파일용)
        self.temp_dir = tempfile.TemporaryDirectory()
        logger.info(f"임시 디렉토리 생성: {self.temp_dir.name}")
        
        # MCP 핸들러 생성
        self.mcp_handler = MCPHandler(config_dir=self.temp_dir.name)
        
        # Local LLM 채팅 함수 등록
        self.mcp_handler.register_function("llm_chat", self._llm_chat_function)
        
        logger.info(f"MCP 핸들러 초기화 완료. 등록된 함수: {list(self.mcp_handler.registered_functions.keys())}")
        
        # 테스트 결과 저장
        self.results = {}
    
    # Local LLM 채팅 함수 구현
    async def _llm_chat_function(self, prompt, system_message=None, temperature=0.7, max_tokens=1000):
        """
        Local LLM 채팅 처리
        
        Args:
            prompt: 질문 내용
            system_message: 시스템 메시지
            temperature: 온도 설정
            max_tokens: 최대 토큰 수
            
        Returns:
            채팅 응답 결과
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
            from local_llm.api import chat
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
                logger.error(f"Local LLM 호출 실패: 잔료 형식 {type(response)}")
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

    def cleanup(self):
        """리소스 정리"""
        logger.info(f"임시 디렉토리 삭제: {self.temp_dir.name}")
        self.temp_dir.cleanup()

    async def test_llm_chat_via_mcp(self):
        """MCP를 통한 LLM 채팅 테스트"""
        logger.info("====== MCP를 통한 LLM 채팅 테스트 시작 ======")
        
        test_prompt = "한국어로 간단한 인사말을 해주세요."
        system_message = "당신은 도움이 되는 AI 비서입니다. 짧고 간결하게 답변해주세요."
        temperature = 0.7
        
        logger.info(f"요청 메시지: '{test_prompt}'")
        logger.info(f"시스템 메시지: '{system_message}'")
        logger.info(f"온도 설정: {temperature}")
        
        # MCP 메시지 생성
        message = MCPMessage(
            type=MCPMessageType.FUNCTION_CALL,
            content=MCPFunctionCall(
                name="llm_chat",
                arguments={
                    "prompt": test_prompt,
                    "system_message": system_message,
                    "temperature": temperature
                },
                call_id="integration-test-1"
            ),
            request_id="req-integration-1"
        )
        
        # 메시지 출력
        logger.info("MCP 메시지:")
        logger.info(json.dumps(message.model_dump(), indent=2, ensure_ascii=False))
        
        try:
            # MCP 메시지 처리
            logger.info("MCP 메시지 처리 시작...")
            start_time = datetime.now()
            
            # 대기 시간 늘리기 (120초)
            result = await asyncio.wait_for(
                self.mcp_handler.handle_message(message.model_dump()),
                timeout=120.0  # 2분
            )
            
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()
            logger.info(f"MCP 메시지 처리 완료. 소요 시간: {elapsed:.2f}초")
            
            # 응답 출력
            logger.info("응답 결과:")
            logger.info(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 결과 확인
            if result["type"] == "function_response" and result["content"]["result"]["success"]:
                content = result["content"]["result"]["content"]
                model_id = result["content"]["result"]["model_id"]
                logger.info(f"테스트 성공! LLM 응답 내용: {content}")
                logger.info(f"사용된 모델: {model_id}")
                
                # 결과 저장
                self.results["test_llm_chat_via_mcp"] = {
                    "success": True,
                    "prompt": test_prompt,
                    "response": content,
                    "model_id": model_id,
                    "elapsed_seconds": elapsed
                }
                
                return True
            else:
                error = result.get("content", {}).get("result", {}).get("error", "알 수 없는 오류")
                logger.error(f"테스트 실패: {error}")
                
                # 결과 저장
                self.results["test_llm_chat_via_mcp"] = {
                    "success": False,
                    "error": error
                }
                
                return False
                
        except Exception as e:
            logger.error(f"테스트 중 예외 발생: {str(e)}")
            
            # 결과 저장
            self.results["test_llm_chat_via_mcp"] = {
                "success": False,
                "error": str(e)
            }
            
            return False

    async def test_file_edit_with_llm_context(self):
        """Local LLM 컨텍스트를 사용한 파일 편집 테스트"""
        logger.info("====== Local LLM 컨텍스트로 파일 편집 테스트 시작 ======")
        
        # 테스트 파일 생성
        test_file_path = os.path.join(self.temp_dir.name, "test_content.txt")
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("이 파일은 LLM의 도움을 받아 편집될 예정입니다.\n이 줄은 편집될 예정입니다.\n이 줄은 유지됩니다.")
        
        logger.info(f"테스트 파일 생성: {test_file_path}")
        
        # 컨텍스트 생성
        context_id = self.mcp_handler.create_context({
            "name": "llm-editing-context",
            "description": "파일 편집 컨텍스트"
        })
        
        logger.info(f"MCP 컨텍스트 생성: ID={context_id}")
        
        # 먼저 LLM에게 어떻게 텍스트를 수정할지 물어보기
        logger.info("LLM에게 텍스트 수정 방법 질문하기")
        
        llm_query_message = MCPMessage(
            type=MCPMessageType.FUNCTION_CALL,
            content=MCPFunctionCall(
                name="llm_chat",
                arguments={
                    "prompt": "다음 텍스트를 더 전문적으로 수정해주세요: '이 줄은 편집될 예정입니다.'",
                    "system_message": "당신은 전문적인 텍스트 에디터입니다. 주어진 텍스트를 더 전문적이고 명확하게 수정해주세요.",
                    "temperature": 0.5
                },
                call_id="llm-edit-suggestion"
            ),
            request_id="req-integration-2"
        )
        
        # LLM 호출
        logger.info("LLM 호출 중... (최대 120초 대기)")
        start_time = datetime.now()
        
        try:
            # 대기 시간 늘리기 (120초)
            llm_response = await asyncio.wait_for(
                self.mcp_handler.handle_message(llm_query_message.model_dump()),
                timeout=120.0  # 2분
            )
            
            end_time = datetime.now()
            elapsed_llm = (end_time - start_time).total_seconds()
            logger.info(f"LLM 응답 완료. 소요 시간: {elapsed_llm:.2f}초")
        except asyncio.TimeoutError:
            logger.error("LLM 응답 타임아웃 (120초 초과)")
            self.results["test_file_edit_with_llm_context"] = {
                "success": False,
                "error": "LLM 응답 타임아웃"
            }
            return False
        
        # LLM 응답 확인
        if llm_response["type"] != "function_response" or not llm_response["content"]["result"]["success"]:
            logger.error("LLM 응답 실패")
            self.results["test_file_edit_with_llm_context"] = {
                "success": False,
                "error": "LLM 응답 실패"
            }
            return False
        
        # LLM 제안 추출
        suggested_text = llm_response["content"]["result"]["content"]
        logger.info(f"LLM 제안 텍스트: '{suggested_text}'")
        
        # 파일 편집 수행
        edit_message = MCPMessage(
            type=MCPMessageType.FUNCTION_CALL,
            content=MCPFunctionCall(
                name="edit_file",
                arguments={
                    "path": test_file_path,
                    "old_text": "이 줄은 편집될 예정입니다.",
                    "new_text": suggested_text
                },
                call_id="integration-file-edit"
            ),
            request_id="req-integration-3"
        )
        
        # 파일 편집 호출
        logger.info("MCP를 통한 파일 편집 실행 중... (최대 30초 대기)")
        start_time = datetime.now()
        
        try:
            # 대기 시간 늘리기 (30초)
            edit_result = await asyncio.wait_for(
                self.mcp_handler.handle_message(edit_message.model_dump()),
                timeout=30.0
            )
            
            end_time = datetime.now()
            elapsed_edit = (end_time - start_time).total_seconds()
            logger.info(f"파일 편집 완료. 소요 시간: {elapsed_edit:.2f}초")
        except asyncio.TimeoutError:
            logger.error("파일 편집 타임아웃 (30초 초과)")
            self.results["test_file_edit_with_llm_context"] = {
                "success": False,
                "error": "파일 편집 타임아웃"
            }
            return False
        
        # 편집 결과 확인
        if edit_result["type"] != "function_response" or not edit_result["content"]["result"]["success"]:
            logger.error("파일 편집 실패")
            self.results["test_file_edit_with_llm_context"] = {
                "success": False,
                "error": "파일 편집 실패"
            }
            return False
        
        # 변경된 파일 내용 확인
        with open(test_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()
        
        logger.info(f"편집 후 파일 내용:\n{'-' * 40}\n{updated_content}\n{'-' * 40}")
        logger.info(f"편집 Diff 정보:\n{edit_result['content']['result']['diff']}")
        
        # 검증: 제안된 텍스트가 파일에 있는지 확인
        if suggested_text in updated_content:
            logger.info("테스트 성공! LLM 제안 텍스트가 파일에 반영됨")
            self.results["test_file_edit_with_llm_context"] = {
                "success": True,
                "original_text": "이 줄은 편집될 예정입니다.",
                "suggested_text": suggested_text,
                "file_path": test_file_path,
                "elapsed_llm_seconds": elapsed_llm,
                "elapsed_edit_seconds": elapsed_edit
            }
            return True
        else:
            logger.error("테스트 실패: LLM 제안 텍스트가 파일에 반영되지 않음")
            self.results["test_file_edit_with_llm_context"] = {
                "success": False,
                "error": "LLM 제안 텍스트가 파일에 반영되지 않음"
            }
            return False

async def run_tests():
    """테스트 실행"""
    logger.info("MCP-Local LLM 통합 테스트 시작")
    logger.info("=" * 60)
    
    # 테스트 객체 생성
    tester = LocalLLMMCPIntegrationTest()
    
    try:
        # 테스트 실행
        chat_test_result = await tester.test_llm_chat_via_mcp()
        file_edit_test_result = await tester.test_file_edit_with_llm_context()
        
        # 결과 요약
        logger.info("\n" + "=" * 60)
        logger.info("통합 테스트 결과 요약")
        logger.info("=" * 60)
        logger.info(f"1. MCP를 통한 LLM 채팅: {'성공' if chat_test_result else '실패'}")
        logger.info(f"2. LLM 컨텍스트를 사용한 파일 편집: {'성공' if file_edit_test_result else '실패'}")
        logger.info(f"전체 결과: {'모두 성공' if all([chat_test_result, file_edit_test_result]) else '일부 실패'}")
        
        # 자세한 결과
        logger.info("\n자세한 테스트 결과:")
        logger.info(json.dumps(tester.results, indent=2, ensure_ascii=False))
        
        return all([chat_test_result, file_edit_test_result])
    
    finally:
        # 리소스 정리
        tester.cleanup()


if __name__ == "__main__":
    # 테스트 실행
    success = asyncio.run(run_tests())
    
    # 종료 코드 설정
    sys.exit(0 if success else 1)
