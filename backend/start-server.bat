@echo off
echo Starting LLMNightRun Backend Server...

echo Starting Primary API Server on port 8000...
start cmd /k "cd /d %~dp0 && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting Backup API Server on port 8001...
start cmd /k "cd /d %~dp0 && uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

echo Servers are starting! You can access them at:
echo Primary server: http://localhost:8000
echo Backup server: http://localhost:8001
echo.
echo Press any key to close this window...
pause > nul
