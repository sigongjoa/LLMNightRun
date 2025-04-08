"""
OpenAPI 생성기 유틸리티

FastAPI의 OpenAPI 스키마를 확장하여 더 풍부한 API 문서를 생성합니다.
"""

import json
from typing import Dict, Any, List, Optional, Union, Set
from pathlib import Path

from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI, APIRouter

from ..config import settings
from ..logger import get_logger

# 로거 설정
logger = get_logger(__name__)


def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    커스텀 OpenAPI 스키마 생성 함수
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
        
    Returns:
        OpenAPI 스키마 사전
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    # 기본 OpenAPI 스키마 생성
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        servers=getattr(app, "servers", None),
    )
    
    # 추가 서버 정보
    if settings.is_production():
        openapi_schema["servers"] = [
            {"url": settings.root_path, "description": "프로덕션 서버"}
        ]
    else:
        openapi_schema["servers"] = [
            {"url": settings.root_path, "description": "개발 서버"}
        ]
    
    # 확장 정보 추가
    openapi_schema["info"]["x-logo"] = {
        "url": "/static/logo.png",
        "altText": settings.app_name
    }
    
    # 추가 태그 정보
    enhance_tags(openapi_schema)
    
    # 보안 스키마 추가
    if settings.security.api_key_enabled:
        add_security_schemes(openapi_schema)
    
    # 응답 예시 추가
    if settings.is_development():
        add_response_examples(openapi_schema)
    
    # 결과 캐싱
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def enhance_tags(openapi_schema: Dict[str, Any]) -> None:
    """
    OpenAPI 스키마에 태그 정보 보강
    
    Args:
        openapi_schema: OpenAPI 스키마 사전
    """
    # 태그가 없는 경우 초기화
    if "tags" not in openapi_schema:
        openapi_schema["tags"] = []
    
    # 기존 태그 ID 추출
    existing_tags = {tag["name"] for tag in openapi_schema["tags"]}
    
    # 추가할 기본 태그 정보
    default_tags = {
        "core": {
            "description": "핵심 Q&A 및 코드 생성 기능",
            "externalDocs": {
                "description": "기능 문서",
                "url": "https://github.com/yourusername/LLMNightRun/blob/main/docs/core.md"
            }
        },
        "agent": {
            "description": "AI 에이전트 및 도구 관련 기능",
            "externalDocs": {
                "description": "기능 문서",
                "url": "https://github.com/yourusername/LLMNightRun/blob/main/docs/agent.md"
            }
        },
        "data": {
            "description": "데이터 관리 및 인덱싱 기능",
            "externalDocs": {
                "description": "기능 문서",
                "url": "https://github.com/yourusername/LLMNightRun/blob/main/docs/data.md"
            }
        },
        "system": {
            "description": "시스템 관리 및 설정 기능",
            "externalDocs": {
                "description": "기능 문서",
                "url": "https://github.com/yourusername/LLMNightRun/blob/main/docs/system.md"
            }
        },
        "monitoring": {
            "description": "시스템 상태 및 모니터링 기능",
            "externalDocs": {
                "description": "기능 문서",
                "url": "https://github.com/yourusername/LLMNightRun/blob/main/docs/monitoring.md"
            }
        }
    }
    
    # 기존 태그에 없는 태그만 추가
    for tag_name, tag_info in default_tags.items():
        if tag_name not in existing_tags:
            openapi_schema["tags"].append({
                "name": tag_name,
                "description": tag_info["description"],
                "externalDocs": tag_info["externalDocs"]
            })


def add_security_schemes(openapi_schema: Dict[str, Any]) -> None:
    """
    OpenAPI 스키마에 보안 스키마 추가
    
    Args:
        openapi_schema: OpenAPI 스키마 사전
    """
    # 보안 스키마가 없는 경우 초기화
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    # API 키 인증 추가
    openapi_schema["components"]["securitySchemes"]["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API 키 인증"
    }
    
    # 전역 보안 요구사항 추가
    openapi_schema["security"] = [{"ApiKeyAuth": []}]


def add_response_examples(openapi_schema: Dict[str, Any]) -> None:
    """
    OpenAPI 스키마에 응답 예시 추가
    
    Args:
        openapi_schema: OpenAPI 스키마 사전
    """
    # 경로 정보가 없는 경우 종료
    if "paths" not in openapi_schema:
        return
    
    # 공통 응답 스키마 정의
    common_responses = {
        "400": {
            "description": "잘못된 요청",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "validation_error",
                        "message": "데이터 검증 오류가 발생했습니다",
                        "detail": [
                            {"loc": ["body", "name"], "msg": "필수 항목입니다"}
                        ]
                    }
                }
            }
        },
        "401": {
            "description": "인증되지 않음",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "unauthorized",
                        "message": "API 키가 필요합니다",
                        "detail": None
                    }
                }
            }
        },
        "404": {
            "description": "찾을 수 없음",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "not_found",
                        "message": "요청한 리소스를 찾을 수 없습니다",
                        "detail": None
                    }
                }
            }
        },
        "500": {
            "description": "서버 내부 오류",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "internal_server_error",
                        "message": "서버 내부 오류가 발생했습니다",
                        "detail": "오류에 대한 자세한 내용"
                    }
                }
            }
        }
    }
    
    # 모든 경로에 공통 응답 추가
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "responses" not in method:
                method["responses"] = {}
            
            # 이미 정의된 응답은 건너뜀
            for status_code, response in common_responses.items():
                if status_code not in method["responses"]:
                    method["responses"][status_code] = response


