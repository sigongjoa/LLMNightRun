# 데이터베이스 스키마 수정 안내

## 문제 상황

현재 데이터베이스 스키마와 코드 사이에 불일치가 있습니다. 코드에서는 `questions` 및 `responses` 테이블에 `project_id` 컬럼이 있다고 가정하고 있으나, 실제 데이터베이스 스키마에는 해당 컬럼이 존재하지 않습니다.

오류 메시지:
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column: questions.project_id
```

## 임시 해결책

현재 제공된 임시 솔루션은 다음과 같습니다:

1. `backend/database/operations/question_fix.py` - 질문 관련 데이터베이스 작업을 수정하여 `project_id` 컬럼에 접근하지 않도록 함
2. `backend/api/question_fix.py` - 수정된 데이터베이스 작업 모듈을 사용하는 API 라우터
3. `backend/database/operations/response_fix.py` - 응답 관련 데이터베이스 작업을 수정
4. `backend/api/response_fix.py` - 수정된 응답 API 라우터
5. `backend/main_fix.py` - 수정된 라우터를 사용하는 임시 메인 애플리케이션
6. `run_backend_fix.py` - 임시 백엔드 서버 실행 스크립트
7. `start_llmnightrun_fix.bat` - 전체 시스템 실행 스크립트 (임시 버전)

이 임시 솔루션은 데이터베이스 구조를 변경하지 않고 코드를 수정하여 오류를 해결합니다. 특정 컬럼만 명시적으로 선택하고 `project_id` 컬럼 관련 작업을 제외하는 방식입니다.

## 영구 해결책

영구적인 해결책으로 다음 두 가지 방법이 있습니다:

### 방법 1: 데이터베이스 스키마 업데이트

SQLite 데이터베이스에 `project_id` 컬럼을 추가하는 마이그레이션 스크립트를 실행합니다:

```sql
-- 질문 테이블에 project_id 추가
ALTER TABLE questions ADD COLUMN project_id INTEGER REFERENCES projects(id);

-- 응답 테이블에 project_id 추가
ALTER TABLE responses ADD COLUMN project_id INTEGER REFERENCES projects(id);
```

이 SQL 스크립트를 다음 방법으로 실행할 수 있습니다:

```python
import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('llmnightrun.db')
cursor = conn.cursor()

# project_id 컬럼 추가
cursor.execute('ALTER TABLE questions ADD COLUMN project_id INTEGER REFERENCES projects(id)')
cursor.execute('ALTER TABLE responses ADD COLUMN project_id INTEGER REFERENCES projects(id)')

# 변경사항 저장
conn.commit()
conn.close()

print("데이터베이스 스키마 업데이트 완료!")
```

### 방법 2: 모델 정의 변경

다른 방법으로는 코드의 모델 정의에서 `project_id` 관련 부분을 제거하여 데이터베이스 스키마와 일치시키는 것입니다:

1. `backend/database/models.py`에서 Question 및 Response 모델 정의에서 `project_id` 컬럼 제거
2. 관련 관계 정의 수정
3. 기타 코드에서 `project_id` 참조 제거

## 권장 사항

1. 임시 해결책으로 제공된 스크립트를 사용하여 시스템을 실행합니다.
2. 시스템의 기능을 제대로 이해한 후, 영구 해결책 중 하나를 선택하여 적용합니다.
3. 가능하면 데이터 무결성을 위해 방법 1(데이터베이스 스키마 업데이트)을 권장합니다.
4. 향후에는 ORM 모델 변경 시 마이그레이션 도구(Alembic 등)를 사용하여 체계적으로 관리하는 것이 좋습니다.

## 주의사항

- 데이터베이스 스키마를 변경하기 전에 반드시 백업을 생성하세요.
- 마이그레이션 스크립트가 기존 데이터에 영향을 주지 않는지 확인하세요.
