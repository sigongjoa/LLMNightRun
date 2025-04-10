@echo off
title LLMNightRun 임시 수정 버전
echo ======================================================================
echo  LLMNightRun 임시 수정 버전 실행 (project_id 컬럼 문제 해결)
echo ======================================================================
echo.
echo 이 스크립트는 project_id 컬럼 문제를 해결한 LLMNightRun 임시 버전을 실행합니다.
echo 두 개의 창이 열립니다:
echo  1. 백엔드 API 서버 (Python/FastAPI)
echo  2. 프론트엔드 UI 서버 (Next.js)
echo.
echo 브라우저에서 http://localhost:3000 에 접속해 UI 대시보드를 사용하세요.
echo API 문서는 http://localhost:8000/docs 에서 확인할 수 있습니다.
echo.
echo 시작하려면 아무 키나 누르세요...
pause > nul

echo 백엔드 서버 시작 중...
start "LLMNightRun 백엔드 (임시 수정)" cmd /k "python run_backend_fix.py"

echo 프론트엔드 서버 시작 중...
start "LLMNightRun 프론트엔드" cmd /k "run_frontend_fix.bat"

echo.
echo 모든 서버가 시작되었습니다.
echo 브라우저에서 http://localhost:3000 에 접속해 UI 대시보드를 사용하세요.
echo 이 창을 닫아도 서버는 계속 실행됩니다.
echo.
