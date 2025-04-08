# Monitoring API

시스템 모니터링 및 상태 확인 엔드포인트

## 엔드포인트

### GET /

**Root**

루트 경로

#### 요청

#### 응답

**상태 코드:** 200

설명: Successful Response

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

### GET /health

**Health Check**

시스템 헬스 체크 엔드포인트.
쿠버네티스, 도커 또는 기타 모니터링 도구에서 사용할 수 있습니다.

#### 요청

#### 응답

**상태 코드:** 200

설명: Successful Response

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
