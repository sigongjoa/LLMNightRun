from fastapi import HTTPException
from typing import Dict, List, Any, Optional
import json
import os
import base64
from pathlib import Path

from .models import (
    MCPResource, MCPTool, MCPPrompt, MCPInitializeRequest, 
    MCPInitializeResponse, MCPResourceContent, MCPTextContent
)

# Manus MCP 서버 클래스
class ManusMCPServer:
    def __init__(self):
        self.resources = []
        self.tools = []
        self.prompts = []
        self.version = "1.0.0"
        self.server_name = "manus-agent"
        
        # 기본 도구 및 리소스 등록
        self._register_default_resources()
        self._register_default_tools()
        self._register_default_prompts()
    
    def _register_default_resources(self):
        # 기본 리소스 등록
        self.resources.append(MCPResource(
            uri="manus://workspace/current",
            name="Current Workspace",
            description="현재 작업 중인 워크스페이스 정보",
            mimeType="application/json"
        ))
        
        self.resources.append(MCPResource(
            uri="manus://history/recent",
            name="Recent Interactions",
            description="최근 상호작용 기록",
            mimeType="application/json"
        ))
        
        # 파일 시스템 리소스 - 워크스페이스 루트 디렉토리
        self.resources.append(MCPResource(
            uri="file://workspace",
            name="Workspace Files",
            description="작업 공간 내 파일들",
            mimeType="directory"
        ))
        
        # 파일 시스템 리소스 - 프로젝트 루트 디렉토리
        self.resources.append(MCPResource(
            uri="file://project",
            name="Project Files",
            description="프로젝트 파일들",
            mimeType="directory"
        ))
    
    def _register_default_tools(self):
        # 코드 생성 도구
        self.tools.append(MCPTool(
            name="generate_code",
            description="주어진 설명에 따라 코드를 생성합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "language": {"type": "string"},
                    "framework": {"type": "string"}
                },
                "required": ["description", "language"]
            }
        ))
        
        # 코드 분석 도구
        self.tools.append(MCPTool(
            name="analyze_code",
            description="코드를 분석하고 개선점을 제안합니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "language": {"type": "string"}
                },
                "required": ["code"]
            }
        ))
        
        # 파일 시스템 도구들
        # 파일 읽기 도구
        self.tools.append(MCPTool(
            name="read_file",
            description="파일의 내용을 읽어옵니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        ))
        
        # 파일 쓰기 도구
        self.tools.append(MCPTool(
            name="write_file",
            description="파일에 내용을 씁니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        ))
        
        # 디렉토리 목록 도구
        self.tools.append(MCPTool(
            name="list_directory",
            description="디렉토리의 파일 및 폴더 목록을 가져옵니다",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        ))
    
    def _register_default_prompts(self):
        # 기능 구현 프롬프트
        self.prompts.append(MCPPrompt(
            name="implement-feature",
            description="새로운 기능을 구현하기 위한 가이드",
            arguments=[
                {
                    "name": "feature_name",
                    "description": "구현할 기능 이름",
                    "required": True
                },
                {
                    "name": "requirements",
                    "description": "기능 요구사항",
                    "required": True
                }
            ]
        ))
        
        # 버그 수정 프롬프트
        self.prompts.append(MCPPrompt(
            name="fix-bug",
            description="버그를 수정하기 위한 가이드",
            arguments=[
                {
                    "name": "bug_description",
                    "description": "버그 설명",
                    "required": True
                },
                {
                    "name": "error_message",
                    "description": "오류 메시지",
                    "required": False
                }
            ]
        ))
    
    # MCP 인터페이스 메서드들
    def initialize(self, request: MCPInitializeRequest) -> MCPInitializeResponse:
        return MCPInitializeResponse(
            serverName=self.server_name,
            serverVersion=self.version,
            capabilities={
                "resources": {},
                "tools": {},
                "prompts": {}
            }
        )
    
    def list_resources(self) -> Dict[str, List[MCPResource]]:
        return {"resources": self.resources}
    
    def read_resource(self, uri: str) -> Dict[str, List[MCPResourceContent]]:
        # 리소스 uri에 따라 적절한 데이터 반환
        for resource in self.resources:
            if resource.uri == uri:
                if uri == "manus://workspace/current":
                    return {"contents": [MCPResourceContent(
                        uri=uri, 
                        text=json.dumps({"workspace": "current", "files": 5, "status": "active"}), 
                        mimeType="application/json"
                    )]}
                elif uri == "manus://history/recent":
                    return {"contents": [MCPResourceContent(
                        uri=uri, 
                        text=json.dumps({"interactions": ["code generation", "bug fix", "refactoring"]}), 
                        mimeType="application/json"
                    )]}
                elif uri == "file://workspace":
                    # 워크스페이스 디렉토리 정보 반환
                    workspace_dir = os.path.join(os.getcwd(), "workspace")
                    if os.path.exists(workspace_dir) and os.path.isdir(workspace_dir):
                        files = os.listdir(workspace_dir)
                        return {"contents": [MCPResourceContent(
                            uri=uri,
                            text=json.dumps({"path": workspace_dir, "files": files}),
                            mimeType="application/json"
                        )]}
                    else:
                        return {"contents": [MCPResourceContent(
                            uri=uri,
                            text=json.dumps({"error": "Workspace directory not found"}),
                            mimeType="application/json"
                        )]}
                elif uri == "file://project":
                    # 프로젝트 디렉토리 정보 반환
                    project_dir = os.getcwd()
                    files = [f for f in os.listdir(project_dir) if os.path.isfile(os.path.join(project_dir, f))]
                    dirs = [d for d in os.listdir(project_dir) if os.path.isdir(os.path.join(project_dir, d))]
                    return {"contents": [MCPResourceContent(
                        uri=uri,
                        text=json.dumps({
                            "path": project_dir,
                            "files": files,
                            "directories": dirs
                        }),
                        mimeType="application/json"
                    )]}
                    
                # 파일 경로인 경우
                elif uri.startswith("file://"):
                    try:
                        file_path = uri[7:]  # 'file://' 제거
                        if os.path.exists(file_path) and os.path.isfile(file_path):
                            # 텍스트 파일인지 확인
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                return {"contents": [MCPResourceContent(
                                    uri=uri,
                                    text=content,
                                    mimeType="text/plain"
                                )]}
                            except UnicodeDecodeError:
                                # 바이너리 파일인 경우
                                with open(file_path, 'rb') as f:
                                    binary_content = f.read()
                                    base64_content = base64.b64encode(binary_content).decode('ascii')
                                return {"contents": [MCPResourceContent(
                                    uri=uri,
                                    blob=base64_content,
                                    mimeType="application/octet-stream"
                                )]}
                        elif os.path.isdir(file_path):
                            # 디렉토리인 경우 목록 반환
                            files = os.listdir(file_path)
                            return {"contents": [MCPResourceContent(
                                uri=uri,
                                text=json.dumps({
                                    "path": file_path,
                                    "contents": files
                                }),
                                mimeType="application/json"
                            )]}
                    except Exception as e:
                        # 에러 발생 시 에러 메시지 반환
                        return {"contents": [MCPResourceContent(
                            uri=uri,
                            text=json.dumps({"error": str(e)}),
                            mimeType="application/json"
                        )]}
        
        raise HTTPException(status_code=404, detail=f"Resource not found: {uri}")
    
    def list_tools(self) -> Dict[str, List[MCPTool]]:
        return {"tools": self.tools}
    
    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # 도구 이름에 따라 적절한 처리
        if name == "generate_code":
            language = arguments.get('language', 'python')
            description = arguments.get('description', '')
            
            # 여기서는 예시로 간단한 응답만 반환
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"# {language} 코드 생성\n\n```{language}\n# {description}\ndef hello_world():\n    print('Hello, world!')\n\nhello_world()\n```"
                    }
                ]
            }
        elif name == "analyze_code":
            code = arguments.get('code', '')
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"## 코드 분석 결과\n\n- 코드 품질: 양호\n- 개선 제안: 주석 추가 필요\n- 성능: 최적화 가능\n\n```\n{code}\n```"
                    }
                ]
            }
        
        # 파일 시스템 도구 처리
        elif name == "read_file":
            try:
                path = arguments.get('path', '')
                if not path:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "오류: 파일 경로를 지정해주세요."
                            }
                        ],
                        "isError": True
                    }
                
                # 경로 정규화 및 안전성 검증
                if path.startswith("file://"):
                    path = path[7:]
                
                # 실제 파일 읽기
                if os.path.exists(path) and os.path.isfile(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": content
                            }
                        ]
                    }
                else:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"오류: 파일을 찾을 수 없습니다: {path}"
                            }
                        ],
                        "isError": True
                    }
            except Exception as e:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"파일 읽기 오류: {str(e)}"
                        }
                    ],
                    "isError": True
                }
                
        elif name == "write_file":
            try:
                path = arguments.get('path', '')
                content = arguments.get('content', '')
                
                if not path:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "오류: 파일 경로를 지정해주세요."
                            }
                        ],
                        "isError": True
                    }
                
                # 경로 정규화 및 안전성 검증
                if path.startswith("file://"):
                    path = path[7:]
                
                # 디렉토리 생성 (필요시)
                directory = os.path.dirname(path)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)
                
                # 파일 쓰기
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"파일이 성공적으로 저장되었습니다: {path}"
                        }
                    ]
                }
            except Exception as e:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"파일 쓰기 오류: {str(e)}"
                        }
                    ],
                    "isError": True
                }
                
        elif name == "list_directory":
            try:
                path = arguments.get('path', '')
                
                if not path:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": "오류: 디렉토리 경로를 지정해주세요."
                            }
                        ],
                        "isError": True
                    }
                
                # 경로 정규화 및 안전성 검증
                if path.startswith("file://"):
                    path = path[7:]
                
                if os.path.exists(path) and os.path.isdir(path):
                    # 파일 및 디렉토리 목록 가져오기
                    items = os.listdir(path)
                    files = []
                    directories = []
                    
                    for item in items:
                        item_path = os.path.join(path, item)
                        if os.path.isfile(item_path):
                            files.append({"name": item, "type": "file"})
                        elif os.path.isdir(item_path):
                            directories.append({"name": item, "type": "directory"})
                    
                    result = {
                        "path": path,
                        "directories": directories,
                        "files": files
                    }
                    
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                else:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"오류: 디렉토리를 찾을 수 없습니다: {path}"
                            }
                        ],
                        "isError": True
                    }
            except Exception as e:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"디렉토리 목록 오류: {str(e)}"
                        }
                    ],
                    "isError": True
                }
        
        raise HTTPException(status_code=404, detail=f"Tool not found: {name}")
    
    def list_prompts(self) -> Dict[str, List[MCPPrompt]]:
        return {"prompts": self.prompts}
    
    def get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "implement-feature":
            feature_name = arguments.get("feature_name", "")
            requirements = arguments.get("requirements", "")
            
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": f"다음 기능을 구현해주세요:\n\n기능명: {feature_name}\n\n요구사항:\n{requirements}"
                        }
                    }
                ]
            }
        elif name == "fix-bug":
            bug_description = arguments.get("bug_description", "")
            error_message = arguments.get("error_message", "")
            
            prompt_text = f"다음 버그를 수정해주세요:\n\n{bug_description}"
            if error_message:
                prompt_text += f"\n\n오류 메시지:\n{error_message}"
            
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }
        
        raise HTTPException(status_code=404, detail=f"Prompt not found: {name}")
