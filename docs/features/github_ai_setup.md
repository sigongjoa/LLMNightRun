# GitHub AI 환경 자동설정 시스템

GitHub AI 환경 자동설정 시스템은 GitHub 저장소를 분석하여 AI 모델 유형을 식별하고 필요한 환경을 자동으로 설정하는 기능을 제공합니다.

## 개요

AI 프로젝트를 설정하는 것은 종종 복잡하고 시간이 많이 소요되는 작업입니다. GitHub AI 환경 자동설정 시스템은 이 과정을 자동화하여 사용자가 빠르게 프로젝트를 시작할 수 있도록 도와줍니다. 이 시스템은 GitHub 저장소의 코드, 설정 파일, 의존성 등을 분석하여 필요한 환경을 자동으로 구성합니다.

## 주요 기능

- **자동 모델 유형 식별**: 저장소 코드를 분석하여 LLaMA, Mistral, Stable Diffusion 등의 모델 유형을 자동으로 식별합니다.
- **의존성 분석**: requirements.txt, environment.yml 등의 파일을 분석하여 필요한 패키지와 의존성을 식별합니다.
- **설정 파일 분석**: 설정 파일을 분석하여 모델 실행에 필요한 설정을 식별합니다.
- **실행 스크립트 식별**: 모델 실행에 필요한 스크립트를 자동으로 식별합니다.
- **환경 자동 설정**: 분석 결과를 바탕으로 모델 실행에 필요한 환경을 자동으로 설정합니다.
- **모델 자동 설치**: 식별된 모델을 자동으로 다운로드하고 설치합니다.

## 시스템 구조

GitHub AI 환경 자동설정 시스템은 다음과 같은 컴포넌트로 구성됩니다:

### 핵심 클래스 

- `GitHubAnalyzer`: GitHub 저장소를 분석하는 클래스로, 모델 유형, 의존성, 설정 파일 등을 식별합니다.

### 주요 메서드

- `clone_repository()`: GitHub 저장소를 클론합니다.
- `analyze()`: 저장소를 분석하고 결과를 반환합니다.
- `_analyze_file_structure()`: 저장소의 파일 구조를 분석합니다.
- `_analyze_readme()`: README 파일을 분석합니다.
- `_analyze_requirements()`: 요구사항 파일을 분석합니다.
- `_analyze_config_files()`: 설정 파일을 분석합니다.
- `_identify_model_type()`: 모델 유형을 식별합니다.
- `_identify_launch_scripts()`: 실행 스크립트를 식별합니다.

## 분석 과정

1. **저장소 클론**: 입력된 GitHub URL을 클론합니다.
2. **파일 구조 분석**: 저장소의 파일 구조를 분석하여 주요 파일과 디렉토리를 식별합니다.
3. **README 분석**: README 파일을 분석하여 프로젝트 정보와 설치 지침을 추출합니다.
4. **요구사항 분석**: requirements.txt, environment.yml 등의 파일을 분석하여 필요한 패키지를 식별합니다.
5. **설정 파일 분석**: YAML, JSON, INI 등의 설정 파일을 분석하여 모델 설정을 추출합니다.
6. **모델 유형 식별**: 파일 구조와 코드를 분석하여 모델 유형(LLaMA, Mistral, Stable Diffusion 등)을 식별합니다.
7. **실행 스크립트 식별**: 모델 실행에 필요한 스크립트를 식별합니다.

## 모델 유형 식별

시스템은 다음과 같은 모델 유형을 식별할 수 있습니다:

- **LLaMA**: LLaMA, Alpaca, Vicuna 등의 키워드로 식별합니다.
- **Mistral**: Mistral 키워드로 식별합니다.
- **Stable Diffusion**: Stable Diffusion, diffusion 등의 키워드로 식별합니다.
- **GPT**: GPT, MiniGPT, TinyGPT 등의 키워드로 식별합니다.
- **BERT**: BERT, RoBERTa, Electra 등의 키워드로 식별합니다.
- **T5**: T5, FLAN-T5 등의 키워드로 식별합니다.
- **Hugging Face**: Transformers, Hugging Face, Tokenizers 등의 키워드로 식별합니다.

