import type { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';

// API 기본 URL 설정
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Console 로그 조회 API
 * /api/mcp/logs?session_id={세션ID}
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // GET 요청만 허용
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  const { session_id } = req.query;

  if (!session_id) {
    return res.status(400).json({ message: 'Session ID is required' });
  }

  try {
    // 백엔드 API 호출
    const response = await axios.get(`${API_BASE_URL}/mcp/console/logs`, {
      params: { session_id },
      timeout: 5000, // 5초 타임아웃
    });

    // 성공 응답
    return res.status(200).json(response.data);
  } catch (error: any) {
    console.error('로그 조회 실패:', error);

    // 에러 응답
    const statusCode = error.response?.status || 500;
    const errorMessage = error.response?.data?.message || error.message || 'Server error';
    
    return res.status(statusCode).json({
      message: '로그 조회 실패',
      error: errorMessage
    });
  }
}
