#!/bin/bash

echo "Starting LLMNightRun Backend Server..."

echo "Starting Primary API Server on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
PRIMARY_PID=$!

echo "Starting Backup API Server on port 8001..."
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
BACKUP_PID=$!

echo "Servers are running!"
echo "Primary server (PID: $PRIMARY_PID): http://localhost:8000"
echo "Backup server (PID: $BACKUP_PID): http://localhost:8001"
echo ""
echo "Press Ctrl+C to stop all servers..."

# 종료 시 서브 프로세스도 함께 종료
trap "kill $PRIMARY_PID $BACKUP_PID; exit" SIGINT SIGTERM

# 부모 프로세스가 종료될 때까지 대기
wait
