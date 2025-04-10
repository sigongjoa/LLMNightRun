import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# 현재 디렉토리를 프로젝트 루트로 변경
os.chdir(project_root)

# uvicorn 모듈 임포트 및 직접 실행
import uvicorn

if __name__ == "__main__":
    uvicorn.run("backend.main_fix:app", host="0.0.0.0", port=8000, reload=True)
