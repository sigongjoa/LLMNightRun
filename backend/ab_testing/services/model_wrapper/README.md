# Model Wrapper Package

이 패키지는 LLM 모델과의 통신을 처리하는 래퍼 클래스를 제공합니다.

## 구조

- `__init__.py`: 패키지 초기화 및 하위 모듈 내보내기
- `model_wrapper.py`: ModelWrapper 추상 클래스 및 구현 클래스

## 클래스

### ModelWrapper (추상 클래스)

LLM 모델 래퍼의 기본 인터페이스를 정의합니다.

### OpenAIWrapper

OpenAI API와 통신하는 래퍼 클래스입니다.

### ClaudeWrapper

Anthropic Claude API와 통신하는 래퍼 클래스입니다.

### MistralWrapper

Mistral AI API와 통신하는 래퍼 클래스입니다.

## 사용법

```python
from backend.ab_testing.services.model_wrapper import get_model_wrapper

# 모델 래퍼 생성
model_wrapper = get_model_wrapper("gpt-4")

# 텍스트 생성
response = await model_wrapper.generate(
    system_message="당신은 유용한 AI 비서입니다.",
    user_message="파이썬에서 비동기 함수를 어떻게 정의하나요?",
    temperature=0.7,
    max_tokens=2000
)

# 응답 처리
print(response)
```

## 참고 사항

`get_model_wrapper()` 함수는 모델 이름을 분석하여 적절한 래퍼 클래스를 반환합니다:

- `gpt-`로 시작하는 모델은 OpenAIWrapper
- `claude-`로 시작하는 모델은 ClaudeWrapper
- `mistral-`로 시작하는 모델은 MistralWrapper
- 기타 모델은 기본적으로 OpenAIWrapper(gpt-4)로 처리
