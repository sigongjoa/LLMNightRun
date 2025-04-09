#!/usr/bin/env python
"""
LLMNightRun 테스트 실행 스크립트

사용법:
    python run_tests.py               # 모든 테스트 실행
    python run_tests.py --unit        # 단위 테스트만 실행
    python run_tests.py --integration # 통합 테스트만 실행
    python run_tests.py --coverage    # 커버리지 리포트 생성
"""

import sys
import subprocess
import argparse


def run_tests(args):
    """테스트 실행 함수"""
    cmd = ["pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.unit:
        cmd.append("tests/unit/")
    elif args.integration:
        cmd.append("tests/integration/")
    
    if args.coverage:
        cmd.extend(["--cov=backend", "--cov-report=term", "--cov-report=html:coverage_report"])
    
    if args.xdist:
        cmd.append(f"-n{args.xdist}")
    
    if args.test_file:
        cmd.append(args.test_file)
    
    if args.failfast:
        cmd.append("-x")
    
    print(f"실행 명령: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLMNightRun 테스트 실행")
    parser.add_argument("--unit", action="store_true", help="단위 테스트만 실행")
    parser.add_argument("--integration", action="store_true", help="통합 테스트만 실행")
    parser.add_argument("--coverage", action="store_true", help="커버리지 리포트 생성")
    parser.add_argument("--xdist", type=int, default=0, help="병렬 실행 프로세스 수 (예: 4)")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 출력")
    parser.add_argument("--failfast", "-x", action="store_true", help="첫 번째 오류 발생 시 중단")
    parser.add_argument("--test-file", type=str, help="특정 테스트 파일 실행")
    
    args = parser.parse_args()
    exit_code = run_tests(args)
    sys.exit(exit_code)
