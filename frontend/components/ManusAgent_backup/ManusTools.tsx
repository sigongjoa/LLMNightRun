import React, { useEffect, useState } from 'react';
import { 
  Box, Paper, Typography, List, ListItem, ListItemText, 
  Dialog, DialogTitle, DialogContent, DialogActions, 
  Button, TextField, Grid, CircularProgress
} from '@mui/material';
import axios from 'axios';

interface Tool {
  name: string;
  description?: string;
  inputSchema: {
    type: string;
    properties: Record<string, any>;
    required?: string[];
  };
}

interface ToolParameter {
  name: string;
  type: string;
  description?: string;
  required: boolean;
}

const ManusTools: React.FC = () => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [parameters, setParameters] = useState<Record<string, string>>({});
  const [toolResult, setToolResult] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState<boolean>(false);

  useEffect(() => {
    const loadTools = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get('/api/manus/tools');
        setTools(response.data);
      } catch (err) {
        console.error('Failed to load tools:', err);
        setError('도구 목록을 불러오는 데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    loadTools();
  }, []);

  const handleToolSelect = (tool: Tool) => {
    setSelectedTool(tool);
    // 파라미터 초기화
    const initialParams: Record<string, string> = {};
    if (tool.inputSchema && tool.inputSchema.properties) {
      Object.keys(tool.inputSchema.properties).forEach(key => {
        initialParams[key] = '';
      });
    }
    setParameters(initialParams);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
  };

  const handleParameterChange = (name: string, value: string) => {
    setParameters(prev => ({ ...prev, [name]: value }));
  };

  const handleToolCall = async () => {
    if (!selectedTool) return;
    
    try {
      setExecuting(true);
      setError(null);
      const response = await axios.post(`/api/manus/tools/${selectedTool.name}`, parameters);
      
      // 결과 처리
      if (response.data.content && response.data.content.length > 0) {
        setToolResult(response.data.content.map((c: any) => c.text).join('\n'));
      } else {
        setToolResult(JSON.stringify(response.data, null, 2));
      }
      
      setDialogOpen(false);
    } catch (err) {
      console.error('Failed to call tool:', err);
      setError(`도구 실행 오류: ${err}`);
    } finally {
      setExecuting(false);
    }
  };

  // 도구의 입력 파라미터 추출
  const getToolParameters = (tool: Tool): ToolParameter[] => {
    if (!tool.inputSchema || !tool.inputSchema.properties) {
      return [];
    }

    const required = tool.inputSchema.required || [];
    
    return Object.entries(tool.inputSchema.properties).map(([name, schema]) => ({
      name,
      type: (schema as any).type || 'string',
      description: (schema as any).description,
      required: required.includes(name)
    }));
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'row', gap: 2 }}>
      <Paper sx={{ width: '30%', maxHeight: '500px', overflow: 'auto', p: 2 }}>
        <Typography variant="h6">Manus Tools</Typography>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <CircularProgress size={24} />
          </Box>
        ) : error ? (
          <Typography variant="body2" color="error">{error}</Typography>
        ) : (
          <List>
            {tools.map((tool) => (
              <ListItem 
                button 
                key={tool.name}
                onClick={() => handleToolSelect(tool)}
              >
                <ListItemText 
                  primary={tool.name} 
                  secondary={tool.description} 
                />
              </ListItem>
            ))}
            {tools.length === 0 && (
              <Typography variant="body2">사용 가능한 도구가 없습니다.</Typography>
            )}
          </List>
        )}
      </Paper>
      
      <Paper sx={{ width: '70%', p: 2 }}>
        <Typography variant="h6">Tool Result</Typography>
        {toolResult ? (
          <Box component="pre" sx={{ whiteSpace: 'pre-wrap', overflow: 'auto', maxHeight: '450px' }}>
            {toolResult}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            도구를 선택하여 실행하면 결과가 표시됩니다.
          </Typography>
        )}
      </Paper>

      {/* Tool parameters dialog */}
      <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedTool?.name}
        </DialogTitle>
        <DialogContent>
          {selectedTool && (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {selectedTool.description}
              </Typography>
              
              <Grid container spacing={2} sx={{ mt: 1 }}>
                {getToolParameters(selectedTool).map((param) => (
                  <Grid item xs={12} key={param.name}>
                    <TextField
                      label={`${param.name}${param.required ? ' *' : ''}`}
                      fullWidth
                      variant="outlined"
                      value={parameters[param.name] || ''}
                      onChange={(e) => handleParameterChange(param.name, e.target.value)}
                      placeholder={param.description}
                      required={param.required}
                      multiline={param.type === 'string' && param.name.toLowerCase().includes('code')}
                      rows={param.type === 'string' && param.name.toLowerCase().includes('code') ? 5 : 1}
                    />
                  </Grid>
                ))}
              </Grid>
              
              {error && (
                <Typography variant="body2" color="error" sx={{ mt: 2 }}>
                  {error}
                </Typography>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDialogClose}>취소</Button>
          <Button 
            onClick={handleToolCall} 
            variant="contained" 
            color="primary"
            disabled={executing}
          >
            {executing ? <CircularProgress size={24} /> : '실행'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ManusTools;