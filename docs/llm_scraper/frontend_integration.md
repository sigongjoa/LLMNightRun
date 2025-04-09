# LLM Scraper 프론트엔드 통합 가이드

LLM Scraper를 LLMNightRun 프론트엔드와 통합하기 위한 가이드입니다. 현재 LLM Scraper는 독립적인 Python 모듈로 구현되어 있으며, 프론트엔드 통합을 위해서는 추가 개발이 필요합니다.

## 1. 통합 아키텍처 개요

LLM Scraper를 기존 LLMNightRun 시스템에 통합하기 위한 전체 아키텍처는 다음과 같습니다:

```
                  +------------------+
                  |  Next.js 프론트엔드  |
                  +------------------+
                          |
                          | HTTP/WebSocket
                          |
                  +------------------+
                  |   FastAPI 백엔드   |
                  +------------------+
                          |
              +-----------------------+
              |                       |
    +-----------------+    +-------------------+
    | 기존 LLMNightRun  |    |   LLM Scraper    |
    |      로직        |    |      모듈         |
    +-----------------+    +-------------------+
```

## 2. 백엔드 통합 방법

### 2.1 API 엔드포인트 생성

FastAPI에 LLM Scraper용 새로운 API 엔드포인트를 추가합니다.

**위치**: `D:\LLMNightRun\backend\api\llm_scraper.py`

