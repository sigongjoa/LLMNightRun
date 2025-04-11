import os
import sys
import time
import threading
import subprocess
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

def run_backend():
    os.chdir(ROOT_DIR)
    print("=" * 50)
    print("백엔드 서버 시작 중...")
    print("URL: http://localhost:8000")
    print("헬스 체크 엔드포인트: http://localhost:8000/health-check")
    print("=" * 50)
    
    os.system("uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")

def run_frontend():
    os.chdir(ROOT_DIR)
    print("=" * 50)
    print("프론트엔드 서버 시작 중...")
    print("URL: http://localhost:3000")
    print("=" * 50)
    
    os.system("npm run dev")

def test_health_check():
    """백엔드 서버의 health-check 엔드포인트 테스트"""
    import requests
    import time
    
    # 서버가 시작될 때까지 대기
    time.sleep(5)
    
    try:
        response = requests.get("http://localhost:8000/health-check", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"헬스 체크 성공: {data}")
            return True
        else:
            print(f"헬스 체크 실패: 상태 코드 {response.status_code}")
            return False
    except Exception as e:
        print(f"헬스 체크 오류: {str(e)}")
        return False

if __name__ == "__main__":
    # 사용자에게 실행할 항목 선택 요청
    print("테스트 실행 옵션:")
    print("1. 백엔드 서버만 실행")
    print("2. 프론트엔드 서버만 실행")
    print("3. 백엔드와 프론트엔드 모두 실행 (별도 터미널에서)")
    print("4. 백엔드 헬스 체크 테스트")
    
    choice = input("선택 (1-4): ")
    
    if choice == "1":
        run_backend()
    elif choice == "2":
        run_frontend()
    elif choice == "3":
        # 백엔드와 프론트엔드를 별도 스레드에서 실행
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()
        
        # 백엔드가 시작될 때까지 잠시 대기
        time.sleep(3)
        
        # 프론트엔드 실행
        run_frontend()
    elif choice == "4":
        # 백엔드를 별도 스레드에서 실행
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()
        
        # 테스트 실행
        success = test_health_check()
        print(f"테스트 결과: {'성공' if success else '실패'}")
        
        # 시스템 종료 전에 몇 초 대기
        time.sleep(5)
    else:
        print("잘못된 선택입니다.")
