# GitHub AI 모델 환경 설정 및 학습 도구

이 도구는 GitHub에서 AI 모델 레포지토리를 다운로드하고, 환경을 설정하며, 데이터를 전처리하고, 모델을 학습 및 시각화하는 기능을 제공합니다.

## 주요 기능

1. **모델 학습 환경 설정**
   - GitHub 레포지토리 다운로드 및 분석
   - 가상 환경 또는 Conda 환경 자동 구성
   - 필요한 패키지 설치

2. **데이터 전처리**
   - 데이터 파일 검색 및 로드
   - 데이터 분할, 정규화, 토큰화 등 기본 전처리 단계 제공
   - 사용자 정의 전처리 스크립트 지원

3. **모델 학습 및 로깅**
   - PyTorch, TensorFlow, scikit-learn 등 다양한 프레임워크 지원
   - TensorBoard를 통한 학습 과정 모니터링
   - 체크포인트 저장 및 관리

4. **결과 시각화**
   - 데이터 분포 시각화
   - 학습 과정 시각화
   - 모델 성능 시각화

## 설치 방법

```bash
# 필요한 패키지 설치
pip install -r requirements.txt
```

## 사용 방법

### 기본 사용법

```bash
python main.py --repo <github_repo_url> --config <config_file_path>
```

### 매개변수 설명

- `--repo`: GitHub 레포지토리 URL (필수)
- `--config`: 설정 파일 경로 (기본값: configs/default_config.yaml)
- `--start-state`: 시작할 단계 (init, download, setup, preprocess, train, visualize)

### 설정 파일

기본 설정 파일(configs/default_config.yaml)은 다음과 같은 섹션으로 구성됩니다:

- `github`: GitHub 관련 설정
- `environment`: 환경 설정
- `data`: 데이터 처리 설정
- `training`: 학습 설정
- `visualization`: 시각화 설정

## 예제

### 기본 워크플로우 실행

```bash
python main.py --repo https://github.com/username/ai-model-repo
```

### 특정 단계부터 실행

```bash
python main.py --repo https://github.com/username/ai-model-repo --start-state train
```

### 사용자 정의 설정 파일 사용

```bash
python main.py --repo https://github.com/username/ai-model-repo --config my_config.yaml
```

## 테스트

테스트를 실행하려면:

```bash
python run_tests.py
```

## 디렉토리 구조

```
github_ai_setup/
├── configs/             # 설정 파일
│   └── default_config.yaml # 기본 설정 파일
├── src/                 # 소스 코드
│   ├── data/            # 데이터 처리 모듈
│   ├── models/          # 모델 관련 모듈
│   ├── utils/           # 유틸리티 모듈
│   └── visualization/   # 시각화 모듈
├── tests/               # 테스트 코드
├── main.py              # 메인 실행 파일
└── run_tests.py         # 테스트 실행 스크립트
```

## 상태 관리

도구는 다음과 같은 상태를 통해 워크플로우를 관리합니다:

1. `init`: 초기 상태
2. `download`: GitHub 레포지토리 다운로드 중
3. `setup`: 환경 설정 중
4. `preprocess`: 데이터 전처리 중
5. `train`: 모델 학습 중
6. `visualize`: 결과 시각화 중
7. `complete`: 워크플로우 완료
8. `error`: 오류 발생

오류가 발생한 경우, 로그 파일과 상태 파일(logs/state.json)에서 자세한 정보를 확인할 수 있습니다.
