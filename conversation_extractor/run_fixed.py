"""
Claude 대화 도구 실행 스크립트 (수정된 버전)
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
            if library == "opencv-python":
                try:
                    import cv2
                    print(f"✓ {library} 확인 완료")
                except ImportError:
                    print(f"• {library} 설치 중...")
                    subprocess.call([sys.executable, "-m", "pip", "install", library])
            elif library == "pytesseract":
                try:
                    import pytesseract
                    print(f"✓ {library} 확인 완료")
                except ImportError:
                    print(f"• {library} 설치 중...")
                    subprocess.call([sys.executable, "-m", "pip", "install", library])
            elif library == "pillow":
                try:
                    from PIL import Image
                    print(f"✓ {library} 확인 완료")
                except ImportError:
                    print(f"• {library} 설치 중...")
                    subprocess.call([sys.executable, "-m", "pip", "install", library])
            elif library == "numpy":
                try:
                    import numpy
                    print(f"✓ {library} 확인 완료")
                except ImportError:
                    print(f"• {library} 설치 중...")
                    subprocess.call([sys.executable, "-m", "pip", "install", library])
            elif library == "pyautogui":
                try:
                    import pyautogui
                    print(f"✓ {library} 확인 완료")
                except ImportError:
                    print(f"• {library} 설치 중...")
                    subprocess.call([sys.executable, "-m", "pip", "install", library])
        except Exception as e:
            print(f"! {library} 설치 중 오류 발생: {e}")
            print(f"  수동으로 설치하세요: pip install {library}")

def main():
    print("=" * 50)
    print("Claude 대화 도구 시작하기 (수정된 버전)")
    print("=" * 50)
    print("필요한 라이브러리를 확인합니다...")
    
    # 필요한 라이브러리 확인 및 설치
    check_and_install_libraries()
    
    print("\nClaude 대화 도구를 시작합니다...")
    
    # 수정된 스크립트 실행
    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "claude_conversation_tool_fixed.py")
        subprocess.call([sys.executable, script_path])
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        input("계속하려면 아무 키나 누르세요...")

if __name__ == "__main__":
    main()
