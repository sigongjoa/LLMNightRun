@echo off
echo Claude 대화 추출기를 시작합니다...
echo.

REM Python 확인
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 Python을 설치해주세요.
    pause
    exit /b
)

REM 필요한 라이브러리 확인 및 설치
echo 필요한 라이브러리를 확인합니다...
python -c "import tkinter" > nul 2>&1 || echo tkinter는 Python과 함께 설치됩니다.
python -c "import cv2" > nul 2>&1 || pip install opencv-python
python -c "import pytesseract" > nul 2>&1 || pip install pytesseract
python -c "import PIL" > nul 2>&1 || pip install pillow
python -c "import numpy" > nul 2>&1 || pip install numpy

echo.
echo 대화 추출기를 실행합니다...
python conversation_extractor_gui.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo 오류가 발생했습니다. 로그를 확인해주세요.
    pause
)
