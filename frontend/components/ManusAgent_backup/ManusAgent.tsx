import React, { useState } from 'react';
import { 
  Box, Paper, Tabs, Tab, Typography, Container
} from '@mui/material';
import ManusResources from './ManusResources';
import ManusTools from './ManusTools';
import ManusPrompts from './ManusPrompts';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`manus-tabpanel-${index}`}
      aria-labelledby={`manus-tab-${index}`}
      {...other}
      style={{ padding: '16px 0' }}
    >
      {value === index && (
        <>{children}</>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `manus-tab-${index}`,
    'aria-controls': `manus-tabpanel-${index}`,
  };
}

const ManusAgent: React.FC = () => {
  const [value, setValue] = useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ width: '100%', mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Manus Agent
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          MCP 인터페이스를 통한 Manus 에이전트 관리
        </Typography>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={value} 
            onChange={handleChange} 
            aria-label="manus agent tabs"
          >
            <Tab label="Resources" {...a11yProps(0)} />
            <Tab label="Tools" {...a11yProps(1)} />
            <Tab label="Prompts" {...a11yProps(2)} />
          </Tabs>
        </Box>
        
        <Box sx={{ p: 3 }}>
          <TabPanel value={value} index={0}>
            <ManusResources />
          </TabPanel>
          
          <TabPanel value={value} index={1}>
            <ManusTools />
          </TabPanel>
          
          <TabPanel value={value} index={2}>
            <ManusPrompts />
          </TabPanel>
        </Box>
      </Paper>
    </Container>
  );
};

export default ManusAgent;