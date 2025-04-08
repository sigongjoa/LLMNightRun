# Local Llm API

Local Llm API

## 엔드포인트

### POST /api/local-llm/chat

**Chat**

로컬 LLM과 채팅

Args:
    request: 채팅 요청 정보
    
Returns:
    LLM 응답

#### 요청

**요청 본문:**

미디어 타입: `application/json`

스키마: `LocalLLMChatRequest`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

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

### PUT /api/local-llm/config

**Update Config**

로컬 LLM 설정 업데이트

Args:
    config: 업데이트할 설정 정보
    
Returns:
    업데이트된 전체 설정

#### 요청

**요청 본문:**

미디어 타입: `application/json`

스키마: `LocalLLMConfigUpdateRequest`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

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

### GET /api/local-llm/ping

**Ping**

프론트엔드와 백엔드 통신 테스트

Returns:
    간단한 응답

#### 요청

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

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

### GET /api/local-llm/status

**Get Status**

로컬 LLM 상태 확인

Returns:
    로컬 LLM 상태 정보

#### 요청

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

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
