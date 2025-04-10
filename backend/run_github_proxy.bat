@echo off
cd /d %~dp0
echo GitHub 저장소 전용 프록시 서버를 시작합니다...
echo 포트 8001에서 실행 중
python github-proxy.py
