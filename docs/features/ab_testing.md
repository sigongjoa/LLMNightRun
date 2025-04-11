# A/B 테스트 시스템

A/B 테스트 시스템은 LLM 모델과 프롬프트 조합의 성능을 비교 평가할 수 있는 기능을 제공합니다.

## 개요

A/B 테스트 시스템을 통해 다양한 LLM 모델과 프롬프트 조합을 체계적으로 테스트하여 최적의 조합을 찾을 수 있습니다. 실험 결과를 분석하고 시각화하여 성능 지표를 쉽게 비교할 수 있습니다.

## 주요 기능

- **실험 세트 관리**: 여러 실험을 그룹화하여 관리할 수 있습니다.
- **템플릿 기반 실험**: 재사용 가능한 템플릿을 통해 일관된 실험을 설계할 수 있습니다.
- **병렬 실행**: 여러 실험을 동시에 실행하여 시간을 절약할 수 있습니다.
- **결과 분석**: 다양한 지표를 통해 실험 결과를 분석할 수 있습니다.
- **실험 최적화**: 실험 결과를 기반으로 최적의 프롬프트와, 파라미터를 자동으로 추천합니다.
- **다국어 테스트**: 여러 언어에서의 성능을 비교할 수 있습니다.
- **일관성 테스트**: 모델 응답의 일관성을 평가할 수 있습니다.
- **코드 내보내기**: 최적화된 실험 설정을 코드로 내보낼 수 있습니다.

## 시스템 구조

A/B 테스트 시스템은 다음과 같은 컴포넌트로 구성됩니다:

### 모델

- `ExperimentSet`: 실험 세트를 정의합니다.
- `Experiment`: 개별 실험을 정의합니다.
- `ExperimentResult`: 실험 결과를 저장합니다.
- `ExperimentTemplate`: 재사용 가능한 실험 템플릿을 정의합니다.

### 서비스

- `ExperimentRunner`: 실험을 실행하고 결과를 수집합니다.
- `Evaluator`: 실험 결과를 평가하고 분석합니다.
- `Reporter`: 실험 결과 보고서를 생성합니다.
- `ModelWrapper`: 다양한 LLM 모델에 대한 일관된 인터페이스를 제공합니다.

## 사용 방법

### 실험 세트 생성

1. A/B 테스트 페이지에서 "새 실험 세트 생성" 버튼을 클릭합니다.
2. 실험 세트의 이름과 설명을 입력합니다.
3. 실험을 추가합니다:
   - 모델 선택
   - 프롬프트 작성
   - 파라미터 설정
4. "저장" 버튼을 클릭하여 실험 세트를 저장합니다.

### 템플릿 생성

1. A/B 테스트 페이지에서 "템플릿" 탭을 선택합니다.
2. "새 템플릿 생성" 버튼을 클릭합니다.
3. 템플릿 이름, 설명, 기본 설정을 입력합니다.
4. "저장" 버튼을 클릭하여 템플릿을 저장합니다.

### 실험 실행

1. A/B 테스트 페이지에서 실험 세트를 선택합니다.
2. "실행" 버튼을 클릭합니다.
3. 실험이 완료되면 결과 페이지로 이동합니다.

### 결과 분석

1. 실험 결과 페이지에서 다양한 지표와 그래프를 확인할 수 있습니다.
2. 모델/프롬프트 조합별 성능을 비교할 수 있습니다.
3. 최적의 조합을 식별하고 추가 분석을 수행할 수 있습니다.

## API 엔드포인트

A/B 테스트 시스템은 다음과 같은 API 엔드포인트를 제공합니다:

### 실험 세트 관리

- `GET /ab-testing/experiment-sets`: 실험 세트 목록 조회
- `POST /ab-testing/experiment-sets`: 새 실험 세트 생성
- `GET /ab-testing/experiment-sets/{set_id}`: 실험 세트 상세 조회
- `PUT /ab-testing/experiment-sets/{set_id}`: 실험 세트 업데이트
- `DELETE /ab-testing/experiment-sets/{set_id}`: 실험 세트 삭제
- `POST /ab-testing/experiment-sets/{set_id}/run`:.실험 세트 실행

### 템플릿 관리

- `GET /ab-testing/templates`: 템플릿 목록 조회
- `POST /ab-testing/templates`: 새 템플릿 생성
- `GET /ab-testing/templates/{template_id}`: 템플릿 상세 조회
- `PUT /ab-testing/templates/{template_id}`: 템플릿 업데이트
- `DELETE /ab-testing/templates/{template_id}`: 템플릿 삭제
- `POST /ab-testing/templates/{template_id}/create-experiment-set`: 템플릿으로부터 실험 세트 생성

### 결과 분석

- `GET /ab-testing/experiment-sets/{set_id}/results`: 실험 세트 결과 조회
- `GET /ab-testing/experiments/{experiment_id}/results`: 개별 실험 결과 조회
- `POST /ab-testing/experiments/{experiment_id}/consistency-test`: 일관성 테스트 실행
- `GET /ab-testing/experiments/{experiment_id}/consistency-results/{test_id}`: 일관성 테스트 결과 조회

### 최적화

- `POST /ab-testing/optimization/experiment-sets/{set_id}/optimize`: 실험 세트 최적화
- `GET /ab-testing/optimization/experiment-sets/{set_id}/results/{task_id}`: 최적화 결과 조회

### 다국어 테스트

- `POST /ab-testing/multi-language/experiment-sets/{set_id}/test`: 다국어 테스트 실행
- `GET /ab-testing/multi-language/experiment-sets/{set_id}/results/{test_id}`: 다국어 테스트 결과 조회

### 배치 작업

- `GET /ab-testing/batch-jobs`: 배치 작업 목록 조회
- `GET /ab-testing/batch-jobs/{job_id}`: 배치 작업 상태 조회
- `DELETE /ab-testing/batch-jobs/{job_id}`: 배치 작업 취소

### 코드 내보내기

- `GET /ab-testing/code-export/experiment-sets/{set_id}`: 실험 세트를 코드로 내보내기

## 사용 예시

### 프롬프트 최적화

1. 기본 프롬프트로 실험 세트를 생성합니다.
2. 여러 변형 프롬프트를 추가합니다.
3. 실험 세트를 실행합니다.
4. 결과를 분석하여 가장 효과적인 프롬프트를 식별합니다.
5. 최적화 기능을 사용하여 더 나은 프롬프트를 생성합니다.

### 모델 비교

1. 동일한 프롬프트로 여러 모델을 비교하는 실험 세트를 생성합니다.
2. 실험 세트를 실행합니다.
3. 결과를 분석하여 각 모델의 성능, 응답 시간, 비용 등을 비교합니다.

### 매개변수 튜닝

1. 동일한 모델과 프롬프트로 다양한 매개변수 조합을 테스트하는 실험 세트를 생성합니다.
2. 실험 세트를 실행합니다.
3. 결과를 분석하여 최적의 매개변수 조합을 찾습니다.

## 주의사항

- 대규모 실험 세트 실행 시 API 비용이 발생할 수 있으므로 주의해야 합니다.
- 일부 API는 비동기적으로 작동하며, 완료까지 시간이 소요될 수 있습니다.
- 병렬 실행 시 API 제한으로 인해 일부 요청이 실패할 수 있습니다.
