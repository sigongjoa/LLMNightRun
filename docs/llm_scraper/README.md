# LLM Scraper 문서

LLM Scraper는 LLMNightRun 프로젝트의 일부로서, 웹 기반 대형 언어 모델(LLM)의 출력을 자동으로 수집하고 비교하는 도구입니다.

## 목차

1. [개요](overview.md) - LLM Scraper 시스템 개요 및 아키텍처
2. [사용 가이드](usage_guide.md) - 설치, 설정 및 사용 방법
3. [프론트엔드 통합](frontend_integration.md) - LLMNightRun 프론트엔드 통합 가이드

## 문서 구성

- **개요**: LLM Scraper의 목적, 주요 기능, 아키텍처 및 작동 방식에 대한 전반적인 개요를 제공합니다.
- **사용 가이드**: 독립형 도구로서 LLM Scraper의 설치, 설정 및 명령줄 인터페이스를 통한 사용 방법을 자세히 설명합니다.
- **프론트엔드 통합**: LLM Scraper를 LLMNightRun 프로젝트의 웹 인터페이스와 통합하는 방법에 대한 가이드를 제공합니다.

## 주요 기능

- ChatGPT, Claude, Gemini 웹 인터페이스 자동화
- 동일한 프롬프트에 대해 여러 모델의 응답 비교
- 다양한 출력 형식 지원 (JSON, CSV, Markdown, 텍스트)
- 배치 처리를 통한 다중 프롬프트 실행
- 프론트엔드 통합을 위한 API 엔드포인트

## 시작하기

```bash
# 필요한 패키지 설치
pip install -r llm_scraper/requirements.txt

# 단일 모델로 프롬프트 실행
python -m llm_scraper.main --model web/chatgpt --prompt "인공지능이란 무엇인가?"

# 모든 모델로 프롬프트 실행 및 비교
python -m llm_scraper.main --model all --prompt "인공지능이란 무엇인가?" --compare
```

## 기술 스택

- **Python 3.8+**: 코어 언어
- **Selenium**: 웹 브라우저 자동화
- **FastAPI**: API 엔드포인트 (향후 프론트엔드 통합)
- **React/Next.js**: 프론트엔드 (통합 시)

## 프론트엔드 통합 상태

현재 LLM Scraper는 독립 실행형 Python 모듈로만 구현되어 있으며, LLMNightRun 프론트엔드와의 통합은 개발 중입니다. 프론트엔드 통합 문서는 통합을 위한 구현 가이드를 제공합니다.

## 참고 사항

- 이 도구는 연구 및 개인 학습 목적으로만 사용하세요.
- 각 서비스의 이용 약관을 준수하세요.
- 웹 인터페이스는 변경될 수 있으므로 정기적인 업데이트가 필요합니다.
