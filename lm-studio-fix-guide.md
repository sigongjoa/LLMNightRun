# LM Studio 연결 문제 해결 가이드

이 문서는 LLMNightRun 애플리케이션에서 LM Studio 연결 문제를 해결하기 위한 변경 사항을 설명합니다.

## 문제 원인

LM Studio의 API 엔드포인트 오류가 지속적으로 발생했습니다:
```
Unexpected endpoint or method. (POST /api/chat). Returning 200 anyway
```

이는 코드에서 잘못된 API 엔드포인트를 사용하고 있었기 때문입니다. LM Studio는 OpenAI 호환 API를 사용하며, 엔드포인트가 `/v1/chat/completions`입니다.

## 주요 변경 사항

1. **API 엔드포인트 수정**
   - `/api/chat` 대신 `/v1/chat/completions` 엔드포인트 사용
   - LM Studio의 OpenAI 호환 API에 맞는 요청 형식 구현

2. **응답 처리 로직 수정**
   - OpenAI 형식의 응답 처리를 우선적으로 사용
   - 도구 호출 응답도 OpenAI 형식으로 처리

3. **모델 ID 처리 개선**
   - 설정에서 모델 ID를 명시적으로 가져와서 요청에 포함
   - 일관성 있는 모델 ID 사용

4. **타임아웃 및 오류 처리 개선**
   - 오류 발생 시 더 상세한 로그 기록
   - 불필요한 옵션 제거 및 타임아웃 설정 최적화

## 구체적인 코드 변경

### 1. API 엔드포인트 수정

LM Studio의 정확한 API 엔드포인트를 사용하도록 수정:

```python
# 이전 코드: 여러 엔드포인트 시도
endpoints = ["/api/chat", "/api/generate", "/v1/chat/completions"]

# 수정된 코드: LM Studio 전용 엔드포인트 사용
endpoint = "/v1/chat/completions"
```

### 2. OpenAI 호환 요청 형식 사용

LM Studio가 예상하는 정확한 요청 형식 사용:

```python
# LM Studio OpenAI 호환 형식으로 요청 데이터 구성
request_data = {
    "model": model_id,
    "messages": formatted_messages,
    "temperature": kwargs.get("temperature", 0.7),
    "max_tokens": kwargs.get("max_tokens", 1000)
}
```

### 3. 응답 처리 우선순위 변경

OpenAI 형식의 응답을 우선적으로 처리하도록 로직 변경:

```python
# OpenAI API 형식 (LM Studio는 이 형식 사용)
if ("choices" in response_data and len(response_data["choices"]) > 0 
    and "message" in response_data["choices"][0]):
    # 응답 처리
```

## 사용 방법

1. 백엔드와 프론트엔드를 재시작하여 변경 사항 적용:
   ```
   # 백엔드 재시작
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   
   # 프론트엔드 재시작
   npm run dev
   ```

2. LM Studio 설정 확인:
   - LM Studio가 실행 중인지 확인
   - LM Studio 서버가 기본 포트 1234에서 실행 중인지 확인
   - "deepseek-r1-distill-qwen-7b" 모델이 LM Studio에 로드되어 있는지 확인

## 문제가 계속되는 경우

로그를 주의 깊게 확인하여 다음 문제를 살펴보세요:

1. LM Studio 로그에서 구체적인 오류 메시지 확인
2. LM Studio 버전 확인 (최신 버전으로 업데이트)
3. 로컬 LLM 설정 페이지에서 직접 설정 업데이트
   - 기본 URL: `http://127.0.0.1:1234` (LM Studio의 기본 포트)
   - 모델 ID: LM Studio에 로드된 정확한 모델 이름

## 참고 사항

LM Studio는 OpenAI 호환 API를 사용하지만, 일부 구현 세부 사항이 다를 수 있습니다. 구현 차이로 인한 문제가 계속되면 LM Studio 문서를 참조하거나 LM Studio GitHub 저장소의 이슈를 확인하세요.
