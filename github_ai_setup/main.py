"""
GitHub AI 모델 환경 설정 및 학습 도구

이 도구는 GitHub에서 AI 모델 레포지토리를 다운로드하고,
환경을 설정하며, 데이터를 전처리하고, 모델을 학습 및 시각화하는 기능을 제공합니다.

실행 방법:
    python main.py --repo <github_repo_url> --config <config_file_path>
    또는
    python main.py (프롬프트에서 GitHub URL 입력)
"""

import argparse
import os
import logging
import yaml
import re
from datetime import datetime

from src.utils.state_manager import StateManager
from src.utils.github_handler import GitHubHandler
from src.utils.environment_setup import EnvironmentSetup
from src.data.data_processor import DataProcessor
from src.models.model_trainer import ModelTrainer
from src.visualization.visualizer import Visualizer

# 로그 디렉토리 생성
os.makedirs("logs", exist_ok=True)

# 로깅 설정
# 모든 로그를 상세하게 출력
log_file = f"logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,  # 디버그 레벨로 변경
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# 모든 라이브러리의 로깅 레벨을 DEBUG로 설정
for name in ['src', 'tests']:
    logging.getLogger(name).setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)

def parse_arguments():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description="GitHub AI 모델 환경 설정 및 학습 도구")
    parser.add_argument("--repo", type=str, help="GitHub 레포지토리 URL")
    parser.add_argument("--config", type=str, default="configs/default_config.yaml", 
                        help="설정 파일 경로")
    parser.add_argument("--start-state", type=str, default="init",
                        choices=["init", "download", "setup", "preprocess", "train", "visualize"],
                        help="시작할 상태 (init, download, setup, preprocess, train, visualize)")
    parser.add_argument("--skip-tests", action="store_true", 
                        help="테스트 실행을 건너뜁니다")
    return parser.parse_args()

