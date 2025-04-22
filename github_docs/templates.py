"""
문서 템플릿 모듈

저장소 문서화를 위한 다양한 템플릿을 제공합니다.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional

from jinja2 import Template, Environment, FileSystemLoader
from pathlib import Path

from core.logging import get_logger
from core.config import get_config

logger = get_logger("github_docs.templates")

# 기본 템플릿 경로
DEFAULT_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

def get_available_templates() -> List[Dict[str, Any]]:
    """
    사용 가능한 템플릿 목록 가져오기
    
    Returns:
        템플릿 정보 목록
    """
    config = get_config()
    
    # 템플릿 디렉토리 설정
    templates_dir = config.get("github_docs", "templates_dir", DEFAULT_TEMPLATES_DIR)
    
    # 디렉토리 확인
    if not os.path.exists(templates_dir):
        logger.warning(f"템플릿 디렉토리가 존재하지 않음: {templates_dir}")
        return []
    
    templates = []
    
    # 템플릿 파일 검색
    for filename in os.listdir(templates_dir):
        if filename.endswith(".j2") or filename.endswith(".jinja2") or filename.endswith(".md"):
            template_path = os.path.join(templates_dir, filename)
            
            # 메타데이터 추출
            metadata = extract_template_metadata(template_path)
            
            templates.append({
                "name": metadata.get("name", os.path.splitext(filename)[0]),
                "description": metadata.get("description", ""),
                "file": filename,
                "path": template_path,
                "metadata": metadata
            })
    
    return templates

def extract_template_metadata(template_path: str) -> Dict[str, Any]:
    """
    템플릿 파일에서 메타데이터 추출
    
    Args:
        template_path: 템플릿 파일 경로
    
    Returns:
        메타데이터 딕셔너리
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 메타데이터 블록 패턴
        metadata_pattern = r'{\s*#\s*METADATA\s*(.*?)\s*#\s*}'
        
        # JSON 형식의 메타데이터 찾기
        match = re.search(metadata_pattern, content, re.DOTALL)
        if match:
            try:
                metadata_str = match.group(1).strip()
                return json.loads(metadata_str)
            except json.JSONDecodeError:
                logger.warning(f"메타데이터 JSON 파싱 실패: {template_path}")
        
        # 간단한 키-값 메타데이터 찾기
        metadata = {}
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if not line.strip().startswith('{#') and i > 5:
                break
            
            metadata_line = re.search(r'{\s*#\s*(\w+):\s*(.*?)\s*#\s*}', line)
            if metadata_line:
                key, value = metadata_line.groups()
                metadata[key] = value
        
        return metadata
    
    except Exception as e:
        logger.error(f"템플릿 메타데이터 추출 중 오류 발생: {str(e)}")
        return {}

