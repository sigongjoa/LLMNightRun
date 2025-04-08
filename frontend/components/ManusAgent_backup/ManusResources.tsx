import React, { useEffect, useState } from 'react';
import { List, ListItem, ListItemText, Typography, Box, Paper } from '@mui/material';
import axios from 'axios';

interface Resource {
  uri: string;
  name: string;
  description?: string;
  mimeType?: string;
}

const ManusResources: React.FC = () => {
  const [resources, setResources] = useState<Resource[]>([]);
  const [selectedResource, setSelectedResource] = useState<string | null>(null);
  const [resourceContent, setResourceContent] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 리소스 목록 로드
    const loadResources = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get('/api/manus/resources');
        setResources(response.data);
      } catch (err) {
        console.error('Failed to load resources:', err);
        setError('리소스를 불러오는 데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    loadResources();
  }, []);

  const handleResourceSelect = async (uri: string) => {
    try {
      setSelectedResource(uri);
      setLoading(true);
      setError(null);
      const encodedUri = encodeURIComponent(uri);
      const response = await axios.get(`/api/manus/resource/${encodedUri}`);
      if (response.data.contents && response.data.contents.length > 0) {
        setResourceContent(response.data.contents[0].text);
      } else {
        setResourceContent(null);
        setError('리소스 내용이 없습니다.');
      }
    } catch (err) {
      console.error('Failed to load resource content:', err);
      setResourceContent(null);
      setError('리소스 내용을 불러오는 데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'row', gap: 2 }}>
      <Paper sx={{ width: '30%', maxHeight: '500px', overflow: 'auto', p: 2 }}>
        <Typography variant="h6">Manus Resources</Typography>
        {loading && resources.length === 0 ? (
          <Typography variant="body2">로딩 중...</Typography>
        ) : error && resources.length === 0 ? (
          <Typography variant="body2" color="error">{error}</Typography>
        ) : (
          <List>
            {resources.map((resource) => (
              <ListItem 
                button 
                key={resource.uri}
                onClick={() => handleResourceSelect(resource.uri)}
                selected={selectedResource === resource.uri}
              >
                <ListItemText 
                  primary={resource.name} 
                  secondary={resource.description || resource.uri} 
                />
              </ListItem>
            ))}
            {resources.length === 0 && (
              <Typography variant="body2">사용 가능한 리소스가 없습니다.</Typography>
            )}
          </List>
        )}
      </Paper>
      
      <Paper sx={{ width: '70%', p: 2 }}>
        <Typography variant="h6">Resource Content</Typography>
        {loading && selectedResource ? (
          <Typography variant="body2">로딩 중...</Typography>
        ) : error && selectedResource ? (
          <Typography variant="body2" color="error">{error}</Typography>
        ) : resourceContent ? (
          <Box component="pre" sx={{ whiteSpace: 'pre-wrap', overflow: 'auto', maxHeight: '450px' }}>
            {resourceContent}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            리소스를 선택하면 내용이 표시됩니다.
          </Typography>
        )}
      </Paper>
    </Box>
  );
};

export default ManusResources;