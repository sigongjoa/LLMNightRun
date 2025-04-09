# Question and Response System

## Overview
The Question and Response system is a core feature of LLMNightRun that allows users to submit queries to the LLM and receive structured responses.

## Components

### Backend Components
- `backend/api/question.py`: Handles question submission and processing
- `backend/api/response.py`: Manages response generation and formatting
- `backend/models/question.py`: Data model for questions
- `backend/models/response.py`: Data model for responses

### API Endpoints

#### Submit Question
```
POST /api/question/
```
**Request Body:**
```json
{
    "text": "Your question here",
    "context": "Optional context",
    "model": "Optional model choice"
}
```
**Response:**
```json
{
    "id": "question_id",
    "text": "Original question",
    "status": "processing|completed|failed",
    "created_at": "timestamp"
}
```

#### Get Response
```
GET /api/response/{question_id}
```
**Response:**
```json
{
    "id": "response_id",
    "question_id": "related_question_id",
    "text": "Response content",
    "model_used": "Model name",
    "created_at": "timestamp"
}
```

## Usage Examples

### Basic Question Submission
```python
import requests

response = requests.post(
    "http://localhost:8000/api/question/",
    json={"text": "What is the capital of France?"}
)
question_id = response.json()["id"]

# Later, get the response
response_data = requests.get(
    f"http://localhost:8000/api/response/{question_id}"
).json()
print(response_data["text"])
```

### Frontend Integration

The question-response system is integrated into the chat interface in the frontend, which communicates with these endpoints to provide a seamless user experience.

## Configuration
The behavior of the question-response system can be configured in `backend/config.py` with settings for:
- Response time limits
- Token limits
- Default models
