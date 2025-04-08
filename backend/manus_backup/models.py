from pydantic import BaseModel
from typing import Dict, List, Any, Optional

# MCP 규격에 맞는 모델 정의
class MCPResource(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None

class MCPTool(BaseModel):
    name: str
    description: Optional[str] = None
    inputSchema: Dict[str, Any]

class MCPPrompt(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None

class MCPInitializeRequest(BaseModel):
    version: str
    capabilities: Dict[str, Any]

class MCPInitializeResponse(BaseModel):
    serverName: str
    serverVersion: str
    capabilities: Dict[str, Any]

class MCPResourceContent(BaseModel):
    uri: str
    text: Optional[str] = None
    blob: Optional[str] = None
    mimeType: Optional[str] = None

class MCPTextContent(BaseModel):
    type: str = "text"
    text: str

class MCPToolResult(BaseModel):
    content: List[Any]
    isError: bool = False

class MCPPromptMessage(BaseModel):
    role: str
    content: Dict[str, Any]

class MCPPromptResult(BaseModel):
    messages: List[MCPPromptMessage]
    description: Optional[str] = None
