# Model Context Protocol (MCP) 표준 구현

이 패키지는 [Model Context Protocol](https://modelcontextprotocol.io/) 명세에 따른 Python 구현을 제공합니다. MCP는 AI 모델(LLM)에 컨텍스트를 제공하는 방법을 표준화하는 개방형 프로토콜입니다.

## 주요 기능

- **MCP 서버**: 리소스, 도구, 프롬프트를 노출하는 서버 구현
- **MCP 클라이언트**: 서버와 통신하는 클라이언트 구현
- **트랜스포트 계층**: stdio 및 SSE 통신 구현
- **타입 시스템**: MCP 타입 정의 및 검증

## 구조

```
mcp_standard/
├── __init__.py       # 패키지 진입점
├── client.py         # MCP 클라이언트 구현
├── server.py         # MCP 서버 구현
├── types.py          # MCP 타입 정의
├── transports/       # 트랜스포트 구현
│   ├── __init__.py
│   ├── base.py       # 기본 트랜스포트 클래스
│   ├── stdio.py      # 표준 입출력 트랜스포트
│   ├── sse.py        # SSE 트랜스포트
│   └── client/       # 클라이언트 트랜스포트
│       ├── __init__.py
│       ├── stdio.py  # 클라이언트 stdio 트랜스포트
│       └── sse.py    # 클라이언트 SSE 트랜스포트
└── examples/         # 예제 구현
    ├── simple_server.py  # 간단한 서버 예제
    └── simple_client.py  # 간단한 클라이언트 예제
```

## 사용 방법

### 서버 구현 예제

```python
from backend.mcp_standard import MCPServer, StdioServerTransport, MCPTool

# 서버 생성
server = MCPServer("example-server", "1.0.0")

# 도구 등록
calculator_tool = MCPTool(
    name="calculator",
    description="Perform basic arithmetic operations",
    inputSchema={
        "type": "object",
        "properties": {
            "operation": { "type": "string" },
            "a": { "type": "number" },
            "b": { "type": "number" }
        },
        "required": ["operation", "a", "b"]
    }
)

async def handle_calculator(arguments):
    operation = arguments.get("operation")
    a = arguments.get("a")
    b = arguments.get("b")
    
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        result = a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")
    
    return ToolCallResult(
        content=[
            ToolContent(
                type="text",
                text=f"Result: {result}"
            )
        ]
    )

server.add_tool(calculator_tool, handle_calculator)

# 트랜스포트 생성 및 연결
transport = StdioServerTransport()
await server.connect(transport)
```

### 클라이언트 구현 예제

```python
from backend.mcp_standard import MCPClient
from backend.mcp_standard.transports.client import StdioClientTransport

# 클라이언트 생성
client = MCPClient("example-client", "1.0.0")

# 트랜스포트 생성
transport = StdioClientTransport(
    command="python",
    args=["server_script.py"]
)

# 클라이언트 연결
await client.connect(transport)

# 서버 초기화
await client.initialize()

# 도구 호출
result = await client.call_tool("calculator", {
    "operation": "add",
    "a": 10,
    "b": 20
})

print(f"Result: {result.content[0].text}")
```

## 예제 실행

### 간단한 서버 실행

```bash
python -m backend.mcp_standard.examples.simple_server [base_directory]
```

### 간단한 클라이언트 실행

```bash
python -m backend.mcp_standard.examples.simple_client [base_directory]
```

## 지원 기능

- [x] 리소스 (Resources)
  - [x] 리소스 목록 조회
  - [x] 리소스 읽기
  - [x] 리소스 구독
  - [x] 리소스 업데이트 알림

- [x] 도구 (Tools)
  - [x] 도구 목록 조회
  - [x] 도구 호출
  - [x] 도구 목록 변경 알림

- [x] 프롬프트 (Prompts)
  - [x] 프롬프트 목록 조회
  - [x] 프롬프트 가져오기
  - [x] 프롬프트 목록 변경 알림

- [x] 로깅 (Logging)
  - [x] 로깅 메시지 전송
  - [x] 로깅 레벨 설정

- [x] 트랜스포트 (Transports)
  - [x] 표준 입출력 (stdio)
  - [x] Server-Sent Events (SSE)

- [ ] 샘플링 (Sampling) *특별 구현 필요*
- [ ] 루트 관리 (Roots) *특별 구현 필요*

## 참고 자료

- [Model Context Protocol 웹사이트](https://modelcontextprotocol.io/)
- [MCP 명세](https://spec.modelcontextprotocol.io/)
- [Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