```python
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
import json
from datetime import datetime

# LLM Scraper 모듈 import
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
from llm_scraper.models.chatgpt.scraper import ChatGPTScraper
from llm_scraper.models.claude.scraper import ClaudeScraper
from llm_scraper.models.gemini.scraper import GeminiScraper
from llm_scraper.utils.data_processor import DataProcessor
from llm_scraper.config.settings import load_config

# 라우터 설정
router = APIRouter(
    prefix="/api/llm-scraper",
    tags=["llm-scraper"],
    responses={404: {"description": "Not found"}},
)

# 요청 모델
class ScraperRequest(BaseModel):
    model: str  # 'chatgpt', 'claude', 'gemini', 'all'
    prompt: str
    headless: bool = True
    timeout: int = 60
    compare: bool = False

# 응답 모델
class ScraperResponse(BaseModel):
    success: bool
    data: Dict[str, Any] = None
    error: str = None
    
# 백그라운드 작업 ID 저장소
background_tasks_status = {}

# 설정 로드
config = load_config()

# 보안을 위한 자격 증명 관리는 환경 변수 사용 (프론트엔드에서 관리하지 않음)

@router.post("/run", response_model=ScraperResponse)
async def run_scraper(request: ScraperRequest, background_tasks: BackgroundTasks):
    """
    LLM Scraper를 실행하여 지정된 모델에서 프롬프트 응답을 가져옵니다.
    """
    try:
        # 작업 ID 생성
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 상태 초기화
        background_tasks_status[task_id] = {
            "status": "pending",
            "progress": 0,
            "result": None,
            "error": None
        }
        
        # 백그라운드 작업으로 스크레이퍼 실행
        background_tasks.add_task(
            run_scraper_task,
            task_id,
            request.model,
            request.prompt,
            request.headless,
            request.timeout,
            request.compare
        )
        
        return ScraperResponse(
            success=True,
            data={"task_id": task_id, "message": "Scraper task started"}
        )
    
    except Exception as e:
        return ScraperResponse(
            success=False,
            error=f"Failed to start scraper task: {str(e)}"
        )

@router.get("/status/{task_id}", response_model=ScraperResponse)
async def get_task_status(task_id: str):
    """
    LLM Scraper 작업의 현재 상태를 가져옵니다.
    """
    if task_id not in background_tasks_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_status = background_tasks_status[task_id]
    
    return ScraperResponse(
        success=True,
        data={
            "task_id": task_id,
            "status": task_status["status"],
            "progress": task_status["progress"],
            "result": task_status["result"],
            "error": task_status["error"]
        }
    )

@router.get("/models", response_model=List[str])
async def get_available_models():
    """
    사용 가능한 모델 목록을 반환합니다.
    """
    return ["chatgpt", "claude", "gemini", "all"]

# 스크레이퍼 클래스 가져오기
def get_scraper_class(model_name):
    if model_name == "chatgpt":
        return ChatGPTScraper
    elif model_name == "claude":
        return ClaudeScraper
    elif model_name == "gemini":
        return GeminiScraper
    return None

# 백그라운드 작업 실행 함수
async def run_scraper_task(task_id, model, prompt, headless, timeout, compare):
    """
    백그라운드에서 스크레이퍼 작업을 실행합니다.
    """
    try:
        background_tasks_status[task_id]["status"] = "running"
        
        # 데이터 프로세서 초기화
        processor = DataProcessor()
        
        # 자격 증명 가져오기 (환경 변수에서)
        credentials = {}
        
        # 환경 변수에서 자격 증명 로드
        env_prefix = config.get("credentials", {}).get("env_prefix", "LLM_SCRAPER_")
        for m in ["chatgpt", "claude", "gemini"]:
            username_var = f"{env_prefix}{m.upper()}_USERNAME"
            password_var = f"{env_prefix}{m.upper()}_PASSWORD"
            
            if username_var in os.environ and password_var in os.environ:
                credentials[m] = {
                    "username": os.environ[username_var],
                    "password": os.environ[password_var]
                }
        
        results = {}
        
        if model == "all":
            # 모든 모델 실행
            all_results = []
            models_to_run = ["chatgpt", "claude", "gemini"]
            
            for i, m in enumerate(models_to_run):
                # 진행 상황 업데이트
                background_tasks_status[task_id]["progress"] = int((i / len(models_to_run)) * 100)
                
                if m in credentials:
                    # 스크레이퍼 인스턴스 생성
                    scraper_class = get_scraper_class(m)
                    if scraper_class:
                        with scraper_class(headless=headless, timeout=timeout, config=config) as scraper:
                            # 로그인
                            if scraper.login(credentials[m]):
                                # 새 대화 시작
                                scraper.start_new_conversation()
                                
                                # 프롬프트 제출
                                if scraper.submit_prompt(prompt):
                                    # 응답 추출
                                    response = scraper.extract_response()
                                    
                                    if response:
                                        # 메타데이터 포함하여 결과 저장
                                        result_data = scraper.save_response(prompt, response)
                                        all_results.append(result_data)
                                        results[m] = result_data
            
            # 비교 옵션이 활성화된 경우
            if compare and len(all_results) > 1:
                comparison = processor.compare_responses(all_results)
                results["comparison"] = comparison
        
        else:
            # 단일 모델 실행
            if model in credentials:
                # 스크레이퍼 인스턴스 생성
                scraper_class = get_scraper_class(model)
                if scraper_class:
                    with scraper_class(headless=headless, timeout=timeout, config=config) as scraper:
                        # 로그인
                        if scraper.login(credentials[model]):
                            # 새 대화 시작
                            scraper.start_new_conversation()
                            
                            # 프롬프트 제출
                            if scraper.submit_prompt(prompt):
                                # 응답 추출
                                response = scraper.extract_response()
                                
                                if response:
                                    # 메타데이터 포함하여 결과 저장
                                    result_data = scraper.save_response(prompt, response)
                                    results[model] = result_data
        
        # 작업 완료 및 결과 저장
        background_tasks_status[task_id]["status"] = "completed"
        background_tasks_status[task_id]["progress"] = 100
        background_tasks_status[task_id]["result"] = results
    
    except Exception as e:
        # 오류 발생 시 상태 업데이트
        background_tasks_status[task_id]["status"] = "failed"
        background_tasks_status[task_id]["error"] = str(e)
```

### 2.2 백엔드 메인 애플리케이션에 라우터 통합

**위치**: `D:\LLMNightRun\backend\main.py`

