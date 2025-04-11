"""
GitHub 저장소 관리 모듈

저장소 생성, 조회, 업데이트, 삭제 등의 기능을 제공합니다.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from backend.database.models import GitHubRepository, Settings, User, UserActivity
from backend.database.operations.settings import get_settings
from .models import GitHubRepositoryData


class RepositoryService:
    """GitHub 저장소 관리 서비스"""
    
    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db
        self.settings = get_settings(db)
    
    def get_repository(self, repo_id: Optional[int] = None) -> GitHubRepository:
        """
        저장소 정보를 가져옵니다. repo_id가 제공되지 않은 경우 기본 저장소를 반환합니다.
        
        Args:
            repo_id: 저장소 ID (선택 사항)
            
        Returns:
            저장소 정보
        """
        if repo_id:
            # 특정 ID의 저장소 조회
            repo = self.db.query(GitHubRepository).filter(GitHubRepository.id == repo_id).first()
            if not repo:
                raise HTTPException(status_code=404, detail=f"저장소 ID {repo_id}를 찾을 수 없습니다.")
            return repo
        
        # 기본 저장소 조회
        repo = self.db.query(GitHubRepository).filter(GitHubRepository.is_default == True).first()
        
        # 기본 저장소가 없으면 전역 설정 확인
        if not repo and self.settings and self.settings.github_token:
            # 전역 설정에서 임시 저장소 객체 생성
            repo = GitHubRepository(
                name=self.settings.github_repo or "default",
                github_owner=self.settings.github_username or "unknown",
                token=self.settings.github_token,
                is_default=True,
                url="",
                user_id=1  # 임시 사용자 ID
            )
        
        if not repo:
            raise HTTPException(
                status_code=400, 
                detail="GitHub 저장소가 설정되지 않았습니다. 설정에서 GitHub 정보를 먼저 설정하거나 저장소를 추가해주세요."
            )
        
        return repo
    
    def create_repository(self, repo_data) -> GitHubRepository:
        """
        새로운 GitHub 저장소 정보를 데이터베이스에 추가합니다.
        
        Args:
            repo_data: 추가할 저장소 정보
            
        Returns:
            저장된 저장소 정보
        """
        try:
            # 필수 필드 검증
            if not hasattr(repo_data, 'name') or not repo_data.name:
                raise HTTPException(status_code=400, detail="저장소 이름은 필수입니다.")
            
            if not hasattr(repo_data, 'owner') or not repo_data.owner:
                raise HTTPException(status_code=400, detail="저장소 소유자는 필수입니다.")
            
            if not hasattr(repo_data, 'token') or not repo_data.token:
                raise HTTPException(status_code=400, detail="GitHub 토큰은 필수입니다.")
            
            # 프로젝트 ID가 있는 경우 프로젝트 존재 여부 확인
            project_id = getattr(repo_data, 'project_id', None)
            
            # 기본 저장소로 설정하려는 경우 기존 기본 저장소 해제
            is_default = getattr(repo_data, 'is_default', False)
            if is_default:
                default_repos = self.db.query(GitHubRepository).filter(GitHubRepository.is_default == True).all()
                for repo in default_repos:
                    repo.is_default = False
                    self.db.add(repo)
            
            # 새 저장소 생성
            name = getattr(repo_data, 'name', '')
            description = getattr(repo_data, 'description', None)
            owner = getattr(repo_data, 'owner', '')
            token = getattr(repo_data, 'token', '')
            is_private = getattr(repo_data, 'is_private', True)
            branch = getattr(repo_data, 'branch', 'main')
            
            # Boolean 타입 검증
            if isinstance(is_private, str):
                is_private = is_private.lower() == 'true'
            
            if isinstance(is_default, str):
                is_default = is_default.lower() == 'true'
            
            # 명시적으로 컬럼을 지정하여 repo_info 컬럼 사용하지 않음
            from sqlalchemy import insert
            from backend.database.models import GitHubRepository
            
            # 저장소 데이터 준비
            repo_values = {
                "name": name,
                "description": description,
                "github_owner": owner,  # owner 대신 github_owner 사용
                "token": token,
                "is_default": is_default,
                "is_private": is_private,
                "branch": branch,
                "url": f"https://github.com/{owner}/{name}",
                "user_id": getattr(repo_data, 'user_id', 1),  # user_id 필드 추가
                "project_id": project_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # SQLAlchemy Core를 사용하여 직접 쿼리 실행
            stmt = insert(GitHubRepository).values(**repo_values)
            result = self.db.execute(stmt)
            self.db.commit()
            
            # 새로 생성된 저장소 ID 가져오기
            new_repo_id = result.inserted_primary_key[0]
            
            # 저장소 객체 조회
            new_repo = self.db.query(GitHubRepository).filter(GitHubRepository.id == new_repo_id).first()
            
            self.db.add(new_repo)
            self.db.commit()
            self.db.refresh(new_repo)
            
            return new_repo
        except HTTPException:
            raise
        except Exception as e:
            # DB 세션 롤백
            self.db.rollback()
            print(f"저장소 생성 오류: {str(e)}")
            raise HTTPException(status_code=500, detail=f"저장소 정보를 추가하는 중 오류가 발생했습니다: {str(e)}")
    
    def update_repository(self, repo_id: int, repo_data: Dict[str, Any]) -> GitHubRepository:
        """
        GitHub 저장소 정보를 업데이트합니다.
        
        Args:
            repo_id: 업데이트할 저장소 ID
            repo_data: 업데이트할 정보
            
        Returns:
            업데이트된 저장소 정보
        """
        repo = self.db.query(GitHubRepository).filter(GitHubRepository.id == repo_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail=f"저장소 ID {repo_id}를 찾을 수 없습니다.")
        
        # 기본 저장소로 설정하려는 경우 기존 기본 저장소 해제
        if repo_data.get("is_default") and not repo.is_default:
            default_repos = self.db.query(GitHubRepository).filter(GitHubRepository.is_default == True).all()
            for default_repo in default_repos:
                default_repo.is_default = False
                self.db.add(default_repo)
        
        # 저장소 정보 업데이트
        for key, value in repo_data.items():
            if hasattr(repo, key) and value is not None:
                setattr(repo, key, value)
        
        # URL 업데이트
        if repo_data.get("owner") or repo_data.get("name"):
            repo.url = f"https://github.com/{repo.owner}/{repo.name}"
        
        self.db.commit()
        self.db.refresh(repo)
        
        return repo
    
    def delete_repository(self, repo_id: int) -> Dict[str, Any]:
        """
        GitHub 저장소 정보를 삭제합니다.
        
        Args:
            repo_id: 삭제할 저장소 ID
            
        Returns:
            삭제 결과
        """
        repo = self.db.query(GitHubRepository).filter(GitHubRepository.id == repo_id).first()
        if not repo:
            raise HTTPException(status_code=404, detail=f"저장소 ID {repo_id}를 찾을 수 없습니다.")
        
        # 삭제할 저장소가 기본 저장소인 경우 다른 저장소를 기본으로 설정
        if repo.is_default:
            new_default = self.db.query(GitHubRepository).filter(GitHubRepository.id != repo_id).first()
            if new_default:
                new_default.is_default = True
                self.db.add(new_default)
        
        # 저장소 삭제
        self.db.delete(repo)
        self.db.commit()
        
        return {"message": f"저장소 ID {repo_id}가 삭제되었습니다."}
    
    def get_repositories(self, project_id: Optional[int] = None) -> List[GitHubRepository]:
        """
        GitHub 저장소 목록을 조회합니다.
        
        Args:
            project_id: 특정 프로젝트의 저장소만 조회할 경우 프로젝트 ID
            
        Returns:
            저장소 목록
        """
        try:
            # 안전하게 컬럼을 명시적으로 선택하여 쿼리
            query = self.db.query(
                GitHubRepository.id,
                GitHubRepository.name,
                GitHubRepository.description,
                GitHubRepository.owner,
                GitHubRepository.token,
                GitHubRepository.is_default,
                GitHubRepository.is_private,
                GitHubRepository.url,
                GitHubRepository.branch,
                GitHubRepository.project_id,
                GitHubRepository.created_at,
                GitHubRepository.updated_at
            )
            
            if project_id:
                query = query.filter(GitHubRepository.project_id == project_id)
            
            # GitHubRepository 객체로 조합
            result = []
            for row in query.all():
                repo = GitHubRepository(
                    id=row.id,
                    name=row.name,
                    description=row.description,
                    owner=row.owner,
                    token=row.token,
                    is_default=row.is_default,
                    is_private=row.is_private,
                    url=row.url,
                    branch=row.branch,
                    project_id=row.project_id,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                result.append(repo)
            
            return result
        except Exception as e:
            # 오류 로깅
            print(f"저장소 목록 조회 중 오류 발생: {str(e)}")
            # 빈 목록 반환
            return []
