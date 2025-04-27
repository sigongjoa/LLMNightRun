<think>
Okay, I'm trying to create an API documentation based on the conversation between a user and an assistant. The main goal is to generate a markdown-formatted API document using the provided template.

First, I'll start by understanding the content of the conversation. The user initially has trouble extracting text from a PDF using PyMuPDF because the Chinese characters were breaking down. The assistant suggests trying 'blocks' mode instead of 'text' and also adjusting the AA level. After that, the user faced issues with line breaks in the extracted text and asked how to make it a clean paragraph.

The assistant provided code examples for each step, including reading the PDF file, extracting blocks, sorting them by coordinates, and joining the text into a single string without line breaks. Then, the assistant offered an endpoint example using FastAPI's POST method with a file upload.

Now, I need to fill in the template based on this information. The API description should explain that it handles PDF file uploads, extracts text properly even for languages like Chinese, and returns the extracted text as JSON.

Looking at the template:
- The API description is straightforward: "PDF file upload endpoint that extracts text from a PDF document."
- The base URL is set to "/api/v1/", which seems appropriate.
- Authentication isn't mentioned here, so I'll leave it blank or indicate no authentication for now.
- The endpoint path is "/upload-pdf", and the HTTP method is POST. The description should explain what this endpoint does—reading the PDF file, extracting text without breaking lines.

For the parameters, only one parameter is needed: "file" of type UploadFile which is required.

The request example can be a simple Python snippet that uploads a sample PDF (like 'sample.pdf') and returns the extracted text as a dictionary with key "text".

In terms of response, since the endpoint returns JSON, I'll provide an example where the text is returned within a dictionary under the "text" key.

For error handling, it's important to mention returning appropriate HTTP status codes like 400 for bad request or 503 for service unavailable if any issues occur during processing.

I also need to add rate limits and version information. The user didn't specify any rate limits beyond standard FastAPI limits, so I can set a reasonable limit like 10 requests per minute. The API version is just "v1" as suggested.

Putting it all together, the markdown should follow the template's structure with each section filled appropriately.
</think>

# API 文서

## 개요
{api_description}

## Basic URL
```
{base_url}
```

## 인증
```
{authentication_description}
```

## 엔드포인트

### /upload-pdf
- **메서드**: POST
- **설명**: PDF file upload endpoint that extracts text from a PDF document.

#### 요청 파라미터
| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| file | UploadFile | yes | Upload file to be processed |

#### 요청 예시
```python
import fitz

async def upload_pdf(file: UploadFile = File(...)):
    contents = await file.read()
    with open("temp.pdf", "wb") as f:
        f.write(contents)
    doc = fitz.open("temp.pdf")
    result = []
    for page in doc:
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (b[1], b[0]))
        result.append(' '.join([b[4] for b in blocks]))
    return {"text": '\n'.join(result)}
```

#### 응답
```json
{"text": "This is the extracted text from the PDF document"}
```

#### 상태 코드
| 코드 |解说 |
|------|------|
| 200  | 成功ful file upload and text extraction|
| 400  | Bad Request (Invalid or empty file)|
| 503  | Service Unavailable|

## Error Handling
API will return appropriate error response with status code.

## Rate Limits
- 10 requests per minute

## Version Information
{version_info}

[docs]