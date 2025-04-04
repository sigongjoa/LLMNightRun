import axios from 'axios'
import { fetchQuestions, fetchQuestion, createQuestion } from '@/utils/api'
import { Question } from '@/types'

// axios 모킹
jest.mock('axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('API Utility Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  test('fetchQuestions should return questions array', async () => {
    // 목 응답 설정
    const mockQuestions = [
      {
        id: 1,
        content: '테스트 질문 1',
        tags: ['테스트'],
        created_at: '2023-04-15T10:00:00Z'
      },
      {
        id: 2,
        content: '테스트 질문 2',
        tags: ['테스트', 'API'],
        created_at: '2023-04-15T11:00:00Z'
      }
    ]
    
    mockedAxios.get.mockResolvedValueOnce({ data: mockQuestions })
    
    // 함수 호출
    const result = await fetchQuestions()
    
    // 검증
    expect(mockedAxios.get).toHaveBeenCalledWith('/questions/', { params: { skip: 0, limit: 100 } })
    expect(result).toEqual(mockQuestions)
  })
  
  test('fetchQuestion should return a single question', async () => {
    // 목 응답 설정
    const mockQuestion = {
      id: 1,
      content: '테스트 질문',
      tags: ['테스트'],
      created_at: '2023-04-15T10:00:00Z'
    }
    
    mockedAxios.get.mockResolvedValueOnce({ data: mockQuestion })
    
    // 함수 호출
    const result = await fetchQuestion(1)
    
    // 검증
    expect(mockedAxios.get).toHaveBeenCalledWith('/questions/1')
    expect(result).toEqual(mockQuestion)
  })
  
  test('createQuestion should post and return a new question', async () => {
    // 목 요청 및 응답 설정
    const newQuestion: Question = {
      content: '새 테스트 질문',
      tags: ['테스트', '새로운']
    }
    
    const mockResponse = {
      ...newQuestion,
      id: 3,
      created_at: '2023-04-15T12:00:00Z'
    }
    
    mockedAxios.post.mockResolvedValueOnce({ data: mockResponse })
    
    // 함수 호출
    const result = await createQuestion(newQuestion)
    
    // 검증
    expect(mockedAxios.post).toHaveBeenCalledWith('/questions/', newQuestion)
    expect(result).toEqual(mockResponse)
  })
  
  test('should handle API error', async () => {
    // 에러 응답 설정
    const errorMessage = '요청 처리 중 오류가 발생했습니다'
    mockedAxios.get.mockRejectedValueOnce({ detail: errorMessage })
    
    // 함수 호출과 에러 처리
    await expect(fetchQuestions()).rejects.toEqual({ detail: errorMessage })
  })
})