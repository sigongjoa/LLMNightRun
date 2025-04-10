@echo off
title 데이터베이스 마이그레이션
echo ======================================================================
echo  LLMNightRun 데이터베이스 마이그레이션
echo ======================================================================
echo.
echo 이 스크립트는 데이터베이스 스키마를 업데이트하여
echo questions 및 responses 테이블에 project_id 컬럼을 추가합니다.
echo.
echo 주의: 마이그레이션 전에 데이터베이스 백업이 자동으로 생성됩니다.
echo 문제가 발생할 경우 백업을 사용하여 복원할 수 있습니다.
echo.

cd /d %~dp0
python scripts\migrate_db.py

echo.
echo 엔터 키를 눌러 종료하세요...
pause > nul
