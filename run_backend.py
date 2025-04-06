import os
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.abspath("."))

# uvicorn 실행
import uvicorn

if __name__ == "__main__":
    # app 모듈을 PYTHONPATH에 추가
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    # absolute 경로 사용
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
