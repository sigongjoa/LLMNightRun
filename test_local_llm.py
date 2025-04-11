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

# 로컬 LLM 엔드포인트 테스트 함수
def test_local_llm_status():
    """
    로컬 LLM 상태 엔드포인트를 테스트합니다.
    """
    print("=" * 50)
    print("로컬 LLM 상태 엔드포인트 테스트")
    print("=" * 50)
    
    try:
        # 엔드포인트 요청
        response = requests.get("http://localhost:8000/api/local-llm/status", timeout=5)
        
        # 응답 확인
        if response.status_code == 200:
            data = response.json()
            print("로컬 LLM 상태 요청 성공:")
            print(f"상태 코드: {response.status_code}")
            print(f"응답 데이터: {data}")
            
            # 연결 상태에 따른 메시지 표시
            if data.get("connected", False):
                print("✅ LM Studio에 연결되었습니다.")
                print(f"사용 중인 모델: {data.get('model_id')}")
            else:
                print("❌ LM Studio에 연결할 수 없습니다.")
                print(f"오류 메시지: {data.get('error')}")
                
            return True
        else:
            print(f"로컬 LLM 상태 요청 실패: 상태 코드 {response.status_code}")
            print(f"응답 내용: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("서버 연결 오류: 서버가 실행 중인지 확인하세요.")
        return False
    except Exception as e:
        print(f"테스트 오류: {str(e)}")
        return False

# 로컬 LLM 핑 테스트 함수
def test_local_llm_ping():
    """
    로컬 LLM 핑 엔드포인트를 테스트합니다.
    """
    print("=" * 50)
    print("로컬 LLM 핑 엔드포인트 테스트")
    print("=" * 50)
    
    try:
        # 엔드포인트 요청
        response = requests.get("http://localhost:8000/api/local-llm/ping", timeout=5)
        
        # 응답 확인
        if response.status_code == 200:
            data = response.json()
            print("로컬 LLM 핑 요청 성공:")
            print(f"상태 코드: {response.status_code}")
            print(f"응답 데이터: {data}")
            return True
        else:
            print(f"로컬 LLM 핑 요청 실패: 상태 코드 {response.status_code}")
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
    print("2. 로컬 LLM 상태 테스트")
    print("3. 로컬 LLM 핑 테스트")
    print("4. 서버 시작 및 모든 테스트")
    
    choice = input("선택 (1-4): ")
    
    if choice == "1":
        run_backend()
    elif choice == "2":
        test_local_llm_status()
    elif choice == "3":
        test_local_llm_ping()
    elif choice == "4":
        # 백엔드를 별도 스레드에서 실행
        backend_thread = threading.Thread(target=run_backend)
        backend_thread.daemon = True
        backend_thread.start()
        
        # 테스트 실행 전 서버가 시작될 때까지 대기
        print("서버가 시작될 때까지 대기 중...")
        time.sleep(5)
        
        # 상태 테스트
        status_success = test_local_llm_status()
        
        # 핑 테스트
        ping_success = test_local_llm_ping()
        
        # 결과 출력
        print("\n" + "=" * 50)
        print("테스트 결과 요약:")
        print(f"로컬 LLM 상태 테스트: {'성공' if status_success else '실패'}")
        print(f"로컬 LLM 핑 테스트: {'성공' if ping_success else '실패'}")
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
        print("잘못된 선택입니다. 1, 2, 3, 또는 4를 입력하세요.")
