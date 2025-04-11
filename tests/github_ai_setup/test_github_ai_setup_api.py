"""
GitHub AI 환경 자동 설정 API 테스트

이 테스트 모듈은 GitHub AI 환경 자동 설정 API의 기능을 검증합니다.
"""

import os
import json
import unittest
from unittest.mock import patch, MagicMock
import sys
import pytest
import logging
from fastapi.testclient import TestClient

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 필요한 경로 추가 (상위 디렉토리 import 가능하게)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# FastAPI 애플리케이션 가져오기
from backend.main import app

# TestClient 생성
client = TestClient(app)


class TestGitHubAISetupAPI(unittest.TestCase):
    """GitHub AI 환경 자동 설정 API 테스트 클래스"""

    def setUp(self):
        """테스트 준비"""
        self.test_repo_url = "https://github.com/sigonjoa/test-repository"
        self.test_token = "test_token"

    @patch('backend.model_installer.github_analyzer.GitHubAnalyzer.clone_repository')
    @patch('backend.model_installer.github_analyzer.GitHubAnalyzer.analyze')
    def test_analyze_endpoint(self, mock_analyze, mock_clone):
        """저장소 분석 엔드포인트 테스트"""
        # 모킹 설정
        mock_clone.return_value = True
        mock_analyze.return_value = {
            "repo_name": "test-repository",
            "repo_url": self.test_repo_url,
            "clone_path": "/tmp/test-repository",
            "model_type": {
                "primary": "llama",
                "all_detected": {"llama": 2}
            },
            "requirements": {
                "requirements.txt": {
                    "content": "torch\ntransformers\n",
                    "path": "/tmp/test-repository/requirements.txt"
                }
            },
            "launch_scripts": ["run.py", "inference.py"]
        }

        # API 호출
        response = client.post(
            "/model-installer/analyze",
            json={"url": self.test_repo_url}
        )

        # 응답 검증
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["repo_name"], "test-repository")
        self.assertEqual(data["model_type"]["primary"], "llama")
        self.assertIn("requirements", data)
        self.assertIn("launch_scripts", data)

    @patch('backend.services.model_installer_service.ModelInstallerService.setup_environment')
    def test_setup_endpoint(self, mock_setup):
        """환경 설정 엔드포인트 테스트"""
        # 모킹 설정
        mock_setup.return_value = {
            "success": True,
            "message": "환경 설정이 완료되었습니다.",
            "config_path": "/tmp/test-repository/config.json"
        }

        # 테스트 분석 결과
        analysis_result = {
            "repo_name": "test-repository",
            "repo_url": self.test_repo_url,
            "clone_path": "/tmp/test-repository",
            "model_type": {
                "primary": "llama",
                "all_detected": {"llama": 2}
            },
            "requirements": {
                "requirements.txt": {
                    "content": "torch\ntransformers\n",
                    "path": "/tmp/test-repository/requirements.txt"
                }
            },
            "launch_scripts": ["run.py", "inference.py"]
        }

        # API 호출
        response = client.post(
            "/model-installer/setup",
            json={
                "url": self.test_repo_url,
                "analysis": analysis_result
            }
        )

        # 응답 검증
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("message", data)
        self.assertIn("config_path", data)

    @patch('backend.services.model_installer_service.ModelInstallerService.install_model')
    def test_install_endpoint(self, mock_install):
        """모델 설치 엔드포인트 테스트"""
        # 모킹 설정
        mock_install.return_value = {
            "installation_id": "test-123",
            "status": "started",
            "message": "모델 설치가 시작되었습니다."
        }

        # API 호출
        response = client.post(
            "/model-installer/install",
            json={"url": self.test_repo_url}
        )

        # 응답 검증
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("installation_id", data)
        self.assertEqual(data["status"], "started")
        self.assertIn("message", data)

    @patch('backend.services.model_installer_service.ModelInstallerService.get_installation_status')
    def test_status_endpoint(self, mock_status):
        """설치 상태 엔드포인트 테스트"""
        # 모킹 설정
        mock_status.return_value = {
            "installation_id": "test-123",
            "status": "in_progress",
            "progress": 50,
            "logs": [
                "설치 시작...",
                "요구사항 설치 중...",
                "모델 다운로드 중..."
            ]
        }

        # API 호출
        response = client.get("/model-installer/status/test-123")

        # 응답 검증
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["installation_id"], "test-123")
        self.assertEqual(data["status"], "in_progress")
        self.assertEqual(data["progress"], 50)
        self.assertIn("logs", data)
        self.assertIsInstance(data["logs"], list)


class TestGitHubAISetupIntegration(unittest.TestCase):
    """GitHub AI 환경 자동 설정 통합 테스트 클래스"""

    @pytest.mark.integration
    @patch('backend.services.github_service.GitHubService.test_connection')
    def test_github_connection(self, mock_test_connection):
        """GitHub 연결 테스트"""
        # 모킹 설정
        mock_test_connection.return_value = {
            "success": True,
            "message": "GitHub 연결 성공",
            "repo_details": {
                "name": "test-repository",
                "owner": "sigonjoa",
                "url": "https://github.com/sigonjoa/test-repository"
            }
        }

        # API 호출
        response = client.post(
            "/github/test-connection",
            json={
                "url": "https://github.com/sigonjoa/test-repository",
                "token": "test_token",
                "username": "sigonjoa"
            }
        )

        # 응답 검증
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("message", data)
        self.assertIn("repo_details", data)


if __name__ == "__main__":
    unittest.main()
