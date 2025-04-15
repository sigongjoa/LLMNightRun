"""
GitHub 저장소 분석기

GitHub 저장소를 분석하여 AI 환경 설정에 필요한 정보를 추출합니다.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple

# 로깅 설정
logger = logging.getLogger("github_ai_setup.analyzer")


class GitHubRepositoryAnalyzer:
    """
    GitHub 저장소 분석 클래스
    
    저장소 구조, 언어, 프레임워크 등을 분석합니다.
    """
    
    def __init__(self, repo_path: str = None, repo_url: str = None):
        """
        분석기 초기화
        
        Args:
            repo_path: 로컬 저장소 경로
            repo_url: GitHub 저장소 URL
        """
        self.repo_path = repo_path
        self.repo_url = repo_url
        self.repo_name = None
        self.repo_owner = None
        
        if repo_url:
            # URL에서 소유자와 저장소 이름 추출
            parts = repo_url.strip('/').split('/')
            if 'github.com' in parts and len(parts) >= 5:
                self.repo_owner = parts[-2]
                self.repo_name = parts[-1]
        
        logger.info(f"저장소 분석기 초기화: {self.repo_owner}/{self.repo_name or '?'}")
    
    async def analyze(self) -> Dict[str, Any]:
        """
        저장소 분석 실행
        
        Returns:
            분석 결과
        """
        try:
            logger.info(f"저장소 분석 시작: {self.repo_owner}/{self.repo_name or '?'}")
            
            # 기본 정보 수집
            repo_info = await self.get_repo_info()
            
            # 언어 통계 분석
            language_stats = await self.analyze_languages()
            
            # 프레임워크 탐지
            frameworks = await self.detect_frameworks()
            
            # 종속성 분석
            dependencies = await self.analyze_dependencies()
            
            # 기존 CI/CD 구성 확인
            ci_cd_config = await self.check_ci_cd_config()
            
            # AI 준비도 평가
            ai_readiness, suggestions = await self.evaluate_ai_readiness()
            
            # 결과 종합
            result = {
                "repo_id": f"{self.repo_owner}/{self.repo_name}" if self.repo_owner and self.repo_name else "unknown",
                "repo_info": repo_info,
                "language_stats": language_stats,
                "frameworks": frameworks,
                "dependencies": dependencies,
                "ci_cd_config": ci_cd_config,
                "ai_readiness": ai_readiness,
                "suggested_improvements": suggestions
            }
            
            logger.info(f"저장소 분석 완료: {result['repo_id']}")
            return result
            
        except Exception as e:
            logger.error(f"저장소 분석 오류: {str(e)}")
            return {
                "error": str(e),
                "repo_id": f"{self.repo_owner}/{self.repo_name}" if self.repo_owner and self.repo_name else "unknown"
            }
    
    async def get_repo_info(self) -> Dict[str, Any]:
        """
        저장소 기본 정보 조회
        
        Returns:
            저장소 정보
        """
        # 실제 구현에서는 GitHub API 또는 로컬 저장소에서 정보 추출
        # 여기서는 샘플 데이터 반환
        return {
            "name": self.repo_name or "sample-project",
            "owner": self.repo_owner or "sample-owner",
            "description": "샘플 프로젝트 설명",
            "default_branch": "main",
            "stars": 42,
            "forks": 7,
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-06-01T00:00:00Z"
        }
    
    async def analyze_languages(self) -> Dict[str, float]:
        """
        저장소 언어 통계 분석
        
        Returns:
            언어별 사용 비율
        """
        # 실제 구현에서는 GitHub API 또는 로컬 파일 분석
        # 여기서는 샘플 데이터 반환
        return {
            "Python": 65.7,
            "JavaScript": 20.3,
            "HTML": 8.5,
            "CSS": 5.5
        }
    
    async def detect_frameworks(self) -> List[Dict[str, Any]]:
        """
        프레임워크 탐지
        
        Returns:
            탐지된 프레임워크 목록
        """
        # 실제 구현에서는 파일 내용 분석
        # 여기서는 샘플 데이터 반환
        return [
            {
                "name": "Flask",
                "language": "Python",
                "confidence": 0.9,
                "version": "2.0.1",
                "files": ["app.py", "requirements.txt"]
            },
            {
                "name": "React",
                "language": "JavaScript",
                "confidence": 0.8,
                "version": "18.2.0",
                "files": ["package.json", "src/App.jsx"]
            }
        ]
    
    async def analyze_dependencies(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        종속성 분석
        
        Returns:
            언어별 종속성 목록
        """
        # 실제 구현에서는 package.json, requirements.txt 등 분석
        # 여기서는 샘플 데이터 반환
        return {
            "python": [
                {"name": "flask", "version": "2.0.1", "is_dev": False},
                {"name": "numpy", "version": "1.21.0", "is_dev": False},
                {"name": "pytest", "version": "6.2.5", "is_dev": True}
            ],
            "javascript": [
                {"name": "react", "version": "18.2.0", "is_dev": False},
                {"name": "axios", "version": "0.24.0", "is_dev": False},
                {"name": "jest", "version": "27.5.1", "is_dev": True}
            ]
        }
    
    async def check_ci_cd_config(self) -> Dict[str, Any]:
        """
        CI/CD 구성 확인
        
        Returns:
            CI/CD 구성 정보
        """
        # 실제 구현에서는 .github/workflows, .gitlab-ci.yml 등 확인
        # 여기서는 샘플 데이터 반환
        return {
            "github_actions": {
                "exists": True,
                "workflows": ["ci.yml", "deploy.yml"]
            },
            "travis_ci": {
                "exists": False
            },
            "circle_ci": {
                "exists": False
            }
        }
    
    async def evaluate_ai_readiness(self) -> Tuple[float, List[str]]:
        """
        AI 준비도 평가
        
        Returns:
            (준비도 점수, 개선 제안 목록) 튜플
        """
        # 실제 구현에서는 여러 요소를 고려하여 평가
        # 여기서는 샘플 데이터 반환
        readiness = 0.75
        suggestions = [
            "requirements.txt에 필수 AI 라이브러리 추가 (tensorflow, scikit-learn)",
            "모델 배포를 위한 CI/CD 파이프라인 구성",
            "모델 서빙을 위한 API 엔드포인트 구현",
            "모델 훈련 스크립트 추가"
        ]
        
        return readiness, suggestions


async def analyze_repository(repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    저장소 분석 함수
    
    Args:
        repo_data: 저장소 정보
        
    Returns:
        분석 결과
    """
    repo_url = repo_data.get("url")
    repo_path = repo_data.get("path")
    
    analyzer = GitHubRepositoryAnalyzer(repo_path, repo_url)
    result = await analyzer.analyze()
    
    return result