## 실행 스크립트 식별

시스템은 다음과 같은 패턴의 실행 스크립트를 식별합니다:

- run.py, app.py, main.py, inference.py, demo.py
- predict.py, serve.py, start.py, server.py
- gradio_*.py, streamlit_*.py, web_*.py
- *.sh, run_*.py, launch_*.py

## 사용 방법

### 웹 인터페이스에서 사용

1. GitHub AI 환경 자동설정 페이지로 이동합니다.
2. GitHub 저장소 URL을 입력합니다.
3. "저장소 분석" 버튼을 클릭합니다.
4. 분석 결과를 확인하고 "다음" 버튼을 클릭합니다.
5. "환경 설정 적용" 버튼을 클릭하여 환경을 설정합니다.
6. "모델 설치" 버튼을 클릭하여 모델을 설치합니다.
7. 설치가 완료되면 모델을 사용할 수 있습니다.

### API 사용

#### 저장소 분석

```
POST /model-installer/analyze
{
  "url": "https://github.com/username/repository"
}
```

응답:

```json
{
  "repo_name": "repository",
  "repo_url": "https://github.com/username/repository",
  "clone_path": "models/repository",
  "model_type": {
    "primary": "llama",
    "all_detected": {
      "llama": 5,
      "huggingface": 2
    }
  },
  "file_structure": [...],
  "readme": {
    "content": "...",
    "full_path": "models/repository/README.md"
  },
  "requirements": {
    "requirements.txt": {
      "content": "...",
      "path": "models/repository/requirements.txt"
    }
  },
  "config_files": {...},
  "launch_scripts": [...]
}
```

#### 환경 설정

```
POST /model-installer/setup
{
  "url": "https://github.com/username/repository",
  "analysis": { ... }
}
```

응답:

```json
{
  "success": true,
  "message": "환경 설정이 완료되었습니다.",
  "setup_details": { ... }
}
```

#### 모델 설치

```
POST /model-installer/install
{
  "url": "https://github.com/username/repository"
}
```

응답:

```json
{
  "success": true,
  "message": "모델 설치가 시작되었습니다.",
  "installation_id": "install_123456"
}
```

#### 설치 상태 확인

```
GET /model-installer/status/{installation_id}
```

응답:

```json
{
  "status": "running",
  "progress": 45,
  "logs": [
    "패키지 설치 중...",
    "모델 다운로드 중...",
    "......"
  ]
}
```

## 사용 예시

### LLaMA 모델 설정

1. LLaMA 또는 Alpaca 모델이 포함된 GitHub 저장소 URL을 입력합니다.
2. 시스템이 자동으로 LLaMA 모델을 식별하고 필요한 환경을 설정합니다.
3. 모델 가중치 파일이 필요한 경우 입력하거나 자동으로 다운로드합니다.
4. 설치가 완료되면 LLaMA 모델을 사용할 수 있습니다.

### Stable Diffusion 모델 설정

1. Stable Diffusion 모델이 포함된 GitHub 저장소 URL을 입력합니다.
2. 시스템이 자동으로 Stable Diffusion 모델을 식별하고 필요한 환경을 설정합니다.
3. 모델 가중치 파일이 필요한 경우 입력하거나 자동으로 다운로드합니다.
4. 설치가 완료되면 Stable Diffusion 모델을 사용할 수 있습니다.

## 주의사항

- 일부 저장소는 분석이 어려울 수 있으며, 수동 설정이 필요할 수 있습니다.
- 모델 가중치 파일은 저장소에 포함되어 있지 않은 경우가 많으므로 별도로 제공해야 할 수 있습니다.
- 설치 과정은 시간이 오래 걸릴 수 있으며, 하드웨어 요구사항을 확인해야 합니다.
- 일부 모델은 특정 버전의 CUDA나 다른 하드웨어 가속기를 필요로 할 수 있습니다.
