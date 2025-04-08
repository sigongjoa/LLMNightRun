import { useMutation, useQuery } from '@tanstack/react-query';
import { GitHubApi } from '../api';

// GitHub 관련 커스텀 훅
export const useUploadToGitHub = () => {
  return useMutation(
    ({ questionId, folderPath }: { questionId: number; folderPath?: string }) => 
      GitHubApi.uploadToGitHub(questionId, folderPath)
  );
};

export const useGenerateCommitMessage = (questionId: number) => {
  return useQuery(
    ['commitMessage', questionId],
    () => GitHubApi.generateCommitMessage(questionId),
    {
      enabled: !!questionId, // questionId가 유효할 때만 쿼리 실행
    }
  );
};

export const useGenerateReadme = (questionId: number) => {
  return useQuery(
    ['readme', questionId],
    () => GitHubApi.generateReadme(questionId),
    {
      enabled: !!questionId, // questionId가 유효할 때만 쿼리 실행
    }
  );
};

export const useRepositoryContents = (path: string = '', branch: string = 'main') => {
  return useQuery(
    ['githubContents', path, branch],
    () => GitHubApi.getRepositoryContents(path, branch)
  );
};

export const useFileContent = (filepath: string, branch: string = 'main') => {
  return useQuery(
    ['githubFile', filepath, branch],
    () => GitHubApi.getFileContent(filepath, branch),
    {
      enabled: !!filepath, // filepath가 유효할 때만 쿼리 실행
    }
  );
};

export const useCreateBranch = () => {
  return useMutation(
    ({ branch, sourceBranch }: { branch: string; sourceBranch?: string }) => 
      GitHubApi.createBranch(branch, sourceBranch)
  );
};

export const useCreatePullRequest = () => {
  return useMutation(
    ({ title, body, headBranch, baseBranch }: 
      { title: string; body: string; headBranch: string; baseBranch?: string }) => 
      GitHubApi.createPullRequest(title, body, headBranch, baseBranch)
  );
};
