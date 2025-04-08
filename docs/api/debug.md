# Debug API

Debug API

## 엔드포인트

### POST /debug/analyze

**Analyze Error**

코드 오류를 분석하고 수정 방안을 제안합니다.

요청 본문:
```json
{
    "error_message": "오류 메시지",
    "traceback": "오류 트레이스백",
    "codebase_id": 1,
    "additional_context": "추가 컨텍스트 정보 (선택 사항)"
}
```

Args:
    error_data: 오류 정보
    llm_type: 사용할 LLM 유형
    db: 데이터베이스 세션
    
Returns:
    분석 결과 및 수정 방안

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| llm_type | query | any |  | 사용할 LLM 유형 |

**요청 본문:**

미디어 타입: `application/json`


#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 리소스를 찾을 수 없음

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

### POST /debug/auto-fix

**Auto Fix Error**

코드 오류를 분석하고 자동으로 수정합니다.

요청 본문:
```json
{
    "error_message": "오류 메시지",
    "traceback": "오류 트레이스백",
    "codebase_id": 1,
    "additional_context": "추가 컨텍스트 정보 (선택 사항)"
}
```

Args:
    error_data: 오류 정보
    apply_fix: 수정 사항 즉시 적용 여부
    llm_type: 사용할 LLM 유형
    db: 데이터베이스 세션
    
Returns:
    수정 결과

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| apply_fix | query | boolean |  | 수정 사항 즉시 적용 여부 |
| llm_type | query | any |  | 사용할 LLM 유형 |

**요청 본문:**

미디어 타입: `application/json`


#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 리소스를 찾을 수 없음

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

### POST /debug/import-error

**Debug Import Error**

모듈 가져오기 오류를 디버깅합니다.

요청 본문:
```json
{
    "module_name": "가져오기 실패한 모듈 이름",
    "error_message": "오류 메시지",
    "codebase_id": 1
}
```

Args:
    import_error_data: 가져오기 오류 정보
    llm_type: 사용할 LLM 유형
    db: 데이터베이스 세션
    
Returns:
    분석 결과 및 해결 방안

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| llm_type | query | any |  | 사용할 LLM 유형 |

**요청 본문:**

미디어 타입: `application/json`


#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 리소스를 찾을 수 없음

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

### GET /debug/verify-environment/{codebase_id}

**Verify Environment**

코드베이스의 환경 설정을 검증합니다.

Args:
    codebase_id: 코드베이스 ID
    db: 데이터베이스 세션
    
Returns:
    환경 검증 결과

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| codebase_id | path | integer | ✓ |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 리소스를 찾을 수 없음

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
