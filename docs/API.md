# API 문서

## 개요

이 문서는 LLMNightRun의 백엔드 API를 설명합니다. LLMNightRun API는 FastAPI 프레임워크를 기반으로 구현되었으며, 다양한 LLM 서비스 통합과 개발 워크플로우 자동화를 위한 엔드포인트를 제공합니다.

## 기본 정보

- **기본 URL**: `http://localhost:8000` (개발 환경)
- **API 문서**: `/docs` 경로에서 Swagger UI를 통해 제공됨
- **인증 방식**: API 키 (일부 엔드포인트)

## 주요 API 그룹

LLMNightRun API는 다음과 같은 주요 그룹으로 구성되어 있습니다:

1. **질문 및 응답**: LLM에 질문을 전송하고 응답을 관리하는 API
2. **코드 관리**: 코드 생성 및 관리 관련 API
3. **에이전트**: 자동화된 작업 수행을 위한 에이전트 API
4. **인덱싱**: 코드 및 문서의 인덱싱 및 검색 API
5. **내보내기**: 결과물 내보내기 관련 API
6. **자동 디버깅**: 코드 문제 분석 및 해결 관련 API
7. **로컬 LLM**: 로컬 LLM 연동 및 관리 API
8. **문서 관리**: 문서 자동화 및 GitHub 연동 API

## 엔드포인트 목록

### 질문 및 응답 API

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/questions` | GET | 질문 목록 조회 |
| `/questions` | POST | 새 질문 제출 |
| `/questions/{question_id}` | GET | 특정 질문 조회 |
| `/responses` | GET | 응답 목록 조회 |
| `/responses/{response_id}` | GET | 특정 응답 조회 |

### 코드 관리 API

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/code` | GET | 코드 목록 조회 |
| `/code` | POST | 새 코드 생성 요청 |
| `/code/{code_id}` | GET | 특정 코드 조회 |
| `/code/{code_id}` | PUT | 코드 업데이트 |
| `/code/{code_id}` | DELETE | 코드 삭제 |

### 에이전트 API

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/agent/tasks` | GET | 에이전트 작업 목록 조회 |
| `/agent/tasks` | POST | 새 에이전트 작업 생성 |
| `/agent/tasks/{task_id}` | GET | 특정 에이전트 작업 조회 |
| `/agent/tasks/{task_id}/status` | GET | 에이전트 작업 상태 조회 |

### 인덱싱 API

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/indexing/projects` | GET | 인덱싱된 프로젝트 목록 조회 |
| `/indexing/projects` | POST | 새 프로젝트 인덱싱 요청 |
| `/indexing/search` | GET | 인덱싱된 내용에서 검색 |

### 내보내기 API

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/export/formats` | GET | 지원하는 내보내기 형식 목록 |
| `/export` | POST | 결과물 내보내기 요청 |
| `/export/{export_id}` | GET | 내보내기 결과 다운로드 |

### 자동 디버깅 API

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/auto-debug` | POST | 자동 디버깅 요청 |
| `/auto-debug/{debug_id}` | GET | 디버깅 결과 조회 |
| `/auto-debug/{debug_id}/suggestions` | GET | 디버깅 제안사항 조회 |

### 로컬 LLM API

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/local-llm/models` | GET | 사용 가능한 로컬 LLM 모델 목록 |
| `/local-llm/models` | POST | 새 로컬 LLM 모델 추가 |
| `/local-llm/predict` | POST | 로컬 LLM을 사용한 예측 요청 |

### 문서 관리 API

| 경로 | 메서드 | 설명 |
|------|--------|------|
| `/docs-manager/list` | GET | 문서 목록 조회 |
| `/docs-manager/generate` | POST | 문서 생성 요청 |
| `/docs-manager/content/{doc_type}` | GET | 특정 문서 내용 조회 |
| `/docs-manager/github/config` | GET | GitHub 연동 설정 조회 |
| `/docs-manager/github/config` | POST | GitHub 연동 설정 저장 |
| `/docs-manager/github/status` | GET | GitHub 저장소 상태 조회 |

## API 사용 예제

### 질문 제출 예제

```bash
curl -X POST "http://localhost:8000/questions" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Python에서 비동기 프로그래밍을 구현하는 방법을 설명해주세요.",
    "model": "gpt-4",
    "temperature": 0.7
  }'
```

### 응답

```json
{
  "id": "q123456",
  "status": "pending",
  "created_at": "2023-09-01T12:34:56Z",
  "message": "질문이 성공적으로 제출되었습니다. 응답을 생성 중입니다."
}
```

### 문서 생성 요청 예제

```bash
curl -X POST "http://localhost:8000/docs-manager/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_types": ["API", "README"],
    "force_update": true,
    "push_to_github": false
  }'
```

### 응답

```json
{
  "status": "success",
  "message": "문서 생성 작업이 시작되었습니다.",
  "doc_types": ["API", "README"]
}
```

## 오류 코드

| 코드 | 설명 |
|------|------|
| 400 | 잘못된 요청 (요청 형식 또는 데이터 오류) |
| 401 | 인증 필요 (인증 정보 누락 또는 잘못됨) |
| 403 | 권한 없음 (접근 권한 부족) |
| 404 | 리소스 없음 (요청한 리소스를 찾을 수 없음) |
| 500 | 서버 오류 (서버 내부 오류) |
| 503 | 서비스 이용 불가 (LLM 서비스 연결 실패 등) |

## API 인증

일부 API 엔드포인트는 인증이 필요합니다. 인증은 HTTP 헤더를 통해 제공됩니다:

```
Authorization: Bearer {api_token}
```

API 토큰은 관리자 계정에서 생성할 수 있으며, 필요한 권한에 따라 다양한 수준의 토큰을
발급할 수 있습니다.

## 웹훅 지원

LLMNightRun API는 다음 이벤트에 대한 웹훅 알림을 지원합니다:

- 작업 완료
- 에이전트 작업 상태 변경
- 문서 생성 완료
- GitHub 커밋 완료

웹훅 설정은 관리자 인터페이스를 통해 구성할 수 있습니다.

## 속도 제한

API 호출 속도는 다음과 같이 제한됩니다:

- 인증되지 않은 사용자: 분당 10건
- 기본 인증 사용자: 분당 60건
- 프리미엄 인증 사용자: 분당 120건

속도 제한을 초과하면 429 상태 코드(Too Many Requests)가 반환됩니다.
