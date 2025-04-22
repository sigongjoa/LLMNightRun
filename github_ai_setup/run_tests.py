"""
테스트 실행 스크립트

모든 단위 테스트 및 통합 테스트를 실행합니다.
"""

import unittest
import sys
import os
import logging
import argparse

# 현재 스크립트의 디렉토리를 기준으로 절대 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(BASE_DIR, "tests")

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG 레벨로 변경하여 더 상세한 로그 출력
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 모든 라이브러리 로그 레벨을 DEBUG로 설정
for name in ['src', 'tests']:
    logging.getLogger(name).setLevel(logging.DEBUG)

logger = logging.getLogger("__main__")

def parse_args():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description="테스트 실행 스크립트")
    parser.add_argument(
        "--test-type", 
        type=str, 
        choices=["unit", "integration", "all"], 
        default="all",
        help="실행할 테스트 유형 (unit: 단위 테스트, integration: 통합 테스트, all: 모든 테스트)"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="상세 출력 활성화"
    )
    parser.add_argument(
        "--pattern", 
        type=str, 
        default="test_*.py",
        help="테스트 파일 패턴"
    )
    return parser.parse_args()

def run_unit_tests(verbose=False, pattern="test_*.py"):
    """단위 테스트를 실행합니다."""
    print(f"\n===== 단위 테스트 실행 시작 (pattern: {pattern}) =====\n")
    logger.info("단위 테스트 실행 중...")
    
    # 테스트 파일 출력
    matching_files = [f for f in os.listdir(TEST_DIR) if f.endswith('.py') and 
                      (f.startswith('test_') if pattern == "test_*.py" else f == pattern)]
    logger.debug(f"매칭되는 테스트 파일: {matching_files}")
    
    # 단위 테스트 발견
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(TEST_DIR, pattern=pattern)
    
    # 테스트 실행 - 항상 상세 모드로 실행
    test_runner = unittest.TextTestRunner(verbosity=2)
    print("\n----- 테스트 실행 결과 -----\n")
    result = test_runner.run(test_suite)
    
    # 실패한 테스트 상세 정보 출력
    if result.failures:
        print("\n===== 실패한 테스트 상세 정보 =====\n")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"\n[{i}] 실패한 테스트: {test}\n")
            print(traceback)
    
    if result.errors:
        print("\n===== 오류가 발생한 테스트 상세 정보 =====\n")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"\n[{i}] 오류 발생 테스트: {test}\n")
            print(traceback)
    
    # 결과 요약 출력
    print("\n===== 테스트 결과 요약 =====\n")
    logger.info(f"단위 테스트 결과: 총={result.testsRun}, 성공={result.testsRun - len(result.failures) - len(result.errors)}, 실패={len(result.failures)}, 오류={len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n===== 단위 테스트 성공적으로 통과 =====\n")
    else:
        print(f"\n===== 테스트 실패! 실패: {len(result.failures)}, 오류: {len(result.errors)} =====\n")
    
    return result.wasSuccessful()

def run_integration_tests(verbose=False, pattern="test_integration.py"):
    """통합 테스트를 실행합니다."""
    print(f"\n===== 통합 테스트 실행 시작 (pattern: {pattern}) =====\n")
    logger.info("통합 테스트 실행 중...")
    
    # 테스트 파일 출력
    matching_files = [f for f in os.listdir(TEST_DIR) if f.endswith('.py') and f == pattern]
    logger.debug(f"통합 테스트 파일: {matching_files}")
    
    # 통합 테스트 발견
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(TEST_DIR, pattern=pattern)
    
    # 테스트 실행 - 항상 상세 모드로 실행
    test_runner = unittest.TextTestRunner(verbosity=2)
    print("\n----- 통합 테스트 실행 결과 -----\n")
    result = test_runner.run(test_suite)
    
    # 실패한 테스트 상세 정보 출력
    if result.failures:
        print("\n===== 실패한 통합 테스트 상세 정보 =====\n")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"\n[{i}] 실패한 테스트: {test}\n")
            print(traceback)
    
    if result.errors:
        print("\n===== 오류가 발생한 통합 테스트 상세 정보 =====\n")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"\n[{i}] 오류 발생 테스트: {test}\n")
            print(traceback)
    
    # 결과 요약 출력
    print("\n===== 통합 테스트 결과 요약 =====\n")
    logger.info(f"통합 테스트 결과: 총={result.testsRun}, 성공={result.testsRun - len(result.failures) - len(result.errors)}, 실패={len(result.failures)}, 오류={len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n===== 통합 테스트 성공적으로 통과 =====\n")
    else:
        print(f"\n===== 통합 테스트 실패! 실패: {len(result.failures)}, 오류: {len(result.errors)} =====\n")
    
    return result.wasSuccessful()

