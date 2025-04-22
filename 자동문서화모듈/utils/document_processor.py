"""
문서 처리 관련 유틸리티
"""

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

class DocumentProcessor:
    """문서 처리 및 관리를 위한 클래스"""
    
    def __init__(self, templates_dir: Path, output_dir: Path, doc_types: Dict[str, Dict[str, Any]]):
        """
        DocumentProcessor 초기화
        
        Args:
            templates_dir: 템플릿 파일이 저장된 디렉토리 경로
            output_dir: 생성된 문서를 저장할 디렉토리 경로
            doc_types: 문서 유형 정보를 담은 딕셔너리
        """
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        self.doc_types = doc_types
        
        # 템플릿 디렉토리가 없으면 생성
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
            
        # 출력 디렉토리가 없으면 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 기본 템플릿 생성 (없는 경우)
        self._create_default_templates()
        
    def _create_default_templates(self):
        """기본 템플릿 파일 생성 (없는 경우)"""
        for doc_type, info in self.doc_types.items():
            template_path = self.templates_dir / info["template_file"]
            if not os.path.exists(template_path):
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(self._get_default_template_content(doc_type))
                    
    def _get_default_template_content(self, doc_type: str) -> str:
        """
        문서 유형에 따른 기본 템플릿 내용 반환
        
        Args:
            doc_type: 문서 유형 (README, INSTALL 등)
            
        Returns:
            템플릿 내용
        """
        templates = {
            "README": """# {project_name}

## 개요
{project_description}

## 기능
- {feature1}
- {feature2}
...

## 설치 방법
```bash
{installation_command}
```

## 사용 방법
```python
{usage_example}
```

## 라이센스
{license}
""",
            "INSTALL": """# 설치 가이드

## 시스템 요구사항
- Python {python_version} 이상
- {requirement1}
- {requirement2}

## 설치 단계
1. {step1}
2. {step2}
...

## 환경 설정
```bash
{environment_setup}
```

## 문제 해결
- **문제**: {common_issue}
  **해결**: {solution}
""",
            "USAGE": """# 사용법 가이드

## 기본 사용법
```python
{basic_usage}
```

## 예제
### 예제 1: {example1_title}
```python
{example1_code}
```

### 예제 2: {example2_title}
```python
{example2_code}
```

## 명령줄 인터페이스
```bash
{cli_command} [옵션]
```

### 옵션
- `--{option1}`: {option1_description}
- `--{option2}`: {option2_description}
""",
            "API": """# API 문서

## 개요
{api_description}

## 엔드포인트

### `{endpoint1_path}`
- **메서드**: {http_method}
- **설명**: {endpoint_description}
- **요청 파라미터**:
  - `{param1}` ({param1_type}): {param1_description}
  - `{param2}` ({param2_type}): {param2_description}
- **응답**:
```json
{response_example}
```

### `{endpoint2_path}`
...
""",
            "MODULE": """# 모듈 문서

## 개요
{module_description}

## 클래스

### `{class_name}`
{class_description}

#### 메서드
- `{method1}({params})`: {method1_description}
- `{method2}({params})`: {method2_description}

## 함수

### `{function_name}({params})`
{function_description}

#### 매개변수
- `{param1}` ({param1_type}): {param1_description}
- `{param2}` ({param2_type}): {param2_description}

#### 반환값
- {return_type}: {return_description}

## 사용 예시
```python
{usage_example}
```
""",
            "RESULTS": """# 실험/결과 요약

## 개요
{experiment_description}

## 실험 설정
- **날짜**: {experiment_date}
- **환경**: {environment}
- **파라미터**:
  - {param1}: {value1}
  - {param2}: {value2}

## 결과
{results_description}

### 표
| {header1} | {header2} | {header3} |
|-----------|-----------|-----------|
| {row1_col1} | {row1_col2} | {row1_col3} |
| {row2_col1} | {row2_col2} | {row2_col3} |

## 결론
{conclusion}
""",
            "PLAN": """# 기획/계획 문서

## 개요
{plan_description}

## 목표
- {goal1}
- {goal2}

## 기능 요구사항
1. {feature1}
   - {subfeature1}
   - {subfeature2}
2. {feature2}
   - {subfeature3}
   - {subfeature4}

## 일정
- **1단계**: {phase1_description}
  - 마감일: {phase1_deadline}
  - 담당자: {phase1_owner}
- **2단계**: {phase2_description}
  - 마감일: {phase2_deadline}
  - 담당자: {phase2_owner}

## 기술 스택
- {technology1}: {technology1_purpose}
- {technology2}: {technology2_purpose}
""",
            "CHANGELOG": """# 변경 이력

## [버전 {version_number}] - {release_date}
### 추가
- {added_feature1}
- {added_feature2}

### 변경
- {changed_feature1}
- {changed_feature2}

### 수정
- {fixed_issue1}
- {fixed_issue2}

### 제거
- {removed_feature1}
- {removed_feature2}

## [버전 {prev_version_number}] - {prev_release_date}
...
""",
            "DEPLOY": """# 배포 가이드

## 요구사항
- {requirement1}
- {requirement2}

## 환경 설정
```bash
{environment_setup}
```

## Docker 배포
### Docker 파일
```dockerfile
{dockerfile_content}
```

### 빌드 및 실행
```bash
{docker_build_command}
{docker_run_command}
```

## 서버 배포
1. {server_step1}
2. {server_step2}
...

## 배포 후 검증
- {validation_step1}
- {validation_step2}
"""
        }
        
        return templates.get(doc_type, "# {doc_type} 문서\n\n## 내용을 입력하세요")
    
    def get_template(self, doc_type: str) -> str:
        """
        문서 유형에 맞는 템플릿 가져오기
        
        Args:
            doc_type: 문서 유형 (README, INSTALL 등)
            
        Returns:
            템플릿 내용
        """
        if doc_type not in self.doc_types:
            return "# 문서\n\n내용을 입력하세요."
            
        template_file = self.doc_types[doc_type]["template_file"]
        template_path = self.templates_dir / template_file
        
        if not os.path.exists(template_path):
            return self._get_default_template_content(doc_type)
            
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def save_document(self, doc_type: str, content: str, base_name: Optional[str] = None) -> Tuple[str, str]:
        """
        생성된 문서 저장
        
        Args:
            doc_type: 문서 유형 (README, INSTALL 등)
            content: 문서 내용
            base_name: 기본 파일명 (없으면 자동 생성)
            
        Returns:
            (파일 경로, 파일명) 튜플
        """
        if doc_type not in self.doc_types:
            doc_type = "README"  # 기본값
            
        file_ext = self.doc_types[doc_type]["file_ext"]
        
        if not base_name:
            # 파일명 자동 생성 (doc_type + 타임스탬프)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{doc_type.lower()}_{timestamp}"
        
        # 파일명에서 특수문자 제거
        base_name = re.sub(r'[^\w\-\.]', '_', base_name)
        file_name = f"{base_name}.{file_ext}"
        file_path = self.output_dir / file_name
        
        # 중복 파일명 처리
        counter = 1
        while os.path.exists(file_path):
            file_name = f"{base_name}_{counter}.{file_ext}"
            file_path = self.output_dir / file_name
            counter += 1
        
        # 문서 저장
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return str(file_path), file_name
    
    def get_saved_documents(self) -> List[Dict[str, str]]:
        """
        저장된 문서 목록 가져오기
        
        Returns:
            문서 정보 리스트 [{name, path, type, size, created}, ...]
        """
        results = []
        
        if not os.path.exists(self.output_dir):
            return results
            
        for file_name in os.listdir(self.output_dir):
            file_path = self.output_dir / file_name
            if os.path.isfile(file_path) and file_name.endswith(('.md', '.rst')):
                # 파일 정보 추출
                stat = os.stat(file_path)
                created = datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
                size = stat.st_size
                
                # 문서 타입 추정
                doc_type = "기타"
                for dt, info in self.doc_types.items():
                    if file_name.lower().startswith(dt.lower()) or \
                       (dt.lower() in file_name.lower()):
                        doc_type = dt
                        break
                
                results.append({
                    "name": file_name,
                    "path": str(file_path),
                    "type": doc_type,
                    "size": f"{size/1024:.1f} KB",
                    "created": created
                })
                
        return results