def load_config(config_path):
    """설정 파일을 로드합니다."""
    try:
        # 설정 파일이 없는 경우 기본 설정 파일 생성
        if not os.path.exists(config_path):
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            default_config = {
                "github": {
                    "repo_dir": "data/repos"
                },
                "environment": {
                    "venv_dir": "venv",
                    "use_conda": False,
                    "python_version": "3.8",
                    "force_reinstall": False,
                    "detect_gpu": True
                },
                "data": {
                    "data_dir": "data/processed",
                    "cache_dir": "data/cache",
                    "max_samples": None
                },
                "training": {
                    "output_dir": "models/output",
                    "epochs": 10,
                    "batch_size": 32,
                    "learning_rate": 0.001,
                    "seed": 42
                },
                "visualization": {
                    "output_dir": "results/visualization",
                    "save_format": "png"
                },
                "state_file": "logs/state.json"
            }
            with open(config_path, 'w', encoding='utf-8') as file:
                yaml.safe_dump(default_config, file)
            logger.info(f"기본 설정 파일 생성됨: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        raise

def is_valid_github_url(url):
    """
    GitHub URL의 유효성을 검사합니다.
    
    Args:
        url (str): 검사할 URL
    
    Returns:
        bool: URL이 유효한 GitHub URL인 경우 True
    """
    # None이나 빈 문자열 검사
    if url is None or not isinstance(url, str) or not url:
        return False
        
    # GitHub URL 패턴
    github_patterns = [
        r'^https?://github\.com/[\w.-]+/[\w.-]+(?:\.git)?$',
        r'^git@github\.com:[\w.-]+/[\w.-]+(?:\.git)?$'
    ]
    
    return any(re.match(pattern, url) for pattern in github_patterns)

def prompt_for_github_url():
    """사용자에게 GitHub URL을 입력 받습니다."""
    while True:
        try:
            url = input("\nGitHub 레포지토리 URL을 입력하세요: ")
            if is_valid_github_url(url):
                return url
            else:
                print("유효하지 않은 GitHub URL입니다. 다시 입력해주세요.")
                print("유효한 형식: 'https://github.com/username/repo' 또는 'git@github.com:username/repo.git'")
        except KeyboardInterrupt:
            print("\n프로그램 종료")
            exit(0)
        except Exception as e:
            print(f"오류 발생: {e}")

def run_tests():
    """단위 테스트를 실행합니다."""
    import subprocess
    import sys
    
    print("\n===== 단위 테스트 실행 시작 =====\n")
    logger.info("단위 테스트 실행 중...")
    try:
        result = subprocess.run(
            [sys.executable, "run_tests.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 테스트 결과 출력 - 디버깅을 위해 상세 로그 출력
        print("\n----- 테스트 출력 -----")
        print(result.stdout)
        
        # 오류가 있는 경우 표시
        if result.stderr:
            print("\n----- 테스트 오류 -----")
            print(result.stderr)
        
        if result.returncode == 0:
            logger.info("단위 테스트 통과")
            print("\n===== 단위 테스트 성공적으로 통과 =====\n")
            return True
        else:
            logger.error(f"단위 테스트 실패: {result.stderr}")
            print(f"\n===== 단위 테스트 실패 ===== \n리턴 코드: {result.returncode}\n")
            return False
    except Exception as e:
        logger.error(f"테스트 실행 중 오류 발생: {e}")
        print(f"\n===== 테스트 실행 오류 =====\n{str(e)}\n")
        return False

def main():
    """메인 실행 함수"""
    # 디버깅 모드 헤더 출력 - 더 명시적으로 표시
    print("\n===== 디버깅 모드 ===== [상세 로그 활성화] =====\n")
    # 인수 파싱
    args = parse_arguments()
    
    # GitHub 레포지토리 URL 가져오기
    repo_url = args.repo
    if not repo_url:
        print("\n=== GitHub AI 모델 환경 설정 및 학습 도구 ===")
        print("이 도구는 GitHub 레포지토리에서 AI 모델을 설정하고 실행합니다.")
        repo_url = prompt_for_github_url()
    
    # URL 유효성 검사
    if not is_valid_github_url(repo_url):
        logger.error(f"유효하지 않은 GitHub URL: {repo_url}")
        print(f"유효하지 않은 GitHub URL입니다: {repo_url}")
        print("유효한 형식: 'https://github.com/username/repo' 또는 'git@github.com:username/repo.git'")
        return
    
    # 설정 파일 로드
    try:
        config = load_config(args.config)
        logger.info(f"설정 파일 '{args.config}' 로드 완료")
        
        # 디버깅을 위해 설정 파일 내용 출력
        print("\n----- 설정 파일 내용 -----")
        for section, settings in config.items():
            print(f"[{section}]")
            if isinstance(settings, dict):
                for key, value in settings.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {settings}")
        print("----------------------------\n")
    except Exception as e:
        logger.error(f"실행 중단: {e}")
        print(f"\n===== 설정 파일 로드 오류 =====\n{str(e)}\n")
        return
    
    # 테스트 실행 (선택 사항)
    if not args.skip_tests:
        if not run_tests():
            print("\n테스트에 실패했습니다. 계속 진행하시겠습니까? (y/n): ", end="")
            response = input().strip().lower()
            if response != 'y':
                print("프로그램 종료")
                return
    
    # 상태 관리자 초기화
    state_manager = StateManager(config.get("state_file", "logs/state.json"))
    
    # 시작 상태 설정
    if args.start_state != "init":
        state_manager.set_state(args.start_state)
    
    # 컴포넌트 초기화
    github_handler = GitHubHandler(config.get("github", {}))
    env_setup = EnvironmentSetup(config.get("environment", {}))
    data_processor = DataProcessor(config.get("data", {}))
    model_trainer = ModelTrainer(config.get("training", {}))
    visualizer = Visualizer(config.get("visualization", {}))
    
    # 워크플로우 실행
    try:
        current_state = state_manager.get_state()
        
        # 초기 상태
        if current_state == "init":
            logger.info("워크플로우 시작: 초기화")
            state_manager.set_state("download")
            current_state = "download"
        
        # GitHub 레포지토리 다운로드
        if current_state == "download":
            logger.info(f"GitHub 레포지토리 다운로드 중: {repo_url}")
            print(f"\n레포지토리 다운로드 중: {repo_url}")
            repo_path = github_handler.clone_repository(repo_url)
            state_manager.set_details("repo_path", repo_path)
            print(f"레포지토리 다운로드 완료: {repo_path}")
            state_manager.set_state("setup")
            current_state = "setup"
        
        # 환경 설정
        if current_state == "setup":
            repo_path = state_manager.get_details("repo_path")
            logger.info(f"환경 설정 중: {repo_path}")
            print(f"\n환경 설정 중: {repo_path}")
            env_path = env_setup.setup_environment(repo_path)
            state_manager.set_details("env_path", env_path)
            print(f"환경 설정 완료: {env_path}")
            state_manager.set_state("preprocess")
            current_state = "preprocess"
        
        # 데이터 전처리
        if current_state == "preprocess":
            logger.info("데이터 전처리 중")
            print("\n데이터 전처리 중...")
            repo_path = state_manager.get_details("repo_path")
            processed_data_path = data_processor.preprocess(repo_path)
            state_manager.set_details("processed_data_path", processed_data_path)
            print(f"데이터 전처리 완료: {processed_data_path}")
            state_manager.set_state("train")
            current_state = "train"
        
        # 모델 학습
        if current_state == "train":
            logger.info("모델 학습 중")
            print("\n모델 학습 중...")
            processed_data_path = state_manager.get_details("processed_data_path")
            model_path = model_trainer.train(processed_data_path)
            state_manager.set_details("model_path", model_path)
            print(f"모델 학습 완료: {model_path}")
            state_manager.set_state("visualize")
            current_state = "visualize"
        
        # 시각화
        if current_state == "visualize":
            logger.info("결과 시각화 중")
            print("\n결과 시각화 중...")
            model_path = state_manager.get_details("model_path")
            processed_data_path = state_manager.get_details("processed_data_path")
            viz_path = visualizer.visualize(model_path, processed_data_path)
            state_manager.set_details("visualization_path", viz_path)
            print(f"결과 시각화 완료: {viz_path}")
            state_manager.set_state("complete")
            logger.info("워크플로우 완료")
            print("\n워크플로우가 성공적으로 완료되었습니다!")
        
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        state_manager.set_error(str(e))
        print(f"\n오류 발생: {e}")
        print("자세한 내용은 로그 파일을 확인하세요.")
        print(f"로그 파일 위치: {log_file}")
        raise

if __name__ == "__main__":
    main()
