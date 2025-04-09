# Code Generation System

## Overview
The Code Generation system allows LLMNightRun to generate, manage, and execute code from user prompts. It provides structured interfaces for converting natural language requests into functional code.

## Components

### Backend Components
- `backend/api/code.py`: Handles code generation requests and responses
- `backend/models/code.py`: Data model for storing generated code
- `backend/services/code_service.py`: Business logic for code generation
- `backend/tool/code_executor.py`: Utility for safe code execution

### API Endpoints

#### Generate Code
```
POST /api/code/generate
```
**Request Body:**
```json
{
    "prompt": "Description of code to generate",
    "language": "python",  // Optional, defaults based on detection
    "context": "Additional context"  // Optional
}
```
**Response:**
```json
{
    "id": "code_id",
    "code": "Generated code",
    "language": "Language detected/used",
    "created_at": "timestamp"
}
```

#### Execute Code
```
POST /api/code/execute
```
**Request Body:**
```json
{
    "code_id": "ID of previously generated code",
    "parameters": {}  // Optional parameters to pass to the code
}
```
**Response:**
```json
{
    "output": "Execution output",
    "status": "success|error",
    "execution_time": 1.23  // Seconds
}
```

#### Get Code History
```
GET /api/code/history
```
**Response:**
```json
{
    "codes": [
        {
            "id": "code_id",
            "prompt": "Original prompt",
            "language": "Language",
            "created_at": "timestamp",
            "execution_count": 2
        },
        // More code items...
    ]
}
```

## Features
- **Multi-language support**: Generates code in Python, JavaScript, and other supported languages
- **Code execution**: Safely executes generated code in isolated environments
- **Context awareness**: Can generate code that builds on previous code or integrates with existing codebase
- **Version tracking**: Maintains history of generated code with metadata

## Usage Examples

### Generate and Execute Code
```python
import requests

# Generate code
code_response = requests.post(
    "http://localhost:8000/api/code/generate",
    json={"prompt": "Create a function to calculate Fibonacci numbers"}
)
code_id = code_response.json()["id"]

# Execute the generated code
execution = requests.post(
    "http://localhost:8000/api/code/execute",
    json={"code_id": code_id}
)
print(execution.json()["output"])
```

### Frontend Integration
The code generation system integrates with the UI through dedicated code blocks with syntax highlighting, execution buttons, and result displays.

## Security Considerations
- Code execution occurs in sandboxed environments to prevent system damage
- Resource limits are enforced to prevent infinite loops or excessive resource consumption
- Input validation is performed on all code before execution
