# Indexing API

Indexing API

## 엔드포인트

### POST /codebases/{codebase_id}/indexing/search

**Search Code**

코드베이스에서 코드를 검색합니다.

Args:
    codebase_id: 코드베이스 ID
    query: 검색 쿼리 정보
    db: 데이터베이스 세션
    
Returns:
    검색 결과
    
Raises:
    HTTPException: 코드베이스가 없거나 검색에 실패한 경우

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| codebase_id | path | integer | ✓ |  |

**요청 본문:**

미디어 타입: `application/json`

스키마: `CodeSearchQuery`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 코드베이스를 찾을 수 없음

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

### GET /codebases/{codebase_id}/indexing/settings

**Get Codebase Indexing Settings**

코드베이스의 인덱싱 설정을 조회합니다.

Args:
    codebase_id: 코드베이스 ID
    db: 데이터베이스 세션
    
Returns:
    인덱싱 설정 정보
    
Raises:
    HTTPException: 코드베이스가 없거나 설정이 없는 경우

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

설명: 코드베이스를 찾을 수 없음

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

### PATCH /codebases/{codebase_id}/indexing/settings

**Update Codebase Indexing Settings**

코드베이스의 인덱싱 설정을 업데이트합니다.

Args:
    codebase_id: 코드베이스 ID
    settings: 업데이트할 설정 정보
    db: 데이터베이스 세션
    
Returns:
    업데이트된 설정 정보
    
Raises:
    HTTPException: 코드베이스가 없거나 설정 업데이트에 실패한 경우

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| codebase_id | path | integer | ✓ |  |

**요청 본문:**

미디어 타입: `application/json`

스키마: `IndexingSettingsUpdate`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 코드베이스를 찾을 수 없음

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

### GET /codebases/{codebase_id}/indexing/status

**Get Codebase Indexing Status**

코드베이스의 인덱싱 상태를 조회합니다.

Args:
    codebase_id: 코드베이스 ID
    db: 데이터베이스 세션
    
Returns:
    인덱싱 상태 정보
    
Raises:
    HTTPException: 코드베이스가 없거나 상태 조회에 실패한 경우

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

설명: 코드베이스를 찾을 수 없음

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

### POST /codebases/{codebase_id}/indexing/trigger

**Trigger Indexing**

코드베이스 인덱싱을 트리거합니다.

Args:
    codebase_id: 코드베이스 ID
    request: 인덱싱 요청 정보
    background_tasks: 백그라운드 태스크 객체
    db: 데이터베이스 세션
    
Returns:
    인덱싱 실행 정보
    
Raises:
    HTTPException: 코드베이스가 없거나 인덱싱 트리거에 실패한 경우

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| codebase_id | path | integer | ✓ |  |

**요청 본문:**

미디어 타입: `application/json`

스키마: `TriggerIndexingRequest`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 코드베이스를 찾을 수 없음

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
