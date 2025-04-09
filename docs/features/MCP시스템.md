# MCP(Model Control Panel) 시스템

## 개요
MCP(Model Control Panel) 시스템은 LLMNightRun에서 다양한 AI 모델의 설정, 미세 조정, 모니터링을 위한 중앙 인터페이스를 제공합니다. 이 시스템을 통해 개발자와 사용자는 모델 동작을 세밀하게 제어하고 최적화할 수 있습니다.

## 구성 요소

### 백엔드 구성 요소
- `backend/mcp/`: MCP 코어 기능
  - `backend/mcp/controller.py`: 모델 제어 로직
  - `backend/mcp/monitor.py`: 성능 모니터링
  - `backend/mcp/optimizer.py`: 매개변수 최적화
- `backend/api/mcp_status.py`: MCP 상태 API 엔드포인트
- `backend/models/mcp.py`: MCP 설정 및 상태를 위한 데이터 모델

### API 엔드포인트

#### MCP 상태 가져오기
```
GET /api/mcp/status
```
**응답:**
```json
{
    "active_models": 4,
    "total_requests": 1542,
    "average_latency": 1.23,  // 초
    "current_usage": {
        "tokens": 35621,
        "cost_estimate": "$0.75"
    },
    "models": [
        {
            "id": "모델_id",
            "name": "모델명",
            "type": "api|local",
            "status": "active|inactive|error",
            "requests_count": 342,
            "average_tokens": 521
        },
        // 추가 모델...
    ]
}
```

#### 모델 설정 업데이트
```
POST /api/mcp/model/{model_id}/configure
```
**요청 본문:**
```json
{
    "parameters": {
        "temperature": 0.8,
        "top_p": 0.95,
        "frequency_penalty": 0.2,
        "presence_penalty": 0.1,
        "max_tokens": 2048
    },
    "rate_limits": {
        "requests_per_minute": 30,
        "tokens_per_day": 100000
    },
    "routing_priority": 2,
    "fallback_models": ["model_id_1", "model_id_2"]
}
```
**응답:**
```json
{
    "model_id": "모델_id",
    "status": "updated",
    "active_from": "타임스탬프"
}
```

#### MCP 로그 가져오기
```
GET /api/mcp/logs
```
**요청 파라미터:**
- `start_time`: 로그 시작 시간(ISO 형식)
- `end_time`: 로그 종료 시간(ISO 형식)
- `level`: 로그 수준(info, warning, error)
- `model_id`: 특정 모델에 대한 로그 필터링(선택사항)

**응답:**
```json
{
    "logs": [
        {
            "timestamp": "타임스탬프",
            "level": "info|warning|error",
            "model_id": "모델_id",
            "message": "로그 메시지",
            "details": {}  // 추가 정보
        },
        // 추가 로그 항목...
    ],
    "total_count": 253,
    "filtered_count": 42
}
```

## 주요 기능

### 모델 관리
- **멀티 모델 지원**: 다양한 공급자(OpenAI, Anthropic, 로컬 모델 등)의 여러 모델 관리
- **API 키 관리**: 다양한 API 키 및 인증 설정 저장
- **쿼터 및 사용량 추적**: 토큰 소비 및 API 호출 모니터링

### 성능 최적화
- **매개변수 최적화**: 다양한 사용 사례에 맞는 최적의 온도, top_p 등 설정
- **A/B 테스트**: 다른 모델 또는 설정 조합의 성능 비교
- **비용 최적화**: 성능과 비용 간의 최적의 균형을 위한 자동 조정

### 라우팅 및 폴백
- **스마트 라우팅**: 요청을 가장 적합한 모델로 자동 라우팅
- **폴백 메커니즘**: 주 모델에 오류가 발생하면 대체 모델로 자동 전환
- **로드 밸런싱**: 여러 모델 또는 엔드포인트 간에 요청 분산

## 사용 예시

### 모델 설정 최적화
```python
import requests

# 특정 모델의 현재 설정 가져오기
model_id = "gpt-4"
model_status = requests.get(
    f"http://localhost:8000/api/mcp/model/{model_id}/status"
).json()

print(f"현재 설정: {model_status['parameters']}")
print(f"현재 성능 메트릭스: {model_status['performance']}")

# 설정 업데이트
new_config = requests.post(
    f"http://localhost:8000/api/mcp/model/{model_id}/configure",
    json={
        "parameters": {
            "temperature": 0.7,  # 약간 낮춤
            "max_tokens": 1500   # 토큰 제한 조정
        }
    }
).json()

print(f"설정 업데이트 상태: {new_config['status']}")
```

### 프론트엔드 통합
MCP 시스템은 모델 및 시스템 성능을 보여주는 대시보드, 설정 조정을 위한 슬라이더 및 컨트롤, 로그 및 분석 뷰 등 프론트엔드 구성 요소와 통합됩니다.

## 고급 기능
- **자동 최적화**: 성능 메트릭스에 따른 모델 매개변수 자동 조정
- **이상 감지**: 모델 성능 또는 동작의 비정상적인 변화 감지
- **맞춤형 프롬프트 템플릿**: 일관된 결과를 위한 모델별 프롬프트 템플릿 정의
- **중앙 집중식 캐싱**: 빠른 응답 및 비용 절감을 위한 결과 캐싱
- **권한 관리**: 모델 및 설정에 대한 사용자별 액세스 제어
