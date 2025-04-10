"""
GitHub 저장소 관리 모듈

저장소 생성, 조회, 업데이트, 삭제 등의 기능을 제공합니다.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.database.models import GitHubRepository, Settings
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
                owner=self.settings.github_username or "unknown",
                token=self.settings.github_token,
                is_default=True
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
            
            new_repo = GitHubRepository(
                name=name,
                description=description,
                owner=owner,
                token=token,
                is_default=is_default,
                is_private=is_private,
                branch=branch,
                url=f"https://github.com/{owner}/{name}",
                project_id=project_id
            )
            
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
        query = self.db.query(GitHubRepository)
        
        if project_id:
            query = query.filter(GitHubRepository.project_id == project_id)
        
        return query.all()
