const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Next.js 앱 경로 지정
  dir: './',
})

// Jest 커스텀 설정
const customJestConfig = {
  // 테스트 환경 추가
  testEnvironment: 'jest-environment-jsdom',
  // 테스트 파일 패턴 설정
  testMatch: ['**/*.test.js', '**/*.test.jsx', '**/*.test.ts', '**/*.test.tsx'],
  // 캐시 설정
  cache: true,
  // 코드 커버리지 설정
  collectCoverage: true,
  collectCoverageFrom: [
    'components/**/*.{js,jsx,ts,tsx}',
    'pages/**/*.{js,jsx,ts,tsx}',
    'utils/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  // 테스트 설정 파일
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  // 모듈 별칭 설정
  moduleNameMapper: {
    '^@/components/(.*)$': '<rootDir>/components/$1',
    '^@/pages/(.*)$': '<rootDir>/pages/$1',
    '^@/utils/(.*)$': '<rootDir>/utils/$1',
    '^@/types/(.*)$': '<rootDir>/types/$1',
    '^@/styles/(.*)$': '<rootDir>/styles/$1',
  },
}

// createJestConfig는 Next.js에 대한 설정을 jest 구성으로 변환합니다
module.exports = createJestConfig(customJestConfig)