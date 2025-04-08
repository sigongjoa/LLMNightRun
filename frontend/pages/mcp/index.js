import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Card, 
  CardContent, 
  Grid, 
  Button, 
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import Head from 'next/head';
import Layout from '../../components/Layout';
import { useSnackbar } from 'notistack';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import DeleteIcon from '@mui/icons-material/Delete';
import SettingsIcon from '@mui/icons-material/Settings';
import axios from 'axios';

const MCPServersPage = () => {
  const [mcpServers, setMcpServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [newServer, setNewServer] = useState({
    name: '',
    command: '',
    args: '',
    description: ''
  });
  const { enqueueSnackbar } = useSnackbar();

  const fetchMCPServers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/mcp/servers');
      setMcpServers(response.data);
    } catch (error) {
      console.error('Error fetching MCP servers:', error);
      enqueueSnackbar('Failed to load MCP servers', { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMCPServers();
  }, []);

  const handleAddServer = async () => {
    try {
      await axios.post('/api/mcp/servers', {
        ...newServer,
        args: newServer.args.split(',').map(arg => arg.trim())
      });
      setOpenDialog(false);
      setNewServer({ name: '', command: '', args: '', description: '' });
      fetchMCPServers();
      enqueueSnackbar('MCP server added successfully', { variant: 'success' });
    } catch (error) {
      console.error('Error adding MCP server:', error);
      enqueueSnackbar('Failed to add MCP server', { variant: 'error' });
    }
  };

  const handleDeleteServer = async (serverId) => {
    try {
      await axios.delete(`/api/mcp/servers/${serverId}`);
      fetchMCPServers();
      enqueueSnackbar('MCP server deleted successfully', { variant: 'success' });
    } catch (error) {
      console.error('Error deleting MCP server:', error);
      enqueueSnackbar('Failed to delete MCP server', { variant: 'error' });
    }
  };

  const handleServerAction = async (serverId, action) => {
    try {
      await axios.post(`/api/mcp/servers/${serverId}/${action}`);
      fetchMCPServers();
      enqueueSnackbar(`Server ${action} successful`, { variant: 'success' });
    } catch (error) {
      console.error(`Error ${action} server:`, error);
      enqueueSnackbar(`Failed to ${action} server`, { variant: 'error' });
    }
  };

  return (
    <Layout>
      <Head>
        <title>MCP Servers - LLMNightRun</title>
      </Head>
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h4" component="h1" gutterBottom>
              MCP Servers
            </Typography>
            <Box>
              <Button 
                variant="contained" 
                startIcon={<RefreshIcon />} 
                onClick={fetchMCPServers}
                sx={{ mr: 1 }}
              >
                Refresh
              </Button>
              <Button 
                variant="contained" 
                color="primary" 
                startIcon={<AddIcon />}
                onClick={() => setOpenDialog(true)}
              >
                Add Server
              </Button>
            </Box>
          </Box>

          {loading ? (
            <Typography>Loading MCP servers...</Typography>
          ) : (
            <Grid container spacing={3}>
              {mcpServers.length === 0 ? (
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="body1" align="center">
                        No MCP servers configured. Add your first server to get started.
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ) : (
                mcpServers.map((server) => (
                  <Grid item xs={12} md={6} key={server.id}>
                    <Card>
                      <CardContent>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                          <Typography variant="h6" component="h2">
                            {server.name}
                          </Typography>
                          <Chip 
                            label={server.status} 
                            color={server.status === 'running' ? 'success' : 'error'} 
                            size="small" 
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          {server.description || 'No description provided'}
                        