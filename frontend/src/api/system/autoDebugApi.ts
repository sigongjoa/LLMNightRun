import axiosInstance from '../axiosInstance';

/**
 * 자동 디버깅 관련 API 함수
 */
export const AutoDebugApi = {
  /**
   * 코드 변경 분석
   */
  analyzeChanges: async (options: {
    repository: string;
    branch: string;
    commit_sha: string;
    changed_files: Array<{ path: string; type: string }>;
  }): Promise<{
    analysis: {
      summary: string;
      complexity_change: string;
      test_coverage_impact: string;
      suggestions: string[];
    };
    file_analyses: Array<{
      path: string;
      change_type: string;
      analysis: string;
      suggestions: string[];
    }>;
  }> => {
    const response = await axiosInstance.post<{
      analysis: {
        summary: string;
        complexity_change: string;
        test_coverage_impact: string;
        suggestions: string[];
      };
      file_analyses: Array<{
        path: string;
        change_type: string;
        analysis: string;
        suggestions: string[];
      }>;
    }>('/ci/analyze-changes', options);
    return response.data;
  },

  /**
   * 코드 자동 디버깅
   */
  debugCode: async (
    code: string,
    language: string,
    errorMessage?: string
  ): Promise<{
    fixed_code: string;
    explanation: string;
    errors_found: string[];
    success: boolean;
  }> => {
    const response = await axiosInstance.post<{
      fixed_code: string;
      explanation: string;
      errors_found: string[];
      success: boolean;
    }>('/auto-debug/fix', {
      code,
      language,
      error_message: errorMessage
    });
    return response.data;
  },

  /**
   * 코드 분석
   */
  analyzeCode: async (
    code: string,
    language: string
  ): Promise<{
    analysis: string;
    suggestions: string[];
    complexity: string;
    maintainability: string;
    code_quality_score: number;
  }> => {
    const response = await axiosInstance.post<{
      analysis: string;
      suggestions: string[];
      complexity: string;
      maintainability: string;
      code_quality_score: number;
    }>('/auto-debug/analyze', {
      code,
      language
    });
    return response.data;
  },

  /**
   * 유닛 테스트 생성
   */
  generateTests: async (
    code: string,
    language: string,
    framework?: string
  ): Promise<{
    test_code: string;
    explanation: string;
    test_cases: number;
    coverage_estimate: number;
  }> => {
    const response = await axiosInstance.post<{
      test_code: string;
      explanation: string;
      test_cases: number;
      coverage_estimate: number;
    }>('/auto-debug/generate-tests', {
      code,
      language,
      framework
    });
    return response.data;
  }
};

export default AutoDebugApi;
