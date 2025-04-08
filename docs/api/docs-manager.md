# Docs-Manager API

Docs-Manager API

## 엔드포인트

### GET /docs-manager/content/{doc_type}

**Get Document Content**

특정 문서의 내용 조회

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| doc_type | path | string | ✓ | 문서 유형 |

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

### POST /docs-manager/generate

**Generate Documents**

선택한 문서 생성 또는 업데이트

#### 요청

**요청 본문:**

미디어 타입: `application/json`

스키마: `DocumentGenerateRequest`

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

### GET /docs-manager/github/config

**Get Github Config**

GitHub 연동 설정 조회

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

### POST /docs-manager/github/config

**Set Github Config**

GitHub 연동 설정 저장

#### 요청

**요청 본문:**

미디어 타입: `application/json`

스키마: `GitHubConfigRequest`

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

### GET /docs-manager/github/status

**Get Github Status**

GitHub 리포지토리 상태 조회

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

### GET /docs-manager/list

**List Documents**

사용 가능한 문서 목록과 상태 조회

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
