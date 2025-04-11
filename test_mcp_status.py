import os
import sys
import requests
import time
import threading
import subprocess
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

# MCP 상태 엔드포인트 테스트 함수
def test_mcp_status():
    """
    MCP 상태 엔드포인트를 테스트합니다.
    """
    print("=" * 50)
    print("MCP 상태 엔드포인트 테스트")
    print("=" * 50)
    
    try:
        # 서버가 시작될 때까지 대기
        time.sleep(3)
        
        # 엔드포인트 요청
        response = requests.get("http://localhost:8000/api/mcp/status", timeout=5)
        
        # 응답 확인
        if response.status_code == 200:
            data = response.json()
            print("MCP 상태 요청 성공:")
            print(f"상태 코드: {response.status_code}")
            print(f"응답 데이터: {data}")
            return True
        else:
            print(f"MCP 상태 요청 실패: 상태 코드 {response.status_code}")
            print(f"응답 내용: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("서버 연결 오류: 서버가 실행 중인지 확인하세요.")
        return False
    except Exception as e:
        print(f"테스트 오류: {str(e)}")
        return False

# 서버 시작 함수
def run_backend():
    """
    백엔드 서버를 시작합니다.
    """
    os.chdir(ROOT_DIR)
    print("=" * 50)
    print("백엔드 서버 시작 중...")
    print("URL: http://localhost:8000")
    print("=" * 50)
    
    os.system("uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload")

if __name__ == "__main__":
    # 사용자에게 실행할 항목 선택 요청
    print("테스트 실행 옵션:")
    print("1. 백엔드 서버 시작")
    print("2. MCP 상태 테스트")
    print("3. 서버 시작 및 테스트")
    
    choice = input("선택 (1-3): ")
    
    if choice == "1":
        run_backend()
    elif choice == "2":
        test_mcp_status()
    elif choice == "3":
        # 백엔드를 별도 스레드에서 실행
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()
        
        # 테스트 실행
        time.sleep(5)  # 서버가 시작될 때까지 대기
        success = test_mcp_status()
        
        # 결과 출력
        print("\n" + "=" * 50)
        print(f"테스트 결과: {'성공' if success else '실패'}")
        print("=" * 50)
        
        # 계속 실행 여부 확인
        keep_running = input("\n서버를 계속 실행하시겠습니까? (y/n): ")
        if keep_running.lower() != "y":
            print("프로그램을 종료합니다.")
            sys.exit(0)
        else:
            # 서버 스레드가 종료될 때까지 대기
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n프로그램을 종료합니다.")
                sys.exit(0)
    else:
        print("잘못된 선택입니다. 1, 2, 또는 3을 입력하세요.")