def run_all_tests(verbose=False):
    """모든 테스트를 실행합니다."""
    print("\n===== 모든 테스트 실행 시작 =====\n")
    logger.info("모든 테스트 실행 중...")
    
    # 테스트 디렉토리 정보 출력
    logger.debug(f"테스트 디렉토리: {TEST_DIR}")
    test_files = [f for f in os.listdir(TEST_DIR) if f.endswith('.py') and f.startswith('test_')]
    logger.debug(f"발견된 테스트 파일: {test_files}")
    
    # 모든 테스트 발견
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(TEST_DIR)
    
    # 테스트 실행 - 반드시 상세 모드로 설정
    test_runner = unittest.TextTestRunner(verbosity=2)  # 항상 상세 정보 출력
    result = test_runner.run(test_suite)
    
    # 실패한 테스트 상세 정보 출력
    if result.failures:
        print("\n===== 실패한 테스트 상세 정보 =====\n")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"\n[{i}] 실패한 테스트: {test}\n")
            print(traceback)
    
    if result.errors:
        print("\n===== 오류가 발생한 테스트 상세 정보 =====\n")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"\n[{i}] 오류 발생 테스트: {test}\n")
            print(traceback)
    
    # 종합 결과 상세 출력
    print("\n===== 테스트 결과 요약 =====\n")
    logger.info(f"모든 테스트 결과: 총={result.testsRun}, 성공={result.testsRun - len(result.failures) - len(result.errors)}, 실패={len(result.failures)}, 오류={len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n===== 모든 테스트 성공적으로 통과 =====\n")
    else:
        print(f"\n===== 테스트 실패! 실패: {len(result.failures)}, 오류: {len(result.errors)} =====\n")
    
    return result.wasSuccessful()

def main():
    """메인 함수"""
    # Python 경로에 프로젝트 루트 추가
    sys.path.insert(0, BASE_DIR)
    
    print("\n===== 디버깅 모드 테스트 시작 =====\n")
    print(f"Python 버전: {sys.version}")
    print(f"운영 체제: {os.name} - {sys.platform}")
    print(f"테스트 디렉토리: {TEST_DIR}")
    print(f"\n전체 테스트 파일: {[f for f in os.listdir(TEST_DIR) if f.endswith('.py') and f.startswith('test_')]}\n")
    
    args = parse_args()
    
    # 환경 변수 출력 (특히 GitHub 관련 테스트를 위한 정보)
    print("\n----- 환경 변수 정보 -----")
    relevant_vars = ['GITHUB_TOKEN', 'PYTHONPATH', 'PATH', 'TEMP', 'TMP']
    for var in relevant_vars:
        if var in os.environ:
            value = os.environ[var]
            # 토큰 같은 민감한 정보는 일부만 표시
            if var == 'GITHUB_TOKEN' and value:
                print(f"{var}: {value[:4]}...{value[-4:]} (길이: {len(value)})")
            else:
                print(f"{var}: {value}")
    print("---------------------------\n")
    
    if args.test_type == "unit":
        success = run_unit_tests(args.verbose, args.pattern)
    elif args.test_type == "integration":
        success = run_integration_tests(args.verbose, args.pattern)
    else:  # all
        success = run_all_tests(args.verbose)
    
    if not success:
        print("\n===== 테스트 실패 추가 디버깅 정보 =====\n")
        
        # 특히 GitHub 테스트 관련 추가 정보 출력
        print("1. 임시 디렉토리 확인:")
        temp_dir = os.environ.get('TEMP', os.environ.get('TMP', '/tmp'))
        print(f"   임시 디렉토리 경로: {temp_dir}")
        try:
            temp_files = os.listdir(temp_dir)
            github_temp_dirs = [f for f in temp_files if 'github' in f.lower() or 'git' in f.lower()]
            print(f"   Git 관련 임시 파일/디렉토리: {github_temp_dirs[:10] if github_temp_dirs else '없음'}")
        except Exception as e:
            print(f"   임시 디렉토리 확인 오류: {e}")
        
        print("\n2. Git 설치 확인:")
        try:
            import subprocess
            git_version = subprocess.run(['git', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"   Git 버전: {git_version.stdout if git_version.returncode == 0 else '설치되지 않음 또는 오류'}")
        except Exception as e:
            print(f"   Git 확인 오류: {e}")
        
        print("\n테스트 실패를 해결하기 위해 위 정보를 확인하세요.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
