@echo off
cd /d %~dp0
echo CORS 헤더가 추가된 백엔드 서버를 시작합니다...
python cors_fix.py
