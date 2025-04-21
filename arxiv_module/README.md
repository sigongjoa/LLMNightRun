# arXiv CS/AI 논문 크롤링 및 분석 모듈

이 모듈은 arXiv API를 사용하여 컴퓨터 과학(CS) 및 인공지능(AI) 관련 논문을 검색하고, 다운로드하며, 핵심 키워드를 추출하고 요약을 생성하는 기능을 제공합니다. 추출된 데이터는 기존 vectorDB에 저장되어 효율적으로 관리되고 검색할 수 있습니다.

## 주요 기능

- **arXiv API 연동**: CS/AI 카테고리의 논문 검색 및 필터링
- **PDF 다운로드**: 논문 PDF 자동 다운로드
- **텍스트 처리**: PDF에서 텍스트 추출 및 전처리
- **키워드 추출**: TF-IDF 및 TextRank 알고리즘 기반 핵심 키워드 추출
- **요약 생성**: 추출적 요약 및 LLM 기반 생성적 요약
- **vectorDB 연동**: 기존 vectorDB와 연동하여 논문 데이터 저장 및 검색
- **사용자 친화적 GUI**: PyQt5 기반 직관적인 사용자 인터페이스

## 시스템 요구사항

- Python 3.8 이상
- 필요 라이브러리: arxiv, PyQt5, PyPDF2, nltk, scikit-learn, networkx 등
- 로컬 LLM API (요약 생성 시 선택적 사용)

## 설치 방법

1. 저장소 클론 또는 다운로드:
   ```
   git clone https://[repository_url]/LLMNightRun_feature.git
   cd LLMNightRun_feature/arxiv_module
   ```

2. 필요한 패키지 설치:
   ```
   pip install -r requirements.txt
   ```

3. NLTK 데이터 다운로드 (자동으로 진행되지만, 수동으로도 가능):
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   nltk.download('wordnet')
   ```

## 사용 방법

### GUI 애플리케이션 실행

```
python main.py
```

GUI 애플리케이션은 다음과 같은 탭으로 구성됩니다:

1. **검색 탭**: 키워드, 카테고리, 날짜 범위를 지정하여 논문 검색
2. **결과 탭**: 검색 결과 확인 및 논문 분석
3. **내 라이브러리 탭**: 저장된 논문 관리
4. **설정 탭**: 애플리케이션 설정

### 모듈별 사용법

각 모듈은 독립적으로도 사용할 수 있습니다:

```python
# 논문 검색 및 다운로드
from arxiv_module.crawler import ArxivCrawler

crawler = ArxivCrawler()
papers = crawler.search(query="transformer", categories=["cs.AI", "cs.LG"])
crawler.download_paper(papers[0]['entry_id'])

# 텍스트 처리 및 키워드 추출
from arxiv_module.processor import TextProcessor
from arxiv_module.keyword_extractor import KeywordExtractor

processor = TextProcessor()
text_data = processor.process_pdf("papers/sample.pdf")

extractor = KeywordExtractor()
keywords = extractor.extract_keywords(text_data)

# 요약 생성
from arxiv_module.summarizer import Summarizer

summarizer = Summarizer()
summary = summarizer.generate_summary(text_data, keywords, title="Sample Paper")

# vectorDB 저장
from arxiv_module.vector_db_handler import ArxivVectorDBHandler

db_handler = ArxivVectorDBHandler()
db_handler.add_paper({
    'id': 'sample_id',
    'title': 'Sample Paper',
    'summary': 'Sample summary',
    'keywords': keywords
})
```

## 폴더 구조

```
arxiv_module/
├── __init__.py           # 패키지 초기화
├── main.py               # 메인 애플리케이션 진입점
├── requirements.txt      # 의존성 목록
├── crawler.py            # arXiv API 크롤링 모듈
├── processor.py          # 텍스트 처리 모듈
├── keyword_extractor.py  # 키워드 추출 모듈
├── summarizer.py         # 요약 생성 모듈
├── vector_db_handler.py  # vectorDB 연동 모듈
├── papers/               # 다운로드된 논문 저장소
└── gui/                  # GUI 관련 모듈
    ├── __init__.py       # GUI 패키지 초기화
    ├── main_window.py    # 메인 윈도우 구현
    ├── search_panel.py   # 검색 패널 구현
    └── results_panel.py  # 결과 표시 패널 구현
```

## vectorDB 연동

이 모듈은 기존 vectorDB와 연동하여 논문 데이터를 저장하고 검색합니다. `vector_db_handler.py` 모듈에서 다음과 같은 기능을 제공합니다:

- 논문 데이터 추가/업데이트/삭제
- 텍스트 임베딩 생성 및 저장
- 유사 논문 검색
- 키워드 기반 검색

기존의 vector_db 모듈의 벡터 스토어와 인코더를 활용하여 논문 데이터를 효율적으로 관리합니다.

## 키워드 추출 알고리즘

이 모듈은 두 가지 방식의 키워드 추출 알고리즘을 사용합니다:

1. **TF-IDF(Term Frequency-Inverse Document Frequency)**: 텍스트에서 단어의 중요도를 통계적으로 계산
2. **TextRank**: 문서 내 단어 간의 관계를 그래프로 모델링하여 중요 단어 추출

두 알고리즘의 결과를 결합하여 더 정확한 키워드를 추출합니다.

## 요약 생성 방식

두 가지 방식의 요약 생성 기능을 제공합니다:

1. **추출적 요약(Extractive Summarization)**: 원본 텍스트에서 중요 문장을 선택하여 요약
2. **생성적 요약(Abstractive Summarization)**: LLM을 활용하여 텍스트의 핵심 내용을 새롭게 생성

로컬 LLM이 사용 가능한 경우 생성적 요약을 제공하고, 그렇지 않은 경우 추출적 요약만 제공합니다.

## 확장 계획

향후 다음과 같은 기능 추가를 계획하고 있습니다:

- **다중 학술 DB 통합**: Semantic Scholar, IEEE Xplore 등 다른 학술 DB와의 통합
- **인용 그래프 분석**: 논문 간 인용 관계 시각화 및 분석
- **연구 트렌드 분석**: 시간에 따른 주제 변화 및 트렌드 분석
- **개인화된 추천**: 사용자 관심사 기반 논문 추천 시스템

## 기여 방법

1. 이슈 등록: 버그 신고 또는 기능 요청은 이슈 트래커를 통해 등록해 주세요.
2. 풀 리퀘스트: 코드 개선이나 새로운 기능을 구현하셨다면 풀 리퀘스트를 보내주세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하세요.
