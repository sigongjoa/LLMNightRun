# Questions API

Questions API

## 엔드포인트

### POST /questions/

**Submit Question**

새로운 질문을 데이터베이스에 저장합니다.

Args:
    question: 질문 내용 및 태그
    db: 데이터베이스 세션
    
Returns:
    QuestionResponse: 생성된 질문 정보
    
Raises:
    HTTPException: 질문 생성 중 오류 발생 시

#### 요청

**요청 본문:**

미디어 타입: `application/json`

스키마: `QuestionCreate`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 질문을 찾을 수 없음

**상태 코드:** 500

설명: 서버 내부 오류

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

---

### GET /questions/

**List Questions**

질문 목록을 페이지네이션과 필터링 옵션으로 조회합니다.

Args:
    skip: 건너뛸 항목 수
    limit: 최대 조회 항목 수
    tag: 필터링할 태그 (선택 사항)
    db: 데이터베이스 세션
    
Returns:
    List[QuestionResponse]: 질문 목록
    
Raises:
    HTTPException: 질문 목록 조회 중 오류 발생 시

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| skip | query | integer |  |  |
| limit | query | integer |  |  |
| tag | query | any |  |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 질문을 찾을 수 없음

**상태 코드:** 500

설명: 서버 내부 오류

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

---

### GET /questions/search/

**Search Questions Endpoint**

질문을 검색어를 기준으로 검색합니다.

Args:
    query: 검색어 (최소 2글자)
    skip: 건너뛸 항목 수
    limit: 최대 조회 항목 수
    db: 데이터베이스 세션
    
Returns:
    List[QuestionResponse]: 검색된 질문 목록
    
Raises:
    HTTPException: 검색 중 오류 발생 시

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| query | query | string | ✓ | 검색어 |
| skip | query | integer |  |  |
| limit | query | integer |  |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 질문을 찾을 수 없음

**상태 코드:** 500

설명: 서버 내부 오류

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

---

### GET /questions/{question_id}

**Get Question**

특정 ID의 질문을 조회합니다.

Args:
    question_id: 질문 ID
    db: 데이터베이스 세션
    
Returns:
    QuestionResponse: 질문 정보
    
Raises:
    HTTPException: 질문을 찾을 수 없거나 조회 중 오류 발생 시

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| question_id | path | integer | ✓ |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 질문을 찾을 수 없음

**상태 코드:** 500

설명: 서버 내부 오류

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

---

### PUT /questions/{question_id}

**Update Question Endpoint**

특정 ID의 질문을 업데이트합니다.

Args:
    question_id: 질문 ID
    question: 업데이트할 질문 정보
    db: 데이터베이스 세션
    
Returns:
    QuestionResponse: 업데이트된 질문 정보
    
Raises:
    HTTPException: 질문을 찾을 수 없거나 업데이트 중 오류 발생 시

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| question_id | path | integer | ✓ |  |

**요청 본문:**

미디어 타입: `application/json`

스키마: `Question`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 질문을 찾을 수 없음

**상태 코드:** 500

설명: 서버 내부 오류

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

---

### DELETE /questions/{question_id}

**Delete Question Endpoint**

특정 ID의 질문을 삭제합니다.

Args:
    question_id: 질문 ID
    db: 데이터베이스 세션
    
Returns:
    Dict[str, Any]: 삭제 성공 메시지
    
Raises:
    HTTPException: 질문을 찾을 수 없거나 삭제 중 오류 발생 시

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| question_id | path | integer | ✓ |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: 질문을 찾을 수 없음

**상태 코드:** 500

설명: 서버 내부 오류

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

---
