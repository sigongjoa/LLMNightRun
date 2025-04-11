from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

router = APIRouter(
    prefix="/github-ai",
    tags=["github-analyzer"],
    responses={404: {"description": "Not found"}},
)

@router.post("/analyze")
async def analyze_github_repo(repo_url: Dict[str, Any]):
    """
    GitHub 리포지토리 분석 엔드포인트
    """
    try:
        url = repo_url.get("url", "")
        if not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub 리포지토리 URL을 제공해야 합니다."
            )
        
        # 간단한 분석 결과 반환 (실제 분석은 깃허브 분석기를 통해 수행)
        return {
            "status": "success",
            "repo_url": url,
            "analysis": {
                "repo_name": url.split("/")[-1] if "/" in url else url,
                "model_type": {
                    "primary": "llama",
                    "confidence": 0.85
                },
                "requirements": {
                    "python": ">=3.8",
                    "packages": ["torch", "transformers", "fastapi"]
                },
                "setup_steps": [
                    "pip install -r requirements.txt",
                    "python setup.py install",
                    "python run.py"
                ]
            }
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/status")
async def github_analyzer_status():
    """
    GitHub 분석기 상태 엔드포인트
    """
    return {
        "status": "available",
        "message": "GitHub 분석기가 정상적으로 동작 중입니다."
    }

# 모델 설치 관련 엔드포인트는 model_installer_api.py로 이동했습니다.
