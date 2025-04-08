# LLM 메모리 관리 및 Vector DB 연동 시스템 가이드

LLMNightRun 플랫폼에 추가된 벡터 데이터베이스 기반 메모리 시스템에 대한 안내 문서입니다.

## 개요

LLM 메모리 시스템은 LLM(Large Language Model)이 과거의 대화, 실험, 코드 등을 "기억"하고 참조할 수 있도록 하는 시스템입니다. 벡터 데이터베이스를 통해 텍스트를 벡터로 변환하여 저장하고, 유사도 기반 검색을 통해 관련 컨텍스트를 제공합니다.

### 주요 기능
- 대화 내용, 실험 결과, 코드 조각 등을 메모리로 저장
- 벡터 유사도 검색을 통한 관련 메모리 찾기
- LLM 프롬프트에 관련 메모리 컨텍스트 자동 삽입
- 메모리 관리를 위한 웹 인터페이스 제공

## 설치 및 설정

### 요구 사항
- Python 3.8 이상
- FAISS 및 Sentence Transformers 설치 필요

### 설치 방법

1. 추가 의존성 설치:
   ```bash
   pip install -r requirements-memory.txt
   ```

2. 메모리 시스템 초기화:
   ```bash
   python scripts/setup_memory.py
   ```

3. 백엔드 서버를 다시 시작합니다:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 메모리 관리 사용법

### 웹 인터페이스를 통한 관리

1. LLMNightRun 웹 인터페이스에서 "메모리 관리" 메뉴를 선택합니다.
2. 메모리를 검색, 생성, 삭제, 편집할 수 있습니다.
3. 태그를 사용하여 메모리를 분류하고 관리할 수 있습니다.

### 메모리 유형

메모리는 다음과 같은 유형으로 분류됩니다:

- **Conversation**: 대화 내용
- **Experiment**: 실험 결과
- **Code**: 코드 조각
- **Result**: 결과 데이터
- **Note**: 일반 메모

### 메모리 검색

1. 검색창에 키워드를 입력합니다.
2. 메모리 유형 필터를 사용해 특정 유형만 표시할 수 있습니다.
3. 검색 결과는 입력 텍스트와의 유사도 순으로 표시됩니다.

### 새 메모리 생성

1. "새 메모리 생성" 폼을 사용합니다.
2. 메모리 유형, 내용, 태그를 입력합니다.
3. "메모리 저장" 버튼을 클릭합니다.

## LLM과의 통합

LLM이 메모리 시스템을 활용하는 방법:

### 메모리 활성화하기

LLM 인스턴스 생성 시 `use_memory` 옵션을 활성화합니다:

```python
from backend.llm import LLM

# 메모리 기능을 활성화한 LLM 인스턴스 생성
llm = LLM(
    config_name="default", 
    llm_type="LOCAL_LLM",
    use_memory=True  # 메모리 기능 활성화
)
```

### 자동 메모리 사용

메모리가 활성화된 LLM은 다음과 같은 기능을 자동으로 수행합니다:

1. **컨텍스트 증강**: 대화 시 관련된 이전 메모리를 검색하여 시스템 프롬프트에 추가합니다.
2. **대화 저장**: 사용자 질문과 LLM 응답을 자동으로 메모리에 저장합니다.
3. **실험 결과 저장**: `store_experiment_memory` 메서드로 실험 결과를 저장할 수 있습니다.

### 실험 결과 저장 예시

```python
# 실험 결과를 메모리에 저장
memory_id = llm.store_experiment_memory({
    "experiment_id": "exp_123",
    "model_name": "gpt-4",
    "prompt": "분석 결과를 요약해주세요...",
    "response": "분석 결과는 다음과 같습니다...",
    "metrics": {"accuracy": 0.87, "latency": 3.2},
    "metadata": {
        "tags": ["summarization", "gpt-4", "high-accuracy"]
    }
})
```

## API 참조

### 백엔드 API 엔드포인트

