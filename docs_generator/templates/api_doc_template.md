# API 문서

## 개요

이 문서는 [프로젝트명]의 API를 설명합니다.

## 엔드포인트 목록

| 경로 | 메서드 | 설명 |
|------|--------|------|
| /api/example | GET | 예시 데이터 조회 |

## 엔드포인트 상세

### GET /api/example

예시 데이터를 조회합니다.

#### 요청

```
GET /api/example
```

#### 응답

```json
{
  "status": "success",
  "data": {
    "example": "value"
  }
}
```

## 오류 코드

| 코드 | 설명 |
|------|------|
| 400 | 잘못된 요청 |
| 401 | 인증 필요 |
| 404 | 리소스 없음 |
| 500 | 서버 오류 |

## 인증

API 인증은 Bearer 토큰 방식을 사용합니다.

```
Authorization: Bearer <token>
```
