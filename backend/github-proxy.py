"""
GitHub 저장소 전용 CORS 프록시 서버

이 스크립트는 GitHub 저장소 API 요청만 처리하는 독립 서버를 실행합니다.
프론트엔드에서 CORS 오류가 지속될 경우, 이 프록시 서버를 사용하세요.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

app = FastAPI(title="GitHub Repository CORS Proxy")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 오리진 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 샘플 데이터
SAMPLE_REPOS = [
    {
        "id": 1,
        "name": "sample-project",
        "owner": "user123",
        "description": "샘플 GitHub 프로젝트입니다.",
        "is_default": True,
        "is_private": False,
        "url": "https://github.com/user123/sample-project",
        "branch": "main",
        "token": "ghp_sampletoken12345",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    },
    {
        "id": 2,
        "name": "private-repo",
        "owner": "organization",
        "description": "비공개 저장소 예시입니다.",
        "is_default": False,
        "is_private": True,
        "url": "https://github.com/organization/private-repo",
        "branch": "main",
        "token": "ghp_privatetoken67890",
        "created_at": "2023-02-01T00:00:00Z",
        "updated_at": "2023-02-01T00:00:00Z"
    }
]

# GET /github-repos/ 엔드포인트
@app.get("/github-repos/")
async def list_repositories():
    """저장소 목록 반환"""
    return SAMPLE_REPOS

# POST /github-repos/ 엔드포인트
@app.post("/github-repos/")
async def create_repository(request: Request):
    """새 저장소 생성"""
    body = await request.json()
    new_repo = {
        "id": len(SAMPLE_REPOS) + 1,
        "name": body.get("name", "new-repo"),
        "owner": body.get("owner", "default-user"),
        "description": body.get("description", ""),
        "is_default": body.get("is_default", False),
        "is_private": body.get("is_private", True),
        "url": f"https://github.com/{body.get('owner', 'default-user')}/{body.get('name', 'new-repo')}",
        "branch": body.get("branch", "main"),
        "token": body.get("token", "ghp_newtoken12345"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    SAMPLE_REPOS.append(new_repo)
    return new_repo

# GET /github-repos/{repo_id} 엔드포인트
@app.get("/github-repos/{repo_id}")
async def get_repository(repo_id: int):
    """특정 저장소 정보 반환"""
    for repo in SAMPLE_REPOS:
        if repo["id"] == repo_id:
            return repo
    return {"error": "Repository not found"}

# PUT /github-repos/{repo_id} 엔드포인트
@app.put("/github-repos/{repo_id}")
async def update_repository(repo_id: int, request: Request):
    """저장소 정보 업데이트"""
    body = await request.json()
    for i, repo in enumerate(SAMPLE_REPOS):
        if repo["id"] == repo_id:
            for key, value in body.items():
                if key in repo:
                    SAMPLE_REPOS[i][key] = value
            SAMPLE_REPOS[i]["updated_at"] = datetime.now().isoformat()
            return SAMPLE_REPOS[i]
    return {"error": "Repository not found"}

# DELETE /github-repos/{repo_id} 엔드포인트
@app.delete("/github-repos/{repo_id}")
async def delete_repository(repo_id: int):
    """저장소 삭제"""
    global SAMPLE_REPOS
    original_count = len(SAMPLE_REPOS)
    SAMPLE_REPOS = [repo for repo in SAMPLE_REPOS if repo["id"] != repo_id]
    if len(SAMPLE_REPOS) < original_count:
        return {"message": f"Repository with ID {repo_id} deleted"}
    return {"error": "Repository not found"}

# 루트 경로
@app.get("/")
async def root():
    """루트 경로"""
    return {
        "message": "GitHub Repository API Proxy Server",
        "endpoints": [
            "/github-repos/ (GET, POST)",
            "/github-repos/{repo_id} (GET, PUT, DELETE)"
        ]
    }

# 서버 실행
if __name__ == "__main__":
    print("GitHub 저장소 프록시 서버 시작 중...")
    uvicorn.run(
        "github-proxy:app",
        host="0.0.0.0",
        port=8001,  # 메인 백엔드와 다른 포트 사용
        reload=True
    )
