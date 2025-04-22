"""
데이터 파일 찾기 모듈

레포지토리에서 데이터 파일을 검색하는 기능을 제공합니다.
"""

import os
import re
import logging

logger = logging.getLogger(__name__)

class DataFileFinder:
    """
    레포지토리에서 데이터 파일을 찾는 클래스
    """
    
    def __init__(self, max_samples=None):
        """
        데이터 파일 검색기를 초기화합니다.
        
        Args:
            max_samples (int, optional): 찾을 최대 파일 수
        """
        self.max_samples = max_samples
        
        # 데이터 파일 패턴
        self.data_patterns = [
            r'\.csv$', r'\.json$', r'\.jsonl$', r'\.txt$', 
            r'\.tsv$', r'\.xlsx$', r'\.h5$', r'\.pkl$',
            r'\.npy$', r'\.npz$'
        ]
        
        # 일반적인 데이터 디렉토리 이름
        self.data_dirs = ['data', 'dataset', 'datasets', 'corpus', 'raw_data']
    
    def find_data_files(self, repo_path):
        """
        레포지토리에서 데이터 파일을 찾습니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            
        Returns:
            list: 데이터 파일 경로 목록
        """
        data_files = []
        
        # 먼저 데이터 디렉토리 찾기
        for root, dirs, files in os.walk(repo_path):
            dir_name = os.path.basename(root)
            
            if dir_name.lower() in self.data_dirs or any(re.search(r'data', d, re.IGNORECASE) for d in dirs):
                # 데이터 디렉토리 내 파일 탐색
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(re.search(pattern, file, re.IGNORECASE) for pattern in self.data_patterns):
                        data_files.append(file_path)
        
        # 데이터 파일이 없으면 레포지토리 전체 검색
        if not data_files:
            for root, _, files in os.walk(repo_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(re.search(pattern, file, re.IGNORECASE) for pattern in self.data_patterns):
                        data_files.append(file_path)
        
        # 최대 샘플 수 적용
        if self.max_samples and len(data_files) > self.max_samples:
            logger.info(f"최대 샘플 수 적용: {self.max_samples}")
            data_files = data_files[:self.max_samples]
        
        return data_files
    
    def find_model_data_files(self, repo_path):
        """
        레포지토리에서 모델 데이터 파일(체크포인트, 가중치 등)을 찾습니다.
        
        Args:
            repo_path (str): 레포지토리 경로
            
        Returns:
            list: 모델 데이터 파일 경로 목록
        """
        model_files = []
        
        # 모델 파일 패턴
        model_patterns = [
            r'\.pt$', r'\.pth$', r'\.h5$', r'\.onnx$',
            r'\.pb$', r'\.tflite$', r'\.weights$',
            r'checkpoint', r'\.bin$', r'\.model$',
            r'pretrained', r'weights'
        ]
        
        # 일반적인 모델 디렉토리 이름
        model_dirs = ['models', 'checkpoints', 'weights', 'pretrained']
        
        # 먼저 모델 디렉토리 찾기
        for root, dirs, files in os.walk(repo_path):
            dir_name = os.path.basename(root)
            
            if dir_name.lower() in model_dirs or any(re.search(r'model|weight', d, re.IGNORECASE) for d in dirs):
                # 모델 디렉토리 내 파일 탐색
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(re.search(pattern, file, re.IGNORECASE) for pattern in model_patterns):
                        model_files.append(file_path)
        
        # 모델 파일이 없으면 레포지토리 전체 검색
        if not model_files:
            for root, _, files in os.walk(repo_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(re.search(pattern, file, re.IGNORECASE) for pattern in model_patterns):
                        model_files.append(file_path)
        
        # 최대 샘플 수 적용
        if self.max_samples and len(model_files) > self.max_samples:
            logger.info(f"최대 모델 파일 수 적용: {self.max_samples}")
            model_files = model_files[:self.max_samples]
        
        return model_files
