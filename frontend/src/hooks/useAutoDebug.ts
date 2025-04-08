import { useMutation } from '@tanstack/react-query';
import { AutoDebugApi } from '../api';

// 자동 디버깅 관련 커스텀 훅
export const useAnalyzeChanges = () => {
  return useMutation(
    (options: {
      repository: string;
      branch: string;
      commit_sha: string;
      changed_files: Array<{ path: string; type: string }>;
    }) => AutoDebugApi.analyzeChanges(options)
  );
};

export const useDebugCode = () => {
  return useMutation(
    ({ code, language, errorMessage }: { code: string; language: string; errorMessage?: string }) => 
      AutoDebugApi.debugCode(code, language, errorMessage)
  );
};

export const useAnalyzeCode = () => {
  return useMutation(
    ({ code, language }: { code: string; language: string }) => 
      AutoDebugApi.analyzeCode(code, language)
  );
};

export const useGenerateTests = () => {
  return useMutation(
    ({ code, language, framework }: { code: string; language: string; framework?: string }) => 
      AutoDebugApi.generateTests(code, language, framework)
  );
};
