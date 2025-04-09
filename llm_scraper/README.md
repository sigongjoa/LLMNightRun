# LLM Scraper

웹 기반 대형 언어 모델(LLM)의 출력을 자동으로 수집하고 비교하는 도구입니다.

## 개요

LLM Scraper는 ChatGPT, Claude, Gemini와 같은 웹 UI 기반 LLM의 출력을 자동으로 크롤링하고 수집합니다. 동일한 프롬프트에 대해 여러 웹 LLM의 응답을 비교할 수 있으며, API 호출이 제한적이거나 유료인 경우에도 실험을 지속할 수 있습니다.

## 주요 기능

- 여러 LLM 웹 인터페이스(ChatGPT, Claude, Gemini) 자동화
- 단일 프롬프트 또는 배치 파일을 통한 다중 프롬프트 처리
- 여러 모델 응답의 비교 및 분석
- 다양한 출력 형식 지원(JSON, CSV, Markdown, 텍스트)
- 브라우저 프로필을 통한 세션 관리

## 설치

1. 의존성 설치:

```bash
pip install -r requirements.txt
```

2. 웹드라이버 설정:
   - Chrome/Chromium 사용 시 Chrome 브라우저가 설치되어 있어야 합니다.
   - webdriver-manager를 통해 자동으로 설치됩니다.

## 필수 환경 변수

각 모델의 인증 정보는 다음과 같은 환경 변수로 설정할 수 있습니다:

```
LLM_SCRAPER_CHATGPT_USERNAME=your_openai_username
LLM_SCRAPER_CHATGPT_PASSWORD=your_openai_password
LLM_SCRAPER_CLAUDE_USERNAME=your_claude_username
LLM_SCRAPER_CLAUDE_PASSWORD=your_claude_password
LLM_SCRAPER_GEMINI_USERNAME=your_google_username
LLM_SCRAPER_GEMINI_PASSWORD=your_google_password
```

또는 다음과 같은 JSON 형식의 자격 증명 파일을 사용할 수 있습니다:

```json
{
  "chatgpt": {
    "username": "your_openai_username",
    "password": "your_openai_password"
  },
  "claude": {
    "username": "your_claude_username",
    "password": "your_claude_password"
  },
  "gemini": {
    "username": "your_google_username",
    "password": "your_google_password"
  }
}
```

## 사용법

### 기본 사용법

```bash
# ChatGPT로 프롬프트 실행
python -m llm_scraper.main --model web/chatgpt --prompt "Explain photosynthesis"

# Claude로 프롬프트 실행
python -m llm_scraper.main --model web/claude --prompt "Explain photosynthesis"

# Gemini로 프롬프트 실행
python -m llm_scraper.main --model web/gemini --prompt "Explain photosynthesis"

# 모든 모델로 동일한 프롬프트 실행 및 응답 비교
python -m llm_scraper.main --model all --prompt "Explain photosynthesis" --compare
```

### 추가 옵션

```bash
# 헤드리스 모드로 실행 (브라우저 UI 표시 없음)
python -m llm_scraper.main --model web/chatgpt --prompt "What is AI?" --headless

# 파일에서 프롬프트 읽기
python -m llm_scraper.main --model web/claude --prompt-file my_prompt.txt

# 배치 모드로 여러 프롬프트 실행
python -m llm_scraper.main --model web/gemini --batch prompts.json

# 출력 형식 지정
python -m llm_scraper.main --model web/chatgpt --prompt "What is Python?" --output-format md

# 브라우저 프로필 디렉토리 지정 (로그인 세션 유지)
python -m llm_scraper.main --model web/claude --prompt "Explain quantum physics" --user-data-dir "./browser_profiles/claude"

# 자격 증명 파일 지정
python -m llm_scraper.main --model all --prompt "How do neural networks work?" --credentials-file credentials.json
```

### 모든 옵션 보기

```bash
python -m llm_scraper.main --help
```

## 구성

구성은 `config/config.yaml` 파일에서 관리됩니다. 이 파일을 수정하여 기본 동작을 변경할 수 있습니다.

## 출력

기본적으로 응답은 `output` 디렉토리에 저장됩니다. 각 파일은 타임스탬프와 모델 이름을 포함하여 고유하게 생성됩니다.

## 모델 비교

`--compare` 옵션을 사용하여 여러 모델의 응답을 비교할 수 있습니다. 이는 `--model all` 옵션과 함께 사용하거나 배치 모드에서 사용할 수 있습니다. 비교 결과는 JSON 파일로 저장됩니다.

## 제한사항 및 고려사항

- 웹 인터페이스는 시간이 지남에 따라 변경될 수 있으므로 선택자를 업데이트해야 할 수 있습니다.
- 각 서비스의 이용 약관을 준수하세요. 이 도구는 개인 연구 및 교육 목적으로만 사용해야 합니다.
- CAPTCHA 또는 이중 인증이 필요한 경우 자동 로그인이 작동하지 않을 수 있습니다. 이 경우 `--user-data-dir` 옵션을 사용하여 기존 브라우저 세션을 활용할 수 있습니다.
- 헤드리스 모드에서는 일부 웹사이트가 봇 감지를 트리거할 수 있습니다. 문제가 발생하면 헤드리스 모드를 비활성화하세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
