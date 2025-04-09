# Agent System

## Overview
The Agent System enables autonomous, goal-oriented behaviors in LLMNightRun. Agents can perform complex sequences of actions to accomplish specific tasks, leveraging LLMs for reasoning and decision-making.

## Components

### Backend Components
- `backend/api/agent.py`: API endpoints for agent management and interaction
- `backend/agent/`: Directory containing agent implementations
  - `backend/agent/base_agent.py`: Abstract base class for all agents
  - `backend/agent/task_agent.py`: General-purpose task execution agent
  - `backend/agent/code_agent.py`: Specialized agent for code-related tasks
- `backend/models/agent.py`: Data models for agent state and configuration
- `backend/services/agent_service.py`: Business logic for agent operations

### API Endpoints

#### Create Agent
```
POST /api/agent/create
```
**Request Body:**
```json
{
    "name": "Agent name",
    "type": "task|code|custom",
    "description": "Agent purpose",
    "config