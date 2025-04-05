*# LLMNightRun API 명세서

## 개요

LLMNightRun API는 다양한 LLM(대규모 언어 모델)을 통합하고 관리하기 위한 백엔드 서비스입니다. 이 문서는 프론트엔드 개발자가 API와 상호 작용하는 데 필요한 모든 정보를 제공합니다.

- **기본 URL**: `http://localhost:8000` (로컬 개발 환경)
- **API 버전**: v1
- **인증**: 현재 버전에서는 별도의 인증이 필요하지 않습니다.

## 목차

1. [공통 사항](#공통-사항)
2. [질문 관리 API](#질문-관리-api)
3. [응답 관리 API](#응답-관리-api)
4. [LLM 요청 API](#llm-요청-api)
5. [코드 스니펫 API](#코드-스니펫-api)
6. [코드 템플릿 API](#코드-템플릿-api)
7. [에이전트 API](#에이전트-api)
8. [인덱싱 API](#인덱싱-api)
9. [내보내기 API](#내보내기-api)
10. [설정 API](#설정-api)
11. [모니터링 API](#모니터링-api)

## 공통 사항

### 응답 형식

모든 API 응답은 JSON 형식으로 반환됩니다. 오류가 발생할 경우 다음과 같은 형식의 응답이 반환됩니다:

```json
{
  "detail": "오류 메시지"
}
```

### HTTP 상태 코드

- `200 OK`: 요청이 성공적으로 처리됨
- `400 Bad Request`: 잘못된 요청 (파라미터 오류 등)
- `404 Not Found`: 요청한 리소스를 찾을 수 없음
- `500 Internal Server Error`: 서버 내부 오류
- `503 Service Unavailable`: LLM 서비스 연결 불가 등의 문제

## 질문 관리 API

질문을 생성하고 관리하기 위한 API입니다.

### 질문 생성

새로운 질문을 생성합니다.

- **URL**: `/questions/`
- **Method**: `POST`
- **요청 본문**:

```json
{
  "content": "맥북과 윈도우 노트북의 차이점은 무엇인가요?",
  "tags": ["컴퓨터", "비교"]
}
```

- **응답**:

```json
{
  "id": 1,
  "content": "맥북과 윈도우 노트북의 차이점은 무엇인가요?",
  "tags": ["컴퓨터", "비교"],
  "created_at": "2023-05-20T14:30:45.123456"
}
```

### 질문 목록 조회

저장된 질문 목록을 조회합니다.

- **URL**: `/questions/`
- **Method**: `GET`
- **쿼리 파라미터**:
  - `skip` (선택): 건너뛸 항목 수 (기본값: 0)
  - `limit` (선택): 최대 항목 수 (기본값: 100)
  - `tag` (선택): 태그로 필터링

- **응답**:

```json
[
  {
    "id": 1,
    "content": "맥북과 윈도우 노트북의 차이점은 무엇인가요?",
    "tags": ["컴퓨터", "비교"],
    "created_at": "2023-05-20T14:30:45.123456"
  },
  {
    "id": 2,
    "content": "파이썬과 자바스크립트의 주요 차이점은?",
    "tags": ["프로그래밍", "언어"],
    "created_at": "2023-05-20T15:45:22.987654"
  }
]
```

### 특정 질문 조회

ID로 특정 질문을 조회합니다.

- **URL**: `/questions/{question_id}`
- **Method**: `GET`
- **URL 파라미터**:
  - `question_id`: 질문 ID

- **응답**:

```json
{
  "id": 1,
  "content": "맥북과 윈도우 노트북의 차이점은 무엇인가요?",
  "tags": ["컴퓨터", "비교"],
  "created_at": "2023-05-20T14:30:45.123456"
}
```

### 질문 수정

기존 질문을 수정합니다.

- **URL**: `/questions/{question_id}`
- **Method**: `PUT`
- **URL 파라미터**:
  - `question_id`: 수정할 질문 ID
- **요청 본문**:

```json
{
  "content": "맥북 프로와 윈도우 노트북의 주요 차이점은 무엇인가요?",
  "tags": ["컴퓨터", "비교", "하드웨어"]
}
```

- **응답**:

```json
{
  "id": 1,
  "content": "맥북 프로와 윈도우 노트북의 주요 차이점은 무엇인가요?",
  "tags": ["컴퓨터", "비교", "하드웨어"],
  "created_at": "2023-05-20T14:30:45.123456"
}
```

### 질문 삭제

질문을 삭제합니다.

- **URL**: `/questions/{question_id}`
- **Method**: `DELETE`
- **URL 파라미터**:
  - `question_id`: 삭제할 질문 ID

- **응답**:

```json
{
  "success": true,
  "message": "질문 ID 1이 삭제되었습니다"
}
```

### 질문 검색

키워드로 질문을 검색합니다.

- **URL**: `/questions/search/`
- **Method**: `GET`
- **쿼리 파라미터**:
  - `query`: 검색어 (필수)
  - `skip` (선택): 건너뛸 항목 수 (기본값: 0)
  - `limit` (선택): 최대 항목 수 (기본값: 100)

- **응답**:

```json
[
  {
    "id": 1,
    "content": "맥북과 윈도우 노트북의 차이점은 무엇인가요?",
    "tags": ["컴퓨터", "비교"],
    "created_at": "2023-05-20T14:30:45.123456"
  }
]
```

## 응답 관리 API

질문에 대한 LLM 응답을 관리하기 위한 API입니다.

### 응답 생성

새로운 응답을 생성합니다.

- **URL**: `/responses/`
- **Method**: `POST`
- **요청 본문**:

```json
{
  "question_id": 1,
  "llm_type": "openai_api",
  "content": "맥북과 윈도우 노트북은 운영체제, 하드웨어, 소프트웨어 생태계 등 여러 측면에서 차이가 있습니다..."
}
```

- **응답**:

```json
{
  "id": 1,
  "question_id": 1,
  "llm_type": "openai_api",
  "content": "맥북과 윈도우 노트북은 운영체제, 하드웨어, 소프트웨어 생태계 등 여러 측면에서 차이가 있습니다...",
  "created_at": "2023-05-20T14:35:12.123456"
}
```

### 응답 목록 조회

저장된 응답 목록을 조회합니다.

- **URL**: `/responses/`
- **Method**: `GET`
- **쿼리 파라미터**:
  - `question_id` (선택): 특정 질문에 대한 응답만 필터링
  - `llm_type` (선택): 특정 LLM 유형에 대한 응답만 필터링
  - `skip` (선택): 건너뛸 항목 수 (기본값: 0)
  - `limit` (선택): 최대 항목 수 (기본값: 100)

- **응답**:

```json
[
  {
    "id": 1,
    "question_id": 1,
    "llm_type": "openai_api",
    "content": "맥북과 윈도우 노트북은 운영체제, 하드웨어, 소프트웨어 생태계 등 여러 측면에서 차이가 있습니다...",
    "created_at": "2023-05-20T14:35:12.123456"
  },
  {
    "id": 2,
    "question_id": 1,
    "llm_type": "claude_api",
    "content": "맥북과 윈도우 노트북의 주요 차이점은 다음과 같습니다...",
    "created_at": "2023-05-20T14:36:30.456789"
  }
]
```

### 특정 응답 조회

ID로 특정 응답을 조회합니다.

- **URL**: `/responses/{response_id}`
- **Method**: `GET`
- **URL 파라미터**:
  - `response_id`: 응답 ID

- **응답**:

```json
{
  "id": 1,
  "question_id": 1,
  "llm_type": "openai_api",
  "content": "맥북과 윈도우 노트북은 운영체제, 하드웨어, 소프트웨어 생태계 등 여러 측면에서 차이가 있습니다...",
  "created_at": "2023-05-20T14:35:12.123456"
}
```

### 응답 삭제

응답을 삭제합니다.

- **URL**: `/responses/{response_id}`
- **Method**: `DELETE`
- **URL 파라미터**:
  - `response_id`: 삭제할 응답 ID

- **응답**:

```json
{
  "success": true,
  "message": "응답 ID 1이 삭제되었습니다"
}
```

## LLM 요청 API

LLM에 질문을 요청하고 응답을 저장하는 API입니다.

### LLM 요청

LLM API에 질문을 요청하고 결과를 저장합니다.

- **URL**: `/ask/{llm_type}`
- **Method**: `POST`
- **URL 파라미터**:
  - `llm_type`: LLM 유형 (openai_api, claude_api 등)
- **요청 본문**:

```json
{
  "content": "맥북과 윈도우 노트북의 차이점은 무엇인가요?",
  "tags": ["컴퓨터", "비교"]
}
```

- **응답**:

```json
{
  "question": {
    "id": 1,
    "content": "맥북과 윈도우 노트북의 차이점은 무엇인가요?",
    "tags": ["컴퓨터", "비교"],
    "created_at": "2023-05-20T14:30:45.123456"
  },
  "response": {
    "id": 1,
    "question_id": 1,
    "llm_type": "openai_api",
    "content": "맥북과 윈도우 노트북은 운영체제, 하드웨어, 소프트웨어 생태계 등 여러 측면에서 차이가 있습니다...",
    "created_at": "2023-05-20T14:35:12.123456"
  }
}
```

## 코드 스니펫 API

LLM으로부터 생성된 코드 스니펫을 관리하기 위한 API입니다.

### 코드 스니펫 생성

새로운 코드 스니펫을 생성합니다.

- **URL**: `/code-snippets/`
- **Method**: `POST`
- **요청 본문**:

```json
{
  "title": "파이썬 배열 정렬 예제",
  "description": "리스트를 정렬하는 간단한 예제 코드",
  "content": "def sort_list(items):\n    return sorted(items)\n\n# 사용 예\nnumbers = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]\nprint(sort_list(numbers))",
  "language": "python",
  "tags": ["파이썬", "정렬", "알고리즘"],
  "source_llm": "openai_api",
  "question_id": 3,
  "response_id": 5
}
```

- **응답**:

```json
{
  "id": 1,
  "title": "파이썬 배열 정렬 예제",
  "description": "리스트를 정렬하는 간단한 예제 코드",
  "content": "def sort_list(items):\n    return sorted(items)\n\n# 사용 예\nnumbers = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]\nprint(sort_list(numbers))",
  "language": "python",
  "tags": ["파이썬", "정렬", "알고리즘"],
  "source_llm": "openai_api",
  "question_id": 3,
  "response_id": 5,
  "version": 1,
  "created_at": "2023-05-20T15:10:22.123456",
  "updated_at": "2023-05-20T15:10:22.123456"
}
```

### 코드 스니펫 목록 조회

저장된 코드 스니펫 목록을 조회합니다.

- **URL**: `/code-snippets/`
- **Method**: `GET`
- **쿼리 파라미터**:
  - `language` (선택): 특정 언어의 스니펫만 필터링
  - `tag` (선택): 특정 태그를 포함한 스니펫만 필터링
  - `skip` (선택): 건너뛸 항목 수 (기본값: 0)
  - `limit` (선택): 최대 항목 수 (기본값: 100)

- **응답**:

```json
[
  {
    "id": 1,
    "title": "파이썬 배열 정렬 예제",
    "description": "리스트를 정렬하는 간단한 예제 코드",
    "content": "def sort_list(items):\n    return sorted(items)\n\n# 사용 예\nnumbers = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]\nprint(sort_list(numbers))",
    "language": "python",
    "tags": ["파이썬", "정렬", "알고리즘"],
    "source_llm": "openai_api",
    "question_id": 3,
    "response_id": 5,
    "version": 1,
    "created_at": "2023-05-20T15:10:22.123456",
    "updated_at": "2023-05-20T15:10:22.123456"
  }
]
```

### 특정 코드 스니펫 조회

ID로 특정 코드 스니펫을 조회합니다.

- **URL**: `/code-snippets/{snippet_id}`
- **Method**: `GET`
- **URL 파라미터**:
  - `snippet_id`: 코드 스니펫 ID

- **응답**:

```json
{
  "id": 1,
  "title": "파이썬 배열 정렬 예제",
  "description": "리스트를 정렬하는 간단한 예제 코드",
  "content": "def sort_list(items):\n    return sorted(items)\n\n# 사용 예\nnumbers = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]\nprint(sort_list(numbers))",
  "language": "python",
  "tags": ["파이썬", "정렬", "알고리즘"],
  "source_llm": "openai_api",
  "question_id": 3,
  "response_id": 5,
  "version": 1,
  "created_at": "2023-05-20T15:10:22.123456",
  "updated_at": "2023-05-20T15:10:22.123456"
}
```

### 코드 스니펫 수정

기존 코드 스니펫을 수정합니다 (새 버전 생성).

- **URL**: `/code-snippets/{snippet_id}`
- **Method**: `PUT`
- **URL 파라미터**:
  - `snippet_id`: 수정할 코드 스니펫 ID
- **요청 본문**:

```json
{
  "title": "파이썬 배열 정렬 예제 (최적화)",
  "description": "리스트를 정렬하는 최적화된 예제 코드",
  "content": "def sort_list(items, reverse=False):\n    return sorted(items, reverse=reverse)\n\n# 사용 예\nnumbers = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]\nprint(sort_list(numbers))\nprint(sort_list(numbers, reverse=True))",
  "tags": ["파이썬", "정렬", "알고리즘", "최적화"]
}
```

- **응답**:

```json
{
  "id": 2,
  "title": "파이썬 배열 정렬 예제 (최적화)",
  "description": "리스트를 정렬하는 최적화된 예제 코드",
  "content": "def sort_list(items, reverse=False):\n    return sorted(items, reverse=reverse)\n\n# 사용 예\nnumbers = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]\nprint(sort_list(numbers))\nprint(sort_list(numbers, reverse=True))",
  "language": "python",
  "tags": ["파이썬", "정렬", "알고리즘", "최적화"],
  "source_llm": "openai_api",
  "question_id": 3,
  "response_id": 5,
  "parent_id": 1,
  "version": 2,
  "created_at": "2023-05-20T15:20:45.123456",
  "updated_at": "2023-05-20T15:20:45.123456"
}
```

### 코드 스니펫 삭제

코드 스니펫을 삭제합니다.

- **URL**: `/code-snippets/{snippet_id}`
- **Method**: `DELETE`
- **URL 파라미터**:
  - `snippet_id`: 삭제할 코드 스니펫 ID

- **응답**:

```json
{
  "success": true,
  "message": "코드 스니펫 ID 1이 삭제되었습니다"
}
```

## 코드 템플릿 API

재사용 가능한 코드 템플릿을 관리하기 위한 API입니다.

### 코드 템플릿 생성

새로운 코드 템플릿을 생성합니다.

- **URL**: `/code-templates/`
- **Method**: `POST`
- **요청 본문**:

```json
{
  "name": "파이썬 웹 서버",
  "description": "간단한 FastAPI 웹 서버 템플릿",
  "content": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'message': 'Hello World'}\n\nif __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host='0.0.0.0', port=8000)",
  "language": "python",
  "tags": ["파이썬", "웹", "FastAPI", "서버"]
}
```

- **응답**:

```json
{
  "id": 1,
  "name": "파이썬 웹 서버",
  "description": "간단한 FastAPI 웹 서버 템플릿",
  "content": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'message': 'Hello World'}\n\nif __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host='0.0.0.0', port=8000)",
  "language": "python",
  "tags": ["파이썬", "웹", "FastAPI", "서버"],
  "created_at": "2023-05-21T10:15:30.123456",
  "updated_at": "2023-05-21T10:15:30.123456"
}
```

### 코드 템플릿 목록 조회

저장된 코드 템플릿 목록을 조회합니다.

- **URL**: `/code-templates/`
- **Method**: `GET`
- **쿼리 파라미터**:
  - `language` (선택): 특정 언어의 템플릿만 필터링
  - `tag` (선택): 특정 태그를 포함한 템플릿만 필터링
  - `skip` (선택): 건너뛸 항목 수 (기본값: 0)
  - `limit` (선택): 최대 항목 수 (기본값: 100)

- **응답**:

```json
[
  {
    "id": 1,
    "name": "파이썬 웹 서버",
    "description": "간단한 FastAPI 웹 서버 템플릿",
    "content": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'message': 'Hello World'}\n\nif __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host='0.0.0.0', port=8000)",
    "language": "python",
    "tags": ["파이썬", "웹", "FastAPI", "서버"],
    "created_at": "2023-05-21T10:15:30.123456",
    "updated_at": "2023-05-21T10:15:30.123456"
  }
]
```

### 특정 코드 템플릿 조회

ID로 특정 코드 템플릿을 조회합니다.

- **URL**: `/code-templates/{template_id}`
- **Method**: `GET`
- **URL 파라미터**:
  - `template_id`: 코드 템플릿 ID

- **응답**:

```json
{
  "id": 1,
  "name": "파이썬 웹 서버",
  "description": "간단한 FastAPI 웹 서버 템플릿",
  "content": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\ndef read_root():\n    return {'message': 'Hello World'}\n\nif __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host='0.0.0.0', port=8000)",
  "language": "python",
  "tags": ["파이썬", "웹", "FastAPI", "서버"],
  "created_at": "2023-05-21T10:15:30.123456",
  "updated_at": "2023-05-21T10:15:30.123456"
}
```

### 코드 템플릿 수정

기존 코드 템플릿을 수정합니다.

- **URL**: `/code-templates/{template_id}`
- **Method**: `PUT`
- **URL 파라미터**:
  - `template_id`: 수정할 코드 템플릿 ID
- **요청 본문**:

```json
{
  "name": "파이썬 웹 서버 (고급)",
  "description": "고급 기능이 포함된 FastAPI 웹 서버 템플릿",
  "content": "from fastapi import FastAPI, Depends, HTTPException\nfrom typing import List\n\napp = FastAPI(title='Advanced API')\n\n@app.get('/')\ndef read_root():\n    return {'message': 'Hello World'}\n\n@app.get('/items/{item_id}')\ndef read_item(item_id: int):\n    return {'item_id': item_id}\n\nif __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host='0.0.0.0', port=8000)",
  "tags": ["파이썬", "웹", "FastAPI", "서버", "고급"]
}
```

- **응답**:

```json
{
  "id": 1,
  "name": "파이썬 웹 서버 (고급)",
  "description": "고급 기능이 포함된 FastAPI 웹 서버 템플릿",
  "content": "from fastapi import FastAPI, Depends, HTTPException\nfrom typing import List\n\napp = FastAPI(title='Advanced API')\n\n@app.get('/')\ndef read_root():\n    return {'message': 'Hello World'}\n\n@app.get('/items/{item_id}')\ndef read_item(item_id: int):\n    return {'item_id': item_id}\n\nif __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host='0.0.0.0', port=8000)",
  "language": "python",
  "tags": ["파이썬", "웹", "FastAPI", "서버", "고급"],
  "created_at": "2023-05-21T10:15:30.123456",
  "updated_at": "2023-05-21T10:30:15.123456"
}
```

### 코드 템플릿 삭제

코드 템플릿을 삭제합니다.

- **URL**: `/code-templates/{template_id}`
- **Method**: `DELETE`
- **URL 파라미터**:
  - `template_id`: 삭제할 코드 템플릿 ID

- **응답**:

```json
{
  "success": true,
  "message": "코드 템플릿 ID 1이 삭제되었습니다"
}
```

## 에이전트 API

자동화된 작업을 위한 에이전트를 관리하는 API입니다.

### 에이전트 생성

새 에이전트 인스턴스를 생성합니다.

- **URL**: `/agent/create`
- **Method**: `POST`
- **요청 본문**: 없음

- **응답**:

```json
{
  "agent_id": "agent_1",
  "state": "idle",
  "messages": [],
  "result": ""
}
```

### 에이전트 실행

에이전트에 작업을 요청합니다.

- **URL**: `/agent/{agent_id}/run`
- **Method**: `POST`
- **URL 파라미터**:
  - `agent_id`: 에이전트 ID
- **요청 본문**:

```json
{
  "prompt": "Python으로 숫자를 입력받아 피보나치 수열을 계산하는 함수를 작성해줘",
  "workspace": "/path/to/workspace",
  "max_steps": 10
}
```

- **응답**:

```json
{
  "agent_id": "agent_1",
  "state": "finished",
  "messages": [
    {
      "role": "user",
      "content": "Python으로 숫자를 입력받아 피보나치 수열을 계산하는 함수를 작성해줘"
    },
    {
      "role": "assistant",
      "content": "피보나치 수열을 계산하는 함수를 작성하겠습니다. 이 함수는 n번째 피보나치 수를 계산합니다.",
      "tool_calls": [
        {
          "id": "call_abcd1234",
          "type": "function",
          "function": {
            "name": "str_replace_editor",
            "arguments": "{\"filepath\": \"fibonacci.py\", \"new_content\": \"def fibonacci(n):\\n    if n <= 0:\\n        return []\\n    elif n == 1:\\n        return [0]\\n    elif n == 2:\\n        return [0, 1]\\n    \\n    fib_list = [0, 1]\\n    for i in range(2, n):\\n        fib_list.append(fib_list[i-1] + fib_list[i-2])\\n    \\n    return fib_list\\n\\ndef main():\\n    try:\\n        n = int(input(\\\"피보나치 수열의 길이를 입력하세요: \\\"))\\n        if n <= 0:\\n            print(\\\"양수를 입력해주세요.\\\")\\n            return\\n        \\n        result = fibonacci(n)\\n        print(f\\\"{n}번째까지의 피보나치 수열: {result}\\\")\\n    except ValueError:\\n        print(\\\"올바른 숫자를 입력해주세요.\\\")\\n\\nif __name__ == \\\"__main__\\\":\\n    main()\"}"
          }
        }
      ]
    },
    {
      "role": "tool",
      "content": "파일 'fibonacci.py'이(가) 업데이트되었습니다. 전체 내용이 새로운 내용으로 대체되었습니다.",
      "tool_call_id": "call_abcd1234",
      "name": "str_replace_editor"
    },
    {
      "role": "assistant",
      "content": "피보나치 수열을 계산하는 Python 함수를 작성했습니다. 코드는 `fibonacci.py` 파일에 저장되었습니다.\n\n이 코드는 다음과 같은 기능을 합니다:\n\n1. `fibonacci(n)` 함수는 n개의 피보나치 수열을 리스트로 반환합니다.\n2. 사용자로부터 양의 정수를 입력받아 해당 길이의 피보나치 수열을 계산합니다.\n3. 유효성 검사를 통해 잘못된 입력에 대한 예외 처리를 합니다.\n\n실행 방법:\n```bash\npython fibonacci.py\n```\n\n예상 출력:\n```\n피보나치 수열의 길이를 입력하세요: 10\n10번째까지의 피보나치 수열: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]\n```"
    }
  ],
  "result": "피보나치 수열 계산 함수가 fibonacci.py 파일에 성공적으로 작성되었습니다."
}
```

### 에이전트 상태 조회

에이전트의 현재 상태를 조회합니다.

- **URL**: `/agent/{agent_id}/status`
- **Method**: `GET`
- **URL 파라미터**:
  - `agent_id`: 에이전트 ID

- **응답**:

```json
{
  "agent_id": "agent_1",
  "state": "finished",
  "messages": [
    {
      "role": "user",
      "content": "Python으로 피보나치 수열 계산 함수를 작성해줘"
    },
    {
      "role": "assistant",
      "content": "피보나치 수열을 계산하는 함수를 작성하겠습니다..."
    }
  ],
  "result": ""
}
```

### 에이전트 삭제

에이전트 인스턴스를 삭제합니다.

- **URL**: `/agent/{agent_id}`
- **Method**: `DELETE`
- **URL 파라미터**:
  - `agent_id`: 에이전트 ID

- **응답**:

```json
{
  "message": "에이전트 agent_1이 삭제되었습니다."
}
```

## 인덱싱 API

코드베이스 인덱싱을 관리하기 위한 API입니다.

### 인덱싱 설정 조회

코드베이스의 인덱싱 설정을 조회합니다.

- **URL**: `/codebases/{codebase_id}/indexing/settings`
- **Method**: `GET`
- **URL 파라미터**:
  - `codebase_id`: 코드베이스 ID

- **응답**:

```json
{
  "is_enabled": true,
  "frequency": "on_commit",
  "excluded_patterns": ["*.log", "node_modules/*", "*.pyc"],
  "priority_patterns": ["src/main/*", "*.py"],
  "embedding_model": "openai/text-embedding-ada-002",
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "include_comments": true,
  "max_files_per_run": 100,
  "created_at": "2023-05-15T10:00:00.123456",
  "updated_at": "2023-05-15T10:00:00.123456"
}
```

### 인덱싱 설정 업데이트

코드베이스의 인덱싱 설정을 업데이트합니다.

- **URL**: `/codebases/{codebase_id}/indexing/settings`
- **Method**: `PATCH`
- **URL 파라미터**:
  - `codebase_id`: 코드베이스 ID
- **요청 본문**:

```json
{
  "is_enabled": true,
  "frequency": "daily",
  "excluded_patterns": ["*.log", "node_modules/*", "*.pyc", "tmp/*"],
  "priority_patterns": ["src/main/*", "*.py", "*.ts"],
  "include_comments": false
}
```

- **응답**:

```json
{
  "success": true,
  "message": "인덱싱 설정이 업데이트되었습니다",
  "settings": {
    "is_enabled": true,
    "frequency": "daily",
    "excluded_patterns": ["*.log", "node_modules/*", "*.pyc", "tmp/*"],
    "priority_patterns": ["src/main/*", "*.py", "*.ts"],
    "embedding_model": "openai/text-embedding-ada-002",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "include_comments": false,
    "max_files_per_run": 100,
    "updated_at": "2023-05-15T15:30:45.123456"
  }
}
```

### 인덱싱 상태 조회

코드베이스의 인덱싱 상태를 조회합니다.

- **URL**: `/codebases/{codebase_id}/indexing/status`
- **Method**: `GET`
- **URL 파라미터**:
  - `codebase_id`: 코드베이스 ID

- **응답**:

```json
{
  "settings": {
    "is_enabled": true,
    "frequency": "daily",
    "excluded_patterns": ["*.log", "node_modules/*", "*.pyc", "tmp/*"],
    "priority_patterns": ["src/main/*", "*.py", "*.ts"],
    "embedding_model": "openai/text-embedding-ada-002",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "include_comments": false,
    "max_files_per_run": 100,
    "last_updated": "2023-05-15T15:30:45.123456"
  },
  "status": {
    "is_indexing_now": false,
    "current_run_id": null,
    "last_run": {
      "id": 5,
      "status": "completed",
      "start_time": "2023-05-15T16:00:00.123456",
      "end_time": "2023-05-15T16:05:30.123456",
      "files_processed": 120,
      "files_indexed": 98,
      "files_skipped": 22,
      "error_message": null
    },
    "recent_runs": [
      {
        "id": 5,
        "status": "completed",
        "start_time": "2023-05-15T16:00:00.123456",
        "end_time": "2023-05-15T16:05:30.123456",
        "is_full_index": false,
        "files_indexed": 98
      },
      {
        "id": 4,
        "status": "completed",
        "start_time": "2023-05-14T16:00:00.123456",
        "end_time": "2023-05-14T16:10:15.123456",
        "is_full_index": true,
        "files_indexed": 350
      }
    ]
  },
  "statistics": {
    "total_embeddings": 12580,
    "indexed_files": 350,
    "last_indexed_at": "2023-05-15T16:05:30.123456",
    "last_index_status": "completed"
  }
}
```

### 인덱싱 트리거

코드베이스 인덱싱을 트리거합니다.

- **URL**: `/codebases/{codebase_id}/indexing/trigger`
- **Method**: `POST`
- **URL 파라미터**:
  - `codebase_id`: 코드베이스 ID
- **요청 본문**:

```json
{
  "codebase_id": 1,
  "is_full_index": false,
  "priority_files": [123, 456, 789]
}
```

- **응답**:

```json
{
  "run_id": 6,
  "status": "pending",
  "message": "인덱싱이 시작되었습니다.",
  "start_time": null
}
```

### 코드 검색

인덱싱된 코드베이스에서 코드를 검색합니다.

- **URL**: `/codebases/{codebase_id}/indexing/search`
- **Method**: `POST`
- **URL 파라미터**:
  - `codebase_id`: 코드베이스 ID
- **요청 본문**:

```json
{
  "codebase_id": 1,
  "query": "파일 업로드 함수",
  "limit": 5,
  "threshold": 0.7,
  "file_patterns": ["*.py", "*.js"],
  "exclude_patterns": ["test/*"]
}
```

- **응답**:

```json
{
  "query": "파일 업로드 함수",
  "result_count": 3,
  "results": [
    {
      "file_id": 123,
      "file_path": "src/utils/file_upload.py",
      "chunk_id": "src/utils/file_upload.py:10-25",
      "content": "def upload_file(file_path, destination):\n    \"\"\"파일을 지정된 위치에 업로드합니다.\"\"\"\n    with open(file_path, 'rb') as f:\n        # 파일 내용 읽기\n        content = f.read()\n        \n        # 목적지에 파일 저장\n        with open(destination, 'wb') as dest_file:\n            dest_file.write(content)\n            \n    return True",
      "similarity_score": 0.89,
      "metadata": {
        "file_name": "file_upload.py",
        "language": "python",
        "code_elements": {
          "functions": ["upload_file"],
          "classes": [],
          "variables": []
        }
      }
    },
    {
      "file_id": 456,
      "file_path": "src/api/uploads.js",
      "chunk_id": "src/api/uploads.js:25-40",
      "content": "/**\n * 파일 업로드 처리 함수\n */\nasync function handleFileUpload(req, res) {\n  try {\n    const uploadedFile = req.files.file;\n    const destination = path.join(uploadDir, uploadedFile.name);\n    \n    await uploadedFile.mv(destination);\n    return res.status(200).json({ success: true });\n  } catch (error) {\n    return res.status(500).json({ error: error.message });\n  }\n}",
      "similarity_score": 0.82,
      "metadata": {
        "file_name": "uploads.js",
        "language": "javascript",
        "code_elements": {
          "functions": ["handleFileUpload"],
          "classes": [],
          "variables": ["uploadedFile", "destination"]
        }
      }
    },
    {
      "file_id": 789,
      "file_path": "src/components/FileUploader.js",
      "chunk_id": "src/components/FileUploader.js:15-30",
      "content": "function uploadFiles(files) {\n  const formData = new FormData();\n  \n  for (let i = 0; i < files.length; i++) {\n    formData.append('files', files[i]);\n  }\n  \n  return fetch('/api/upload', {\n    method: 'POST',\n    body: formData\n  }).then(response => response.json());\n}",
      "similarity_score": 0.75,
      "metadata": {
        "file_name": "FileUploader.js",
        "language": "javascript",
        "code_elements": {
          "functions": ["uploadFiles"],
          "classes": [],
          "variables": ["formData"]
        }
      }
    }
  ]
}
```

## 내보내기 API

데이터를 다양한 형식으로 내보내기 위한 API입니다.

### 질문 내보내기

질문과 관련된 데이터를 내보냅니다.

- **URL**: `/export/question/{question_id}`
- **Method**: `GET`
- **URL 파라미터**:
  - `question_id`: 질문 ID
- **쿼리 파라미터**:
  - `format`: 내보내기 형식 (markdown, json, html, pdf, code_package)
  - `include_metadata`: 메타데이터 포함 여부 (기본값: true)
  - `include_tags`: 태그 포함 여부 (기본값: true)
  - `include_timestamps`: 타임스탬프 포함 여부 (기본값: true)
  - `include_llm_info`: LLM 정보 포함 여부 (기본값: true)
  - `code_highlighting`: 코드 하이라이팅 여부 (기본값: true)

- **응답**: 
  선택한 형식에 따라 적절한 Content-Type으로 파일이 반환됩니다.

### 코드 스니펫 내보내기

코드 스니펫을 내보냅니다.

- **URL**: `/export/code-snippet/{snippet_id}`
- **Method**: `GET`
- **URL 파라미터**:
  - `snippet_id`: 코드 스니펫 ID
- **쿼리 파라미터**:
  - `format`: 내보내기 형식 (markdown, json, code_package)
  - `include_metadata`: 메타데이터 포함 여부 (기본값: true)
  - `include_tags`: 태그 포함 여부 (기본값: true)
  - `include_timestamps`: 타임스탬프 포함 여부 (기본값: true)
  - `include_llm_info`: LLM 정보 포함 여부 (기본값: true)

- **응답**: 
  선택한 형식에 따라 적절한 Content-Type으로 파일이 반환됩니다.

### 에이전트 로그 내보내기

에이전트 실행 로그를 내보냅니다.

- **URL**: `/export/agent-logs/{session_id}`
- **Method**: `GET`
- **URL 파라미터**:
  - `session_id`: 에이전트 세션 ID
- **쿼리 파라미터**:
  - `format`: 내보내기 형식 (json, markdown, html)
  - `include_timestamps`: 타임스탬프 포함 여부 (기본값: true)

- **응답**: 
  선택한 형식에 따라 적절한 Content-Type으로 파일이 반환됩니다.

### 일괄 내보내기

여러 항목을 일괄적으로 내보냅니다.

- **URL**: `/export/batch`
- **Method**: `POST`
- **쿼리 파라미터**:
  - `format`: 내보내기 형식 (markdown, json, html, pdf, code_package)
  - `include_metadata`: 메타데이터 포함 여부 (기본값: true)
  - `include_tags`: 태그 포함 여부 (기본값: true)
  - `include_timestamps`: 타임스탬프 포함 여부 (기본값: true)
  - `include_llm_info`: LLM 정보 포함 여부 (기본값: true)
- **요청 본문**:

```json
[
  {"type": "question", "id": 1},
  {"type": "code_snippet", "id": 2},
  {"type": "agent_logs", "id": "session_xyz"}
]
```

- **응답**: 
  ZIP 형식으로 압축된 파일이 반환됩니다.

## 설정 API

시스템 설정을 관리하기 위한 API입니다.

### 설정 조회

시스템 설정을 조회합니다.

- **URL**: `/settings`
- **Method**: `GET`

- **응답**:

```json
{
  "openai_api_key": "sk-***************",
  "claude_api_key": "sk-***************",
  "github_token": "ghp-***************",
  "github_repo": "username/repo-name",
  "github_username": "username",
  "updated_at": "2023-05-15T10:00:00.123456"
}
```

### 설정 업데이트

시스템 설정을 업데이트합니다.

- **URL**: `/settings`
- **Method**: `POST`
- **요청 본문**:

```json
{
  "openai_api_key": "sk-new-key",
  "claude_api_key": "sk-new-key",
  "github_token": "ghp-new-token",
  "github_repo": "username/new-repo",
  "github_username": "username"
}
```

- **응답**:

```json
{
  "success": true,
  "message": "설정이 업데이트되었습니다",
  "updated_at": "2023-05-15T15:30:45.123456"
}
```

## 모니터링 API

시스템 상태를 모니터링하기 위한 API입니다.

### 헬스 체크

서비스의 전반적인 상태를 확인합니다.

- **URL**: `/health`
- **Method**: `GET`

- **응답**:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2023-05-15T15:30:45.123456"
}
```

## API 예제 코드

프론트엔드에서 API를 사용하는 예제 코드입니다.

### JavaScript (fetch)

```javascript
// 질문 생성 예제
async function createQuestion() {
  const response = await fetch('http://localhost:8000/questions/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content: '맥북과 윈도우 노트북의 차이점은 무엇인가요?',
      tags: ['컴퓨터', '비교']
    }),
  });
  
  const data = await response.json();
  console.log('생성된 질문:', data);
  return data;
}

// LLM에 질문 요청 예제
async function askLLM(questionContent, tags) {
  const response = await fetch('http://localhost:8000/ask/openai_api', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      content: questionContent,
      tags: tags
    }),
  });
  
  const data = await response.json();
  console.log('질문 및 응답:', data);
  return data;
}

// 에이전트 사용 예제
async function runAgent() {
  // 에이전트 생성
  const createResponse = await fetch('http://localhost:8000/agent/create', {
    method: 'POST',
  });
  const agent = await createResponse.json();
  
  // 에이전트 실행
  const runResponse = await fetch(`http://localhost:8000/agent/${agent.agent_id}/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt: 'Python으로 숫자를 입력받아 피보나치 수열을 계산하는 함수를 작성해줘',
      max_steps: 10
    }),
  });
  
  const result = await runResponse.json();
  console.log('에이전트 실행 결과:', result);
  return result;
}
```

### TypeScript (Axios)

```typescript
import axios from 'axios';

// 기본 API 구성
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// 질문 타입 정의
interface Question {
  id?: number;
  content: string;
  tags: string[];
  created_at?: string;
}

// 응답 타입 정의
interface Response {
  id?: number;
  question_id: number;
  llm_type: string;
  content: string;
  created_at?: string;
}

// 질문 생성
async function createQuestion(content: string, tags: string[]): Promise<Question> {
  const response = await api.post<Question>('/questions/', { content, tags });
  return response.data;
}

// 질문 목록 조회
async function getQuestions(skip: number = 0, limit: number = 100): Promise<Question[]> {
  const response = await api.get<Question[]>('/questions/', {
    params: { skip, limit }
  });
  return response.data;
}

// LLM에 질문 요청
async function askLLM(llmType: string, content: string, tags: string[]): Promise<{
  question: Question;
  response: Response;
}> {
  const response = await api.post(`/ask/${llmType}`, { content, tags });
  return response.data;
}
```

## 개발 헬퍼

프론트엔드 개발을 위한 유용한 정보입니다.

### API 문서

더 자세한 API 문서는 다음 URL에서 확인할 수 있습니다:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### CORS 설정

현재 CORS는 모든 오리진에서의 요청을 허용하도록 설정되어 있습니다. 프로덕션 환경에서는 허용된 오리진만 지정하는 것이 좋습니다.

### 오류 처리

모든 API는 오류 발생 시 적절한 HTTP 상태 코드와 함께 다음과 같은 형식의 JSON 응답을 반환합니다:

```json
{
  "detail": "오류 메시지"
}
```

프론트엔드에서는 이 응답을 캐치하고 적절히 처리해야 합니다.