def render_template(template_name: str, data: Dict[str, Any]) -> str:
    """
    템플릿 렌더링
    
    Args:
        template_name: 템플릿 이름 또는 경로
        data: 템플릿 데이터
    
    Returns:
        렌더링된 문서 문자열
    """
    config = get_config()
    
    # 템플릿 디렉토리 설정
    templates_dir = config.get("github_docs", "templates_dir", DEFAULT_TEMPLATES_DIR)
    
    try:
        # Jinja2 환경 설정
        env = Environment(
            loader=FileSystemLoader([templates_dir, os.path.dirname(os.path.abspath(template_name))]),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 사용자 정의 필터 추가
        env.filters["tojson"] = lambda obj: json.dumps(obj, ensure_ascii=False, indent=2)
        
        # 파일 이름 또는 전체 경로로 템플릿 로드
        if os.path.isfile(template_name):
            template_path = template_name
            template = env.from_string(open(template_path, 'r', encoding='utf-8').read())
        elif os.path.isfile(os.path.join(templates_dir, template_name)):
            template_path = os.path.join(templates_dir, template_name)
            template = env.get_template(os.path.basename(template_name))
        else:
            # 파일 확장자 추가
            for ext in ['.j2', '.jinja2', '.md', '']:
                if os.path.isfile(os.path.join(templates_dir, template_name + ext)):
                    template = env.get_template(template_name + ext)
                    break
            else:
                logger.error(f"템플릿을 찾을 수 없음: {template_name}")
                return f"Error: Template not found: {template_name}"
        
        # 템플릿 렌더링
        return template.render(**data)
    
    except Exception as e:
        logger.error(f"템플릿 렌더링 중 오류 발생: {str(e)}")
        return f"Error rendering template: {str(e)}"

def create_default_templates() -> None:
    """
    기본 템플릿 생성
    """
    # 기본 템플릿 디렉토리 확인 및 생성
    os.makedirs(DEFAULT_TEMPLATES_DIR, exist_ok=True)
    
    # README 템플릿
    readme_template = """
{# METADATA
{
    "name": "README Template",
    "description": "Standard README template for GitHub repositories",
    "version": "1.0.0",
    "author": "LLM Night Run"
}
#}
# {{ repo_name }}

{{ repo_description }}

## Features

{% if features %}
{% for feature in features %}
- {{ feature }}
{% endfor %}
{% else %}
- Feature 1
- Feature 2
- Feature 3
{% endif %}

## Installation

```bash
# Installation commands
{% if installation_commands %}
{% for command in installation_commands %}
{{ command }}
{% endfor %}
{% else %}
git clone {{ repo_url }}
cd {{ repo_name }}
pip install -r requirements.txt
{% endif %}
```

## Usage

```python
{% if usage_example %}
{{ usage_example }}
{% else %}
# Example code
from {{ repo_name }} import main

main.run()
{% endif %}
```

## Project Structure

```
{{ repo_name }}/
{% if directory_structure %}
{% for item in directory_structure %}
{{ item }}
{% endfor %}
{% else %}
├── docs/               # Documentation
├── src/                # Source code
├── tests/              # Tests
├── README.md           # This file
└── requirements.txt    # Dependencies
{% endif %}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

{% if license %}
{{ license }}
{% else %}
This project is licensed under the MIT License - see the LICENSE file for details.
{% endif %}
"""
    
    # API 문서 템플릿
    api_template = """
{# METADATA
{
    "name": "API Documentation",
    "description": "API documentation template for Python projects",
    "version": "1.0.0",
    "author": "LLM Night Run"
}
#}
# {{ module_name }} API Documentation

{{ module_doc }}

## Modules

{% for module in modules %}
### {{ module.module_name }}

{{ module.module_doc }}

{% if module.functions %}
#### Functions

{% for function in module.functions %}
##### `{{ function.name }}({{ function.arguments|join(', ') }})`

{{ function.docstring }}

{% endfor %}
{% endif %}

{% if module.classes %}
#### Classes

{% for class in module.classes %}
##### `{{ class.name }}{% if class.base_classes %}({{ class.base_classes|join(', ') }}){% endif %}`

{{ class.docstring }}

{% if class.methods %}
**Methods:**

{% for method in class.methods %}
- `{{ method.name }}({{ method.arguments|join(', ') }})`: {{ method.docstring }}
{% endfor %}
{% endif %}

{% endfor %}
{% endif %}

{% endfor %}
"""
    
    # 템플릿 저장
    templates = {
        "readme.md.j2": readme_template,
        "api_docs.md.j2": api_template
    }
    
    for filename, content in templates.items():
        file_path = os.path.join(DEFAULT_TEMPLATES_DIR, filename)
        
        # 파일이 없는 경우에만 생성
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"기본 템플릿 생성됨: {filename}")

def generate_documentation(repo_path: str, output_path: str, template_name: str, analysis_result: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
    """
    문서 생성
    
    Args:
        repo_path: 저장소 경로
        output_path: 출력 경로
        template_name: 템플릿 이름
        analysis_result: 저장소 분석 결과
        options: 문서 생성 옵션
    
    Returns:
        생성 결과 딕셔너리
    """
    logger.info(f"문서 생성 중: {repo_path} -> {output_path}")
    
    # 출력 디렉토리 확인 및 생성
    os.makedirs(output_path, exist_ok=True)
    
    # 템플릿 데이터 준비
    repo_name = os.path.basename(repo_path)
    
    template_data = {
        "repo_name": repo_name,
        "repo_path": repo_path,
        "repo_description": analysis_result.get("module_doc", ""),
        "analysis": analysis_result,
        "options": options,
        "timestamp": os.path.getmtime(repo_path),
        "date": os.path.getmtime(repo_path),
    }
    
    # 결과 파일 목록
    generated_files = []
    
    try:
        # README.md 생성
        readme_content = render_template(template_name, template_data)
        readme_path = os.path.join(output_path, "README.md")
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        generated_files.append({
            "name": "README.md",
            "path": readme_path,
            "type": "markdown"
        })
        
        # API 문서 생성 (Python 프로젝트인 경우)
        if any(file.get("language") == "python" for file in analysis_result.get("file_stats", [])):
            api_template = "api_docs.md.j2"
            
            api_data = template_data.copy()
            api_data["modules"] = []
            
            # 모듈별 데이터 구성
            for module in analysis_result.get("modules", []):
                if "module_name" in module:
                    api_data["modules"].append(module)
            
            if api_data["modules"]:
                api_content = render_template(api_template, api_data)
                api_path = os.path.join(output_path, "API.md")
                
                with open(api_path, 'w', encoding='utf-8') as f:
                    f.write(api_content)
                
                generated_files.append({
                    "name": "API.md",
                    "path": api_path,
                    "type": "markdown"
                })
        
        logger.info(f"문서 생성 완료: {len(generated_files)}개 파일")
        
        return {
            "success": True,
            "files": generated_files,
            "output_path": output_path
        }
    
    except Exception as e:
        logger.error(f"문서 생성 중 오류 발생: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "files": generated_files
        }