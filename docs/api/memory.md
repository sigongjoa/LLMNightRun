# Memory API

LLM 메모리 관리 및 벡터 DB 연동 기능

## 엔드포인트

### POST /memory/add

**Add Memory**

Add a new memory to the store.

Args:
    memory: Memory object to add
    background_tasks: FastAPI background tasks
    
Returns:
    Dictionary with memory ID

#### 요청

**요청 본문:**

미디어 타입: `application/json`

스키마: `Memory`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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

### POST /memory/attach-context

**Attach Context To Prompt**

Attach memory context to a prompt.

Args:
    prompt: Original prompt
    query: Query to get context for, or use prompt if empty
    top_k: Number of memories to include
    
Returns:
    Prompt with memory context

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| prompt | query | string | ✓ |  |
| query | query | string |  |  |
| top_k | query | integer |  |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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

### POST /memory/batch

**Add Memories Batch**

Add multiple memories in batch.

Args:
    batch: Batch of memories to add
    background_tasks: FastAPI background tasks
    
Returns:
    Dictionary with memory IDs

#### 요청

**요청 본문:**

미디어 타입: `application/json`

스키마: `MemoryBatch`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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

### POST /memory/clear

**Clear Memories**

Clear all memories of specified type, or all if type is None.

Args:
    memory_type: Type of memories to clear, or all if None
    background_tasks: FastAPI background tasks
    
Returns:
    Success status

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| memory_type | query | any |  |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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

### POST /memory/context

**Get Memory Context**

Get memory context for a query.

Args:
    query: Query to get context for
    top_k: Number of memories to include
    
Returns:
    Memory context

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| query | query | string | ✓ |  |
| top_k | query | integer |  |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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

### GET /memory/count

**Count Memories**

Get the total number of memories.

Returns:
    Number of memories

#### 요청

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

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

### DELETE /memory/delete/{memory_id}

**Delete Memory**

Delete memory by ID.

Args:
    memory_id: ID of memory to delete
    background_tasks: FastAPI background tasks
    
Returns:
    Success status

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| memory_id | path | string | ✓ |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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

### POST /memory/experiment

**Store Experiment Memory**

Store memory about an experiment.

Args:
    experiment_data: Data about the experiment
    background_tasks: FastAPI background tasks
    
Returns:
    ID of the created memory

#### 요청

**요청 본문:**

미디어 타입: `application/json`


#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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

### GET /memory/get/{memory_id}

**Get Memory**

Get memory by ID.

Args:
    memory_id: ID of memory to retrieve
    
Returns:
    Memory if found

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| memory_id | path | string | ✓ |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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

### GET /memory/health

**Health Check**

Check the health of the memory system.

Returns:
    Status message

#### 요청

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

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

### POST /memory/related

**Retrieve Related Memories**

Retrieve memories related to a prompt.

Args:
    prompt: Prompt to find related memories for
    top_k: Number of memories to return
    memory_types: Types of memories to include
    
Returns:
    List of related memories

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| prompt | query | string | ✓ |  |
| top_k | query | integer |  |  |
| memory_types | query | any |  |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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

### POST /memory/search

**Search Memories**

Search for memories.

Args:
    search: Search parameters
    
Returns:
    List of matching memories

#### 요청

**요청 본문:**

미디어 타입: `application/json`

스키마: `MemorySearch`

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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

### GET /memory/working

**Get Working Memory**

Get current working memory.

Returns:
    List of memories in working memory

#### 요청

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

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

### POST /memory/working/limit

**Set Working Memory Limit**

Set the working memory limit.

Args:
    limit: New working memory limit
    
Returns:
    New limit

#### 요청

**파라미터:**

| 이름 | 위치 | 타입 | 필수 | 설명 |
| ---- | ---- | ---- | ---- | ---- |
| limit | query | integer | ✓ |  |

#### 응답

**상태 코드:** 200

설명: Successful Response

미디어 타입: `application/json`

**상태 코드:** 404

설명: Not found

**상태 코드:** 400

설명: Bad request

**상태 코드:** 500

설명: Internal server error

**상태 코드:** 422

설명: Validation Error

미디어 타입: `application/json`

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
