import { NextApiRequest, NextApiResponse } from 'next';
import axios from 'axios';
import { API_BASE_URL } from '../../../utils/constants';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    // 백엔드 API 호출
    const response = await axios.get(`${API_BASE_URL}/api/mcp/functions`);
    
    // 백엔드 응답 전달
    return res.status(200).json(response.data);
  } catch (error) {
    console.error('MCP 함수 정의 가져오기 오류:', error);
    
    // 오류 응답
    return res.status(500).json({
      success: false,
      message: error.message || '알 수 없는 오류',
      functions: {}
    });
  }
}