def export_openapi_schema(app: FastAPI, output_path: Optional[Path] = None) -> None:
    """
    OpenAPI 스키마를 파일로 내보내기
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
        output_path: 출력 파일 경로 (None인 경우 기본 경로 사용)
    """
    # 기본 출력 경로 설정
    if output_path is None:
        output_path = settings.base_dir / "openapi.json"
    
    # OpenAPI 스키마 생성
    openapi_schema = custom_openapi(app)
    
    # 파일로 저장
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, ensure_ascii=False, indent=2)
    
    logger.info(f"OpenAPI 스키마가 {output_path}에 저장되었습니다")


def create_api_documentation(app: FastAPI, output_dir: Optional[Path] = None) -> None:
    """
    API 문서를 마크다운 파일로 생성
    
    Args:
        app: FastAPI 애플리케이션 인스턴스
        output_dir: 출력 디렉토리 경로 (None인 경우 기본 경로 사용)
    """
    # 기본 출력 디렉토리 설정
    if output_dir is None:
        output_dir = settings.base_dir / "docs" / "api"
    
    # 디렉토리 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # OpenAPI 스키마 생성
    openapi_schema = custom_openapi(app)
    
    # 태그별 문서 생성
    tag_endpoints = {}
    
    # 엔드포인트 정보 수집
    for path, path_info in openapi_schema["paths"].items():
        for method, operation in path_info.items():
            if "tags" in operation and operation["tags"]:
                tag = operation["tags"][0]
                if tag not in tag_endpoints:
                    tag_endpoints[tag] = []
                
                tag_endpoints[tag].append({
                    "path": path,
                    "method": method.upper(),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "operation_id": operation.get("operationId", ""),
                    "parameters": operation.get("parameters", []),
                    "request_body": operation.get("requestBody", {}),
                    "responses": operation.get("responses", {})
                })
    
    # 태그별 문서 작성
    for tag, endpoints in tag_endpoints.items():
        # 태그 정보 찾기
        tag_info = None
        for t in openapi_schema.get("tags", []):
            if t["name"] == tag:
                tag_info = t
                break
        
        # 문서 제목 설정
        tag_title = tag.title()
        tag_description = tag_info["description"] if tag_info else f"{tag_title} API"
        
        # 문서 내용 생성
        content = [
            f"# {tag_title} API",
            "",
            f"{tag_description}",
            "",
            "## 엔드포인트",
            ""
        ]
        
        # 엔드포인트 정보 추가
        for endpoint in sorted(endpoints, key=lambda x: x["path"]):
            content.extend([
                f"### {endpoint['method']} {endpoint['path']}",
                "",
                f"**{endpoint['summary']}**",
                "",
                f"{endpoint['description']}",
                "",
                "#### 요청",
                ""
            ])
            
            # 파라미터 정보 추가
            if endpoint["parameters"]:
                content.append("**파라미터:**")
                content.append("")
                content.append("| 이름 | 위치 | 타입 | 필수 | 설명 |")
                content.append("| ---- | ---- | ---- | ---- | ---- |")
                
                for param in endpoint["parameters"]:
                    required = "✓" if param.get("required", False) else ""
                    schema = param.get("schema", {})
                    param_type = schema.get("type", "any")
                    description = param.get("description", "")
                    
                    content.append(f"| {param['name']} | {param['in']} | {param_type} | {required} | {description} |")
                
                content.append("")
            
            # 요청 본문 정보 추가
            if endpoint["request_body"]:
                content.append("**요청 본문:**")
                content.append("")
                
                request_content = endpoint["request_body"].get("content", {})
                for media_type, schema_info in request_content.items():
                    content.append(f"미디어 타입: `{media_type}`")
                    content.append("")
                    
                    # 스키마 예시 또는 참조 추가
                    schema = schema_info.get("schema", {})
                    if "$ref" in schema:
                        ref = schema["$ref"].split("/")[-1]
                        content.append(f"스키마: `{ref}`")
                    elif "example" in schema_info:
                        content.append("예시:")
                        content.append("```json")
                        content.append(json.dumps(schema_info["example"], ensure_ascii=False, indent=2))
                        content.append("```")
                    
                    content.append("")
            
            # 응답 정보 추가
            content.append("#### 응답")
            content.append("")
            
            for status_code, response in endpoint["responses"].items():
                content.append(f"**상태 코드:** {status_code}")
                content.append("")
                content.append(f"설명: {response.get('description', '')}")
                content.append("")
                
                response_content = response.get("content", {})
                for media_type, schema_info in response_content.items():
                    content.append(f"미디어 타입: `{media_type}`")
                    content.append("")
                    
                    # 응답 예시 추가
                    if "example" in schema_info:
                        content.append("예시:")
                        content.append("```json")
                        content.append(json.dumps(schema_info["example"], ensure_ascii=False, indent=2))
                        content.append("```")
                        content.append("")
            
            content.append("---")
            content.append("")
        
        # 파일로 저장
        output_file = output_dir / f"{tag}.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        
        logger.info(f"{tag} API 문서가 {output_file}에 저장되었습니다")
    
    # 색인 파일 생성
    index_content = [
        "# API 문서",
        "",
        "LLMNightRun API 문서에 오신 것을 환영합니다.",
        "",
        "## 목차",
        ""
    ]
    
    # 태그별 링크 추가
    for tag in sorted(tag_endpoints.keys()):
        tag_title = tag.title()
        index_content.append(f"- [{tag_title} API](./{tag}.md)")
    
    # 색인 파일 저장
    index_file = output_dir / "index.md"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write("\n".join(index_content))
    
    logger.info(f"API 문서 색인이 {index_file}에 저장되었습니다")