기존 FastAPI 앱에 새로운 라우터를 추가합니다:

```python
# llm_scraper 라우터 추가
from api import llm_scraper
app.include_router(llm_scraper.router)
```

## 3. 프론트엔드 통합

### 3.1 새로운 컴포넌트 생성

LLM 스크레이퍼 UI 컴포넌트를 생성합니다.

**위치**: `D:\LLMNightRun\frontend\components\LLMScraper\index.tsx`

```tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Divider,
  FormControl,
  FormControlLabel,
  Grid,
  MenuItem,
  Paper,
  Select,
  TextField,
  Typography,
  useTheme,
} from '@mui/material';
import axios from 'axios';

// LLM Scraper 컴포넌트
const LLMScraper: React.FC = () => {
  const theme = useTheme();
  
  // 상태 관리
  const [model, setModel] = useState<string>('chatgpt');
  const [prompt, setPrompt] = useState<string>('');
  const [headless, setHeadless] = useState<boolean>(true);
  const [timeout, setTimeout] = useState<number>(60);
  const [compare, setCompare] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  
  // 사용 가능한 모델 목록
  const [availableModels, setAvailableModels] = useState<string[]>([
    'chatgpt', 'claude', 'gemini', 'all'
  ]);
  
  // 모델 목록 가져오기
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await axios.get('/api/llm-scraper/models');
        if (response.data) {
          setAvailableModels(response.data);
        }
      } catch (err) {
        console.error('Failed to fetch models:', err);
      }
    };
    
    fetchModels();
  }, []);
  
  // 작업 상태 정기적으로 확인
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (taskId && loading) {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`/api/llm-scraper/status/${taskId}`);
          const data = response.data.data;
          
          setTaskStatus(data);
          
          // 작업 완료되면 로딩 종료
          if (data.status === 'completed' || data.status === 'failed') {
            setLoading(false);
            clearInterval(interval);
            
            if (data.status === 'failed') {
              setError(data.error || 'Task failed');
            }
          }
        } catch (err) {
          console.error('Failed to fetch task status:', err);
          setLoading(false);
          clearInterval(interval);
        }
      }, 2000); // 2초마다 상태 확인
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [taskId, loading]);
  
  // 스크레이퍼 실행
  const runScraper = async () => {
    if (!prompt) {
      setError('Please enter a prompt');
      return;
    }
    
    setLoading(true);
    setError(null);
    setTaskStatus(null);
    
    try {
      const response = await axios.post('/api/llm-scraper/run', {
        model,
        prompt,
        headless,
        timeout,
        compare: model === 'all' ? compare : false,
      });
      
      if (response.data.success) {
        setTaskId(response.data.data.task_id);
      } else {
        setError(response.data.error || 'Failed to start task');
        setLoading(false);
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred');
      setLoading(false);
    }
  };
  
  // 결과 렌더링
  const renderResults = () => {
    if (!taskStatus || !taskStatus.result) return null;
    
    const results = taskStatus.result;
    
    return (
      <Box mt={4}>
        <Typography variant="h6">Results</Typography>
        <Divider sx={{ my: 2 }} />
        
        {Object.keys(results).map((key) => (
          <Paper key={key} sx={{ p: 2, mb: 2, bgcolor: theme.palette.background.paper }}>
            <Typography variant="subtitle1" fontWeight="bold" color="primary">
              {key === 'comparison' ? 'Comparison' : key.toUpperCase()}
            </Typography>
            
            {key === 'comparison' ? (
              <Box>
                <Typography variant="body2" component="div">
                  <Box sx={{ mt: 1 }}>
                    <strong>Average word count:</strong> {results[key].metrics.avg_word_count.toFixed(2)}
                  </Box>
                  <Box sx={{ mt: 1 }}>
                    <strong>Min words:</strong> {results[key].metrics.min_words.model} ({results[key].metrics.min_words.word_count} words)
                  </Box>
                  <Box sx={{ mt: 1 }}>
                    <strong>Max words:</strong> {results[key].metrics.max_words.model} ({results[key].metrics.max_words.word_count} words)
                  </Box>
                </Typography>
              </Box>
            ) : (
              <Box>
                <Typography variant="body2" component="div">
                  <Box sx={{ mt: 1, mb: 2 }}>
                    <strong>Model:</strong> {results[key].metadata.model}
                  </Box>
                  <Box sx={{ mt: 1, p: 2, bgcolor: theme.palette.grey[100], borderRadius: 1 }}>
                    <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                      {results[key].response}
                    </pre>
                  </Box>
                </Typography>
              </Box>
            )}
          </Paper>
        ))}
      </Box>
    );
  };
  
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        LLM Scraper
      </Typography>
      <Typography variant="body1" color="textSecondary" paragraph>
        Submit prompts to web-based LLMs and compare their responses.
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <Typography variant="subtitle2" gutterBottom>
                Select Model
              </Typography>
              <Select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                disabled={loading}
              >
                {availableModels.map((m) => (
                  <MenuItem key={m} value={m}>
                    {m === 'all' ? 'All Models' : m.charAt(0).toUpperCase() + m.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <Typography variant="subtitle2" gutterBottom>
                Timeout (seconds)
              </Typography>
              <TextField
                type="number"
                value={timeout}
                onChange={(e) => setTimeout(parseInt(e.target.value) || 60)}
                disabled={loading}
                inputProps={{ min: 30, max: 300 }}
              />
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <FormControl fullWidth>
              <Typography variant="subtitle2" gutterBottom>
                Prompt
              </Typography>
              <TextField
                multiline
                rows={4}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={loading}
                placeholder="Enter your prompt here..."
              />
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={headless}
                  onChange={(e) => setHeadless(e.target.checked)}
                  disabled={loading}
                />
              }
              label="Run in headless mode"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={compare}
                  onChange={(e) => setCompare(e.target.checked)}
                  disabled={loading || model !== 'all'}
                />
              }
              label="Compare responses (when using All Models)"
            />
          </Grid>
          
          <Grid item xs={12}>
            <Button
              variant="contained"
              color="primary"
              onClick={runScraper}
              disabled={loading || !prompt}
              fullWidth
            >
              {loading ? (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CircularProgress size={24} color="inherit" sx={{ mr: 1 }} />
                  Running...
                </Box>
              ) : (
                'Run'
              )}
            </Button>
          </Grid>
        </Grid>
        
        {loading && taskStatus && (
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <CircularProgress
              variant="determinate"
              value={taskStatus.progress || 0}
              size={60}
            />
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              {taskStatus.status === 'running' ? `Progress: ${taskStatus.progress}%` : taskStatus.status}
            </Typography>
          </Box>
        )}
        
        {error && (
          <Box sx={{ mt: 2, p: 2, bgcolor: '#FFF4F4', color: 'error.main', borderRadius: 1 }}>
            <Typography variant="body2">{error}</Typography>
          </Box>
        )}
      </Paper>
      
      {renderResults()}
    </Box>
  );
};

export default LLMScraper;
```

