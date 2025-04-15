"""
MCP 파일 편집 기능 테스트

MCP 핸들러의 edit_file 기능을 테스트합니다.
"""

import os
import sys
import tempfile
import asyncio

# 프로젝트 루트 디렉터리를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from mcp.handler import MCPHandler
from mcp.protocol import MCPMessage, MCPMessageType, MCPFunctionCall


class MCPFileEditTest:
    """MCP 파일 편집 기능 테스트 클래스"""
    
    def __init__(self):
        """초기화"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name
        
        # 테스트 파일 생성
        self.test_file_path = os.path.join(self.test_dir, "test_file.txt")
        with open(self.test_file_path, 'w', encoding='utf-8') as f:
            f.write("이것은 테스트 파일입니다.\n")
            f.write("이 내용은 MCP edit_file 기능으로 수정됩니다.\n")
            f.write("테스트가 완료되면 임시 파일은 자동으로 삭제됩니다.\n")
        
        # MCP 핸들러 초기화
        self.mcp_handler = MCPHandler(config_dir=self.test_dir)
    
    def cleanup(self):
        """정리"""
        self.temp_dir.cleanup()
    
    async def test_edit_file(self):
        """edit_file 함수 테스트"""
        print("\n========== 테스트: 파일 편집 기능 ==========")
        
        # 테스트용 MCP 메시지 생성
        message = MCPMessage(
            type=MCPMessageType.FUNCTION_CALL,
            content=MCPFunctionCall(
                name="edit_file",
                arguments={
                    "path": self.test_file_path,
                    "old_text": "이 내용은 MCP edit_file 기능으로 수정됩니다.",
                    "new_text": "이 내용은 성공적으로 수정되었습니다!"
                },
                call_id="test-edit-1"
            ),
            request_id="req-1"
        )
        
        print(f"테스트 파일 경로: {self.test_file_path}")
        print("원본 텍스트: '이 내용은 MCP edit_file 기능으로 수정됩니다.'")
        print("변경할 텍스트: '이 내용은 성공적으로 수정되었습니다!'")
        
        # 메시지 처리
        result = await self.mcp_handler.handle_message(message.model_dump())
        
        # 결과 출력
        print("\n응답 결과:")
        print(f"타입: {result['type']}")
        print(f"호출 ID: {result['content']['call_id']}")
        print(f"성공 여부: {result['content']['result']['success']}")
        
        if result['content']['result']['success']:
            print(f"변경 사항 (diff):\n{result['content']['result']['diff']}")
            
            # 파일 내용 확인
            with open(self.test_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("\n수정된 파일 내용:")
            print(content)
            
            # 내용이 올바르게 수정되었는지 확인
            if "이 내용은 성공적으로 수정되었습니다!" in content:
                print("\n✓ 테스트 통과: 파일이 성공적으로 수정되었습니다.")
            else:
                print("\n❌ 테스트 실패: 파일이 제대로 수정되지 않았습니다.")
        else:
            print(f"오류 메시지: {result['content']['result']['error']}")
            print("\n❌ 테스트 실패: 파일 편집 함수가 성공적으로 실행되지 않았습니다.")


async def run_tests():
    """테스트 실행"""
    print("MCP 파일 편집 기능 테스트 시작")
    print("=" * 50)
    
    tester = MCPFileEditTest()
    try:
        await tester.test_edit_file()
    finally:
        tester.cleanup()
    
    print("\n테스트가 완료되었습니다.")


if __name__ == "__main__":
    # 비동기 테스트 실행
    asyncio.run(run_tests())
