# LLMNightRun 문제 해결 가이드

## 백엔드 연결 문제

### 증상: "ERR_CONNECTION_REFUSED" 오류
브라우저 콘솔에서 다음과 같은 오류가 나타납니다:
```
GET http://localhost:8000/questions/?skip=0&limit=100 net::ERR_CONNECTION_REFUSED
```

### 해결 방법:

1. **백엔드 서버 실행 확인**
   ```bash
   # Windows
   cd D:\LLMNightRun\backend
   start-server.bat
   
   # Linux/Mac
   cd /path/to/LLMNightRun/backend
   chmod +x start-server.sh
   ./start-server.sh
   ```

2. **포트 충돌 확인**
   다른 프로세스가 8000번과 8001번 포트를 사용하고 있는지 확인합니다:
   ```bash
   # Windows (관리자 권한 명령 프롬프트)
   netstat -ano | findstr :8000
   netstat -ano | findstr :8001
   
   # Linux/Mac
   lsof -i :8000
   lsof -i :8001
   ```
   
   충돌이 있다면 해당 프로세스를 종료하거나, 백엔드 서버 포트를 변경하세요.

3. **방화벽 확인**
   로컬 방화벽에서 8000번과 8001번 포트에 대한 액세스를 허용했는지 확인하세요.

4. **백업 서버 URL 확인**
   `.env.local` 파일에서 백업 서버 URL이 올바르게 설정되어 있는지 확인합니다:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_BACKUP_API_URL=http://localhost:8001
   ```

## Pydantic 검증 오류

### 증상: 저장소 생성 시 오류
```
저장소 생성 중 오류가 발생했습니다: 1 validation error for GitHubRepositoryResponse
owner
Input should be a valid string [type=string_type, input_value=<backend.database.models....t at 0x000002AED65667D0>, input_type=User]
```

### 해결 방법:

1. **백엔드 스키마 수정 확인**
   `schemas.py` 파일에서 GitHubRepositoryResponse 모델이 올바르게 수정되었는지 확인하세요:
   ```python
   class GitHubRepositoryResponse(GitHubRepositoryBase):
       id: int
       owner_id: int  # User.id
       owner_name: str  # User.username
       
       class Config:
           orm_mode = True
   ```

2. **API 엔드포인트 응답 형식 확인**
   `main.py` 파일에서 저장소 API 응답이 스키마에 맞게 구성되는지 확인하세요.

## 서버 자동 전환이 작동하지 않는 경우

### 증상: 기본 서버가 다운되어도 백업 서버로 전환되지 않음

### 해결 방법:

1. **브라우저 콘솔 확인**
   개발자 도구의 콘솔에서 서버 전환 관련 로그를 확인하세요.

2. **서버 상태 확인 수동 실행**
   ```bash
   # 프론트엔드 디렉토리에서
   cd D:\LLMNightRun\frontend
   npm run check-server
   ```

3. **API 수동 테스트**
   ```bash
   # 기본 서버 테스트
   curl http://localhost:8000/health-check
   
   # 백업 서버 테스트
   curl http://localhost:8001/health-check
   ```

4. **타임아웃 설정 확인**
   `useApi.ts` 파일의 타임아웃 설정값이 너무 길지 않은지 확인하세요.

## 프론트엔드 빌드 오류

### 증상: "Module not found" 오류
```
Uncaught Error: Module not found: Can't resolve '../src/hooks/useApi'
```

### 해결 방법:

1. **파일 경로 확인**
   import 문에서 경로가 올바른지 확인하세요. Next.js 프로젝트에서는 일반적으로:
   ```typescript
   // 잘못된 경로
   import { useApi } from '../src/hooks/useApi';
   
   // 올바른 경로 (루트 기준)
   import { useApi } from '@/hooks/useApi';
   // 또는
   import { useApi } from '../hooks/useApi';
   ```

2. **종속성 설치 확인**
   ```bash
   cd D:\LLMNightRun\frontend
   npm install
   ```

3. **캐시 정리 및 재빌드**
   ```bash
   npm run dev -- --clear
   # 또는
   rm -rf .next && npm run dev
   ```

## 기타 문제 해결

### 서버 상태 로그 확인
```bash
cat D:\LLMNightRun\frontend\server-status.log
```

### 프론트엔드 로그 확인
개발자 도구의 콘솔 탭에서 로그를 확인하세요.

### 백엔드 로그 확인
백엔드 서버 실행 터미널의 로그를 확인하세요.

### 전체 재설치
문제가 지속되면 다음 단계로 전체 재설치를 시도하세요:

1. 백엔드:
   ```bash
   cd D:\LLMNightRun\backend
   pip install -r requirements.txt
   ```

2. 프론트엔드:
   ```bash
   cd D:\LLMNightRun\frontend
   rm -rf node_modules package-lock.json
   npm install
   ```
