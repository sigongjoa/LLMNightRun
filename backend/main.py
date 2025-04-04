from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import uvicorn
import os
from dotenv import load_dotenv  
import datetime

# 내부 모듈 가져오기
# 상대 경로 임포트로 변경
from .models import Question, Response, LLMType, CodeSnippet
from .database.connection import get_db
from .database.operations import (
    get_questions,
    create_question,
    get_responses,
    create_response,
    get_code_snippets,
    create_code_snippet
)
from .llm_api import get_llm_response
from .github_uploader import upload_to_github
from .codebase_api import router as codebase_router
from .indexing_api import router as indexing_router
from .routers.agent import router as agent_router

# 환경 변수 로드
load_dotenv()

app = FastAPI(title="LLMNightRun API", description="멀티 LLM 통합 자동화 플랫폼 API")


@app.get("/")
async def root():
    return {"message": "LLMNightRun API에 오신 것을 환영합니다!"}

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 오리진 허용, 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "LLMNightRun API에 오신 것을 환영합니다!"}

# 질문 관련 엔드포인트
@app.post("/questions/", response_model=Question)
async def submit_question(question: Question, db=Depends(get_db)):
    """새로운 질문을 제출합니다."""
    return create_question(db, question)

@app.get("/questions/", response_model=List[Question])
async def list_questions(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    """모든 질문을 조회합니다."""
    return get_questions(db, skip=skip, limit=limit)

# 응답 관련 엔드포인트
@app.post("/responses/", response_model=Response)
async def submit_response(response: Response, db=Depends(get_db)):
    """새로운 응답을 저장합니다. (수동 등록용)"""
    return create_response(db, response)

@app.get("/responses/", response_model=List[Response])
async def list_responses(
    question_id: Optional[int] = None, 
    llm_type: Optional[LLMType] = None,
    skip: int = 0, 
    limit: int = 100, 
    db=Depends(get_db)
):
    """응답을 조회합니다. 선택적으로 질문 ID나 LLM 유형으로 필터링 가능합니다."""
    return get_responses(db, question_id=question_id, llm_type=llm_type, skip=skip, limit=limit)

# LLM API 요청 엔드포인트
@app.post("/ask/{llm_type}")
async def ask_llm(llm_type: LLMType, question: Question, db=Depends(get_db)):
    """LLM API에 질문을 요청하고 결과를 저장합니다."""
    try:
        # 질문 저장
        saved_question = create_question(db, question)
        # LLM에 질문 요청
        response_text = get_llm_response(llm_type, question.content)
        
        # 응답 생성 및 저장
        response = Response(
            question_id=saved_question.id,
            llm_type=llm_type,
            content=response_text
        )
        saved_response = create_response(db, response)
        
        return {
            "question": saved_question,
            "response": saved_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 코드 스니펫 관련 엔드포인트
@app.post("/code-snippets/", response_model=CodeSnippet)
async def create_code(code_snippet: CodeSnippet, db=Depends(get_db)):
    """새로운 코드 스니펫을 생성합니다."""
    return create_code_snippet(db, code_snippet)

@app.get("/code-snippets/", response_model=List[CodeSnippet])
async def list_code_snippets(
    language: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    """코드 스니펫을 조회합니다. 언어나 태그로 필터링 가능합니다."""
    return get_code_snippets(db, language=language, tag=tag, skip=skip, limit=limit)

# GitHub 업로드 엔드포인트
@app.post("/github/upload")
async def upload_response_to_github(question_id: int, db=Depends(get_db)):
    """특정 질문의 모든 응답을 GitHub에 업로드합니다."""
    try:
        # 질문과 모든 응답 조회
        question = get_questions(db, question_id=question_id, single=True)
        responses = get_responses(db, question_id=question_id)
        
        if not question:
            raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다")
        
        # GitHub에 업로드
        github_url = upload_to_github(question, responses)
        
        return {"message": "GitHub에 성공적으로 업로드되었습니다", "url": github_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    시스템 헬스 체크 엔드포인트.
    쿠버네티스, 도커 또는 기타 모니터링 도구에서 사용할 수 있습니다.
    """
    try:
        # 데이터베이스 연결 확인
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "version": "0.1.0",  # 애플리케이션 버전
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, 500


# 질문 관련 엔드포인트
@app.post("/questions/", response_model=Question)
async def submit_question(question: Question, db=Depends(get_db)):
    """새로운 질문을 제출합니다."""
    return create_question(db, question)

@app.get("/questions/", response_model=List[Question])
async def list_questions(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    """모든 질문을 조회합니다."""
    return get_questions(db, skip=skip, limit=limit)

# 응답 관련 엔드포인트
@app.post("/responses/", response_model=Response)
async def submit_response(response: Response, db=Depends(get_db)):
    """새로운 응답을 저장합니다. (수동 등록용)"""
    return create_response(db, response)

@app.get("/responses/", response_model=List[Response])
async def list_responses(
    question_id: Optional[int] = None, 
    llm_type: Optional[LLMType] = None,
    skip: int = 0, 
    limit: int = 100, 
    db=Depends(get_db)
):
    """응답을 조회합니다. 선택적으로 질문 ID나 LLM 유형으로 필터링 가능합니다."""
    return get_responses(db, question_id=question_id, llm_type=llm_type, skip=skip, limit=limit)

# LLM API 요청 엔드포인트
@app.post("/ask/{llm_type}")
async def ask_llm(llm_type: LLMType, question: Question, db=Depends(get_db)):
    """LLM API에 질문을 요청하고 결과를 저장합니다."""
    try:
        # 질문 저장
        saved_question = create_question(db, question)
        # LLM에 질문 요청
        response_text = get_llm_response(llm_type, question.content)
        
        # 응답 생성 및 저장
        response = Response(
            question_id=saved_question.id,
            llm_type=llm_type,
            content=response_text
        )
        saved_response = create_response(db, response)
        
        return {
            "question": saved_question,
            "response": saved_response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 코드 스니펫 관련 엔드포인트
@app.post("/code-snippets/", response_model=CodeSnippet)
async def create_code(code_snippet: CodeSnippet, db=Depends(get_db)):
    """새로운 코드 스니펫을 생성합니다."""
    return create_code_snippet(db, code_snippet)

@app.get("/code-snippets/", response_model=List[CodeSnippet])
async def list_code_snippets(
    language: Optional[str] = None,
    tag: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    """코드 스니펫을 조회합니다. 언어나 태그로 필터링 가능합니다."""
    return get_code_snippets(db, language=language, tag=tag, skip=skip, limit=limit)

# GitHub 업로드 엔드포인트
@app.post("/github/upload")
async def upload_response_to_github(question_id: int, db=Depends(get_db)):
    """특정 질문의 모든 응답을 GitHub에 업로드합니다."""
    try:
        # 질문과 모든 응답 조회
        question = get_questions(db, question_id=question_id, single=True)
        responses = get_responses(db, question_id=question_id)
        
        if not question:
            raise HTTPException(status_code=404, detail="질문을 찾을 수 없습니다")
        
        # GitHub에 업로드
        github_url = upload_to_github(question, responses)
        
        return {"message": "GitHub에 성공적으로 업로드되었습니다", "url": github_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(codebase_router)
app.include_router(indexing_router)
app.include_router(agent_router)

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)