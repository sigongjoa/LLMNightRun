"""
GitHub AI 환경 자동 설정 테스트 실행 스크립트

이 스크립트는 GitHub AI 환경 자동 설정 관련 테스트를 간편하게 실행할 수 있게 해줍니다.
"""

import os
import sys
import argparse
import unittest
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 필요한 경로 추가 (상위 디렉토리 import 가능하게)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def run_all_tests():
    """모든 테스트 실행"""
    logger.info("GitHub AI 환경 자동 설정 테스트 실행 시작")
    
    loader = unittest.TestLoader()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 테스트 디렉토리에서 테스트 모듈 로드
    suite = loader.discover(current_dir, pattern="test_*.py")
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info(f"테스트 완료: {result.testsRun}개 실행, {len(result.errors)}개 오류, {len(result.failures)}개 실패")
    
    return result.wasSuccessful()

def run_unit_tests():
    """단위 테스트만 실행"""
    logger.info("GitHub AI 환경 자동 설정 단위 테스트 실행")
    
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # 분석기 테스트 추가
    from test_github_analyzer import TestGitHubAnalyzer
    suite.addTest(loader.loadTestsFromTestCase(TestGitHubAnalyzer))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info(f"단위 테스트 완료: {result.testsRun}개 실행, {len(result.errors)}개 오류, {len(result.failures)}개 실패")
    
    return result.wasSuccessful()

def run_api_tests():
    """API 테스트만 실행"""
    logger.info("GitHub AI 환경 자동 설정 API 테스트 실행")
    
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # API 테스트 추가
    from test_github_ai_setup_api import TestGitHubAISetupAPI
    suite.addTest(loader.loadTestsFromTestCase(TestGitHubAISetupAPI))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info(f"API 테스트 완료: {result.testsRun}개 실행, {len(result.errors)}개 오류, {len(result.failures)}개 실패")
    
    return result.wasSuccessful()

def run_e2e_tests():
    """E2E 테스트만 실행"""
    logger.info("GitHub AI 환경 자동 설정 E2E 테스트 실행")
    
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # E2E 테스트 추가
    from test_github_ai_setup_e2e import TestGitHubAISetupE2E, TestGitHubAISetupMockE2E
    suite.addTest(loader.loadTestsFromTestCase(TestGitHubAISetupE2E))
    suite.addTest(loader.loadTestsFromTestCase(TestGitHubAISetupMockE2E))
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    logger.info(f"E2E 테스트 완료: {result.testsRun}개 실행, {len(result.errors)}개 오류, {len(result.failures)}개 실패")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description="GitHub AI 환경 자동 설정 테스트 실행")
    parser.add_argument("--all", action="store_true", help="모든 테스트 실행")
    parser.add_argument("--unit", action="store_true", help="단위 테스트만 실행")
    parser.add_argument("--api", action="store_true", help="API 테스트만 실행")
    parser.add_argument("--e2e", action="store_true", help="E2E 테스트만 실행")
    
    args = parser.parse_args()
    success = True
    
    # 각 테스트 타입에 따라 실행
    if args.all or (not args.unit and not args.api and not args.e2e):
        success = run_all_tests()
    else:
        if args.unit:
            success &= run_unit_tests()
        if args.api:
            success &= run_api_tests()
        if args.e2e:
            success &= run_e2e_tests()
    
    # 프로세스 종료 코드 설정
    sys.exit(0 if success else 1)
