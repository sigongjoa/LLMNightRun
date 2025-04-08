import { useMutation } from '@tanstack/react-query';
import { ExportApi } from '../api';
import { ExportFormat, ExportOptions } from '../types';

// 내보내기 관련 커스텀 훅
export const useExportQuestion = () => {
  return useMutation(
    ({ questionId, format, options }: 
      { questionId: number; format: ExportFormat; options?: ExportOptions }) => 
      ExportApi.exportQuestion(questionId, format, options || {})
  );
};

export const useExportCodeSnippet = () => {
  return useMutation(
    ({ snippetId, format, options }: 
      { snippetId: number; format: ExportFormat; options?: ExportOptions }) => 
      ExportApi.exportCodeSnippet(snippetId, format, options || {})
  );
};

export const useExportAgentLogs = () => {
  return useMutation(
    ({ sessionId, format, options }: 
      { sessionId: string; format: ExportFormat; options?: ExportOptions }) => 
      ExportApi.exportAgentLogs(sessionId, format, options || {})
  );
};

export const useExportBatch = () => {
  return useMutation(
    ({ items, format, options }: { 
      items: Array<{ type: 'question' | 'code_snippet' | 'agent_logs'; id: number | string }>;
      format: ExportFormat;
      options?: ExportOptions 
    }) => ExportApi.exportBatch(items, format, options || {})
  );
};

// 내보내기 후 다운로드 헬퍼 함수
export const useDownloadExport = () => {
  return (blob: Blob, filename: string) => {
    ExportApi.downloadBlob(blob, filename);
  };
};
