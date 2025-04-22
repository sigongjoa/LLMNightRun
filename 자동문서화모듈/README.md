# 자동문서화모듈

## 개요
자동문서화모듈은 LLM(Large Language Model)을 활용해 대화 기반으로 다양한 형식의 문서를 자동으로 생성하는 도구입니다. 대화 로그를 분석하여 의도를 파악하고, 적절한 문서 형식으로 변환해 관리할 수 있습니다.

## 주요 기능
- 대화 로그에서 의도와 키워드 자동 추출
- 다양한 문서 유형 지원 (README, API 문서, 사용법 가이드 등)
- 템플릿 기반 문서 자동 생성
- Git 연동을 통한 문서 자동 커밋
- 직관적인 GUI 인터페이스

## 시스템 요구사항
- Python 3.7 이상
- LM Studio 또는 호환 가능한 LLM API 서버

## 설치 방법
1. 저장소 클론:
```bash
git clone https://github.com/yourusername/LLMNightRun_feature.git
cd LLMNightRun_feature/자동문서화모듈
```

2. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

## 사용 방법
1. LM Studio를 실행하고 모델을 로드합니다.
2. 자동문서화모듈 실행:
```bash
python main.py
```
3. GUI에서 대화 로그 파일을 선택합니다.
4. 문서 유형을 선택하고 '문서 생성' 버튼을 클릭합니다.
5. 생성된 문서를 검토하고 저장합니다.
6. (선택 사항) Git 연동을 활성화하여 자동으로 커밋합니다.

## 폴더 구조
- `templates/` - 문서 템플릿 파일
- `logs/` - 대화 로그 저장 폴더
- `generated_docs/` - 생성된 문서 저장 폴더
- `utils/` - 유틸리티 모듈

## 확장 가능성
- 문서 히스토리 시각화 기능 추가
- 자동 문서 피드백 시스템 구현
- 템플릿 편집 기능 추가
- 문서 버전 관리 시스템 연동

## 라이센스
MIT License
