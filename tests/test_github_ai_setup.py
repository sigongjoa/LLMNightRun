"""
GitHub AI 환경 설정 시스템 테스트

GitHub AI 환경 설정 시스템의 기능을 테스트합니다.
"""

import unittest
import asyncio
import json
import os
from unittest.mock import patch, MagicMock

# 테스트 대상 모듈 임포트
import sys

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from github_ai_setup.analyzer import analyze_repository, GitHubRepositoryAnalyzer
from github_ai_setup.generator import generate_ai_setup, AISetupGenerator
from github_ai_setup.applier import apply_ai_setup, AISetupApplier


class TestGitHubAISetupSystem(unittest.TestCase):
    """GitHub AI 환경 설정 시스템 테스트 클래스"""
    
    def setUp(self):
        """테스트 설정"""
        # 비동기 이벤트 루프 설정
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # 테스트 데이터 설정
        self.test_repo_data = {
            "url": "https://github.com/example/test-repo",
            "path": None,
            "branch": "main",
            "access_token": "test_token"
        }
        
        # 테스트 분석 결과
        self.test_analysis_result = {
            "repo_id": "example/test-repo",
            "repo_info": {
                "name": "test-repo",
                "owner": "example",
                "description": "테스트 저장소입니다."
            },
            "language_stats": {
                "Python": 75.5,
                "JavaScript": 20.0,
                "HTML": 4.5
            },
            "frameworks": [
                {
                    "name": "Flask",
                    "language": "Python",
                    "confidence": 0.9
                },
                {
                    "name": "React",
                    "language": "JavaScript",
                    "confidence": 0.8
                }
            ],
            "dependencies": {
                "python": [
                    {"name": "flask", "version": "2.0.1"},
                    {"name": "numpy", "version": "1.21.0"}
                ],
                "javascript": [
                    {"name": "react", "version": "18.2.0"},
                    {"name": "axios", "version": "0.24.0"}
                ]
            },
            "ai_readiness": 0.65,
            "suggested_improvements": [
                "requirements.txt에 AI 라이브러리 추가",
                "모델 훈련을 위한 스크립트 추가"
            ]
        }
    
    def tearDown(self):
        """테스트 정리"""
        self.loop.close()
    
    @patch('github_ai_setup.analyzer.GitHubRepositoryAnalyzer.analyze')
    def test_analyze_repository(self, mock_analyze):
        """저장소 분석 테스트"""
        # 모의 응답 설정
        mock_analyze.return_value = self.test_analysis_result
        
        # 함수 호출
        result = self.loop.run_until_complete(
            analyze_repository(self.test_repo_data)
        )
        
        # 결과 검증
        self.assertEqual(result["repo_id"], "example/test-repo")
        self.assertEqual(result["ai_readiness"], 0.65)
        self.assertIn("language_stats", result)
        self.assertIn("frameworks", result)
        self.assertEqual(len(result["suggested_improvements"]), 2)
    
    def test_repository_analyzer_initialization(self):
        """저장소 분석기 초기화 테스트"""
        # URL로 초기화
        analyzer = GitHubRepositoryAnalyzer(
            repo_url="https://github.com/example/test-repo"
        )
        self.assertEqual(analyzer.repo_owner, "example")
        self.assertEqual(analyzer.repo_name, "test-repo")
        
        # 경로로 초기화
        analyzer = GitHubRepositoryAnalyzer(
            repo_path="/path/to/repo"
        )
        self.assertEqual(analyzer.repo_path, "/path/to/repo")
        self.assertIsNone(analyzer.repo_owner)
    
    @patch('github_ai_setup.generator.AISetupGenerator.generate_setup')
    def test_generate_ai_setup(self, mock_generate_setup):
        """AI 환경 설정 생성 테스트"""
        # 모의 응답 설정
        test_setup_result = {
            "repo_id": "example/test-repo",
            "config_files": [
                {
                    "path": "requirements-ai.txt",
                    "content": "tensorflow>=2.8.0\npytorch>=1.10.0",
                    "description": "AI 관련 Python 종속성"
                },
                {
                    "path": ".env.example",
                    "content": "MODEL_PATH=./models\nDEFAULT_MODEL=efficientnet_b0",
                    "description": "AI 환경 변수 예시"
                }
            ],
            "setup_scripts": [
                {
                    "path": "scripts/setup_ai_env.py",
                    "content": "# 설정 스크립트 내용",
                    "description": "AI 환경 설정 스크립트"
                }
            ],
            "workflows": [
                {
                    "path": ".github/workflows/ai-ci.yml",
                    "content": "# CI 워크플로우 내용",
                    "description": "AI 구성요소 CI 워크플로우"
                }
            ],
            "documentation": {
                "path": "docs/ai_integration.md",
                "content": "# AI 통합 가이드",
                "description": "AI 통합 가이드"
            }
        }
        mock_generate_setup.return_value = test_setup_result
        
        # 함수 호출
        result = self.loop.run_until_complete(
            generate_ai_setup("example/test-repo", self.test_analysis_result)
        )
        
        # 결과 검증
        self.assertEqual(result["repo_id"], "example/test-repo")
        self.assertEqual(len(result["config_files"]), 2)
        self.assertEqual(len(result["setup_scripts"]), 1)
        self.assertEqual(len(result["workflows"]), 1)
        self.assertEqual(result["documentation"]["path"], "docs/ai_integration.md")
    
    def test_setup_generator_initialization(self):
        """설정 생성기 초기화 테스트"""
        generator = AISetupGenerator(self.test_analysis_result)
        self.assertEqual(generator.repo_id, "example/test-repo")
        self.assertEqual(generator.primary_language, "Python")
    
    @patch('github_ai_setup.applier.AISetupApplier.apply')
    def test_apply_ai_setup(self, mock_apply):
        """AI 환경 설정 적용 테스트"""
        # 모의 응답 설정
        apply_result = {
            "repo_id": "example/test-repo",
            "status": "completed",
            "applied_files": [
                "requirements-ai.txt",
                ".env.example",
                "scripts/setup_ai_env.py",
                ".github/workflows/ai-ci.yml",
                "docs/ai_integration.md"
            ],
            "pull_request_url": "https://github.com/example/test-repo/pull/123"
        }
        mock_apply.return_value = apply_result
        
        # 테스트 설정 결과
        test_setup_result = {
            "repo_id": "example/test-repo",
            "config_files": [
                {"path": "requirements-ai.txt", "content": "content"}
            ],
            "setup_scripts": [
                {"path": "scripts/setup_ai_env.py", "content": "content"}
            ]
        }
        
        # 함수 호출
        result = self.loop.run_until_complete(
            apply_ai_setup(
                repo_data=self.test_repo_data,
                setup_result=test_setup_result,
                create_pr=True,
                pr_title="AI 환경 설정 추가"
            )
        )
        
        # 결과 검증
        self.assertEqual(result["repo_id"], "example/test-repo")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["applied_files"]), 5)
        self.assertEqual(result["pull_request_url"], "https://github.com/example/test-repo/pull/123")
    
    def test_setup_applier_initialization(self):
        """설정 적용기 초기화 테스트"""
        # 설정 결과로 초기화
        test_setup_result = {"repo_id": "example/test-repo"}
        
        applier = AISetupApplier(self.test_repo_data, test_setup_result)
        self.assertEqual(applier.repo_id, "example/test-repo")
        self.assertEqual(applier.repo_url, "https://github.com/example/test-repo")
        self.assertEqual(applier.branch, "main")
        
        # repo_id가 없는 경우 URL에서 추출
        applier = AISetupApplier(self.test_repo_data, {})
        self.assertEqual(applier.repo_id, "example/test-repo")
    
    @patch('github_ai_setup.applier.AISetupApplier._apply_to_local_repo')
    def test_apply_to_local_repo(self, mock_apply_to_local):
        """로컬 저장소에 적용 테스트"""
        # 모의 응답 설정
        mock_apply_to_local.return_value = [
            "requirements-ai.txt", 
            ".env.example", 
            "scripts/setup_ai_env.py"
        ]
        
        # 로컬 경로가 있는 테스트 데이터
        local_repo_data = {
            "url": "https://github.com/example/test-repo",
            "path": "/fake/path",  # 테스트용 가짜 경로
            "branch": "main"
        }
        
        # 테스트 설정 결과
        test_setup_result = {
            "repo_id": "example/test-repo",
            "config_files": [
                {"path": "requirements-ai.txt", "content": "content"}
            ],
            "setup_scripts": [
                {"path": "scripts/setup_ai_env.py", "content": "content"}
            ]
        }
        
        # 적용기 생성 및 패치
        applier = AISetupApplier(local_repo_data, test_setup_result)
        
        # os.path.exists를 패치하여 로컬 경로가 존재하는 것처럼 설정
        with patch('os.path.exists', return_value=True):
            # 함수 호출
            result = self.loop.run_until_complete(applier.apply())
        
        # 결과 검증
        self.assertEqual(result["repo_id"], "example/test-repo")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(result["applied_files"]), 3)
        self.assertNotIn("pull_request_url", result)


if __name__ == '__main__':
    unittest.main()
