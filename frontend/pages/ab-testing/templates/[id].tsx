import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Button,
  CircularProgress,
  Alert,
  Snackbar,
  IconButton,
  Divider,
  TextField
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import Layout from '../../../components/Layout';
import { useRouter } from 'next/router';
import { useApi } from '../../../src/hooks/useApi';

// DO NOT CHANGE CODE: 이 코드는 AB 테스트 템플릿 상세 페이지의 기본 구조입니다.
// TEMP: 임시 구현 코드입니다. 백엔드 통합 완료 후 정식 버전으로 업데이트 예정입니다.
const TemplateDetailPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const api = useApi();
  const [isLoading, setIsLoading] = useState(true);
  const [template, setTemplate] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedTemplate, setEditedTemplate] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    if (id) {
      fetchTemplateData();
    }
  }, [id]);

  const fetchTemplateData = async () => {
    setIsLoading(true);
    try {
      const response = await api.get(`/ab-testing/templates/${id}`);
      if (response.status === 200) {
        setTemplate(response.data);
        setEditedTemplate(response.data);
      }
    } catch (error) {
      console.error('템플릿 데이터 로딩 오류:', error);
      setSnackbar({
        open: true,
        message: '템플릿 정보를 불러오는 중 오류가 발생했습니다.',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoBack = () => {
    router.push('/ab-testing');
  };

  const handleToggleEdit = () => {
    setIsEditing(!isEditing);
    if (!isEditing) {
      setEditedTemplate({...template});
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setEditedTemplate({
      ...editedTemplate,
      [name]: value,
    });
  };

  const handleSaveTemplate = async () => {
    // JSON 형식 검증
    try {
      JSON.parse(editedTemplate.defaultConfig);
    } catch (error) {
      setSnackbar({
        open: true,
        message: '기본 구성이 유효한 JSON 형식이 아닙니다.',
        severity: 'error'
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await api.put(`/ab-testing/templates/${id}`, editedTemplate);
      if (response.status === 200) {
        setTemplate(response.data);
        setIsEditing(false);
        setSnackbar({
          open: true,
          message: '템플릿이 성공적으로 업데이트되었습니다.',
          severity: 'success'
        });
      }
    } catch (error) {
      console.error('템플릿 업데이트 오류:', error);
      setSnackbar({
        open: true,
        message: '템플릿 업데이트 중 오류가 발생했습니다.',
        severity: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseTemplate = () => {
    router.push({
      pathname: '/ab-testing/create',
      query: { template_id: id }
    });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  if (isLoading) {
    return (
      <Layout>
        <Container>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
            <CircularProgress />
          </Box>
        </Container>
      </Layout>
    );
  }

  if (!template) {
    return (
      <Layout>
        <Container>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
            <IconButton onClick={handleGoBack} sx={{ mr: 2 }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h4" component="h1">
              템플릿 상세 정보
            </Typography>
          </Box>
          <Alert severity="error">
            템플릿을 찾을 수 없습니다. 이미 삭제되었거나 접근 권한이 없습니다.
          </Alert>
        </Container>
      </Layout>
    );
  }

  return (
    <Layout>
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
            <IconButton onClick={handleGoBack} sx={{ mr: 2 }}>
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h4" component="h1">
              템플릿: {template.name}
            </Typography>
            <Box sx={{ flexGrow: 1 }} />
            <Button
              variant={isEditing ? "outlined" : "contained"}
              color="primary"
              startIcon={isEditing ? <SaveIcon /> : <EditIcon />}
              onClick={isEditing ? handleSaveTemplate : handleToggleEdit}
              sx={{ ml: 2 }}
            >
              {isEditing ? '저장' : '편집'}
            </Button>
            {!isEditing && (
              <Button
                variant="contained"
                color="secondary"
                onClick={handleUseTemplate}
                sx={{ ml: 2 }}
              >
                이 템플릿으로 생성
              </Button>
            )}
          </Box>

          <Paper sx={{ p: 3 }}>
            <Grid container spacing={3}>
              {/* 기본 정보 */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  기본 정보
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {isEditing ? (
                  <>
                    <TextField
                      name="name"
                      label="템플릿 이름"
                      fullWidth
                      required
                      value={editedTemplate.name}
                      onChange={handleInputChange}
                      sx={{ mb: 2 }}
                    />
                    
                    <TextField
                      name="description"
                      label="설명"
                      fullWidth
                      multiline
                      rows={3}
                      value={editedTemplate.description}
                      onChange={handleInputChange}
                      sx={{ mb: 2 }}
                    />
                  </>
                ) : (
                  <>
                    <Typography variant="subtitle1" gutterBottom>
                      이름
                    </Typography>
                    <Typography variant="body1" paragraph>
                      {template.name}
                    </Typography>
                    
                    <Typography variant="subtitle1" gutterBottom>
                      설명
                    </Typography>
                    <Typography variant="body1" paragraph>
                      {template.description || '설명 없음'}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold', mr: 1 }}>
                        생성일:
                      </Typography>
                      <Typography variant="body2">
                        {new Date(template.created_at).toLocaleString()}
                      </Typography>
                    </Box>
                  </>
                )}
              </Grid>

              {/* 기본 구성 */}
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  기본 구성 (JSON)
                </Typography>
                <Divider sx={{ mb: 2 }} />
                
                {isEditing ? (
                  <TextField
                    name="defaultConfig"
                    label="기본 구성 JSON"
                    fullWidth
                    required
                    multiline
                    rows={10}
                    value={editedTemplate.defaultConfig}
                    onChange={handleInputChange}
                    sx={{ fontFamily: 'monospace' }}
                  />
                ) : (
                  <Box 
                    component="pre" 
                    sx={{ 
                      p: 2, 
                      bgcolor: 'background.paper', 
                      border: '1px solid', 
                      borderColor: 'divider',
                      borderRadius: 1,
                      overflow: 'auto',
                      maxHeight: '400px',
                      fontFamily: 'monospace'
                    }}
                  >
                    {JSON.stringify(JSON.parse(template.defaultConfig), null, 2)}
                  </Box>
                )}
              </Grid>
            </Grid>
          </Paper>
        </Box>

        {/* 스낵바 알림 */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
        >
          <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </Layout>
  );
};
// END-DO-NOT-CHANGE

export default TemplateDetailPage;
