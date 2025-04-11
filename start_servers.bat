@echo off
echo LLMNightRun Server Startup
echo =========================
echo.
echo 디버그 수정 사항:
echo 1. 헬스 체크 엔드포인트 추가 (/health-check)
echo 2. 메모리 관련 엔드포인트 추가 (/memory/search, /memory/count, /memory/health)
echo 3. GitHub AI 분석기 API 엔드포인트 추가
echo 4. 모델 설치 API 엔드포인트 추가 (/model-installer/analyze 등)
echo.

:: 백엔드 서버 시작
echo Starting Backend Server...
start cmd /k "cd /d D:\LLMNightRun && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

:: 잠시 대기
timeout /t 5

:: 프론트엔드 서버 시작 (프론트엔드 서버가 npm을 사용하는 경우)
echo Starting Frontend Server...
start cmd /k "cd /d D:\LLMNightRun\frontend && npm run dev"

echo.
echo Servers started!
echo Backend running at: http://localhost:8000
echo Frontend running at: http://localhost:3000
echo.
echo 백엔드 API 확인:
echo - 헬스 체크: http://localhost:8000/health-check
echo - GitHub 분석: http://localhost:8000/model-installer/analyze
echo.
echo Press any key to exit this window...
pause > nul