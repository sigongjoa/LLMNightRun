import React from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Chip,
  Box,
  Skeleton,
  Paper,
  Divider
} from '@mui/material';
import { Visibility as VisibilityIcon } from '@mui/icons-material';
import { Question } from '@/types';
import Link from 'next/link';

interface RecentQuestionsProps {
  questions: Question[];
  loading?: boolean;
}

const RecentQuestions: React.FC<RecentQuestionsProps> = ({ questions, loading = false }) => {
  // 날짜 포맷팅
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };
  
  // 질문 내용 요약
  const summarizeContent = (content: string, maxLength: number = 100) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };
  
  // 로딩 상태
  if (loading) {
    return (
      <List>
        {[1, 2, 3, 4, 5].map((item) => (
          <React.Fragment key={item}>
            <ListItem>
              <ListItemText
                primary={<Skeleton width="80%" height={28} />}
                secondary={<Skeleton width="40%" height={20} />}
              />
              <ListItemSecondaryAction>
                <Skeleton variant="circular" width={40} height={40} />
              </ListItemSecondaryAction>
            </ListItem>
            {item < 5 && <Divider />}
          </React.Fragment>
        ))}
      </List>
    );
  }
  
  // 데이터가 없는 경우
  if (questions.length === 0) {
    return (
      <Paper elevation={0} sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="text.secondary">
          최근 질문이 없습니다.
        </Typography>
      </Paper>
    );
  }
  
  // 질문 목록 렌더링
  return (
    <List>
      {questions.map((question, index) => (
        <React.Fragment key={question.id || index}>
          <ListItem alignItems="flex-start">
            {/* ListItemText를 사용하지 않고 직접 구성 */}
            <Box sx={{ flexGrow: 1, pr: 3 }}>
              <Typography variant="subtitle1" component="div" gutterBottom>
                {summarizeContent(question.content)}
              </Typography>
              
              <Box sx={{ mt: 0.5 }}>
                <Typography variant="body2" color="text.secondary" component="div">
                  {formatDate(question.created_at)}
                </Typography>
                
                {question.tags && question.tags.length > 0 && (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                    {question.tags.map((tag, tagIndex) => (
                      <Chip key={tagIndex} label={tag} size="small" variant="outlined" />
                    ))}
                  </Box>
                )}
              </Box>
            </Box>
            
            <ListItemSecondaryAction>
              <IconButton 
                edge="end" 
                component={Link} 
                href={`/results?questionId=${question.id}`}
                aria-label="view results"
              >
                <VisibilityIcon />
              </IconButton>
            </ListItemSecondaryAction>
          </ListItem>
          {index < questions.length - 1 && <Divider />}
        </React.Fragment>
      ))}
    </List>
  );
};

export default RecentQuestions;