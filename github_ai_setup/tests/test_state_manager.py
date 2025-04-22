"""
StateManager 단위 테스트

상태 관리자(StateManager) 클래스의 실제 동작을 테스트합니다.
"""

import unittest
import os
import json
import tempfile
import shutil
import sys
import time
from pathlib import Path

# 상위 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.state_manager import StateManager

# 로깅 레벨 설정 (불필요한 로그 메시지 제거)
import logging
logging.basicConfig(level=logging.ERROR)

class TestStateManager(unittest.TestCase):
    """StateManager 클래스의 실제 동작을 테스트합니다."""
    
    def setUp(self):
        """테스트 환경을 설정합니다."""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.test_dir, "test_state.json")
        self.state_manager = StateManager(self.state_file)
    
    def tearDown(self):
        """테스트 환경을 정리합니다."""
        # 임시 디렉토리 삭제
        shutil.rmtree(self.test_dir)
    
    def test_initial_state_file_creation(self):
        """초기 상태 파일이 올바르게 생성되는지 테스트합니다."""
        # 상태 관리자 생성 후 파일이 생성됐는지 확인
        self.assertTrue(os.path.exists(self.state_file))
        
        # 파일 내용이 유효한 JSON인지 확인
        with open(self.state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
            
            # 필수 키가 있는지 확인
            self.assertIn("state", state_data)
            self.assertIn("timestamp", state_data)
            self.assertIn("details", state_data)
            self.assertIn("error", state_data)
            
            # 초기 상태가 'init'인지 확인
            self.assertEqual(state_data["state"], "init")
            
            # details가 빈 딕셔너리인지 확인
            self.assertEqual(state_data["details"], {})
            
            # error가 None인지 확인
            self.assertIsNone(state_data["error"])
    
    def test_set_and_get_state(self):
        """상태 설정 및 가져오기가 올바르게 작동하는지 테스트합니다."""
        # 초기 상태 확인
        self.assertEqual(self.state_manager.get_state(), "init")
        
        # 상태 변경
        self.state_manager.set_state("download")
        
        # 변경된 상태 확인
        self.assertEqual(self.state_manager.get_state(), "download")
        
        # 파일에 상태가 저장됐는지 확인
        with open(self.state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
            self.assertEqual(state_data["state"], "download")
        
        # 다른 상태로 변경 테스트
        states = ["setup", "preprocess", "train", "visualize", "complete", "error"]
        for state in states:
            self.state_manager.set_state(state)
            self.assertEqual(self.state_manager.get_state(), state)
            
            # 파일에도 상태가 정확히 저장됐는지 확인
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                self.assertEqual(state_data["state"], state)
    
    def test_invalid_state(self):
        """유효하지 않은 상태 설정 시 예외가 발생하는지 테스트합니다."""
        invalid_states = ["invalid", "unknown", "processing", "", None, 123]
        
        for invalid_state in invalid_states:
            with self.assertRaises(ValueError):
                self.state_manager.set_state(invalid_state)
                
        # 실패 후에도 원래 상태가 유지되는지 확인
        self.assertEqual(self.state_manager.get_state(), "init")
    
    def test_set_and_get_details(self):
        """세부 정보 설정 및 가져오기가 올바르게 작동하는지 테스트합니다."""
        # 초기에는 세부 정보가 비어있는지 확인
        self.assertEqual(self.state_manager.get_details(), {})
        
        # 문자열 세부 정보 설정
        self.state_manager.set_details("repo_url", "https://github.com/test/repo")
        self.assertEqual(self.state_manager.get_details("repo_url"), "https://github.com/test/repo")
        
        # 숫자 세부 정보 설정
        self.state_manager.set_details("count", 42)
        self.assertEqual(self.state_manager.get_details("count"), 42)
        
        # 리스트 세부 정보 설정
        test_list = [1, 2, 3, "test"]
        self.state_manager.set_details("items", test_list)
        self.assertEqual(self.state_manager.get_details("items"), test_list)
        
        # 딕셔너리 세부 정보 설정
        test_dict = {"name": "test", "value": 123}
        self.state_manager.set_details("config", test_dict)
        self.assertEqual(self.state_manager.get_details("config"), test_dict)
        
        # 모든 세부 정보 가져오기 테스트
        all_details = self.state_manager.get_details()
        self.assertEqual(all_details["repo_url"], "https://github.com/test/repo")
        self.assertEqual(all_details["count"], 42)
        self.assertEqual(all_details["items"], test_list)
        self.assertEqual(all_details["config"], test_dict)
        
        # 파일에 세부 정보가 저장됐는지 확인
        with open(self.state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
            self.assertEqual(state_data["details"]["repo_url"], "https://github.com/test/repo")
            self.assertEqual(state_data["details"]["count"], 42)
            self.assertEqual(state_data["details"]["items"], test_list)
            self.assertEqual(state_data["details"]["config"], test_dict)
    
    def test_nonexistent_detail(self):
        """존재하지 않는 세부 정보를 요청했을 때 None을 반환하는지 테스트합니다."""
        self.assertIsNone(self.state_manager.get_details("nonexistent_key"))
    
    def test_set_and_get_error(self):
        """오류 설정 및 가져오기가 올바르게 작동하는지 테스트합니다."""
        # 초기에는 오류가 없는지 확인
        self.assertIsNone(self.state_manager.get_error())
        
        # 오류 설정
        error_message = "테스트 오류 메시지"
        self.state_manager.set_error(error_message)
        
        # 오류 가져오기
        self.assertEqual(self.state_manager.get_error(), error_message)
        
        # 상태가 'error'로 변경됐는지 확인
        self.assertEqual(self.state_manager.get_state(), "error")
        
        # 파일에 오류가 저장됐는지 확인
        with open(self.state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
            self.assertEqual(state_data["error"], error_message)
            self.assertEqual(state_data["state"], "error")
    
    def test_clear_error(self):
        """오류 지우기가 올바르게 작동하는지 테스트합니다."""
        # 오류 설정
        self.state_manager.set_error("테스트 오류")
        
        # 오류 지우기
        self.state_manager.clear_error()
        
        # 오류가 지워졌는지 확인
        self.assertIsNone(self.state_manager.get_error())
        
        # 파일에서도 오류가 지워졌는지 확인
        with open(self.state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
            self.assertIsNone(state_data["error"])
    
    def test_state_persistence(self):
        """상태 파일이 여러 인스턴스 간에 공유되는지 테스트합니다."""
        # 첫 번째 인스턴스로 상태 설정
        self.state_manager.set_state("download")
        self.state_manager.set_details("repo_url", "https://github.com/test/repo")
        
        # 두 번째 인스턴스 생성
        second_manager = StateManager(self.state_file)
        
        # 두 번째 인스턴스에서 상태 및 세부 정보 확인
        self.assertEqual(second_manager.get_state(), "download")
        self.assertEqual(second_manager.get_details("repo_url"), "https://github.com/test/repo")
        
        # 두 번째 인스턴스로 상태 변경
        second_manager.set_state("setup")
        
        # 첫 번째 인스턴스에서 변경된 상태 확인
        self.assertEqual(self.state_manager.get_state(), "setup")
    
    def test_directory_creation(self):
        """상태 파일의 디렉토리가 없을 때 자동으로 생성되는지 테스트합니다."""
        # 중첩된 디렉토리 경로
        nested_dir = os.path.join(self.test_dir, "nested", "dirs", "state")
        nested_file = os.path.join(nested_dir, "state.json")
        
        # 디렉토리가 존재하지 않는지 확인
        self.assertFalse(os.path.exists(nested_dir))
        
        # 해당 경로로 상태 관리자 생성
        nested_manager = StateManager(nested_file)
        
        # 디렉토리와 파일이 생성됐는지 확인
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(nested_file))
        
        # 상태 확인
        self.assertEqual(nested_manager.get_state(), "init")
    
    def test_load_corrupted_file(self):
        """손상된 상태 파일을 로드할 때 처리가 올바른지 테스트합니다."""
        # 손상된 JSON 파일 생성
        with open(self.state_file, 'w', encoding='utf-8') as f:
            f.write("{invalid json content")
        
        # 손상된 파일로 상태 관리자 생성
        corrupted_manager = StateManager(self.state_file)
        
        # 상태가 'error'로 설정되었는지 확인
        self.assertEqual(corrupted_manager.get_state(), "error")
        
        # 오류 메시지가 설정됐는지 확인
        self.assertIsNotNone(corrupted_manager.get_error())

if __name__ == '__main__':
    unittest.main()
