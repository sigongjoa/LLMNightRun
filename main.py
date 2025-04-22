"""
GitHub AI 모델 환경 설정 및 학습 도구

이 도구는 GitHub에서 AI 모델 레포지토리를 다운로드하고,
환경을 설정하며, 데이터를 전처리하고, 모델을 학습 및 시각화하는 기능을 제공합니다.

실행 방법:
    python main.py --repo <github_repo_url> --config <config_file_path>
"""

import argparse
import os
import logging
import yaml
from datetime import datetime

from src.utils.state_manager import StateManager
from src.utils.github_handler import GitHubHandler
from src.utils.environment_setup import EnvironmentSetup
from src.data.data_processor import DataProcessor
from src.models.model_trainer import ModelTrainer
from src.visualization.visualizer import Visualizer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """명령줄 인수를 파싱합니다."""
    parser = argparse.ArgumentParser(description="GitHub AI 모델 환경 설정 및 학습 도구")
    parser.add_argument("--repo", type=str, required=True, help="GitHub 레포지토리 URL")
    parser.add_argument("--config", type=str, default="configs/default_config.yaml", 
                        help="설정 파일 경로")
    parser.add_argument("--start-state", type=str, default="init",
                        help="시작할 상태 (init, download, setup, preprocess, train, visualize)")
    return parser.parse_args()

def load_config(config_path):
    """설정 파일을 로드합니다."""
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        raise

def main():
    """메인 실행 함수"""
    # 인수 파싱
    args = parse_arguments()
    
    # 설정 파일 로드
    try:
        config = load_config(args.config)
        logger.info(f"설정 파일 '{args.config}' 로드 완료")
    except Exception as e:
        logger.error(f"실행 중단: {e}")
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
            logger.info(f"GitHub 레포지토리 다운로드 중: {args.repo}")
            repo_path = github_handler.clone_repository(args.repo)
            state_manager.set_details("repo_path", repo_path)
            state_manager.set_state("setup")
            current_state = "setup"
        
        # 환경 설정
        if current_state == "setup":
            repo_path = state_manager.get_details("repo_path")
            logger.info(f"환경 설정 중: {repo_path}")
            env_setup.setup_environment(repo_path)
            state_manager.set_state("preprocess")
            current_state = "preprocess"
        
        # 데이터 전처리
        if current_state == "preprocess":
            logger.info("데이터 전처리 중")
            processed_data_path = data_processor.preprocess()
            state_manager.set_details("processed_data_path", processed_data_path)
            state_manager.set_state("train")
            current_state = "train"
        
        # 모델 학습
        if current_state == "train":
            logger.info("모델 학습 중")
            processed_data_path = state_manager.get_details("processed_data_path")
            model_path = model_trainer.train(processed_data_path)
            state_manager.set_details("model_path", model_path)
            state_manager.set_state("visualize")
            current_state = "visualize"
        
        # 시각화
        if current_state == "visualize":
            logger.info("결과 시각화 중")
            model_path = state_manager.get_details("model_path")
            processed_data_path = state_manager.get_details("processed_data_path")
            visualizer.visualize(model_path, processed_data_path)
            state_manager.set_state("complete")
            logger.info("워크플로우 완료")
        
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        state_manager.set_error(str(e))
        raise

if __name__ == "__main__":
    main()
