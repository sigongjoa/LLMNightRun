"""
간단한 테스트 실행 스크립트
"""

import os
import sys
import unittest

# 현재 스크립트의 절대 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 절대 경로 (이미 루트에 있으므로 동일)
project_root = current_dir
# 루트 디렉토리를 시스템 경로에 추가
sys.path.insert(0, project_root)

# GitHub 분석기 테스트 실행
from tests.github_ai_setup.test_github_analyzer import TestGitHubAnalyzer, TestGitHubAnalyzerIntegration

# 테스트 실행
if __name__ == "__main__":
    # 테스트 로더 생성
    loader = unittest.TestLoader()
    
    # 테스트 스위트 생성
    suite = unittest.TestSuite()
    
    # 테스트 케이스 추가
    suite.addTest(loader.loadTestsFromTestCase(TestGitHubAnalyzer))
    suite.addTest(loader.loadTestsFromTestCase(TestGitHubAnalyzerIntegration))
    
    # 테스트 러너 생성 및 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 종료 코드 설정 (성공: 0, 실패: 1)
    sys.exit(not result.wasSuccessful())
