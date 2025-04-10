"""
백엔드 서버 실행 스크립트
"""

import os
import sys
import uvicorn
from backend.config import settings

def main():
    """백엔드 서버 실행 함수"""
    # 실행 안내 메시지
    print("=" * 80)
    print(f"  {settings.app_name} 백엔드 서버 실행")
    print(f"  환경: {settings.env.value.upper()}")
    print(f"  host: {settings.host}")
    print(f"  port: {settings.port}")
    print(f"  debug: {settings.debug}")
    print(f"  log_level: {settings.logging.level}")
    print("=" * 80)
    
    # 서버 실행
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.logging.level.lower()
    )

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    main()
