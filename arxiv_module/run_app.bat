@echo off
echo ArXiv CS/AI Paper Analyzer
echo ===========================
echo.
echo 필요한 NLTK 데이터를 설정합니다...
python nltk_setup.py
echo.
echo NLTK 데이터 설정 완료
echo.
echo 애플리케이션을 시작합니다...
python main.py
echo.
echo 종료되었습니다.
pause