### 3.2 페이지 생성

**위치**: `D:\LLMNightRun\frontend\pages\llm-scraper\index.tsx`

```tsx
import React from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import Layout from '../../components/Layout';
import LLMScraper from '../../components/LLMScraper';

const LLMScraperPage: NextPage = () => {
  return (
    <Layout>
      <Head>
        <title>LLM Scraper | LLMNightRun</title>
      </Head>
      <LLMScraper />
    </Layout>
  );
};

export default LLMScraperPage;
```

### 3.3 내비게이션에 링크 추가

**위치**: `D:\LLMNightRun\frontend\components\Sidebar\index.tsx` (또는 내비게이션 컴포넌트)

다음 항목을 사이드바 메뉴에 추가합니다:

```tsx
// LLM Scraper 링크 추가
{
  title: 'LLM Scraper',
  path: '/llm-scraper',
  icon: <CompareIcon />, // 적절한 아이콘 선택
}
```

## 4. 배포 및 테스트

### 4.1 필요한 패키지 설치

백엔드에 필요한 패키지를 설치합니다:

```bash
pip install -r llm_scraper/requirements.txt
```

### 4.2 환경 변수 설정

서버에 필요한 환경 변수를 설정합니다:

```bash
# Windows
set LLM_SCRAPER_CHATGPT_USERNAME=your_openai_email
set LLM_SCRAPER_CHATGPT_PASSWORD=your_openai_password
set LLM_SCRAPER_CLAUDE_USERNAME=your_anthropic_email
set LLM_SCRAPER_CLAUDE_PASSWORD=your_anthropic_password
set LLM_SCRAPER_GEMINI_USERNAME=your_google_email
set LLM_SCRAPER_GEMINI_PASSWORD=your_google_password

# Linux/Mac
export LLM_SCRAPER_CHATGPT_USERNAME=your_openai_email
export LLM_SCRAPER_CHATGPT_PASSWORD=your_openai_password
# 기타 변수도 동일하게 설정
```