메모리 시스템은 다음과 같은 API 엔드포인트를 제공합니다:

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/memory/add` | POST | 새 메모리 추가 |
| `/api/memory/batch` | POST | 여러 메모리 일괄 추가 |
| `/api/memory/search` | POST | 메모리 검색 |
| `/api/memory/get/{memory_id}` | GET | 특정 메모리 조회 |
| `/api/memory/delete/{memory_id}` | DELETE | 메모리 삭제 |
| `/api/memory/clear` | POST | 모든 메모리 삭제 |
| `/api/memory/count` | GET | 메모리 총 개수 조회 |
| `/api/memory/context` | POST | 쿼리에 대한 메모리 컨텍스트 조회 |
| `/api/memory/attach-context` | POST | 프롬프트에 메모리 컨텍스트 추가 |
| `/api/memory/experiment` | POST | 실험 메모리 저장 |
| `/api/memory/related` | POST | 프롬프트 관련 메모리 검색 |
| `/api/memory/health` | GET | 메모리 시스템 상태 확인 |

### Python API

메모리 매니저를 직접 사용하는 예시:

```python
from backend.memory.memory_manager import get_memory_manager

# 메모리 매니저 인스턴스 가져오기
memory_manager = get_memory_manager()

# 메모리 추가
memory_id = memory_manager.add_memory({
    "content": "중요한 정보",
    "type": "note",
    "metadata": {
        "tags": ["important", "reminder"]
    }
})

# 메모리 검색
memories = memory_manager.search_memories({
    "query": "중요한",
    "top_k": 5
})

# 프롬프트에 컨텍스트 추가
enhanced_prompt = memory_manager.attach_context_to_prompt(
    prompt="이 문제를 해결해주세요",
    query="문제 해결"
)
```

## 성능 최적화 및 문제 해결

### 성능 최적화 팁

1. **메모리 제한**: 오래된 메모리는 자동으로 90일 후 정리됩니다. 필요에 따라 `max_memory_days` 매개변수를 조정할 수 있습니다.

2. **벡터 인덱스 최적화**: 대규모 데이터셋의 경우 `use_ivf_index=True` 옵션을 사용하면 검색 성능이 향상됩니다.

3. **배치 처리**: 다수의 메모리를 추가할 때는 `add_memories` 배치 메서드를 사용하세요.

### 일반적인 문제 해결

1. **메모리 저장 실패**: 
   - 디스크 공간이 충분한지 확인
   - 데이터 디렉토리 접근 권한 확인
   - 로그 파일에서 자세한 오류 확인

2. **검색 결과 부족**:
   - 검색어를 좀 더 구체적으로 변경
   - 필터링 조건 완화
   - 임베딩 모델이 제대로 로드되었는지 확인

3. **응답 지연**:
   - 메모리 개수가 많을 경우 인덱스 최적화 필요
   - `top_k` 값을 낮춰 검색 범위 축소
   - 필요에 따라 로컬 캐싱 활용

## 고급 기능

### 임베딩 모델 변경

기본 임베딩 모델(sentence-transformers/all-MiniLM-L6-v2) 대신 다른 모델을 사용하려면:

```python
from backend.memory.embeddings import get_embedding_model
from backend.memory.vector_store import get_vector_store

# 다른 임베딩 모델 지정
embedding_model = get_embedding_model("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# 벡터 스토어 생성 시 모델 지정
vector_store = get_vector_store(embedding_model=embedding_model)
```

### 메타데이터 필터링

태그 및 날짜 기반 검색 예시:

```python
import datetime

# 특정 태그와 날짜 범위로 검색
memories = memory_manager.search_memories({
    "query": "성능 테스트",
    "tags": ["optimization", "benchmark"],
    "date_from": datetime.datetime.now() - datetime.timedelta(days=30),
    "date_to": datetime.datetime.now(),
    "memory_types": ["experiment", "result"]
})
```

## 보안 및 유지 관리

### 데이터 백업

1. 벡터 DB 파일은 `backend/data/faiss_store` 디렉토리에 저장됩니다.
2. 정기적으로 이 디렉토리를 백업하는 것이 좋습니다.
3. `faiss.index` 및 `metadata.pkl` 파일을 함께 백업하세요.

### 정기 유지 관리

1. 오래된 메모리 정리:
   ```python
   # 30일 이상 된 메모리 정리 (기본값은 90일)
   vector_store = get_vector_store(max_memory_days=30)
   ```

2. 인덱스 최적화 (선택 사항):
   ```bash
   # 벡터 인덱스 재구축 및 최적화 스크립트 실행
   python scripts/optimize_vector_index.py
   ```

## 결론

LLM 메모리 시스템은 LLM의 컨텍스트 인식 능력을 크게 향상시킵니다. 이 시스템을 통해 LLM은 과거 대화와 실험에서 학습한 내용을 활용하여 더 일관되고 정확한 응답을 제공할 수 있습니다.

문제나 개선 사항이 있으면 개발팀에 문의하거나 이슈 트래커에 보고해 주세요.
