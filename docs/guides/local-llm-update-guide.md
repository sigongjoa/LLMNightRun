# 로컬 LLM 연결 문제 해결 가이드

이 문서는 LLMNightRun 애플리케이션에서 로컬 LLM 연결 문제를 해결하기 위한 변경 사항을 설명합니다.

## 주요 변경 사항

1. **여러 LLM API 엔드포인트 지원**
   - 다양한 로컬 LLM 서버(LM Studio, Ollama)에 대응할 수 있도록 여러 엔드포인트를 시도
   - `/api/chat`, `/api/generate`, `/v1/chat/completions` 등의 엔드포인트 자동 시도
   - 첫 번째 성공하는 엔드포인트 사용

2. **모델 ID 설정 개선**
   - 설정 파일에서 `local_llm_model_id` 필드 추가
   - 환경 변수 `LOCAL_LLM_MODEL_ID`로 모델 ID 설정 가능
   - API 요청 시 모델 ID를 명시적으로 전달

3. **기본 API URL 수정**
   - 프론트엔드 기본 API URL을 `http://127.0.0.1:1234`에서 `http://127.0.0.1:11434`로 변경
   - 백엔드와 프론트엔드의 기본 설정 일치

## 구체적인 코드 변경

### 1. LLM Studio/Ollama API 요청 로직 개선
- 여러 API 엔드포인트를 순차적으로 시도하는 로직 추가
- 각 요청 시도에서 에러 발생 시 다음 엔드포인트로 진행
- 모든 엔드포인트 실패 시 명확한 오류 메시지 반환

### 2. 설정 업데이트
- `settings.py`에 `local_llm_model_id` 필드 추가
- 모델 ID의 기본값을 `deepseek-r1-distill-qwen-7b`로 설정
- 환경 변수 지원으로 배포 환경에서 쉽게 구성 가능

### 3. 프론트엔드 개선
- 기본 URL을 올바른 포트로 수정
- 헬프텍스트를 LM Studio와 Ollama 모두 지원함을 나타내도록 변경

## 문제 해결 전략

이제 애플리케이션은 다음 문제를 해결하기 위한 개선된 전략을 가지고 있습니다:

1. **API 엔드포인트 불일치**: 여러 인기 있는 로컬 LLM 도구의 API 엔드포인트를 자동으로 시도합니다.
2. **모델 ID 불일치**: 모델 ID를 명시적으로 설정하고 API 요청에 포함합니다.
3. **연결 오류 처리 개선**: 보다 구체적인 오류 메시지와 로깅을 제공합니다.

## 사용 방법

1. **환경 변수 설정** (선택 사항):
   ```
   LOCAL_LLM_URL=http://127.0.0.1:11434
   LOCAL_LLM_MODEL_ID=deepseek-r1-distill-qwen-7b
   ```

2. **로컬 LLM 서버 실행**:
   - Ollama: `ollama run deepseek-r1-distill-qwen-7b`
   - LM Studio: UI에서 모델을 선택하고 서버 시작

3. **애플리케이션 실행**:
   - 백엔드: `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`
   - 프론트엔드: `npm run dev`

## 문제가 계속되는 경우

로컬 LLM 연결 문제가 계속되는 경우:

1. 로그 확인: 백엔드 로그에서 구체적인 오류 메시지 확인
2. 로컬 LLM 서버가 정상적으로 실행 중인지 확인
3. 방화벽 설정으로 로컬 포트 연결이 차단되지 않았는지 확인
4. 사용 중인 모델이 실제로 로컬 LLM 서버에 설치되어 있는지 확인
