@echo off
cd /d %~dp0
echo CORS 패치가 적용된 백엔드 서버를 시작합니다...
python patch_cors.py
