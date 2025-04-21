# arXiv CS/AI 논문 분석기

arXiv CS/AI 카테고리의 논문을 검색하고, 다운로드하며, 분석할 수 있는 데스크톱 애플리케이션입니다.

## 주요 기능

- arXiv API를 통한 CS/AI 카테고리 논문 검색
- 논문 PDF 다운로드 및 관리
- 자동 키워드 추출 및 요약 생성
- 논문 라이브러리 관리 및 벡터 검색

## 설치 방법

1. 저장소 클론:
```bash
git clone https://github.com/your-username/arxiv-analyzer.git
cd arxiv-analyzer
```

2. 필요한 패키지 설치:
```bash
pip install -r arxiv_module/requirements.txt
```

3. 실행:
```bash
cd arxiv_module
python main.py
```
또는 Windows에서는 `run_app.bat` 파일을 실행하세요.

## 사용 방법

1. "Search Papers" 탭에서 키워드, 저자, 날짜 등으로 논문을 검색합니다.
2. 검색 결과에서 관심 있는 논문을 선택하여 상세 정보를 확인합니다.
3. "Actions" 탭에서 논문을 처리하고 라이브러리에 저장합니다.
4. "My Library" 탭에서 저장된 논문을 관리하고 검색합니다.

## 최근 업데이트

- datetime 객체의 JSON 직렬화 문제 해결
- 논문 업데이트 기능 구현
- 라이브러리 데이터 표시 개선
- 오류 처리 및 로깅 강화

## 요구 사항

- Python 3.7 이상
- PyQt5
- NLTK
- Sentence-Transformers
- arXiv API 클라이언트
- VectorDB (로컬 벡터 데이터베이스)

## 문제 해결

- 애플리케이션 실행 중 오류가 발생하면 `arxiv_app.log` 파일을 확인하세요.
- NLTK 데이터가 누락된 경우 자동으로 다운로드를 시도합니다.

## 줄 바꿈 문자(Line Ending) 관련 주의사항

이 프로젝트는 Windows와 Linux/Mac 환경 모두에서 개발될 수 있으므로, Git에서 줄 바꿈 문자 변환 관련 경고가 발생할 수 있습니다. 필요한 경우 다음 Git 설정을 고려하세요:

```bash
# Windows 사용자:
git config --global core.autocrlf true

# Linux/Mac 사용자:
git config --global core.autocrlf input
```

## 라이선스

[라이선스 정보를 여기에 추가]

## 기여 방법

1. 이 저장소를 포크합니다.
2. 새 기능 브랜치를 만듭니다 (`git checkout -b feature/amazing-feature`).
3. 변경 사항을 커밋합니다 (`git commit -m 'Add some amazing feature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`).
5. Pull Request를 생성합니다.
