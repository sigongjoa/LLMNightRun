"""
MCP Server Manager for LLMNightRun.
Manages Model Context Protocol servers using JSON configuration.
"""

import os
import json
import subprocess
import logging
import sys
import signal
from typing import Dict, List, Optional, Any, Tuple
import threading
import time
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPServerManager:
    """
    Manages MCP servers for LLMNightRun.
    Similar to Claude Desktop, allows configuration via JSON.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize the MCP Server Manager.
        
        Args:
            config_path: Path to the MCP configuration file
        """
        self.config_path = config_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                                      "config", "mcp_config.json")
        self.servers = {}  # server_id -> process_info
        self.server_processes = {}  # server_id -> subprocess.Popen
        self.running = False
        
        # Create config directory if it doesn't exist
        config_dir = os.path.dirname(self.config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        # Create default config if it doesn't exist
        if not os.path.exists(self.config_path):
            self._create_default_config()
            
        # Load config
        self.load_config()
        
    def _create_default_config(self):
        """Create default MCP configuration."""
        default_config = {
            "mcpServers": {
                "example": {
                    "command": "npx",
                    "args": [
                        "-y", 
                        "@modelcontextprotocol/server-memory"
                    ],
                    "env": {}
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
            
    def load_config(self) -> Dict:
        """Load the MCP configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
                
            # Ensure the config has the expected structure
            if 'mcpServers' not in self.config:
                self.config['mcpServers'] = {}
                
            return self.config
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            self.config = {"mcpServers": {}}
            return self.config
            
    def save_config(self) -> bool:
        """Save the current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving MCP config: {e}")
            return False
            
    def get_server_config(self, server_id: str) -> Optional[Dict]:
        """Get configuration for a specific server."""
        if not self.config or 'mcpServers' not in self.config:
            return None
            
        return self.config['mcpServers'].get(server_id)
        
    def update_server_config(self, server_id: str, config: Dict) -> bool:
        """Update configuration for a specific server."""
        if not self.config:
            self.config = {"mcpServers": {}}
            
        self.config['mcpServers'][server_id] = config
        return self.save_config()
        
    def remove_server_config(self, server_id: str) -> bool:
        """Remove a server from the configuration."""
        if not self.config or 'mcpServers' not in self.config:
            return False
            
        if server_id in self.config['mcpServers']:
            del self.config['mcpServers'][server_id]
            return self.save_config()
            
        return False
        
    def list_servers(self) -> List[Dict]:
        """List all configured servers with their status."""
        if not self.config or 'mcpServers' not in self.config:
            return []
            
        server_list = []
        for server_id, config in self.config['mcpServers'].items():
            is_running = server_id in self.server_processes and self.server_processes[server_id].poll() is None
            
            server_info = {
                "id": server_id,
                "command": config.get("command", ""),
                "args": config.get("args", []),
                "running": is_running
            }
            server_list.append(server_info)
            
        return server_list
        
    def start_server(self, server_id: str) -> Tuple[bool, Optional[str]]:
        """Start a specific MCP server."""
        if server_id in self.server_processes and self.server_processes[server_id].poll() is None:
            return True, "Server already running"
            
        server_config = self.get_server_config(server_id)
        if not server_config:
            return False, f"Server '{server_id}' not found in configuration"
            
        try:
            command = server_config.get("command")
            args = server_config.get("args", [])
            env_vars = server_config.get("env", {})
            
            # Validate command
            if not command:
                return False, "Invalid server configuration: command is missing"
            
            # Check if command exists
            cmd_exists = True
            try:
                # For Windows
                if sys.platform == "win32":
                    subprocess.run(["where", command], capture_output=True, check=True)
                else:
                    # For Unix-like systems
                    subprocess.run(["which", command], capture_output=True, check=True)
            except subprocess.SubprocessError:
                cmd_exists = False
                logger.warning(f"Command '{command}' not found in PATH")
            
            # Prepare environment variables
            full_env = os.environ.copy()
            full_env.update(env_vars)
            
            # Provide more useful debug info
            cmd = [command] + args
            logger.info(f"Starting MCP server '{server_id}' with command: {' '.join(cmd)}")
            
            try:
                # Start the server process with appropriate settings for Windows
                if sys.platform == "win32":
                    # On Windows, use startupinfo to hide console window
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE
                    
                    # For npx commands on Windows, shell=True works better
                    process = subprocess.Popen(
                        ' '.join(cmd),
                        env=full_env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        shell=True,
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW  # Hide console window
                    )
                else:
                    # On Unix-like systems, we can use the list form
                    process = subprocess.Popen(
                        cmd,
                        env=full_env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1
                    )
                
                self.server_processes[server_id] = process
                
                # Start threads to monitor stdout/stderr
                threading.Thread(
                    target=self._monitor_process_output,
                    args=(server_id, process.stdout, "stdout"),
                    daemon=True
                ).start()
                
                threading.Thread(
                    target=self._monitor_process_output,
                    args=(server_id, process.stderr, "stderr"),
                    daemon=True
                ).start()
                
                # Wait a bit longer to check if process starts successfully
                time.sleep(2.0)
                if process.poll() is not None:
                    stderr_output = []
                    if process.stderr:
                        stderr_output = [line.strip() for line in process.stderr.readlines()]
                    
                    error_msg = f"Server failed to start (exit code: {process.poll()})"
                    if stderr_output:
                        error_msg += f"\nError details: {' '.join(stderr_output)}"
                    
                    logger.error(error_msg)
                    return False, error_msg
                    
                logger.info(f"Started MCP server '{server_id}' (PID: {process.pid})")
                return True, f"Server started (PID: {process.pid})"
                
            except subprocess.SubprocessError as se:
                # Specific subprocess error handling
                logger.error(f"Subprocess error starting MCP server '{server_id}': {se}")
                return False, f"Error starting server: {str(se)}"
            
        except Exception as e:
            # General exception handling
            logger.error(f"Error starting MCP server '{server_id}': {e}", exc_info=True)
            return False, f"Error starting server: {str(e)}"
            
    def _monitor_process_output(self, server_id: str, stream, stream_name: str):
        """Monitor and log process output."""
        for line in iter(stream.readline, ''):
            if not line:
                break
            logger.debug(f"MCP Server '{server_id}' {stream_name}: {line.strip()}")
            
    def stop_server(self, server_id: str) -> Tuple[bool, Optional[str]]:
        """Stop a specific MCP server."""
        if server_id not in self.server_processes:
            return False, f"Server '{server_id}' not running"
            
        process = self.server_processes[server_id]
        if process.poll() is not None:
            # Process already exited
            del self.server_processes[server_id]
            return True, f"Server already stopped (exit code: {process.poll()})"
            
        try:
            # Try to terminate gracefully first
            process.terminate()
            
            # Wait for process to terminate
            for _ in range(5):  # Wait up to 5 seconds
                if process.poll() is not None:
                    break
                time.sleep(1)
                
            # If still running, kill forcefully
            if process.poll() is None:
                process.kill()
                process.wait()
                
            del self.server_processes[server_id]
            logger.info(f"Stopped MCP server '{server_id}'")
            return True, "Server stopped"
            
        except Exception as e:
            logger.error(f"Error stopping MCP server '{server_id}': {e}")
            return False, f"Error stopping server: {str(e)}"
            
    def restart_server(self, server_id: str) -> Tuple[bool, Optional[str]]:
        """Restart a specific MCP server."""
        stop_success, stop_msg = self.stop_server(server_id)
        if not stop_success:
            # If server isn't running, that's okay - we can still try to start it
            if "not running" not in stop_msg:
                return False, f"Failed to stop server: {stop_msg}"
                
        # Try to start the server
        return self.start_server(server_id)
        
    def start_all_servers(self) -> Dict[str, Tuple[bool, str]]:
        """Start all configured MCP servers."""
        self.running = True
        results = {}
        
        if not self.config or 'mcpServers' not in self.config:
            return results
            
        for server_id in self.config['mcpServers']:
            success, msg = self.start_server(server_id)
            results[server_id] = (success, msg)
            
        return results
        
    def stop_all_servers(self) -> Dict[str, Tuple[bool, str]]:
        """Stop all running MCP servers."""
        self.running = False
        results = {}
        
        for server_id in list(self.server_processes.keys()):
            success, msg = self.stop_server(server_id)
            results[server_id] = (success, msg)
            
        return results
        
    def get_server_status(self, server_id: str) -> Dict:
        """Get detailed status of a specific server."""
        server_config = self.get_server_config(server_id)
        if not server_config:
            return {"id": server_id, "exists": False, "running": False}
            
        is_running = server_id in self.server_processes and self.server_processes[server_id].poll() is None
        
        # Get process info if running
        pid = None
        uptime = None
        if is_running:
            process = self.server_processes[server_id]
            pid = process.pid
            # Additional process info could be added here
            
        return {
            "id": server_id,
            "exists": True,
            "running": is_running,
            "config": server_config,
            "pid": pid,
            "uptime": uptime
        }
        
    def cleanup(self):
        """Clean up all resources and stop all servers."""
        self.stop_all_servers()
        
    def __del__(self):
        """Destructor to ensure all servers are stopped."""
        try:
            self.cleanup()
        except:
            pass

# Singleton instance
_manager_instance = None

def get_mcp_manager(config_path: str = None) -> MCPServerManager:
    """Get the singleton instance of the MCP Server Manager."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MCPServerManager(config_path)
    return _manager_instance
