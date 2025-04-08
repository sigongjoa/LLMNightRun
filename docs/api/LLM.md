# Llm API

Llm API

## 엔드포인트

### POST /api/v2/llm/generate

**LLM 텍스트 생성**

LLM에 프롬프트를 전송하고 텍스트를 생성합니다.

Args:
    request: LLM 프롬프트 요청 데이터
    controller: LLM 컨트롤러 인스턴스
    
Returns:
    생성된 텍스트와 메타데이터

#### 요청

**요청 본문:**

미디어 타입: `application/json`

스키마: `LLMPromptRequest`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

**상태 코드:** 400

설명: 잘못된 요청

미디어 타입: `application/json`

예시:
```json
{
  "error_code": "validation_error",
  "message": "데이터 검증 오류가 발생했습니다",
  "detail": [
    {
      "loc": [
        "body",
        "name"
      ],
      "msg": "필수 항목입니다"
    }
  ]
}
```

**상태 코드:** 401

설명: 인증되지 않음

미디어 타입: `application/json`

예시:
```json
{
  "error_code": "unauthorized",
  "message": "API 키가 필요합니다",
  "detail": null
}
```

**상태 코드:** 404

설명: 찾을 수 없음

미디어 타입: `application/json`

예시:
```json
{
  "error_code": "not_found",
  "message": "요청한 리소스를 찾을 수 없습니다",
  "detail": null
}
```

**상태 코드:** 500

설명: 서버 내부 오류

미디어 타입: `application/json`

예시:
```json
{
  "error_code": "internal_server_error",
  "message": "서버 내부 오류가 발생했습니다",
  "detail": "오류에 대한 자세한 내용"
}
```

---

### GET /api/v2/llm/models

**사용 가능한 LLM 모델 목록 조회**

사용 가능한 LLM 모델 목록을 반환합니다.

Args:
    llm_type: LLM 유형 (선택 사항)
    controller: LLM 컨트롤러 인스턴스
    
Returns:
    사용 가능한 모델 목록

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| llm_type | query | any |  |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

**상태 코드:** 400

설명: 잘못된 요청

미디어 타입: `application/json`

예시:
```json
{
  "error_code": "validation_error",
  "message": "데이터 검증 오류가 발생했습니다",
  "detail": [
    {
      "loc": [
        "body",
        "name"
      ],
      "msg": "필수 항목입니다"
    }
  ]
}
```

**상태 코드:** 401

설명: 인증되지 않음

미디어 타입: `application/json`

예시:
```json
{
  "error_code": "unauthorized",
  "message": "API 키가 필요합니다",
  "detail": null
}
```

**상태 코드:** 404

설명: 찾을 수 없음

미디어 타입: `application/json`

예시:
```json
{
  "error_code": "not_found",
  "message": "요청한 리소스를 찾을 수 없습니다",
  "detail": null
}
```

**상태 코드:** 500

설명: 서버 내부 오류

미디어 타입: `application/json`

예시:
```json
{
  "error_code": "internal_server_error",
  "message": "서버 내부 오류가 발생했습니다",
  "detail": "오류에 대한 자세한 내용"
}
```

---
