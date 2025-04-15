"""
MCP 파일 작업 테스트 실행 스크립트
"""

import os
import sys
import unittest

# 프로젝트 루트 디렉토리 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 테스트 모듈 가져오기
from tests.mcp.test_file_operations import TestMCPFileOperations


if __name__ == "__main__":
    # 테스트 세트 생성
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 테스트 추가
    suite.addTest(loader.loadTestsFromTestCase(TestMCPFileOperations))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 결과 출력
    print("\n결과 요약:")
    print(f"총 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.errors) - len(result.failures)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    
    # 종료 코드 설정 (실패가 있으면 1, 없으면 0)
    sys.exit(1 if result.failures or result.errors else 0)
