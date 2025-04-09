# LLM Scraper 사용 가이드

## 설치 및 설정

### 필수 요구사항

- Python 3.8 이상
- Chrome 브라우저 (또는 Chromium)
- 인터넷 연결
- 각 LLM 서비스의 계정 (ChatGPT, Claude, Gemini)

### 패키지 설치

```bash
# 필요한 패키지 설치
cd D:\LLMNightRun
pip install -r llm_scraper/requirements.txt

# 웹드라이버 설치 (자동)
# webdriver-manager 패키지가 자동으로 처리합니다
```

### 자격 증명 설정

LLM 서비스에 로그인하기 위한 자격 증명을 제공하는 방법은 두 가지가 있습니다:

#### 1. 환경 변수 사용

```bash
# Windows
set LLM_SCRAPER_CHATGPT_USERNAME=your_openai_email
set LLM_SCRAPER_CHATGPT_PASSWORD=your_openai_password
set LLM_SCRAPER_CLAUDE_USERNAME=your_anthropic_email
set LLM_SCRAPER_CLAUDE_PASSWORD=your_anthropic_password
set LLM_SCRAPER_GEMINI_USERNAME=your_google_email
set LLM_SCRAPER_GEMINI_PASSWORD=your_google_password

# Linux/Mac
export LLM_SCRAPER_CHATGPT_USERNAME=your_openai_email
export LLM_SCRAPER_CHATGPT_PASSWORD=your_openai_password
# 기타 변수도 동일하게 설정
```

#### 2. 자격 증명 파일 사용

`credentials.json` 파일 생성:

```json
{
  "chatgpt": {
    "username": "your_openai_email",
    "password": "your_openai_password"
  },
  "claude": {
    "username": "your_anthropic_email",
    "password": "your_anthropic_password"
  },
  "gemini": {
    "username": "your_google_email",
    "password": "your_google_password"
  }
}
```

## 기본 사용법

### 단일 모델 실행

```bash
# ChatGPT 사용
python -m llm_scraper.main --model web/chatgpt --prompt "우주의 크기를 설명해주세요"

# Claude 사용
python -m llm_scraper.main --model web/claude --prompt "우주의 크기를 설명해주세요"

# Gemini 사용
python -m llm_scraper.main --model web/gemini --prompt "우주의 크기를 설명해주세요"
```

### 파일에서 프롬프트 읽기

```bash
# 파일에서 프롬프트 읽기
python -m llm_scraper.main --model web/chatgpt --prompt-file my_prompt.txt
```

### 모든 모델 실행 및 비교

```bash
# 모든 모델로 동일한 프롬프트 실행 및 응답 비교
python -m llm_scraper.main --model all --prompt "인공지능의 미래는 어떻게 될까요?" --compare
```

### 헤드리스 모드 실행

```bash
# 브라우저 UI를 표시하지 않고 실행 (서버 환경에 유용)
python -m llm_scraper.main --model web/chatgpt --prompt "양자 컴퓨팅이란?" --headless
```

### 출력 형식 지정

```bash
# JSON 형식으로 출력 (기본값)
python -m llm_scraper.main --model web/claude --prompt "블록체인 기술 설명" --output-format json

# CSV 형식으로 출력
python -m llm_scraper.main --model web/claude --prompt "블록체인 기술 설명" --output-format csv

# Markdown 형식으로 출력
python -m llm_scraper.main --model web/claude --prompt "블록체인 기술 설명" --output-format md

# 텍스트 형식으로 출력
python -m llm_scraper.main --model web/claude --prompt "블록체인 기술 설명" --output-format txt
```

### 배치 처리

여러 프롬프트를 일괄 처리하려면 JSON 또는 CSV 형식의 배치 파일을 생성합니다:

**batch_prompts.json** (예시):
```json
[
  "인공지능이란 무엇인가?",
  "머신러닝과 딥러닝의 차이점은?",
  "강화학습의 기본 원리를 설명하세요",
  "자연어 처리의 주요 과제는 무엇인가요?"
]
```

또는 **batch_prompts.csv** (예시):
```csv
prompt
"인공지능이란 무엇인가?"
"머신러닝과 딥러닝의 차이점은?"
"강화학습의 기본 원리를 설명하세요"
"자연어 처리의 주요 과제는 무엇인가요?"
```

