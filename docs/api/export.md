# Export API

Export API

## 엔드포인트

### GET /export/agent-logs/{session_id}

**Export Agent Logs**

Agent 실행 로그를 내보냅니다.

Args:
    session_id: Agent 세션 ID
    format: 내보내기 형식 (json, markdown, html)
    include_timestamps: 타임스탬프 포함 여부
    db: 데이터베이스 세션
    
Returns:
    형식에 맞는 내보내기 파일

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| session_id | path | string | ✓ |  |
| format | query | string |  | 내보내기 형식 |
| include_timestamps | query | boolean |  | 타임스탬프 포함 여부 |

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

### POST /export/batch

**Export Batch**

여러 항목을 일괄 내보내기합니다.

요청 형식:
```
[
    {"type": "question", "id": 1},
    {"type": "code_snippet", "id": 2},
    {"type": "agent_logs", "id": "session_xyz"}
]
```

Args:
    item_ids: 내보낼 항목 목록
    format: 내보내기 형식
    include_metadata: 메타데이터 포함 여부
    include_tags: 태그 포함 여부
    include_timestamps: 타임스탬프 포함 여부
    include_llm_info: LLM 정보 포함 여부
    db: 데이터베이스 세션
    
Returns:
    zip 파일 형태로 모든 내보내기 항목을 포함

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| format | query | string |  | 내보내기 형식 |
| include_metadata | query | boolean |  | 메타데이터 포함 여부 |
| include_tags | query | boolean |  | 태그 포함 여부 |
| include_timestamps | query | boolean |  | 타임스탬프 포함 여부 |
| include_llm_info | query | boolean |  | LLM 정보 포함 여부 |

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

### GET /export/code-snippet/{snippet_id}

**Export Code Snippet**

특정 코드 스니펫을 내보냅니다.

Args:
    snippet_id: 코드 스니펫 ID
    format: 내보내기 형식 (markdown, json, code_package)
    include_metadata: 메타데이터 포함 여부
    include_tags: 태그 포함 여부
    include_timestamps: 타임스탬프 포함 여부
    include_llm_info: LLM 정보 포함 여부
    db: 데이터베이스 세션
    
Returns:
    형식에 맞는 내보내기 파일

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| snippet_id | path | integer | ✓ |  |
| format | query | string |  | 내보내기 형식 |
| include_metadata | query | boolean |  | 메타데이터 포함 여부 |
| include_tags | query | boolean |  | 태그 포함 여부 |
| include_timestamps | query | boolean |  | 타임스탬프 포함 여부 |
| include_llm_info | query | boolean |  | LLM 정보 포함 여부 |

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

### GET /export/question/{question_id}

**Export Question**

질문과 관련된 모든 응답 및 코드 스니펫을 내보냅니다.

Args:
    question_id: 질문 ID
    format: 내보내기 형식 (markdown, json, html, pdf, code_package)
    include_metadata: 메타데이터 포함 여부
    include_tags: 태그 포함 여부
    include_timestamps: 타임스탬프 포함 여부
    include_llm_info: LLM 정보 포함 여부
    code_highlighting: 코드 하이라이팅 여부
    db: 데이터베이스 세션
    
Returns:
    형식에 맞는 내보내기 파일

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| question_id | path | integer | ✓ |  |
| format | query | string |  | 내보내기 형식 |
| include_metadata | query | boolean |  | 메타데이터 포함 여부 |
| include_tags | query | boolean |  | 태그 포함 여부 |
| include_timestamps | query | boolean |  | 타임스탬프 포함 여부 |
| include_llm_info | query | boolean |  | LLM 정보 포함 여부 |
| code_highlighting | query | boolean |  | 코드 하이라이팅 여부 |

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
