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
const BACKUP_SERVER = process.env.NEXT_PUBLIC_BACKUP_API_URL || 'http://localhost:8001';

// 로그 파일 경로
const LOG_FILE = path.resolve(process.cwd(), 'server-status.log');

/**
 * 서버 상태 확인 함수
 */
async function checkServer(url) {
  return new Promise((resolve) => {
    const client = url.startsWith('https') ? https : http;
    const timeoutId = setTimeout(() => {
      req.abort();
      resolve({ url, status: 'timeout', statusCode: null, message: '연결 시간 초과' });
    }, 5000);

    const req = client.get(`${url}/health-check`, (res) => {
      clearTimeout(timeoutId);
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          resolve({ 
            url, 
            status: res.statusCode === 200 ? 'online' : 'error',
            statusCode: res.statusCode,
            message: response.message || response.status || '알 수 없는 응답'
          });
        } catch (e) {
          resolve({ 
            url, 
            status: 'error', 
            statusCode: res.statusCode,
            message: '잘못된 응답 형식'
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
        message: error.message
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
  const backupStatus = await checkServer(BACKUP_SERVER);
  
  const timestamp = new Date().toISOString();
  let summaryMessage = `[${timestamp}] 서버 상태 요약:\n`;
  
  // 기본 서버 상태
  summaryMessage += `  기본 서버 (${PRIMARY_SERVER}): ${primaryStatus.status.toUpperCase()}`;
  if (primaryStatus.statusCode) {
    summaryMessage += ` (${primaryStatus.statusCode})`;
  }
  summaryMessage += `\n    ${primaryStatus.message}\n`;
  
  // 백업 서버 상태
  summaryMessage += `  백업 서버 (${BACKUP_SERVER}): ${backupStatus.status.toUpperCase()}`;
  if (backupStatus.statusCode) {
    summaryMessage += ` (${backupStatus.statusCode})`;
  }
  summaryMessage += `\n    ${backupStatus.message}\n`;
  
  // 권장 서버
  if (primaryStatus.status === 'online') {
    summaryMessage += '  권장 서버: 기본 서버\n';
  } else if (backupStatus.status === 'online') {
    summaryMessage += '  권장 서버: 백업 서버\n';
  } else {
    summaryMessage += '  권장 서버: 사용 가능한 서버 없음\n';
  }
  
  // 로그에 기록
  writeLog(summaryMessage);
  
  return {
    timestamp,
    primary: primaryStatus,
    backup: backupStatus,
    recommended: primaryStatus.status === 'online' ? 'primary' : 
                 backupStatus.status === 'online' ? 'backup' : null
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
