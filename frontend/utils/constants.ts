/**
 * Global constants for the application
 */

// API base URL - Change this according to your environment
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// GitHub 저장소 API 전용 URL (CORS 문제 시 GitHub 전용 프록시 서버 사용)
export const GITHUB_API_URL = process.env.NEXT_PUBLIC_GITHUB_API_URL || 'http://localhost:8001';

// CORS 패치된 백엔드 URL (기존 백엔드와 충돌 방지를 위해 다른 포트 사용)
export const CORS_FIXED_API_URL = process.env.NEXT_PUBLIC_CORS_FIXED_API_URL || 'http://localhost:8002';

// 우선 순위를 변경 - GitHub 프록시 서버를 첫 번째로 사용
export const PREFERRED_GITHUB_API_URL = GITHUB_API_URL;

// Other constants
export const APP_NAME = 'LLMNightRun';
export const APP_VERSION = '0.1.0';

// Timeout settings
export const DEFAULT_TIMEOUT = 60000; // 60 seconds
