"""
GitHub 생성 API 모듈

GitHub 커밋 메시지 및 README 생성 관련 API 엔드포인트를 제공합니다.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from ...database.connection import get_db

# 라우터 정의
router = APIRouter(
    prefix="/generate",
    tags=["github"],
    responses={404: {"description": "Not found"}},
)

@router.get("/commit-message/{question_id}", response_model=Dict[str, str])
async def generate_commit_message(
    question_id: int,
    repo_id: Optional[int] = Query(None, description="저장소 ID"),
    db: Session = Depends(get_db)
):
    """
    GitHub 커밋 메시지를 생성합니다. (스텁 구현)
    """
    return {
        "message": f"feat: Add solution for question #{question_id}"
    }


@router.get("/readme/{question_id}", response_model=Dict[str, str])
async def generate_readme(
    question_id: int,
    repo_id: Optional[int] = Query(None, description="저장소 ID"),
    db: Session = Depends(get_db)
):
    """
    GitHub README 파일을 생성합니다. (스텁 구현)
    """
    return {
        "content": f"""# 질문 #{question_id} 솔루션

이 저장소는 질문 #{question_id}에 대한 솔루션을 포함하고 있습니다.

## 파일 구성

- `main.py` - 메인 코드
- `util.py` - 유틸리티 함수
- `README.md` - 이 파일

## 사용 방법

```python
from main import solution

result = solution()
print(result)
```
"""
    }
