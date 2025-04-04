import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Tabs,
  Tab,
  Button,
  Divider,
  Card,
  CardHeader,
  CardContent,
  CardActions,
  TextField,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  CircularProgress,
  Menu,
  MenuItem,
  Tooltip,
  Alert,
  Breadcrumbs,
  Link as MuiLink,
  Snackbar
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Code as CodeIcon,
  Article as ArticleIcon,
  Search as SearchIcon,
  GitHub as GitHubIcon,
  CloudDownload as CloudDownloadIcon,
  CloudUpload as CloudUploadIcon,
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  FolderOpen as FolderOpenIcon,
  History as HistoryIcon,
  BugReport as BugReportIcon,
  Psychology as PsychologyIcon,
  BarChart as BarChartIcon,
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayArrowIcon,
  Commit as CommitIcon,
  TextSnippet as TextSnippetIcon,
  Settings as SettingsIcon,
  Comment as CommentIcon,
  Memory as MemoryIcon
} from '@mui/icons-material';
import Link from 'next/link';

// 코드베이스 인덱싱 컴포넌트 임포트
import CodebaseIndexing from '../components/CodebaseIndexing';

// 기존 TabPanel 컴포넌트
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`codebase-tab-${index}`}
      aria-labelledby={`codebase-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const CodebaseDetail = () => {
  const router = useRouter();
  const { id: codebaseId } = router.query;
  
  // 기본 상태 관리...
  const [activeTab, setActiveTab] = useState(0);
  
  // 탭 변경 핸들러
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  // 기존 코드...
  
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        {/* 상단 헤더 (기존 코드...) */}
        
        {/* 메인 컨텐츠 */}
        <Paper elevation={3} sx={{ mb: 3 }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab icon={<CodeIcon />} label="코드" />
            <Tab icon={<HistoryIcon />} label="버전 기록" />
            <Tab icon={<BugReportIcon />} label="이슈" />
            <Tab icon={<PsychologyIcon />} label="LLM 피드백" />
            {/* 인덱싱 탭 추가 */}
            <Tab icon={<MemoryIcon />} label="인덱싱" />
            <Tab icon={<BarChartIcon />} label="통계" />
          </Tabs>
          
          {/* 기존 탭 패널들 (코드, 버전 기록, 이슈, LLM 피드백, 통계) */}
          <TabPanel value={activeTab} index={0}>
            {/* 코드 탭 내용 */}
          </TabPanel>
          
          <TabPanel value={activeTab} index={1}>
            {/* 버전 기록 탭 내용 */}
          </TabPanel>
          
          <TabPanel value={activeTab} index={2}>
            {/* 이슈 탭 내용 */}
          </TabPanel>
          
          <TabPanel value={activeTab} index={3}>
            {/* LLM 피드백 탭 내용 */}
          </TabPanel>
          
          {/* 인덱싱 탭 패널 추가 */}
          <TabPanel value={activeTab} index={4}>
            <CodebaseIndexing codebaseId={codebaseId} />
          </TabPanel>
          
          <TabPanel value={activeTab} index={5}>
            {/* 통계 탭 내용 */}
          </TabPanel>
        </Paper>
      </Box>
      
      {/* 기존 다이얼로그들... */}
    </Container>
  );
};

export default CodebaseDetail;