배치 파일 실행:
```bash
# 배치 파일로 여러 프롬프트 처리
python -m llm_scraper.main --model web/gemini --batch batch_prompts.json

# 모든 모델로 배치 처리 및 비교
python -m llm_scraper.main --model all --batch batch_prompts.json --compare
```

### 브라우저 프로필 사용

브라우저 프로필을 지정하여 로그인 세션을 유지할 수 있습니다:

```bash
# 브라우저 프로필 디렉토리 지정
python -m llm_scraper.main --model web/claude --prompt "양자역학 설명" --user-data-dir "./browser_profiles/claude"
```

## 고급 사용법

### 타임아웃 설정

```bash
# 타임아웃 값 증가 (초 단위)
python -m llm_scraper.main --model web/chatgpt --prompt "긴 소설을 써줘" --timeout 300
```

### 디버그 모드

```bash
# 디버그 모드 활성화 (상세 로깅)
python -m llm_scraper.main --model web/gemini --prompt "프롬프트 엔지니어링 팁" --debug
```

### 사용자 정의 구성 파일

기본 설정을 재정의하는 사용자 정의 구성 파일을 생성할 수 있습니다:

**custom_config.yaml** (예시):
```yaml
browser:
  type: chrome
  headless: true
  timeout: 120

output:
  format: md
  directory: "custom_output"

models:
  chatgpt:
    url: "https://chat.openai.com/"
    selectors:
      # 사용자 정의 선택자 (필요한 경우)
```

사용자 정의 구성 사용:
```bash
python -m llm_scraper.main --model web/chatgpt --prompt "AI 윤리" --config custom_config.yaml
```

## 출력 및 결과 분석

### 출력 파일 위치

기본적으로 모든 출력은 `llm_scraper/output` 디렉토리에 저장됩니다. 이는 `--output-dir` 옵션으로 변경할 수 있습니다.

### 출력 파일 형식

각 파일은 다음 형식으로 이름이 지정됩니다:
```
{model_name}_{timestamp}.{format}
```

예: `chatgpt_20230415_123045.json`

### 비교 결과 분석

`--compare` 옵션을 사용하면 비교 결과가 다음 형식으로 저장됩니다:
```
comparison_{timestamp}.json
```

비교 파일에는 다음 정보가 포함됩니다:
- 원본 프롬프트
- 각 모델의 응답
- 응답 길이, 단어 수 등의 기본 메트릭
- 최소/최대 길이 응답 식별
- 평균 응답 길이

## 문제 해결

### 로그인 문제

- **2단계 인증 요구**: 헤드리스 모드를 비활성화하고 2단계 인증을 수동으로 완료한 후 `--user-data-dir` 옵션을 사용하여 세션을 유지합니다.
- **CAPTCHA 도전**: 헤드리스 모드를 비활성화하고 CAPTCHA를 수동으로 완료합니다.

### 선택자 문제

웹 인터페이스가 변경되면 `config/config.yaml` 파일에서 선택자를 업데이트해야 할 수 있습니다:

```yaml
models:
  chatgpt:
    selectors:
      # 업데이트된 선택자
      prompt_textarea: "새로운_선택자"
```

### 일반적인 오류

- **타임아웃 오류**: `--timeout` 값을 늘려보세요.
- **응답 추출 실패**: 디버그 모드를 활성화하고 로그를 확인하세요.
- **브라우저 드라이버 오류**: webdriver-manager를 업데이트하거나 수동으로 드라이버를 설치하세요.

## 고려사항 및 제한사항

- 이 도구는 개인 학습 및 연구 목적으로만 사용하세요.
- 각 서비스의 이용 약관을 숙지하고 준수하세요.
- 과도한 자동화된 쿼리는 계정 제한으로 이어질 수 있습니다.
- 헤드리스 모드는 일부 사이트에서 봇 감지를 트리거할 수 있습니다.
- 웹 인터페이스는 예고 없이 변경될 수 있으므로 정기적으로 스크레이퍼를 업데이트하세요.

## 로깅 및 디버깅

로그 파일은 `logs` 디렉토리에 저장되며 다음 형식으로 이름이 지정됩니다:
```
llm_scraper_{date}.log
```

디버그 모드에서는 다음과 같은 추가 정보가 로깅됩니다:
- 세부적인 브라우저 작업
- 선택자 정보
- 대기 시간 및 타임아웃
- 오류 및 예외의 전체 스택 트레이스
