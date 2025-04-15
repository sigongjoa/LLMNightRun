"""
MCP 파일 작업 기능 테스트

MCP handler의 파일 관련 작업 기능을 테스트합니다.
"""

import os
import sys
import tempfile
import unittest
import asyncio
import json
import difflib
import logging
from unittest.mock import patch, MagicMock, Mock
from io import StringIO

# 프로젝트 루트 디렉토리 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mcp.handler import MCPHandler
from mcp.protocol import MCPMessage, MCPMessageType, MCPFunctionCall


class TestMCPFileOperations(unittest.TestCase):
    """MCP 파일 작업 기능 테스트 클래스"""
    
    def setUp(self):
        """테스트 환경 설정"""
        # 로깅 설정
        self.log_stream = StringIO()
        handler = logging.StreamHandler(self.log_stream)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger = logging.getLogger('mcp')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        print(f"\n테스트용 임시 디렉토리 생성: {self.temp_dir.name}")
        
        # 테스트용 파일 생성
        self.test_file_path = os.path.join(self.temp_dir.name, 'test_file.txt')
        test_content = "이것은 테스트 파일입니다.\n여기에 내용을 추가합니다.\n이 줄은 유지됩니다."
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print(f"테스트 파일 생성: {self.test_file_path}")
        print(f"초기 파일 내용:\n{'-' * 40}\n{test_content}\n{'-' * 40}")
        
        # MCP 핸들러 생성
        self.mcp_handler = MCPHandler(config_dir=self.temp_dir.name)
        print(f"MCP 핸들러 초기화 완료, 등록된 함수: {list(self.mcp_handler.registered_functions.keys())}")
        
        # 비동기 이벤트 루프 생성
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """테스트 환경 정리"""
        print(f"\n테스트 환경 정리 중... 임시 디렉토리 삭제: {self.temp_dir.name}")
        self.temp_dir.cleanup()
        self.loop.close()
        
        # 로그 출력
        log_content = self.log_stream.getvalue()
        if log_content:
            print(f"\nMCP 로그:\n{'-' * 40}\n{log_content}\n{'-' * 40}")
    
    def test_edit_file_direct(self):
        """edit_file 함수 직접 호출 테스트"""
        print("\n==== test_edit_file_direct 시작 ====\n")
        
        # 원본 텍스트와 교체할 텍스트 정의
        old_text = "여기에 내용을 추가합니다."
        new_text = "이 줄은 수정되었습니다."
        
        print(f"수정 내용: '{old_text}' -> '{new_text}'")
        
        # edit_file 함수 직접 호출
        result = self.mcp_handler.edit_file(
            path=self.test_file_path,
            old_text=old_text,
            new_text=new_text
        )
        
        # 결과 출력
        print("\n함수 호출 결과:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 결과 확인
        self.assertTrue(result["success"])
        self.assertEqual(result["path"], self.test_file_path)
        self.assertIn("diff", result)
        self.assertIn("changes", result)
        self.assertEqual(result["changes"]["old_text"], old_text)
        self.assertEqual(result["changes"]["new_text"], new_text)
        
        # 파일 내용 확인
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n수정 후 파일 내용:")
        print(f"{'-' * 40}\n{content}\n{'-' * 40}")
        
        self.assertIn("이것은 테스트 파일입니다.", content)
        self.assertIn("이 줄은 수정되었습니다.", content)
        self.assertNotIn("여기에 내용을 추가합니다.", content)
        
        print("\n==== test_edit_file_direct 완료 ====\n")
    
    def test_edit_file_mcp_protocol(self):
        """MCP 프로토콜을 통한 edit_file 함수 호출 테스트"""
        print("\n==== test_edit_file_mcp_protocol 시작 ====\n")
        
        # 테스트를 위해 파일 초기 상태 복원
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.write("이것은 테스트 파일입니다.\n여기에 내용을 추가합니다.\n이 줄은 유지됩니다.")
        
        # 원본 텍스트와 교체할 텍스트 정의
        old_text = "이것은 테스트 파일입니다."
        new_text = "이것은 MCP로 수정된 테스트 파일입니다."
        
        print(f"수정 내용: '{old_text}' -> '{new_text}'")
        
        # MCP 메시지 생성
        message = MCPMessage(
            type=MCPMessageType.FUNCTION_CALL,
            content=MCPFunctionCall(
                name="edit_file",
                arguments={
                    "path": self.test_file_path,
                    "old_text": old_text,
                    "new_text": new_text
                },
                call_id="test-edit-1"
            ),
            request_id="req-1234"
        )
        
        # 메시지 내용 출력
        print("MCP 메시지:")
        print(json.dumps(message.model_dump(), indent=2, ensure_ascii=False))
        
        # MCP 핸들러 호출
        response = self.loop.run_until_complete(
            self.mcp_handler.handle_message(message.model_dump())
        )
        
        # 응답 출력
        print("\nMCP 응답:")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        
        # 응답 확인
        self.assertEqual(response["type"], "function_response")
        self.assertEqual(response["content"]["call_id"], "test-edit-1")
        self.assertTrue(response["content"]["result"]["success"])
        
        # 파일 내용 확인
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n수정 후 파일 내용:")
        print(f"{'-' * 40}\n{content}\n{'-' * 40}")
        
        self.assertIn("이것은 MCP로 수정된 테스트 파일입니다.", content)
        self.assertNotIn("이것은 테스트 파일입니다.", content)
        
        print("\n==== test_edit_file_mcp_protocol 완료 ====\n")
    
    def test_edit_file_nonexistent(self):
        """존재하지 않는 파일 편집 테스트"""
        print("\n==== test_edit_file_nonexistent 시작 ====\n")
        
        non_existent_path = os.path.join(self.temp_dir.name, 'non_existent.txt')
        print(f"존재하지 않는 파일 경로: {non_existent_path}")
        
        # edit_file 함수 호출
        result = self.mcp_handler.edit_file(
            path=non_existent_path,
            old_text="아무 내용",
            new_text="새 내용"
        )
        
        # 결과 출력
        print("\n함수 호출 결과:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 결과 확인
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("파일을 찾을 수 없습니다", result["error"])
        
        print("\n==== test_edit_file_nonexistent 완료 ====\n")
    
    def test_edit_file_text_not_found(self):
        """원본 텍스트가 파일에 없는 경우 테스트"""
        print("\n==== test_edit_file_text_not_found 시작 ====\n")
        
        # 테스트를 위해 파일 초기 상태 복원
        original_content = "이것은 테스트 파일입니다.\n여기에 내용을 추가합니다.\n이 줄은 유지됩니다."
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        print(f"초기 파일 내용:\n{'-' * 40}\n{original_content}\n{'-' * 40}")
        
        # edit_file 함수 호출
        not_found_text = "이 텍스트는 파일에 없습니다"
        print(f"찾으려는 텍스트: '{not_found_text}' (파일에 없음)")
        
        result = self.mcp_handler.edit_file(
            path=self.test_file_path,
            old_text=not_found_text,
            new_text="새 내용"
        )
        
        # 결과 출력
        print("\n함수 호출 결과:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 결과 확인
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("원본 텍스트를 파일에서 찾을 수 없습니다", result["error"])
        
        # 파일 내용이 변경되지 않았는지 확인
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\n테스트 후 파일 내용 (변경되지 않아야 함):")
        print(f"{'-' * 40}\n{content}\n{'-' * 40}")
        
        self.assertEqual(content, original_content)
        
        print("\n==== test_edit_file_text_not_found 완료 ====\n")
    
    def test_multiple_edits(self):
        """여러 번 수정 테스트"""
        print("\n==== test_multiple_edits 시작 ====\n")
        
        # 테스트를 위해 파일 초기 상태 복원
        original_content = "이것은 테스트 파일입니다.\n여기에 내용을 추가합니다.\n이 줄은 유지됩니다."
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        print(f"초기 파일 내용:\n{'-' * 40}\n{original_content}\n{'-' * 40}")
        
        # 첫 번째 수정
        old_text1 = "이것은 테스트 파일입니다."
        new_text1 = "이것은 첫 번째 수정입니다."
        print(f"\n첫 번째 수정: '{old_text1}' -> '{new_text1}'")
        
        result1 = self.mcp_handler.edit_file(
            path=self.test_file_path,
            old_text=old_text1,
            new_text=new_text1
        )
        
        print("\n첫 번째 수정 결과:")
        print(json.dumps(result1, indent=2, ensure_ascii=False))
        
        self.assertTrue(result1["success"])
        
        # 첫 번째 수정 후 파일 내용 확인
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            content_after_first = f.read()
        
        print(f"\n첫 번째 수정 후 파일 내용:\n{'-' * 40}\n{content_after_first}\n{'-' * 40}")
        
        # 두 번째 수정
        old_text2 = "여기에 내용을 추가합니다."
        new_text2 = "이것은 두 번째 수정입니다."
        print(f"\n두 번째 수정: '{old_text2}' -> '{new_text2}'")
        
        result2 = self.mcp_handler.edit_file(
            path=self.test_file_path,
            old_text=old_text2,
            new_text=new_text2
        )
        
        print("\n두 번째 수정 결과:")
        print(json.dumps(result2, indent=2, ensure_ascii=False))
        
        self.assertTrue(result2["success"])
        
        # 최종 파일 내용 확인
        with open(self.test_file_path, 'r', encoding='utf-8') as f:
            final_content = f.read()
        
        print(f"\n최종 파일 내용:\n{'-' * 40}\n{final_content}\n{'-' * 40}")
        
        self.assertIn("이것은 첫 번째 수정입니다.", final_content)
        self.assertIn("이것은 두 번째 수정입니다.", final_content)
        self.assertNotIn("이것은 테스트 파일입니다.", final_content)
        self.assertNotIn("여기에 내용을 추가합니다.", final_content)
        
        print("\n==== test_multiple_edits 완료 ====\n")


if __name__ == "__main__":
    # 더 자세한 출력을 위한 설정
    unittest.main(verbosity=2)
