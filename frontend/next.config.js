/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  async rewrites() {
    return [
      {
        source: '/mcp/:path*',
        destination: 'http://localhost:8000/mcp/:path*',
      },
      {
        source: '/ws/:path*',
        destination: 'http://localhost:8000/ws/:path*',
      },
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      }
    ]
  },
}

module.exports = nextConfig