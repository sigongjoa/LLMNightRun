/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // 에러 오버레이 커스텀
  onDemandEntries: {
    // 페이지 유지 시간
    maxInactiveAge: 60 * 60 * 1000, // 1시간
    // 메모리에 유지할 페이지 수
    pagesBufferLength: 5,
  },
  // 이미지 도메인 허용 목록
  images: {
    domains: ['localhost'],
  },
  // 국제화 설정
  i18n: {
    locales: ['ko', 'en'],
    defaultLocale: 'ko',
  },
};

module.exports = nextConfig;
