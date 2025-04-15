"""
Claude 대화 도구 실행 스크립트
"""

import os
import sys
import subprocess

def check_and_install_libraries():
    """필요한 라이브러리 확인 및 설치"""
    required_libraries = [
        "opencv-python",
        "pytesseract",
        "pillow",
        "numpy",
        "pyautogui"
    ]
    
    for library in required_libraries:
        try:
            __import__(library.replace("-", "_"))
            print(f"✓ {library} 확인 완료")
        except ImportError:
            print(f"• {library} 설치 중...")
            subprocess.call([sys.executable, "-m", "pip", "install", library])
            print(f"✓ {library} 설치 완료")

def main():
    print("=" * 50)
    print("Claude 대화 도구 시작하기")
    print("=" * 50)
    print("필요한 라이브러리를 확인합니다...")
    
    # 필요한 라이브러리 확인 및 설치
    check_and_install_libraries()
    
    print("\nClaude 대화 도구를 시작합니다...")
    
    # 현재 디렉토리에서 claude_conversation_tool.py 실행
    try:
        from claude_conversation_tool import main
        main()
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        input("계속하려면 아무 키나 누르세요...")

if __name__ == "__main__":
    main()
