"""
DataProcessor 단위 테스트

데이터 처리기(DataProcessor) 클래스의 실제 동작을 테스트합니다.
"""

import unittest
import os
import json
import tempfile
import shutil
import sys
from pathlib import Path

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.data_processor import DataProcessor
from src.data.file_finder import DataFileFinder

# 로깅 레벨 설정 (불필요한 로그 메시지 제거)
import logging
logging.basicConfig(level=logging.ERROR)

class TestDataProcessor(unittest.TestCase):
    """DataProcessor 클래스의 실제 동작을 테스트합니다."""
    
    def setUp(self):
        """테스트 환경을 설정합니다."""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        
        # 테스트 설정
        self.config = {
            "data_dir": os.path.join(self.test_dir, "processed"),
            "cache_dir": os.path.join(self.test_dir, "cache"),
            "max_samples": 10,
            "preprocessing_steps": []
        }
        
        self.data_processor = DataProcessor(self.config)
        
        # 테스트용 레포지토리 생성
        self.repo_path = os.path.join(self.test_dir, "repo")
        os.makedirs(self.repo_path, exist_ok=True)
        
        # 테스트용 데이터 디렉토리 생성
        self.data_path = os.path.join(self.repo_path, "data")
        os.makedirs(self.data_path, exist_ok=True)
        
        # 테스트용 데이터 파일 생성
        self.csv_path = os.path.join(self.data_path, "sample.csv")
        with open(self.csv_path, 'w') as f:
            f.write("id,value\n1,10\n2,20\n3,30")
        
        self.json_path = os.path.join(self.data_path, "config.json")
        with open(self.json_path, 'w') as f:
            f.write('{"param1": 10, "param2": 20}')
    
    def tearDown(self):
        """테스트 환경을 정리합니다."""
        # 임시 디렉토리 삭제
        shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """초기화가 올바르게 작동하는지 테스트합니다."""
        # 디렉토리가 생성됐는지 확인
        self.assertTrue(os.path.exists(self.config["data_dir"]))
        self.assertTrue(os.path.exists(self.config["cache_dir"]))
        
        # 설정이 올바르게 적용됐는지 확인
        self.assertEqual(self.data_processor.data_dir, self.config["data_dir"])
        self.assertEqual(self.data_processor.cache_dir, self.config["cache_dir"])
        self.assertEqual(self.data_processor.max_samples, self.config["max_samples"])
        self.assertEqual(self.data_processor.preprocessing_steps, self.config["preprocessing_steps"])
        
        # 관련 모듈이 초기화됐는지 확인
        self.assertIsNotNone(self.data_processor.file_finder)
        self.assertIsNotNone(self.data_processor.script_runner)
        self.assertIsNotNone(self.data_processor.steps_runner)
    
    def test_clean_data_directory(self):
        """데이터 디렉토리 정리가 올바르게 작동하는지 테스트합니다."""
        # 데이터 디렉토리에 테스트 파일 생성
        test_file = os.path.join(self.config["data_dir"], "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        
        # 테스트 서브디렉토리 생성
        test_subdir = os.path.join(self.config["data_dir"], "subdir")
        os.makedirs(test_subdir, exist_ok=True)
        subdir_file = os.path.join(test_subdir, "subtest.txt")
        with open(subdir_file, 'w') as f:
            f.write("subtest")
        
        # 파일이 생성됐는지 확인
        self.assertTrue(os.path.exists(test_file))
        self.assertTrue(os.path.exists(test_subdir))
        self.assertTrue(os.path.exists(subdir_file))
        
        # 디렉토리 정리
        self.data_processor._clean_data_directory()
        
        # 파일이 삭제됐는지 확인
        self.assertFalse(os.path.exists(test_file))
        self.assertFalse(os.path.exists(test_subdir))
        self.assertFalse(os.path.exists(subdir_file))
    
    def test_find_data_files(self):
        """데이터 파일 찾기가 올바르게 작동하는지 테스트합니다."""
        # 데이터 파일 찾기
        file_finder = DataFileFinder(max_samples=10)
        data_files = file_finder.find_data_files(self.repo_path)
        
        # 결과 확인
        self.assertEqual(len(data_files), 2, "찾은 파일 수가 예상과 다름")
        self.assertIn(self.csv_path, data_files, "CSV 파일을 찾지 못함")
        self.assertIn(self.json_path, data_files, "JSON 파일을 찾지 못함")
    
    def test_preprocess_basic(self):
        """기본 전처리 과정이 올바르게 작동하는지 테스트합니다."""
        # 환경 정보 파일 생성
        env_info = {
            "type": "venv",
            "path": os.path.join(self.repo_path, "venv"),
            "python_path": sys.executable
        }
        
        env_info_path = os.path.join(self.repo_path, "env_info.json")
        with open(env_info_path, 'w', encoding='utf-8') as f:
            json.dump(env_info, f, ensure_ascii=False, indent=2)
        
        # 전처리 수행
        processed_dir = self.data_processor.preprocess(self.repo_path)
        
        # 결과 확인
        self.assertEqual(processed_dir, self.config["data_dir"], "반환된 데이터 디렉토리가 예상과 다름")
        
        # 파일이 복사됐는지 확인
        copied_csv = os.path.join(processed_dir, "data", "sample.csv")
        copied_json = os.path.join(processed_dir, "data", "config.json")
        
        self.assertTrue(os.path.exists(copied_csv), "CSV 파일이 복사되지 않음")
        self.assertTrue(os.path.exists(copied_json), "JSON 파일이 복사되지 않음")
        
        # 전처리 정보 파일이 생성됐는지 확인
        info_path = os.path.join(processed_dir, "preprocessing_info.json")
        self.assertTrue(os.path.exists(info_path), "전처리 정보 파일이 생성되지 않음")
        
        # 전처리 정보 내용 확인
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
            self.assertIn("timestamp", info, "타임스탬프 정보가 없음")
            self.assertIn("file_count", info, "파일 수 정보가 없음")
            self.assertEqual(info["data_dir"], self.config["data_dir"], "데이터 디렉토리 정보가 잘못됨")
    
    def test_preprocess_with_steps(self):
        """전처리 단계를 포함한 전처리가 올바르게 작동하는지 테스트합니다."""
        # 전처리 단계 설정
        self.data_processor.preprocessing_steps = [
            {"name": "split_data", "type": "builtin", "params": {"train_ratio": 0.8, "val_ratio": 0.1, "test_ratio": 0.1}},
            {"name": "normalize", "type": "builtin", "params": {"method": "zscore"}}
        ]
        
        # 전처리 수행
        processed_dir = self.data_processor.preprocess(self.repo_path)
        
        # 결과 확인
        self.assertEqual(processed_dir, self.config["data_dir"], "반환된 데이터 디렉토리가 예상과 다름")
        
        # 분할 디렉토리가 생성됐는지 확인
        train_dir = os.path.join(processed_dir, "train")
        val_dir = os.path.join(processed_dir, "val")
        test_dir = os.path.join(processed_dir, "test")
        
        self.assertTrue(os.path.exists(train_dir), "학습 디렉토리가 생성되지 않음")
        self.assertTrue(os.path.exists(val_dir), "검증 디렉토리가 생성되지 않음")
        self.assertTrue(os.path.exists(test_dir), "테스트 디렉토리가 생성되지 않음")
        
        # 정규화 정보 파일이 생성됐는지 확인
        norm_info_path = os.path.join(processed_dir, "normalization_info.json")
        self.assertTrue(os.path.exists(norm_info_path), "정규화 정보 파일이 생성되지 않음")
        
        # 정규화 정보 내용 확인
        with open(norm_info_path, 'r', encoding='utf-8') as f:
            norm_info = json.load(f)
            self.assertEqual(norm_info["method"], "zscore", "정규화 방법이 잘못됨")
    
    def test_nonexistent_repo(self):
        """존재하지 않는 레포지토리에 대한 전처리가 오류를 발생시키지 않는지 테스트합니다."""
        # 존재하지 않는 레포지토리 경로
        nonexistent_path = os.path.join(self.test_dir, "nonexistent")
        
        # 전처리 수행
        processed_dir = self.data_processor.preprocess(nonexistent_path)
        
        # 결과 확인
        self.assertEqual(processed_dir, self.config["data_dir"], "반환된 데이터 디렉토리가 예상과 다름")
        
        # 전처리 정보 파일이 생성됐는지 확인
        info_path = os.path.join(processed_dir, "preprocessing_info.json")
        self.assertTrue(os.path.exists(info_path), "전처리 정보 파일이 생성되지 않음")
    
    def test_custom_script(self):
        """사용자 정의 스크립트가 올바르게 실행되는지 테스트합니다."""
        # 사용자 정의 스크립트 생성
        script_dir = os.path.join(self.repo_path, "scripts")
        os.makedirs(script_dir, exist_ok=True)
        
        script_path = os.path.join(script_dir, "custom_preprocess.py")
        with open(script_path, 'w') as f:
            f.write("""
def preprocess(data_dir=None, cache_dir=None):
    import os
    import json
    
    # 간단한 마커 파일 생성
    marker_path = os.path.join(data_dir, "custom_script_ran.txt")
    with open(marker_path, 'w') as f:
        f.write("This file indicates that the custom script ran successfully.")
    
    # 처리 정보 저장
    info_path = os.path.join(data_dir, "custom_info.json")
    with open(info_path, 'w') as f:
        json.dump({"status": "success", "data_dir": data_dir}, f)
""")
        
        # 전처리 수행
        processed_dir = self.data_processor.preprocess(self.repo_path, custom_script=script_path)
        
        # 결과 확인
        marker_path = os.path.join(processed_dir, "custom_script_ran.txt")
        info_path = os.path.join(processed_dir, "custom_info.json")
        
        self.assertTrue(os.path.exists(marker_path), "사용자 정의 스크립트가 실행되지 않음")
        self.assertTrue(os.path.exists(info_path), "사용자 정의 스크립트 정보 파일이 생성되지 않음")
    
    def test_invalid_preprocessing_step(self):
        """유효하지 않은 전처리 단계가 오류를 발생시키는지 테스트합니다."""
        # 유효하지 않은 전처리 단계 설정
        self.data_processor.preprocessing_steps = [
            {"name": "nonexistent_step", "type": "builtin"}
        ]
        
        # 전처리 수행 시 오류 발생 확인
        with self.assertRaises(RuntimeError):
            self.data_processor.preprocess(self.repo_path)

if __name__ == '__main__':
    unittest.main()
