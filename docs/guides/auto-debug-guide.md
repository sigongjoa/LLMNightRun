# 자동 디버깅 시스템 사용 가이드

LLMNightRun의 자동 디버깅 시스템은 코드 오류를 자동으로 분석하고 해결하기 위한 다양한 기능을 제공합니다. 이 가이드에서는 각 기능의 사용 방법과 예시를 설명합니다.

## 목차

1. [에러 분석](#1-에러-분석)
2. [자동 수정](#2-자동-수정)
3. [모듈 가져오기 오류 디버깅](#3-모듈-가져오기-오류-디버깅)
4. [환경 검증](#4-환경-검증)
5. [Python 클라이언트 예제](#5-python-클라이언트-예제)

## 1. 에러 분석

에러 메시지와 트레이스백을 분석하여 오류 원인을 파악하고 수정 방안을 제안합니다.

### 엔드포인트

- **URL**: `/debug/analyze`
- **Method**: `POST`
- **쿼리 파라미터**:
  - `llm_type` (선택): 사용할 LLM 유형 (기본값: `openai_api`)

### 요청 본문

```json
{
  "error_message": "오류 메시지",
  "traceback": "오류 트레이스백",
  "codebase_id": 1,
  "additional_context": "추가 컨텍스트 정보 (선택 사항)"
}
```

### 응답

```json
{
  "error_info": {
    "error_message": "ImportError: No module named 'tensorflow'",
    "traceback_text": "Traceback (most recent call last):\n  File \"app.py\", line 10, in <module>\n    import tensorflow as tf\nImportError: No module named 'tensorflow'",
    "error_type": "ImportError",
    "error_location": {
      "file": "app.py",
      "line": 10,
      "function": "<module>"
    },
    "code_lines": ["import tensorflow as tf"]
  },
  "relevant_code": {
    "error_file": "app.py",
    "error_file_content": "# 머신러닝 모델 애플리케이션\n\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nimport sklearn\n\n# 텐서플로우 가져오기\nimport tensorflow as tf\n\n# 모델 정의\ndef create_model():\n    model = tf.keras.Sequential([\n        tf.keras.layers.Dense(128, activation='relu'),\n        tf.keras.layers.Dense(10, activation='softmax')\n    ])\n    return model",
    "related_files": ["app.py"],
    "similar_code": []
  },
  "analysis": "이 오류는 'tensorflow' 모듈을 찾을 수 없어서 발생한 ImportError입니다. 이는 텐서플로우 패키지가 설치되지 않았거나, 현재 사용 중인 Python 환경에서 접근할 수 없기 때문입니다.",
  "fix_suggestions": [
    {
      "file": "app.py",
      "line": 10,
      "original_code": "import tensorflow as tf",
      "fixed_code": "import tensorflow as tf",
      "explanation": "텐서플로우 패키지를 설치해야 합니다. 터미널에서 'pip install tensorflow' 명령어를 실행하세요."
    }
  ],
  "confidence": 0.95
}
```

## 2. 자동 수정

코드 오류를 분석하고 자동으로 수정 사항을 생성합니다. 선택적으로 수정 사항을 즉시 적용할 수 있습니다.

### 엔드포인트

- **URL**: `/debug/auto-fix`
- **Method**: `POST`
- **쿼리 파라미터**:
  - `apply_fix` (선택): 수정 사항 즉시 적용 여부 (기본값: `false`)
  - `llm_type` (선택): 사용할 LLM 유형 (기본값: `openai_api`)

### 요청 본문

```json
{
  "error_message": "오류 메시지",
  "traceback": "오류 트레이스백",
  "codebase_id": 1,
  "additional_context": "추가 컨텍스트 정보 (선택 사항)"
}
```

### 응답

```json
{
  "analysis": "이 오류는 함수 호출 시 필요한 인자를 제공하지 않아 발생한 TypeError입니다.",
  "fix_suggestions": [
    {
      "file": "app.py",
      "line": 25,
      "original_code": "result = calculate_total()",
      "fixed_code": "result = calculate_total(items)",
      "explanation": "calculate_total 함수는 인자가 필요합니다. items 변수를 인자로 전달해야 합니다."
    }
  ],
  "fixed_files": [
    {
      "file": "app.py",
      "original_content": "def calculate_total(items):\n    return sum(item.price for item in items)\n\nitems = get_items()\nresult = calculate_total()\nprint(f\"Total: {result}\")",
      "updated_content": "def calculate_total(items):\n    return sum(item.price for item in items)\n\nitems = get_items()\nresult = calculate_total(items)\nprint(f\"Total: {result}\")",
      "modification": {
        "line": 25,
        "original_code": "result = calculate_total()",
        "fixed_code": "result = calculate_total(items)",
        "explanation": "calculate_total 함수는 인자가 필요합니다. items 변수를 인자로 전달해야 합니다."
      }
    }
  ],
  "applied_fixes": [
    {
      "file": "app.py",
      "success": true,
      "message": "수정 사항이 적용되었습니다."
    }
  ]
}
```

## 3. 모듈 가져오기 오류 디버깅

가져오기에 실패한 모듈을 분석하고 문제 해결 방법을 제안합니다.

### 엔드포인트

- **URL**: `/debug/import-error`
- **Method**: `POST`
- **쿼리 파라미터**:
  - `llm_type` (선택): 사용할 LLM 유형 (기본값: `openai_api`)

### 요청 본문

```json
{
  "module_name": "가져오기 실패한 모듈 이름",
  "error_message": "오류 메시지",
  "codebase_id": 1
}
```

### 응답

```json
{
  "module_name": "tensorflow",
  "error_message": "No module named 'tensorflow'",
  "installation_status": {
    "module_name": "tensorflow",
    "status": "not_found",
    "installed_version": null,
    "installation_path": null,
    "is_standard_library": false
  },
  "dependencies": {
    "module_name": "tensorflow",
    "related_files": ["app.py", "model.py"],
    "import_patterns": ["import tensorflow as tf"]
  },
  "analysis": "텐서플로우 패키지가 현재 환경에 설치되어 있지 않습니다. 이 모듈은 app.py와 model.py 파일에서 사용되고 있습니다.",
  "solution": "다음 명령어로 텐서플로우를 설치하세요:\n\n```bash\npip install tensorflow\n```\n\n가상환경을 사용 중이라면, 해당 환경이 활성화되어 있는지 확인하세요.",
  "install_command": "pip install tensorflow"
}
```

## 4. 환경 검증

코드베이스의 환경 설정을 검증하고 필요한 패키지와 설정을 확인합니다.

### 엔드포인트

- **URL**: `/debug/verify-environment/{codebase_id}`
- **Method**: `GET`

### 응답

```json
{
  "environment_files": [
    {
      "file_path": "requirements.txt",
      "file_type": "requirements.txt",
      "content": "numpy==1.21.0\npandas>=1.3.0\ntensorflow==2.6.0\nscikit-learn==1.0.0"
    },
    {
      "file_path": ".env",
      "file_type": ".env",
      "content": "DEBUG=True\nPYTHON_VERSION=3.8"
    }
  ],
  "requirements": {
    "required_packages": [
      {
        "name": "numpy",
        "version_requirement": "==1.21.0"
      },
      {
        "name": "pandas",
        "version_requirement": ">=1.3.0"
      },
      {
        "name": "tensorflow",
        "version_requirement": "==2.6.0"
      },
      {
        "name": "scikit-learn",
        "version_requirement": "==1.0.0"
      }
    ],
    "direct_imports": ["numpy", "pandas", "tensorflow", "sklearn", "matplotlib"],
    "third_party_imports": {
      "numpy": ["app.py", "model.py"],
      "pandas": ["app.py"],
      "tensorflow": ["app.py", "model.py"],
      "sklearn": ["model.py"],
      "matplotlib": ["app.py"]
    },
    "has_requirements_file": true,
    "has_setup_py": false,
    "detected_python_version": "3.8"
  },
  "environment_analysis": {
    "missing_packages": [
      {
        "name": "tensorflow",
        "requirement": "==2.6.0"
      }
    ],
    "version_mismatch": [
      {
        "name": "numpy",
        "expected_version": "1.21.0",
        "current_version": "1.22.3"
      }
    ],
    "satisfied_requirements": [
      {
        "name": "pandas",
        "version": "1.4.1"
      },
      {
        "name": "scikit-learn",
        "version": "1.0.0"
      }
    ],
    "setup_commands": [
      "# 가상환경 생성 권장",
      "python -m venv venv",
      "# Windows: venv\\Scripts\\activate",
      "# Linux/Mac: source venv/bin/activate",
      "pip install tensorflow==2.6.0",
      "pip install numpy==1.21.0 --upgrade",
      "# 모든 의존성 설치",
      "pip install -r requirements.txt"
    ]
  },
  "missing_packages": [
    {
      "name": "tensorflow",
      "requirement": "==2.6.0"
    }
  ],
  "version_mismatch": [
    {
      "name": "numpy",
      "expected_version": "1.21.0",
      "current_version": "1.22.3"
    }
  ],
  "setup_commands": [
    "# 가상환경 생성 권장",
    "python -m venv venv",
    "# Windows: venv\\Scripts\\activate",
    "# Linux/Mac: source venv/bin/activate",
    "pip install tensorflow==2.6.0",
    "pip install numpy==1.21.0 --upgrade",
    "# 모든 의존성 설치",
    "pip install -r requirements.txt"
  ]
}
```

## 5. Python 클라이언트 예제

다음은 Python으로 자동 디버깅 API를 사용하는 예제입니다.

### 에러 분석 요청 예제

```python
import requests
import json

def analyze_error(error_message, traceback, codebase_id, additional_context=None):
    """에러 분석 요청 함수"""
    
    url = "http://localhost:8000/debug/analyze"
    
    data = {
        "error_message": error_message,
        "traceback": traceback,
        "codebase_id": codebase_id
    }
    
    if additional_context:
        data["additional_context"] = additional_context
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"오류 발생: {response.status_code}")
        print(response.text)
        return None

# 사용 예시
if __name__ == "__main__":
    error_msg = "TypeError: calculate_total() missing 1 required positional argument: 'items'"
    traceback_text = """Traceback (most recent call last):
  File "app.py", line 25, in <module>
    result = calculate_total()
TypeError: calculate_total() missing 1 required positional argument: 'items'"""
    
    result = analyze_error(error_msg, traceback_text, 1)
    
    if result:
        print("분석 결과:")
        print(f"분석: {result['analysis']}")
        
        print("\n수정 제안:")
        for suggestion in result['fix_suggestions']:
            print(f"파일: {suggestion['file']}")
            print(f"라인: {suggestion['line']}")
            print(f"원본 코드: {suggestion['original_code']}")
            print(f"수정 코드: {suggestion['fixed_code']}")
            print(f"설명: {suggestion['explanation']}")
```

### 자동 수정 요청 예제

```python
def auto_fix_error(error_message, traceback, codebase_id, apply_fix=False, additional_context=None):
    """자동 수정 요청 함수"""
    
    url = f"http://localhost:8000/debug/auto-fix?apply_fix={str(apply_fix).lower()}"
    
    data = {
        "error_message": error_message,
        "traceback": traceback,
        "codebase_id": codebase_id
    }
    
    if additional_context:
        data["additional_context"] = additional_context
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"오류 발생: {response.status_code}")
        print(response.text)
        return None

# 사용 예시
result = auto_fix_error(error_msg, traceback_text, 1, apply_fix=True)

if result:
    print("자동 수정 결과:")
    print(f"분석: {result['analysis']}")
    
    print("\n수정된 파일:")
    for file in result.get('fixed_files', []):
        print(f"파일: {file['file']}")
        print(f"수정 내용: {file['modification']['explanation']}")
    
    print("\n적용 결과:")
    for fix in result.get('applied_fixes', []):
        print(f"파일: {fix['file']}")
        print(f"성공 여부: {fix['success']}")
        print(f"메시지: {fix['message']}")
```

### 환경 검증 요청 예제

```python
def verify_environment(codebase_id):
    """환경 검증 요청 함수"""
    
    url = f"http://localhost:8000/debug/verify-environment/{codebase_id}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"오류 발생: {response.status_code}")
        print(response.text)
        return None

# 사용 예시
env_result = verify_environment(1)

if env_result:
    print("환경 검증 결과:")
    
    print("\n환경 파일:")
    for file in env_result.get('environment_files', []):
        print(f"- {file['file_path']}")
    
    print("\n필요한 패키지:")
    for pkg in env_result.get('requirements', {}).get('required_packages', []):
        print(f"- {pkg['name']} {pkg['version_requirement']}")
    
    print("\n누락된 패키지:")
    for pkg in env_result.get('missing_packages', []):
        print(f"- {pkg['name']} {pkg['requirement']}")
    
    print("\n설치 명령어:")
    for cmd in env_result.get('setup_commands', []):
        print(cmd)
```

## 통합 사용 시나리오

다음은 일반적인 워크플로우에서 자동 디버깅 시스템을 활용하는 시나리오입니다:

1. 프로젝트를 처음 설정할 때 `verify-environment` 엔드포인트를 사용하여 필요한 환경을 검증합니다.
2. 프로젝트 실행 중 오류가 발생하면 `analyze` 엔드포인트를 사용하여 문제를 분석합니다.
3. 자동으로 수정 가능한 오류는 `auto-fix` 엔드포인트를 사용하여 해결합니다.
4. 모듈 가져오기 오류가 발생하면 `import-error` 엔드포인트를 사용하여 패키지 문제를 진단합니다.

자동 디버깅 시스템은 개발자의 디버깅 시간을 단축시키고, 특히 복잡한 에러나 의존성 문제를 해결하는 데 큰 도움이 됩니다.
