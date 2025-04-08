import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Box, Typography, Paper, Tabs, Tab, Button, 
         CircularProgress, Alert, Snackbar, Grid, Divider,
         List, ListItem, ListItemText, ListItemSecondaryAction,
         TextField, IconButton, Dialog, DialogTitle, 
         DialogContent, DialogActions, Chip } from '@mui/material';
import { Refresh as RefreshIcon, Edit as EditIcon, GitHub as GitHubIcon, 
         Visibility as VisibilityIcon, Code as CodeIcon,
         Save as SaveIcon, Close as CloseIcon } from '@mui/icons-material';
import Markdown from 'react-markdown';

import { useTheme } from '@mui/material/styles';
import { API_BASE_URL } from '../config';

// 문서 정보 타입 정의
interface DocumentInfo {
  doc_type: string;
  path: string;
  last_updated: string | null;
  exists: boolean;
}

// GitHub 설정 타입 정의
interface GitHubConfig {
  repo_url: string;
  branch: string;
  auth_token: string;
  auto_push: boolean;
  updated_at?: string;
}

// Git 상태 타입 정의
interface GitStatus {
  current_branch: string;
  staged_files: string[];
  uncommitted_changes: string[];
  has_changes: boolean;
}

const DocsManager: React.FC = () => {
  const theme = useTheme();
  
  // 상태 관리
  const [activeTab, setActiveTab] = useState(0);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentInfo | null>(null);
  const [docContent, setDocContent] = useState('');
  const [isEditMode, setIsEditMode] = useState(false);
  const [editableContent, setEditableContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingContent, setLoadingContent] = useState(false);
  const [gitHubConfig, setGitHubConfig] = useState<GitHubConfig | null>(null);
  const [gitStatus, setGitStatus] = useState<GitStatus | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [openGitHubDialog, setOpenGitHubDialog] = useState(false);
  
  // GitHub 설정 폼 상태
  const [formGitHubConfig, setFormGitHubConfig] = useState<GitHubConfig>({
    repo_url: '',
    branch: 'main',
    auth_token: '',
    auto_push: false
  });

  // 초기 데이터 로드
  useEffect(() => {
    fetchDocuments();
    fetchGitHubConfig();
    fetchGitStatus();
  }, []);

  // 문서 목록 가져오기
  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/docs-manager/list`);
      if (response.data.status === 'success') {
        setDocuments(response.data.documents);
      }
    } catch (error) {
      console.error('문서 목록을 가져오는 중 오류가 발생했습니다:', error);
      showSnackbar('문서 목록을 가져오는 중 오류가 발생했습니다.', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 문서 내용 가져오기
  const fetchDocumentContent = async (docType: string) => {
    setLoadingContent(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/docs-manager/content/${docType}`);
      if (response.data.status === 'success') {
        setDocContent(response.data.content);
        setEditableContent(response.data.content);
      } else {
        setDocContent('');
        setEditableContent('');
        showSnackbar(response.data.message, 'warning');
      }
    } catch (error) {
      console.error('문서 내용을 가져오는 중 오류가 발생했습니다:', error);
      showSnackbar('문서 내용을 가져오는 중 오류가 발생했습니다.', 'error');
      setDocContent('');
      setEditableContent('');
    } finally {
      setLoadingContent(false);
    }
  };

  // GitHub 설정 가져오기
  const fetchGitHubConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/docs-manager/github/config`);
      if (response.data.status === 'success') {
        setGitHubConfig(response.data.config);
        // 폼 상태 업데이트 (비밀번호는 제외)
        if (response.data.config) {
          setFormGitHubConfig({
            ...response.data.config,
            auth_token: '' // 보안을 위해 토큰은 비움
          });
        }
      }
    } catch (error) {
      console.error('GitHub 설정을 가져오는 중 오류가 발생했습니다:', error);
    }
  };

  // Git 상태 가져오기
  const fetchGitStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/docs-manager/github/status`);
      if (response.data.status === 'success') {
        setGitStatus(response.data.git_status);
      }
    } catch (error) {
      console.error('Git 상태를 가져오는 중 오류가 발생했습니다:', error);
    }
  };

  // 문서 선택 처리
  const handleDocumentSelect = (doc: DocumentInfo) => {
    setSelectedDoc(doc);
    setIsEditMode(false);
    if (doc.exists) {
      fetchDocumentContent(doc.doc_type);
    } else {
      setDocContent('');
      setEditableContent('');
      showSnackbar('선택한 문서가 아직 존재하지 않습니다. 생성 버튼을 눌러 문서를 만드세요.', 'info');
    }
  };

  // 문서 생성 처리
  const handleGenerateDocument = async () => {
    if (!selectedDoc) return;
    
    setIsGenerating(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/docs-manager/generate`, {
        doc_types: [selectedDoc.doc_type],
        force_update: true,
        push_to_github: gitHubConfig?.auto_push || false
      });
      
      if (response.data.status === 'success') {
        showSnackbar('문서 생성 작업이 시작되었습니다. 잠시 후 새로고침 하세요.', 'success');
        // 3초 후 자동 새로고침
        setTimeout(() => {
          fetchDocuments();
          if (selectedDoc) {
            fetchDocumentContent(selectedDoc.doc_type);
          }
          fetchGitStatus();
        }, 3000);
      }
    } catch (error) {
      console.error('문서 생성 중 오류가 발생했습니다:', error);
      showSnackbar('문서 생성 중 오류가 발생했습니다.', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  // 모든 문서 업데이트 처리
  const handleUpdateAllDocuments = async () => {
    setIsGenerating(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/docs-manager/generate`, {
        doc_types: ['ALL'],
        force_update: true,
        push_to_github: gitHubConfig?.auto_push || false
      });
      
      if (response.data.status === 'success') {
        showSnackbar('모든 문서 업데이트 작업이 시작되었습니다. 잠시 후 새로고침 하세요.', 'success');
        // 5초 후 자동 새로고침
        setTimeout(() => {
          fetchDocuments();
          fetchGitStatus();
        }, 5000);
      }
    } catch (error) {
      console.error('문서 업데이트 중 오류가 발생했습니다:', error);
      showSnackbar('문서 업데이트 중 오류가 발생했습니다.', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  // 편집 모드 전환
  const handleEditToggle = () => {
    setIsEditMode(!isEditMode);
    if (!isEditMode) {
      setEditableContent(docContent);
    }
  };

  // GitHub 설정 저장
  const handleSaveGitHubConfig = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/docs-manager/github/config`, formGitHubConfig);
      
      if (response.data.status === 'success') {
        showSnackbar('GitHub 설정이 저장되었습니다.', 'success');
        fetchGitHubConfig();
        setOpenGitHubDialog(false);
      }
    } catch (error) {
      console.error('GitHub 설정 저장 중 오류가 발생했습니다:', error);
      showSnackbar('GitHub 설정 저장 중 오류가 발생했습니다.', 'error');
    }
  };

  // 탭 변경 처리
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // 스낵바 표시
  const showSnackbar = (message: string, severity: 'success' | 'info' | 'warning' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  // 스낵바 닫기
  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ my: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          문서 자동화 관리
        </Typography>
        
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          sx={{ mb: 2 }}
        >
          <Tab label="문서 관리" />
          <Tab label="GitHub 설정" />
        </Tabs>

        {/* 문서 관리 탭 */}
        {activeTab === 0 && (
          <Paper sx={{ p: 2 }}>
            <Grid container spacing={2}>
              {/* 문서 목록 */}
              <Grid item xs={12} md={3}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">문서 목록</Typography>
                  <IconButton onClick={fetchDocuments} size="small">
                    <RefreshIcon />
                  </IconButton>
                </Box>
                
                {loading ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
                    <CircularProgress size={30} />
                  </Box>
                ) : (
                  <List sx={{ maxHeight: '500px', overflow: 'auto' }}>
                    {documents.map((doc) => (
                      <ListItem
                        key={doc.doc_type}
                        button
                        selected={selectedDoc?.doc_type === doc.doc_type}
                        onClick={() => handleDocumentSelect(doc)}
                      >
                        <ListItemText 
                          primary={doc.doc_type}
                          secondary={doc.exists ? `마지막 수정: ${doc.last_updated || '알 수 없음'}` : '아직 생성되지 않음'}
                        />
                        <ListItemSecondaryAction>
                          {doc.exists && (
                            <Chip 
                              size="small" 
                              color="success" 
                              label="생성됨" 
                              sx={{ mr: 1 }} 
                            />
                          )}
                        </ListItemSecondaryAction>
                      </ListItem>
                    ))}
                  </List>
                )}
                
                <Box sx={{ mt: 2 }}>
                  <Button 
                    variant="contained" 
                    color="primary" 
                    fullWidth
                    onClick={handleUpdateAllDocuments}
                    disabled={isGenerating}
                    startIcon={isGenerating ? <CircularProgress size={20} /> : <RefreshIcon />}
                  >
                    모든 문서 업데이트
                  </Button>
                </Box>
              </Grid>
              
              {/* 문서 내용 */}
              <Grid item xs={12} md={9}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    {selectedDoc ? `${selectedDoc.doc_type} 문서` : '문서를 선택하세요'}
                  </Typography>
                  <Box>
                    {selectedDoc && (
                      <>
                        <Button
                          variant="outlined"
                          color="primary"
                          startIcon={isEditMode ? <VisibilityIcon /> : <EditIcon />}
                          onClick={handleEditToggle}
                          sx={{ mr: 1 }}
                          disabled={!selectedDoc.exists || loadingContent}
                        >
                          {isEditMode ? '미리보기' : '편집'}
                        </Button>
                        <Button
                          variant="contained"
                          color="primary"
                          startIcon={isGenerating ? <CircularProgress size={20} /> : <CodeIcon />}
                          onClick={handleGenerateDocument}
                          disabled={isGenerating || loadingContent}
                        >
                          {selectedDoc.exists ? '업데이트' : '생성'}
                        </Button>
                      </>
                    )}
                  </Box>
                </Box>
                
                <Paper 
                  variant="outlined" 
                  sx={{ 
                    p: 2, 
                    minHeight: '500px', 
                    maxHeight: '700px', 
                    overflow: 'auto',
                    backgroundColor: isEditMode ? '#f5f5f5' : 'white'
                  }}
                >
                  {loadingContent ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                      <CircularProgress />
                    </Box>
                  ) : selectedDoc ? (
                    isEditMode ? (
                      <TextField
                        multiline
                        fullWidth
                        variant="outlined"
                        value={editableContent}
                        onChange={(e) => setEditableContent(e.target.value)}
                        sx={{ fontSize: '0.9rem', fontFamily: 'monospace' }}
                      />
                    ) : (
                      <Markdown>{docContent}</Markdown>
                    )
                  ) : (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                      <Typography color="textSecondary">왼쪽에서 문서를 선택하세요</Typography>
                    </Box>
                  )}
                </Paper>
              </Grid>
            </Grid>
          </Paper>
        )}

        {/* GitHub 설정 탭 */}
        {activeTab === 1 && (
          <Paper sx={{ p: 2 }}>
            <Grid container spacing={3}>
              {/* 현재 설정 */}
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  현재 GitHub 설정
                </Typography>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  {gitHubConfig ? (
                    <Box>
                      <Typography variant="body1">저장소 URL: {gitHubConfig.repo_url}</Typography>
                      <Typography variant="body1">브랜치: {gitHubConfig.branch}</Typography>
                      <Typography variant="body1">자동 푸시: {gitHubConfig.auto_push ? '활성화' : '비활성화'}</Typography>
                      <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                        마지막 업데이트: {gitHubConfig.updated_at || '알 수 없음'}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography color="textSecondary">
                      GitHub 설정이 없습니다. 설정 버튼을 클릭하여 연결 정보를 등록하세요.
                    </Typography>
                  )}
                </Paper>
                
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<GitHubIcon />}
                  sx={{ mt: 2 }}
                  onClick={() => setOpenGitHubDialog(true)}
                >
                  GitHub 설정 {gitHubConfig ? '수정' : '등록'}
                </Button>
              </Grid>
              
              {/* Git 상태 */}
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Git 저장소 상태
                </Typography>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  {gitStatus ? (
                    <Box>
                      <Typography variant="body1">현재 브랜치: {gitStatus.current_branch}</Typography>
                      <Typography variant="body1" sx={{ mt: 1 }}>
                        변경사항: {gitStatus.has_changes ? (
                          <Chip color="warning" size="small" label="변경사항 있음" />
                        ) : (
                          <Chip color="success" size="small" label="깨끗함" />
                        )}
                      </Typography>
                      
                      {gitStatus.staged_files.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="body2">스테이징된 파일:</Typography>
                          <List dense>
                            {gitStatus.staged_files.map((file, index) => (
                              <ListItem key={`staged-${index}`} dense>
                                <ListItemText primary={file} />
                              </ListItem>
                            ))}
                          </List>
                        </Box>
                      )}
                      
                      {gitStatus.uncommitted_changes.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Typography variant="body2">커밋되지 않은 변경사항:</Typography>
                          <List dense>
                            {gitStatus.uncommitted_changes.map((file, index) => (
                              <ListItem key={`uncommitted-${index}`} dense>
                                <ListItemText primary={file} />
                              </ListItem>
                            ))}
                          </List>
                        </Box>
                      )}
                    </Box>
                  ) : (
                    <Typography color="textSecondary">
                      Git 상태 정보를 불러오는 중입니다...
                    </Typography>
                  )}
                </Paper>
                
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<RefreshIcon />}
                  sx={{ mt: 2 }}
                  onClick={fetchGitStatus}
                >
                  상태 새로고침
                </Button>
              </Grid>
            </Grid>
          </Paper>
        )}
        
        {/* GitHub 설정 다이얼로그 */}
        <Dialog 
          open={openGitHubDialog} 
          onClose={() => setOpenGitHubDialog(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>GitHub 연동 설정</DialogTitle>
          <DialogContent>
            <TextField
              margin="dense"
              label="GitHub 저장소 URL"
              fullWidth
              variant="outlined"
              value={formGitHubConfig.repo_url}
              onChange={(e) => setFormGitHubConfig({...formGitHubConfig, repo_url: e.target.value})}
              placeholder="https://github.com/username/repo.git"
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="브랜치 이름"
              fullWidth
              variant="outlined"
              value={formGitHubConfig.branch}
              onChange={(e) => setFormGitHubConfig({...formGitHubConfig, branch: e.target.value})}
              placeholder="main"
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="인증 토큰 (Personal Access Token)"
              fullWidth
              variant="outlined"
              type="password"
              value={formGitHubConfig.auth_token}
              onChange={(e) => setFormGitHubConfig({...formGitHubConfig, auth_token: e.target.value})}
              placeholder="ghp_xxxxxxxxxxxx"
              sx={{ mb: 2 }}
              helperText="기존 토큰을 유지하려면 비워두세요"
            />
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <input
                type="checkbox"
                id="auto-push"
                checked={formGitHubConfig.auto_push}
                onChange={(e) => setFormGitHubConfig({...formGitHubConfig, auto_push: e.target.checked})}
              />
              <label htmlFor="auto-push" style={{ marginLeft: '8px' }}>
                문서 생성/업데이트 후 자동으로 GitHub에 푸시
              </label>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenGitHubDialog(false)}>취소</Button>
            <Button onClick={handleSaveGitHubConfig} color="primary">저장</Button>
          </DialogActions>
        </Dialog>
        
        {/* 스낵바 */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity as any} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </Container>
  );
};

export default DocsManager;
