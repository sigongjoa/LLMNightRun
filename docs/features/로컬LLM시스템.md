# 로컬 LLM 시스템

## 개요
로컬 LLM 시스템은 LLMNightRun이 클라우드 API에 의존하지 않고 로컬에서 실행되는 대규모 언어 모델(LLM)을 활용할 수 있게 해주는 기능입니다. 이 시스템은 개인 정보 보호, 오프라인 액세스, 비용 효율성을 향상시킵니다.

## 구성 요소

### 백엔드 구성 요소
- `backend/api/local_llm.py`: 로컬 LLM API 엔드포인트
- `backend/services/local_llm_service.py`: 로컬 모델 관리 및 추론 서비스
- `backend/models/local_llm.py`: 로컬 모델 정보를 위한 데이터 모델
- `backend/model_installer/`: 모델 설치 및 관리 도구

### API 엔드포인트

#### 사용 가능한 모델 목록
```
GET /api/local_llm/models
```
**응답:**
```json
{
    "models": [
        {
            "id": "모델_id",
            "name": "모델명",
            "version": "버전",
            "parameters": "7B",
            "status": "ready|loading|not_installed",
            "installed_at": "설치 타임스탬프",
            "last_used": "마지막 사용 타임스탬프",
            "performance_metrics": {
                "tokens_per_second": 25,
                "memory_usage": "4GB"
            }
        },
        // 추가 모델...
    ]
}
```

#### 모델 설치
```
POST /api/local_llm/install
```
**요청 본문:**
```json
{
    "model_name": "설치할 모델",
    "version": "모델 버전",
    "quantization": "4bit|8bit|16bit",
    "source": "huggingface|custom_url",
    "source_url": "HF 모델 ID 또는 다운로드 URL"
}
```
**응답:**
```json
{
    "install_id": "설치_작업_id",
    "status": "started",
    "estimated_completion": "예상 완료 시간"
}
```

#### 모델 상태 확인
```
GET /api/local_llm/status/{model_id}
```
**응답:**
```json
{
    "id": "모델_id",
    "status": "ready|loading|not_installed|error",
    "memory_usage": "4GB",
    "loaded_at": "로드 타임스탬프",
    "error": "오류 메시지(있는 경우)"
}
```

#### 로컬 LLM으로 추론
```
POST /api/local_llm/generate
```
**요청 본문:**
```json
{
    "model_id": "모델_id",
    "prompt": "LLM에 제공할 프롬프트",
    "max_tokens": 1024,
    "temperature": 0.7,
    "top_p": 0.95,
    "stop_sequences": ["##", "종료"]
}
```
**응답:**
```json
{
    "generated_text": "모델에서 생성된 텍스트",
    "tokens_generated": 512,
    "generation_time": 3.45,  // 초
    "model_used": "모델_id"
}
```

## 지원되는 모델 유형

### 텍스트 생성 모델
- **Llama 2**: Meta의 오픈 소스 LLM
- **Mistral**: 고성능 오픈 소스 모델
- **Falcon**: 기술 혁신 연구소(TII)의 LLM
- **MPT**: MosaicML의 상업적 사용 가능 LLM

### 양자화 버전
- **GGUF(GGML) 포맷**: 효율적인 추론용으로 최적화된 양자화 포맷
- **GPTQ/AWQ**: 정밀도를 유지하면서 모델 크기 감소
- **4-bit, 8-bit 양자화**: 다양한 하드웨어에 맞게 최적화

## 사용 예시

### 로컬 모델로 텍스트 생성
```python
import requests

# 사용 가능한 모델 확인
models_response = requests.get("http://localhost:8000/api/local_llm/models").json()
local_models = models_response["models"]

# 상태가 'ready'인 첫 번째 모델 선택
ready_model = next((model for model in local_models if model["status"] == "ready"), None)

if ready_model:
    # 선택한 모델로 텍스트 생성
    generation_response = requests.post(
        "http://localhost:8000/api/local_llm/generate",
        json={
            "model_id": ready_model["id"],
            "prompt": "다음 수학 문제를 풀어주세요: 2x + 5 = 15",
            "max_tokens": 512,
            "temperature": 0.3
        }
    ).json()
    
    print("생성된 텍스트:")
    print(generation_response["generated_text"])
    print(f"생성 시간: {generation_response['generation_time']}초")
else:
    print("사용 가능한 로컬 모델이 없습니다. 먼저 모델을 설치하세요.")
```

### 프론트엔드 통합
로컬 LLM 시스템은 모델 설치 및 관리 UI, 모델 선택 드롭다운, 로컬 또는 API 모델 간 전환 옵션을 통해 프론트엔드에 통합됩니다.

## 하드웨어 요구 사항

### 최소 요구 사항
- **CPU**: 최소 4코어(7B 모델용)
- **RAM**: 8GB 이상
- **스토리지**: 모델당 4-8GB
- **GPU**: 선택사항(CPU 추론 가능)

### 권장 사양
- **CPU**: 8코어 이상
- **RAM**: 16GB 이상
- **GPU**: NVIDIA GPU, 최소 8GB VRAM
- **스토리지**: 고성능 SSD, 모델당 10-20GB 여유 공간

## 고급 기능
- **모델 미세 조정**: 특정 사용 사례에 맞게 로컬 모델 미세 조정
- **모델 병합**: 여러 모델의 강점을 결합
- **동적 로드/언로드**: 메모리 관리를 위한 자동 모델 로드/언로드
- **멀티 GPU 지원**: 대형 모델을 위한 여러 GPU에 걸친 모델 분산
- **API 호환성 레이어**: OpenAI API 형식으로 로컬 모델 액세스
