구현된 백엔드 구성 요소:

1. FastAPI 기반 서버 (main.py)  
* API 엔드포인트 및 라우팅
* 오류 처리 및 응답 형식


2. 데이터 모델 및 데이터베이스 연결
* Pydantic 모델 정의
* SQLAlchemy ORM 구현
* CRUD 작업 함수


3. LLM API 연동
* OpenAI, Claude API 호출 기능
* 오류 처리 및 재시도 메커니즘


3. 웹 크롤링 모듈
* Selenium 기반 자동화
* ChatGPT, Claude 웹 인터페이스 통합


4. GitHub 연동
* 결과를 마크다운으로 변환
* 저장소에 자동 커밋, PR 생성


5. 코드 관리 모듈
* 코드 스니펫 추출 및 저장
* 버전 관리 및 태그 시스템
* 유사 코드 검색 및 비교


6. 스케줄러
* 작업 예약 및 실행
* 상태 저장 및 복원



7. 구현된 프론트엔드 구성 요소:

* 대시보드 (index.tsx)
* 시스템 통계 및 요약
* 최근 질문 목록


8. 질문 제출 페이지 (submit.tsx)
* 다중 LLM 선택 인터페이스
* 태그 관리 시스템


9. 결과 비교 페이지 (results.tsx)
* 여러 LLM 응답 비교 뷰
* GitHub 업로드 통합


10. 코드 관리 페이지 (code-manager.tsx)
* 코드 스니펫 표시 및 편집
* 언어별 필터링 및 검색


11. 설정 페이지 (settings.tsx)
* API 키 및 GitHub 토큰 관리
* 웹 크롤링 계정 설정



12. 추가 파일:

* 환경 설정 (.env)
* API 키 및 서버 구성

* README 문서
* 설치 및 사용 방법 안내
의존성 정의 (requirements.txt)  
필요한 Python 패키지 목록