#!/usr/bin/env python3
"""
문서 생성 스크립트

이 스크립트는 docs_generator 패키지를 사용하여 프로젝트 문서를 생성합니다.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# 상위 디렉토리를 모듈 검색 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from docs_generator import run_workflow


def main():
    """
    메인 함수
    
    명령행 인자를 파싱하고 워크플로우를 실행합니다.
    """
    parser = argparse.ArgumentParser(description="프로젝트 문서 자동 생성")
    
    parser.add_argument(
        "--repo-path", "-r",
        default=".",
        help="Git 저장소 경로 (기본값: 현재 디렉토리)"
    )
    
    parser.add_argument(
        "--force-all", "-f",
        action="store_true",
        help="모든 문서 강제 업데이트"
    )
    
    parser.add_argument(
        "--push", "-p",
        action="store_true",
        help="변경사항 자동 푸시"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="상세 로깅 활성화"
    )
    
    args = parser.parse_args()
    
    # 로깅 레벨 설정
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 워크플로우 실행
    success = run_workflow(
        repo_path=args.repo_path,
        force_all=args.force_all,
        push_changes=args.push
    )
    
    # 결과 출력
    if success:
        print("문서 생성 완료!")
        sys.exit(0)
    else:
        print("문서 생성 실패. 자세한 내용은 로그를 확인하세요.")
        sys.exit(1)


if __name__ == "__main__":
    main()