### 4.3 서버 실행

개발 모드에서 서버를 실행합니다:

```bash
# 백엔드 실행
cd D:\LLMNightRun
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 프론트엔드 실행
cd D:\LLMNightRun
npm run dev
```

### 4.4 테스트

1. 브라우저에서 `http://localhost:3000/llm-scraper`로 이동
2. 프롬프트를 입력하고 모델을 선택
3. "Run" 버튼을 클릭하여 스크레이퍼 실행
4. 결과 확인

## 5. 보안 고려사항

1. **자격 증명 관리**: 
   - 자격 증명은 절대로 프론트엔드 코드에 저장해서는 안 됩니다.
   - 환경 변수나 암호화된 서버 저장소를 사용하세요.

2. **백그라운드 작업**:
   - 메모리 내 작업 상태 대신 Redis나 데이터베이스를 사용하여 영속적인 작업 상태 관리를 고려하세요.

3. **브라우저 자동화**:
   - 서버에서 브라우저를 실행할 때 적절한 권한과 샌드박스 설정이 필요합니다.
   - Docker 컨테이너 내에서 브라우저를 실행하는 것이 더 안전할 수 있습니다.

4. **사용자 인증**:
   - LLM Scraper 기능에 접근하기 전에 사용자 인증을 요구하세요.
   - 기존 LLMNightRun 인증 시스템을 활용하세요.

## 6. 성능 고려사항

1. **브라우저 인스턴스 관리**:
   - 여러 사용자가 동시에 스크레이퍼를 실행할 경우, 브라우저 인스턴스 수를 제한하는 큐 시스템 구현을 고려하세요.

2. **메모리 사용량**:
   - 브라우저 자동화는 메모리를 많이 사용할 수 있으므로, 서버 리소스를 모니터링하세요.

3. **캐싱**:
   - 동일한 프롬프트에 대한 응답을 캐싱하여 중복 요청 처리를 방지하세요.

4. **동시성 제한**:
   - 동시에 실행될 수 있는 스크레이퍼 작업 수를 제한하세요.

## 7. 확장 아이디어

1. **결과 저장소**:
   - 사용자가 이전 실행 결과를 검색하고 비교할 수 있는 결과 저장소 기능

2. **스케줄링**:
   - 특정 시간에 자동으로 실행되는, 예약된 프롬프트 실행 기능

3. **템플릿**:
   - 재사용 가능한 프롬프트 템플릿 기능

4. **결과 내보내기**:
   - CSV, PDF 또는 API를 통한 결과 내보내기 기능

5. **고급 비교**:
   - 시맨틱 유사성 분석 및 시각화 도구

6. **통합**:
   - 메모리 시스템, 블록 시스템을 포함한 다른 LLMNightRun 기능과의 통합
