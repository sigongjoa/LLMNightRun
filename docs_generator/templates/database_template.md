# 데이터베이스 설계

## 개요

이 문서는 [프로젝트명]의 데이터베이스 구조를 설명합니다.

## 데이터베이스 스키마

### 테이블 목록

| 테이블명 | 설명 |
|---------|------|
| users | 사용자 정보 |
| items | 아이템 정보 |

### 테이블 상세

#### users

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|---------|------|
| id | INTEGER | PRIMARY KEY | 사용자 ID |
| username | VARCHAR(255) | NOT NULL, UNIQUE | 사용자명 |
| email | VARCHAR(255) | NOT NULL, UNIQUE | 이메일 |
| created_at | TIMESTAMP | NOT NULL | 생성일 |

#### items

| 필드명 | 타입 | 제약조건 | 설명 |
|--------|------|---------|------|
| id | INTEGER | PRIMARY KEY | 아이템 ID |
| name | VARCHAR(255) | NOT NULL | 아이템명 |
| user_id | INTEGER | FOREIGN KEY | 소유자 ID |
| created_at | TIMESTAMP | NOT NULL | 생성일 |

## 테이블 간 관계

* **users - items**: 1:N 관계 (한 사용자는 여러 아이템 소유)

## 인덱스

| 테이블 | 인덱스명 | 필드 | 설명 |
|--------|---------|------|------|
| users | idx_users_email | email | 이메일 검색 최적화 |
| items | idx_items_user_id | user_id | 사용자별 아이템 검색 최적화 |

## 마이그레이션

마이그레이션은 [방식]으로 관리됩니다.

### 마이그레이션 실행

```
[마이그레이션 실행 명령어]
```
