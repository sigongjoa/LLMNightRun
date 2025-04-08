import React, { useEffect, useState } from 'react';
import { 
  Box, Paper, Typography, List, ListItem, ListItemText, 
  Dialog, DialogTitle, DialogContent, DialogActions, 
  Button, TextField, Grid, CircularProgress
} from '@mui/material';
import axios from 'axios';

interface PromptArgument {
  name: string;
  description?: string;
  required?: boolean;
}

interface Prompt {
  name: string;
  description?: string;
  arguments?: PromptArgument[];
}

const ManusPrompts: React.FC = () => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [promptArgs, setPromptArgs] = useState<Record<string, string>>({});
  const [promptResult, setPromptResult] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [executing, setExecuting] = useState<boolean>(false);

  useEffect(() => {
    const loadPrompts = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get('/api/manus/prompts');
        setPrompts(response.data);
      } catch (err) {
        console.error('Failed to load prompts:', err);
        setError('프롬프트 목록을 불러오는 데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    loadPrompts();
  }, []);

  const handlePromptSelect = (prompt: Prompt) => {
    setSelectedPrompt(prompt);
    // 인자 초기화
    const initialArgs: Record<string, string> = {};
    if (prompt.arguments) {
      prompt.arguments.forEach(arg => {
        initialArgs[arg.name] = '';
      });
    }
    setPromptArgs(initialArgs);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
  };

  const handleArgumentChange = (name: string, value: string) => {
    setPromptArgs(prev => ({ ...prev, [name]: value }));
  };

  const handleExecutePrompt = async () => {
    if (!selectedPrompt) return;
    
    try {
      setExecuting(true);
      setError(null);
      const response = await axios.post(`/api/manus/prompts/${selectedPrompt.name}`, promptArgs);
      
      // 결과 처리
      if (response.data.messages && response.data.messages.length > 0) {
        const messages = response.data.messages.map((m: any) => 
          `${m.role}: ${m.content.type === 'text' ? m.content.text : JSON.stringify(m.content)}`
        );
        setPromptResult(messages.join('\n\n'));
      } else {
        setPromptResult(JSON.stringify(response.data, null, 2));
      }
      
      setDialogOpen(false);
    } catch (err) {
      console.error('Failed to execute prompt:', err);
      setError(`프롬프트 실행 오류: ${err}`);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'row', gap: 2 }}>
      <Paper sx={{ width: '30%', maxHeight: '500px', overflow: 'auto', p: 2 }}>
        <Typography variant="h6">Manus Prompts</Typography>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <CircularProgress size={24} />
          </Box>
        ) : error ? (
          <Typography variant="body2" color="error">{error}</Typography>
        ) : (
          <List>
            {prompts.map((prompt) => (
              <ListItem 
                button 
                key={prompt.name}
                onClick={() => handlePromptSelect(prompt)}
              >
                <ListItemText 
                  primary={prompt.name} 
                  secondary={prompt.description} 
                />
              </ListItem>
            ))}
            {prompts.length === 0 && (
              <Typography variant="body2">사용 가능한 프롬프트가 없습니다.</Typography>
            )}
          </List>
        )}
      </Paper>
      
      <Paper sx={{ width: '70%', p: 2 }}>
        <Typography variant="h6">Prompt Result</Typography>
        {promptResult ? (
          <Box component="pre" sx={{ whiteSpace: 'pre-wrap', overflow: 'auto', maxHeight: '450px' }}>
            {promptResult}
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            프롬프트를 선택하여 실행하면 결과가 표시됩니다.
          </Typography>
        )}
      </Paper>

      {/* Prompt arguments dialog */}
      <Dialog open={dialogOpen} onClose={handleDialogClose} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedPrompt?.name}
        </DialogTitle>
        <DialogContent>
          {selectedPrompt && (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {selectedPrompt.description}
              </Typography>
              
              <Grid container spacing={2} sx={{ mt: 1 }}>
                {selectedPrompt.arguments?.map((arg) => (
                  <Grid item xs={12} key={arg.name}>
                    <TextField
                      label={`${arg.name}${arg.required ? ' *' : ''}`}
                      fullWidth
                      variant="outlined"
                      value={promptArgs[arg.name] || ''}
                      onChange={(e) => handleArgumentChange(arg.name, e.target.value)}
                      placeholder={arg.description}
                      required={arg.required}
                      multiline={arg.name.toLowerCase().includes('description') || arg.name.toLowerCase().includes('requirements')}
                      rows={arg.name.toLowerCase().includes('description') || arg.name.toLowerCase().includes('requirements') ? 4 : 1}
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
            onClick={handleExecutePrompt} 
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

export default ManusPrompts;