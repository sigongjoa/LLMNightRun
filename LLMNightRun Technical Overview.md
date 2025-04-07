# 🚀 LLMNightRun: LLM 기반 자동화 및 Agent 시스템

## 📌 프로젝트 개요

LLMNightRun은 프롬프트 실행, 평가, 리라이팅, 문서화, 배포까지 반복되는 LLM 활용 흐름을 자동화하고, LLM을 단순 API 도구가 아닌 **능동적인 실행 주체(Agent)**로 작동시킬 수 있도록 구성한 통합 시스템입니다.  
현재는 다양한 기능을 중심으로 개발 및 디버깅을 진행 중이며, LLM 기반 실용 도구화, MCP 서버 연동, 워크플로우 Agent 설계 등 여러 기능이 구현되어 있습니다.

---

## ✅ 주요 기능

### 1. LLM 자동 실행 시스템 (NightRun)

- 심야 시간대 프롬프트 자동 실행 및 응답 저장
- 프롬프트 템플릿 관리 및 반복 실행 자동화
- 실행 로그 및 응답 메타 데이터 기록

### 2. 모델 실행 자동화

- `setup.sh` / `config.yaml` 기반 환경 설정 자동화
- GPT-4, Claude, Mistral, KoAlpaca 등 로컬/클라우드 모델 간 전환 지원
- GPU 자원 자동 탐지 및 모델 배치

### 3. 응답 평가 및 리라이팅

- 로컬 평가 모델을 통한 응답 품질 스코어링
- 평가 결과 기반 재질문 및 리라이팅 트리거
- 반복 실험 루프 구성 가능

### 4. LLM 기반 CI/CD 자동화

- 코드/설정 파일 자동 분석 및 개선
- `Dockerfile`, `GitHub Actions`, `yaml` 파일 자동 수정 및 커밋
- **커밋 메시지도 LLM이 자동 생성**
- LLM 기반 GitHub 문서 자동 생성 (README, API 명세 등)

### 5. MCP 시스템 (Model Context Protocol 기반)

- Claude의 MCP 구조 기반 자체 MCP 서버 구현
- 사용자 명령어 + context + tool 정보를 JSON으로 구조화
- 웹브라우저 및 콘솔 기반 MCP 명령 처리 가능
- Agent가 MCP로 전달된 문맥을 받아 실행하는 구조까지 구현

### 6. manus 기반 워크플로우 Agent

- 자연어 명령 기반 다단계 작업 자동화
- `"데이터 정제 → 모델 실행 → 응답 평가"` 같은 복합 워크플로우 구성
- 실행 흐름 시각화 및 step-by-step 결과 추적 가능

---

## 🧾 문서 자동화 및 GitHub 연동

- 응답 결과를 기반으로 LLM이 Markdown 형식의 문서 자동 생성
- README, 실험 요약, API 명세서 자동화 기능
- LLM이 생성한 문서를 GitHub에 커밋 및 푸시까지 자동 수행

---

## 🔭 확장 방향

- LangChain, AutoGen 등 LLM 프레임워크와의 연동 고려
- RLHF 실험 자동화 기능 추가 예정
- 실시간 콘솔 UI/웹 대시보드 제공 목표

---

> 👨‍💻 개발자: [서재용 (sigongjoa)](https://github.com/sigongjoa)  
> 📂 Repository: [github.com/sigongjoa/LLMNightRun](https://github.com/sigongjoa/LLMNightRun)
