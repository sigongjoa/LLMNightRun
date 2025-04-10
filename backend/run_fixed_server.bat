@echo off
cd /d %~dp0
echo CORS 문제가 해결된 FastAPI 서버를 시작합니다...
echo 포트 8002에서 실행 중 (기존 백엔드와 포트 충돌 방지)
python -m uvicorn main_cors_fixed:app --host 0.0.0.0 --port 8002 --reload
