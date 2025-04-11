/**
 * 서버 상태 확인 스크립트
 * 
 * 이 스크립트는 백엔드 서버의 상태를 확인하고 상태 보고서를 생성합니다.
 * Next.js 애플리케이션 시작 시 자동으로 실행됩니다.
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const dotenv = require('dotenv');

// 환경 변수 로드
const envPath = path.resolve(process.cwd(), '.env.local');
if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
}

// 서버 URL 설정
const PRIMARY_SERVER = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
// 백업 서버는 이제 사용하지 않음
// const BACKUP_SERVER = process.env.NEXT_PUBLIC_BACKUP_API_URL || 'http://localhost:8001';
const BACKUP_SERVER = null;

// 로그 파일 경로
const LOG_FILE = path.resolve(process.cwd(), 'server-status.log');

/**
 * 서버 상태 확인 함수
 */
async function checkServer(url) {
  return new Promise((resolve) => {
    if (!url) {
      resolve({ url, status: 'disabled', statusCode: null, message: '서버 URL이 설정되지 않음' });
      return;
    }
    
    // 루트 경로만 확인 (다른 엔드포인트는 사용하지 않음)
    const client = url.startsWith('https') ? https : http;
    let req;
    const timeoutId = setTimeout(() => {
      if (req && typeof req.abort === 'function') {
        req.abort();
      } else if (req && typeof req.destroy === 'function') {
        req.destroy();
      }
      resolve({ url, status: 'timeout', statusCode: null, message: '연결 시간 초과' });
    }, 5000);

    // 루트 경로 시도
    req = client.get(`${url}/`, (res) => {
      clearTimeout(timeoutId);
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          // 200 응답이면 서버가 동작 중인 것으로 간주
          if (res.statusCode === 200) {
            try {
              const response = JSON.parse(data);
              resolve({ 
                url, 
                status: 'online',
                statusCode: res.statusCode,
                message: response.message || response.status || '서버 온라인'
              });
            } catch (e) {
              resolve({ 
                url, 
                status: 'online', 
                statusCode: res.statusCode,
                message: '서버 온라인 (루트 경로)'
              });
            }
          } else {
            // 다른 상태 코드는 오류로 간주하지만 서버는 작동 중
            resolve({
              url,
              status: 'error',
              statusCode: res.statusCode,
              message: `서버 응답 오류: ${res.statusCode}`
            });
          }
        } catch (e) {
          // 파싱 실패해도 서버가 응답했으므로 온라인으로 간주
          resolve({ 
            url, 
            status: 'online', 
            statusCode: res.statusCode,
            message: '서버 응답 확인됨'
          });
        }
      });
    });
    
    req.on('error', (error) => {
      clearTimeout(timeoutId);
      resolve({ 
        url, 
        status: 'offline', 
        statusCode: null,
        message: error.message || '서버 연결 실패'
      });
    });
  });
}

/**
 * 로그 작성 함수
 */
function writeLog(message) {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}\n`;
  
  fs.appendFileSync(LOG_FILE, logMessage);
  console.log(message);
}

/**
 * 메인 함수
 */
async function main() {
  console.log('백엔드 서버 상태 확인 중...');
  
  const primaryStatus = await checkServer(PRIMARY_SERVER);
  let backupStatus = { status: 'disabled', message: '백업 서버 비활성화됨' };
  
  // 백업 서버가 설정된 경우에만 확인
  if (BACKUP_SERVER) {
    backupStatus = await checkServer(BACKUP_SERVER);
  }
  
  const timestamp = new Date().toISOString();
  let summaryMessage = `[${timestamp}] 서버 상태 요약:\n`;
  
  // 기본 서버 상태
  summaryMessage += `  기본 서버 (${PRIMARY_SERVER}): ${primaryStatus.status.toUpperCase()}`;
  if (primaryStatus.statusCode) {
    summaryMessage += ` (${primaryStatus.statusCode})`;
  }
  summaryMessage += `\n    ${primaryStatus.message}\n`;
  
  // 백업 서버 상태 (활성화된 경우에만)
  if (BACKUP_SERVER) {
    summaryMessage += `  백업 서버 (${BACKUP_SERVER}): ${backupStatus.status.toUpperCase()}`;
    if (backupStatus.statusCode) {
      summaryMessage += ` (${backupStatus.statusCode})`;
    }
    summaryMessage += `\n    ${backupStatus.message}\n`;
  } else {
    summaryMessage += `  백업 서버: 비활성화됨\n`;
  }
  
  // 권장 서버
  if (primaryStatus.status === 'online') {
    summaryMessage += '  권장 서버: 기본 서버\n';
  } else if (BACKUP_SERVER && backupStatus.status === 'online') {
    summaryMessage += '  권장 서버: 백업 서버\n';
  } else {
    summaryMessage += '  권장 서버: 사용 가능한 서버 없음\n';
  }
  
  // 로그에 기록
  writeLog(summaryMessage);
  
  return {
    timestamp,
    primary: primaryStatus,
    backup: BACKUP_SERVER ? backupStatus : null,
    recommended: primaryStatus.status === 'online' ? 'primary' : 
                 (BACKUP_SERVER && backupStatus.status === 'online') ? 'backup' : null
  };
}

// 스크립트가 직접 실행된 경우 메인 함수 호출
if (require.main === module) {
  main().then(result => {
    console.log('서버 상태 확인 완료');
    console.log(JSON.stringify(result, null, 2));
  });
}

module.exports = { checkServer, writeLog, main };