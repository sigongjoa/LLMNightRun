import React, { useState, useEffect } from 'react';
import { NextPage } from 'next';
import { 
  Container, 
  Grid, 
  Box, 
  Typography, 
  Snackbar, 
  Alert,
  Tabs,
  Tab,
  Paper
} from '@mui/material';
import Head from 'next/head';
import Layout from '../components/Layout';
import PromptTemplateList from '../components/PromptTemplateList';
import PromptTemplateEditor from '../components/PromptTemplateEditor';
import { PromptTemplate } from '../types';

enum TabType {
  LIST = 'list',
  EDITOR = 'editor',
}

const PromptEngineeringPage: NextPage = () => {
  // 상태
  const [activeTab, setActiveTab] = useState<TabType>(TabType.LIST);
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplate | undefined>(undefined);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');
  
  // 새 템플릿 생성 처리
  const handleNewTemplate = () => {
    setSelectedTemplate(undefined);
    setActiveTab(TabType.EDITOR);
  };
  
  // 템플릿 편집 처리
  const handleEditTemplate = (template: PromptTemplate) => {
    setSelectedTemplate(template);
    setActiveTab(TabType.EDITOR);
  };
  
  // 템플릿 선택 처리
  const handleSelectTemplate = (template: PromptTemplate) => {
    setSelectedTemplate(template);
    setActiveTab(TabType.EDITOR);
  };
  
  // 템플릿 삭제 처리
  const handleDeleteTemplate = (id: number) => {
    showSnackbar('템플릿이 삭제되었습니다.', 'success');
    setActiveTab(TabType.LIST);
    setSelectedTemplate(undefined);
  };
  
  // 템플릿 저장 처리
  const handleSaveTemplate = (template: PromptTemplate) => {
    setSelectedTemplate(template);
    showSnackbar('템플릿이 저장되었습니다.', 'success');
    setActiveTab(TabType.LIST);
  };
  
  // 템플릿 편집 취소 처리
  const handleCancel = () => {
    setActiveTab(TabType.LIST);
  };
  
  // 스낵바 표시 유틸리티
  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };
  
  // 탭 변경 처리
  const handleTabChange = (event: React.SyntheticEvent, newValue: TabType) => {
    setActiveTab(newValue);
  };

  return (
    <>
      <Head>
        <title>프롬프트 엔지니어링 - LLMNightRun</title>
        <meta name="description" content="프롬프트 템플릿을 관리하고 LLM과 함께 활용하세요" />
      </Head>
      
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom>
            프롬프트 엔지니어링
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            프롬프트 템플릿을 관리하고 LLM과 함께 활용하세요
          </Typography>
        </Box>
        
        <Paper sx={{ mb: 2 }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab label="템플릿 목록" value={TabType.LIST} />
            <Tab label="템플릿 편집" value={TabType.EDITOR} />
          </Tabs>
        </Paper>
        
        <Box sx={{ mt: 3 }}>
          {activeTab === TabType.LIST ? (
            <PromptTemplateList 
              onNew={handleNewTemplate}
              onEdit={handleEditTemplate}
              onSelect={handleSelectTemplate}
            />
          ) : (
            <PromptTemplateEditor 
              template={selectedTemplate}
              onSave={handleSaveTemplate}
              onCancel={handleCancel}
              onDelete={handleDeleteTemplate}
            />
          )}
        </Box>
      </Container>
      
      {/* 알림 스낵바 */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={() => setSnackbarOpen(false)} 
          severity={snackbarSeverity}
          sx={{ width: '100%' }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  );
};

export default PromptEngineeringPage;