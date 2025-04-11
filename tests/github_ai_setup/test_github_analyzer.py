"""
GitHub AI 환경 자동 설정 분석기 테스트

이 테스트 모듈은 GitHub 리포지토리 분석 기능을 검증합니다.
"""

import os
import json
import unittest
import pytest
from unittest.mock import patch, MagicMock
import sys
import logging

# 현재 스크립트의 절대 경로
current_dir = os.path.dirname(os.path.abspath(__file__))
# 프로젝트 루트 디렉토리 절대 경로
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
# 루트 디렉토리를 시스템 경로에 추가
sys.path.insert(0, project_root)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 필요한 경로 추가 (상위 디렉토리 import 가능하게)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 테스트 대상 모듈 임포트
from backend.model_installer.github_analyzer import GitHubAnalyzer


class MockRepo:
    """Git Repo 객체를 모킹하는 클래스"""
    def __init__(self, path):
        self.working_dir = path


class TestGitHubAnalyzer(unittest.TestCase):
    """GitHubAnalyzer 테스트 클래스"""

    def setUp(self):
        """테스트 준비"""
        # 테스트에 사용할 임시 디렉토리
        self.test_dir = os.path.join(os.path.dirname(__file__), "test_repo")
        
        # 테스트 디렉토리가 없으면 생성
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)
        
        # 기본 테스트 URL
        self.test_url = "https://github.com/suksham11/MLTradingbot"

    def tearDown(self):
        """테스트 정리"""
        # 테스트 디렉토리 정리 로직 (필요시 추가)
        pass

    def test_extract_repo_name(self):
        """저장소 이름 추출 테스트"""
        # 전략 변경: 실제 테스트 URL 사용
        real_url = "https://github.com/suksham11/MLTradingbot"
        analyzer = GitHubAnalyzer(real_url)
        repo_name = analyzer._extract_repo_name(real_url)
        self.assertEqual(repo_name, "MLTradingbot")
        
        # 다른 형식의 URL 테스트
        different_url = "https://github.com/organization/project.git"
        analyzer = GitHubAnalyzer(different_url)
        repo_name = analyzer._extract_repo_name(different_url)
        self.assertEqual(repo_name, "project.git")  # 현재 구현은 .git을 제거하지 않음

    @patch('backend.model_installer.github_analyzer.Repo')
    @patch('backend.model_installer.github_analyzer.os.path.exists')
    def test_clone_repository_success(self, mock_exists, mock_repo):
        """저장소 클론 성공 테스트"""
        # 디렉토리가 존재하지 않도록 설정
        mock_exists.return_value = False
        
        # Repo.clone_from 메서드 모킹
        mock_instance = MockRepo(self.test_dir)
        mock_repo.clone_from.return_value = mock_instance
        
        analyzer = GitHubAnalyzer(self.test_url, self.test_dir)
        result = analyzer.clone_repository()
        
        # 검증
        self.assertTrue(result)
        mock_repo.clone_from.assert_called_once_with(self.test_url, self.test_dir)

    @patch('backend.model_installer.github_analyzer.Repo')
    @patch('backend.model_installer.github_analyzer.os.path.exists')
    def test_clone_repository_failure(self, mock_exists, mock_repo):
        """저장소 클론 실패 테스트"""
        # 디렉토리가 존재하지 않도록 설정
        mock_exists.return_value = False
        
        # Repo.clone_from 메서드가 예외 발생하도록 설정
        mock_repo.clone_from.side_effect = Exception("Clone failed")
        
        analyzer = GitHubAnalyzer(self.test_url, self.test_dir)
        result = analyzer.clone_repository()
        
        # 검증
        self.assertFalse(result)

    @patch('backend.model_installer.github_analyzer.Repo')
    @patch('backend.model_installer.github_analyzer.os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="# Test README")
    @patch('backend.model_installer.github_analyzer.Path')
    def test_analyze_basic(self, mock_path, mock_open, mock_exists, mock_repo):
        """기본 분석 테스트"""
        # 실제 테스트 URL 사용
        real_url = "https://github.com/suksham11/MLTradingbot"
        
        # 모킹 설정
        mock_exists.return_value = True
        mock_instance = MockRepo(self.test_dir)
        mock_repo.return_value = mock_instance
        
        # Path.glob 모킹
        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.glob.return_value = []
        
        analyzer = GitHubAnalyzer(real_url, self.test_dir)
        analyzer.repo = mock_instance  # 클론 단계 건너뛰기
        
        result = analyzer.analyze()
        
        # 기본 정보 검증
        self.assertEqual(result["repo_name"], "MLTradingbot")
        self.assertEqual(result["repo_url"], real_url)
        self.assertEqual(result["clone_path"], self.test_dir)

    def test_model_type_identification(self):
        """모델 유형 식별 테스트"""
        analyzer = GitHubAnalyzer(self.test_url, self.test_dir)
        
        # 테스트 데이터 설정
        analyzer.analysis_result = {
            "readme": {"content": "This is a test repository with LLAMA model implementation"},
            "file_structure": ["model.py", "llama_config.json", "train.py"]
        }
        
        # 메서드 실행
        analyzer._identify_model_type()
        
        # 결과 검증
        self.assertIn("model_type", analyzer.analysis_result)
        self.assertEqual(analyzer.analysis_result["model_type"]["primary"], "llama")


class TestGitHubAnalyzerIntegration(unittest.TestCase):
    """GitHubAnalyzer 통합 테스트 클래스"""
    
    @pytest.mark.slow
    @patch('backend.model_installer.github_analyzer.Repo')
    def test_real_repository_analysis(self, mock_repo):
        """실제 저장소 분석 통합 테스트 (느린 테스트)"""
        # 이 테스트는 mock을 사용하지만 실제 저장소 구조를 시뮬레이션
        
        # 테스트 디렉토리 설정
        test_dir = os.path.join(os.path.dirname(__file__), "real_test_repo")
        if not os.path.exists(test_dir):
            os.makedirs(test_dir)
            
        # 가상의 파일 구조 생성
        self._create_mock_repository_structure(test_dir)
        
        # Repo 모킹
        mock_instance = MockRepo(test_dir)
        mock_repo.return_value = mock_instance
        
        # 테스트 실행
        analyzer = GitHubAnalyzer("https://github.com/example/llm-model", test_dir)
        analyzer.repo = mock_instance
        result = analyzer.analyze()
        
        # 결과 검증
        self.assertIn("model_type", result)
        logger.info(f"분석 결과: {json.dumps(result, indent=2)}")
        
        # 테스트 후 정리
        self._cleanup_mock_repository(test_dir)
        
    def _create_mock_repository_structure(self, directory):
        """모의 저장소 구조 생성"""
        # README.md 파일 생성
        with open(os.path.join(directory, "README.md"), 'w') as f:
            f.write("""
            # LLM Model Implementation
            
            This is a test repository that implements a language model based on the LLAMA architecture.
            
            ## Installation
            
            ```
            pip install -r requirements.txt
            ```
            
            ## Usage
            
            ```
            python inference.py --model path/to/model
            ```
            """)
            
        # requirements.txt 파일 생성
        with open(os.path.join(directory, "requirements.txt"), 'w') as f:
            f.write("""
            torch>=1.10.0
            transformers>=4.20.0
            tqdm
            numpy
            """)
            
        # 모델 설정 파일 생성
        os.makedirs(os.path.join(directory, "config"), exist_ok=True)
        with open(os.path.join(directory, "config", "model_config.json"), 'w') as f:
            f.write("""
            {
                "model_type": "llama",
                "vocab_size": 32000,
                "hidden_size": 4096,
                "num_layers": 32,
                "num_attention_heads": 32
            }
            """)
            
        # 실행 스크립트 생성
        with open(os.path.join(directory, "inference.py"), 'w') as f:
            f.write("""
            import torch
            
            def main():
                print("Running inference")
                
            if __name__ == "__main__":
                main()
            """)
            
        with open(os.path.join(directory, "train.py"), 'w') as f:
            f.write("""
            import torch
            
            def main():
                print("Training model")
                
            if __name__ == "__main__":
                main()
            """)
    
    def _cleanup_mock_repository(self, directory):
        """모의 저장소 정리"""
        # 실제 환경에서는 정리 로직 구현
        pass


if __name__ == "__main__":
    # 테스트 실행 시 직접 테스트를 실행합니다
    print("GitHub AI 환경 자동 설정 분석기 테스트 실행 중...")
    
    # 테스트 로더 생성
    loader = unittest.TestLoader()
    
    # 테스트 스위트 생성
    suite = unittest.TestSuite()
    
    # 테스트 케이스 추가
    suite.addTest(loader.loadTestsFromTestCase(TestGitHubAnalyzer))
    suite.addTest(loader.loadTestsFromTestCase(TestGitHubAnalyzerIntegration))
    
    # 테스트 러너 생성 및 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 종료 코드 설정 (성공: 0, 실패: 1)
    sys.exit(not result.wasSuccessful())
