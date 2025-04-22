"""
데이터 프로세서 (Data Processor)

AI 학습을 위한 데이터 전처리 기능을 제공합니다.
"""

import os
import logging
import json
import shutil
from pathlib import Path

from .file_finder import DataFileFinder
from .script_runner import ScriptRunner
from .preprocessing_steps import PreprocessingStepsRunner

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    AI 학습 데이터를 전처리하는 클래스
    """
    
    def __init__(self, config):
        """
        데이터 프로세서를 초기화합니다.
        
        Args:
            config (dict): 데이터 처리 관련 설정
                - data_dir (str): 데이터 디렉토리 (기본값: 'data/processed')
                - cache_dir (str): 캐시 디렉토리 (기본값: 'data/cache')
                - max_samples (int, optional): 처리할 최대 샘플 수
                - preprocessing_steps (list, optional): 전처리 단계 목록
        """
        self.data_dir = config.get("data_dir", os.path.join("data", "processed"))
        self.cache_dir = config.get("cache_dir", os.path.join("data", "cache"))
        self.max_samples = config.get("max_samples")
        self.preprocessing_steps = config.get("preprocessing_steps", [])
        
        # 디렉토리 생성
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 관련 모듈 초기화
        self.file_finder = DataFileFinder(self.max_samples)
        self.script_runner = ScriptRunner(self.data_dir, self.cache_dir)
        self.steps_runner = PreprocessingStepsRunner(self.data_dir, self.cache_dir)
    
    def preprocess(self, repo_path=None, custom_script=None):
        """
        데이터 전처리를 수행합니다.
        
        Args:
            repo_path (str, optional): 레포지토리 경로
            custom_script (str, optional): 사용자 정의 전처리 스크립트 경로
            
        Returns:
            str: 처리된 데이터의 경로
            
        Raises:
            ValueError: 전처리 단계가 유효하지 않은 경우
            RuntimeError: 전처리 중 오류가 발생한 경우
        """
        logger.info("데이터 전처리 시작")
        
        # 레포지토리 경로가 제공된 경우 환경 정보 로드
        env_info = None
        if repo_path:
            env_info_path = os.path.join(repo_path, "env_info.json")
            if os.path.exists(env_info_path):
                try:
                    with open(env_info_path, 'r', encoding='utf-8') as f:
                        env_info = json.load(f)
                    logger.info(f"환경 정보 로드됨: {env_info}")
                except Exception as e:
                    logger.warning(f"환경 정보 로드 실패: {e}")
        
        try:
            # 1. 데이터 디렉토리 정리
            self._clean_data_directory()
            
            # 2. 데이터 파일 찾기 및 복사
            if repo_path:
                data_files = self.file_finder.find_data_files(repo_path)
                logger.info(f"찾은 데이터 파일: {len(data_files)}")
                
                # 데이터 파일 복사
                for file_path in data_files:
                    rel_path = os.path.relpath(file_path, repo_path)
                    dest_path = os.path.join(self.data_dir, rel_path)
                    
                    # 대상 디렉토리 생성
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # 파일 복사
                    shutil.copy2(file_path, dest_path)
                    logger.debug(f"파일 복사됨: {rel_path}")
            
            # 3. 사용자 정의 전처리 스크립트 실행
            if custom_script and os.path.exists(custom_script):
                self.script_runner.run_custom_script(custom_script, env_info)
            
            # 4. 레포지토리 내 전처리 스크립트 찾기 및 실행
            if repo_path:
                self.script_runner.find_and_run_preprocessing_scripts(repo_path, env_info)
            
            # 5. 설정된 전처리 단계 실행
            for step in self.preprocessing_steps:
                self.steps_runner.run_preprocessing_step(step)
            
            # 6. 전처리 결과 정보 저장
            self._save_preprocessing_info()
            
            logger.info(f"데이터 전처리 완료: {self.data_dir}")
            return self.data_dir
            
        except Exception as e:
            error_msg = f"데이터 전처리 실패: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _clean_data_directory(self):
        """데이터 디렉토리를 정리합니다."""
        try:
            # 이전 처리 결과 삭제
            for item in os.listdir(self.data_dir):
                item_path = os.path.join(self.data_dir, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            logger.info(f"데이터 디렉토리 정리 완료: {self.data_dir}")
        except Exception as e:
            logger.warning(f"데이터 디렉토리 정리 실패: {e}")
    
    def _save_preprocessing_info(self):
        """전처리 결과 정보를 저장합니다."""
        info = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "data_dir": self.data_dir,
            "file_count": sum(1 for _ in Path(self.data_dir).rglob("*") if _.is_file()),
            "preprocessing_steps": self.preprocessing_steps
        }
        
        info_path = os.path.join(self.data_dir, "preprocessing_info.json")
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
            
        logger.info(f"전처리 정보 저장 완료: {info_path}")
