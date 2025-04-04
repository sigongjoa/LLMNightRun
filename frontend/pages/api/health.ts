import type { NextApiRequest, NextApiResponse } from 'next'

type HealthResponse = {
  status: string
  version: string
  timestamp: string
  environment: string
}

export default function handler(
  req: NextApiRequest,
  res: NextApiResponse<HealthResponse>
) {
  // API 상태 확인 (필요한 경우)
  // const apiStatus = await checkApiStatus()
  
  res.status(200).json({
    status: 'healthy',
    version: process.env.NEXT_PUBLIC_VERSION || '0.1.0',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development'
  })
}