"""
A/B 테스트 코드 내보내기 컨트롤러

실험 세트를 코드로 내보내는 비즈니스 로직을 구현합니다.
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import textwrap

from backend.logger import get_logger
from backend.ab_testing import models, schemas

# 로거 설정
logger = get_logger(__name__)


async def export_code(
    db: Session, 
    experiment_set_id: int, 
    language: str = "python", 
    experiment_id: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """실험 세트를 코드로 내보냅니다."""
    try:
        # 실험 세트 조회
        experiment_set = db.query(models.ExperimentSet).filter(models.ExperimentSet.id == experiment_set_id).first()
        if not experiment_set:
            return None
        
        # 특정 실험 조회 (지정된 경우)
        experiments = []
        if experiment_id:
            experiment = db.query(models.Experiment).filter(
                models.Experiment.id == experiment_id,
                models.Experiment.experiment_set_id == experiment_set_id
            ).first()
            if experiment:
                experiments = [experiment]
        else:
            # 모든 실험 조회
            experiments = experiment_set.experiments
        
        if not experiments:
            return None
        
        # 언어별로 코드 생성
        if language == "python":
            code_snippet = generate_python_code(experiment_set, experiments)
            dependencies = ["openai", "anthropic", "aiohttp", "asyncio"]
            usage_instructions = textwrap.dedent("""
            ### 사용 방법
            
            1. 필요한 패키지를 설치합니다:
               ```
               pip install openai anthropic aiohttp asyncio
               ```
            
            2. API 키를 설정합니다:
               ```python
               import os
               os.environ["OPENAI_API_KEY"] = "your-openai-api-key"
               os.environ["ANTHROPIC_API_KEY"] = "your-anthropic-api-key"
               ```
            
            3. 스크립트를 실행합니다:
               ```
               python experiment.py
               ```
            """).strip()
            
        elif language == "javascript":
            code_snippet = generate_javascript_code(experiment_set, experiments)
            dependencies = ["openai", "anthropic", "axios"]
            usage_instructions = textwrap.dedent("""
            ### 사용 방법
            
            1. 필요한 패키지를 설치합니다:
               ```
               npm install openai anthropic axios
               ```
            
            2. API 키를 설정합니다:
               ```javascript
               process.env.OPENAI_API_KEY = "your-openai-api-key";
               process.env.ANTHROPIC_API_KEY = "your-anthropic-api-key";
               ```
            
            3. 스크립트를 실행합니다:
               ```
               node experiment.js
               ```
            """).strip()
            
        elif language == "typescript":
            code_snippet = generate_typescript_code(experiment_set, experiments)
            dependencies = ["openai", "anthropic", "axios", "typescript", "ts-node"]
            usage_instructions = textwrap.dedent("""
            ### 사용 방법
            
            1. 필요한 패키지를 설치합니다:
               ```
               npm install openai anthropic axios
               npm install -D typescript ts-node @types/node
               ```
            
            2. API 키를 설정합니다:
               ```typescript
               process.env.OPENAI_API_KEY = "your-openai-api-key";
               process.env.ANTHROPIC_API_KEY = "your-anthropic-api-key";
               ```
            
            3. 스크립트를 실행합니다:
               ```
               npx ts-node experiment.ts
               ```
            """).strip()
        else:
            return None
        
        # 결과 반환
        return {
            "experiment_set_id": experiment_set_id,
            "language": language,
            "code_snippet": code_snippet,
            "dependencies": dependencies,
            "usage_instructions": usage_instructions
        }
        
    except Exception as e:
        logger.error(f"코드 내보내기 중 오류 발생: {str(e)}")
        return None


def generate_python_code(
    experiment_set: models.ExperimentSet,
    experiments: List[models.Experiment]
) -> str:
    """실험 세트를 Python 코드로 변환합니다."""
    code = textwrap.dedent(f"""
    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    
    """
    f"""
    # {experiment_set.name} - A/B Testing Code
    # {"=" * 50}
    # Description: {experiment_set.description or 'No description provided'}
    # Created from LLMNightRun Export
    
    import os
    import json
    import asyncio
    import time
    from typing import Dict, Any, List, Optional
    
    # OpenAI 클라이언트 설정
    from openai import AsyncOpenAI
    
    # Anthropic 클라이언트 설정
    from anthropic import AsyncAnthropic
    
    # 결과 저장을 위한 클래스
    class ExperimentResult:
        def __init__(self, name: str, model: str, output: str, execution_time: float, token_usage: Dict[str, int]):
            self.name = name
            self.model = model
            self.output = output
            self.execution_time = execution_time
            self.token_usage = token_usage
        
        def to_dict(self) -> Dict[str, Any]:
            return {{
                "name": self.name,
                "model": self.model,
                "output": self.output,
                "execution_time": self.execution_time,
                "token_usage": self.token_usage
            }}
    
    # OpenAI 모델 실행 함수
    async def run_openai_experiment(name: str, model: str, prompt: str, params: Dict[str, Any]) -> ExperimentResult:
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 기본 파라미터 설정
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 1000)
        top_p = params.get("top_p", 1.0)
        frequency_penalty = params.get("frequency_penalty", 0.0)
        presence_penalty = params.get("presence_penalty", 0.0)
        
        start_time = time.time()
        response = await client.chat.completions.create(
            model=model,
            messages=[{{"role": "user", "content": prompt}}],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        output = response.choices[0].message.content
        
        token_usage = {{
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }}
        
        return ExperimentResult(name, model, output, execution_time, token_usage)
    
    # Anthropic 모델 실행 함수
    async def run_anthropic_experiment(name: str, model: str, prompt: str, params: Dict[str, Any]) -> ExperimentResult:
        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # 기본 파라미터 설정
        temperature = params.get("temperature", 0.7)
        max_tokens = params.get("max_tokens", 1000)
        
        start_time = time.time()
        response = await client.messages.create(
            model=model,
            messages=[{{"role": "user", "content": prompt}}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        end_time = time.time()
        
        execution_time = end_time - start_time
        output = response.content[0].text
        
        token_usage = {{
            "prompt_tokens": 0,  # Anthropic API는 현재 토큰 사용량을 제공하지 않음
            "completion_tokens": 0,
            "total_tokens": 0
        }}
        
        return ExperimentResult(name, model, output, execution_time, token_usage)
    
    # 실험 실행 함수
    async def run_experiment(name: str, model: str, prompt: str, params: Dict[str, Any]) -> ExperimentResult:
        if "gpt" in model:
            return await run_openai_experiment(name, model, prompt, params)
        elif "claude" in model:
            return await run_anthropic_experiment(name, model, prompt, params)
        else:
            raise ValueError(f"Unsupported model: {{model}}")
    
    # 모든 실험 실행
    async def run_all_experiments() -> List[ExperimentResult]:
        results = []
        
        # 실험 정의
    """)
    
    # 각 실험 추가
    for i, experiment in enumerate(experiments):
        model_params = json.dumps(experiment.params, indent=4, ensure_ascii=False) if experiment.params else "{}"
        model_params = "\n        ".join(model_params.split("\n"))
        
        code += textwrap.dedent(f"""
        # 실험 {i+1}: {experiment.name}
        experiment_{i+1} = {{
            "name": "{experiment.name}",
            "model": "{experiment.model}",
            "prompt": \"\"\"
{experiment.prompt}
\"\"\",
            "params": {model_params}
        }}
        
        result_{i+1} = await run_experiment(**experiment_{i+1})
        results.append(result_{i+1})
        print(f"실험 {i+1} ({experiment.name}) 완료")
        """)
    
    # 메인 실행 코드 추가
    code += textwrap.dedent("""
    
    # 결과 비교 및 분석
    def compare_results(results: List[ExperimentResult]) -> None:
        print("\\n결과 비교:")
        print("-" * 50)
        
        for i, result in enumerate(results):
            print(f"\\n실험 {i+1}: {result.name} (모델: {result.model})")
            print(f"실행 시간: {result.execution_time:.2f}초")
            print(f"토큰 사용량: {result.token_usage}")
            print("\\n출력:")
            print(result.output[:500] + "..." if len(result.output) > 500 else result.output)
        
        # 실행 시간 비교
        min_time = min(results, key=lambda r: r.execution_time)
        print("\\n가장 빠른 모델:", min_time.name, f"({min_time.execution_time:.2f}초)")
        
        # 토큰 사용량 비교 (OpenAI 모델만)
        openai_results = [r for r in results if "gpt" in r.model]
        if openai_results:
            min_tokens = min(openai_results, key=lambda r: r.token_usage.get("total_tokens", 0))
            print("가장 적은 토큰 사용:", min_tokens.name, f"({min_tokens.token_usage.get('total_tokens', 0)}개)")
    
    # 결과 저장
    def save_results(results: List[ExperimentResult], filename: str = "ab_test_results.json") -> None:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in results], f, ensure_ascii=False, indent=2)
        print(f"결과가 {filename}에 저장되었습니다.")
    
    
    # 메인 실행
    async def main():
        try:
            print("A/B 테스트 실행 중...")
            results = await run_all_experiments()
            
            compare_results(results)
            save_results(results)
            
            print("\\nA/B 테스트 완료!")
        except Exception as e:
            print(f"오류 발생: {str(e)}")
    
    
    if __name__ == "__main__":
        asyncio.run(main())
    """)
    
    return code.strip()


def generate_javascript_code(
    experiment_set: models.ExperimentSet,
    experiments: List[models.Experiment]
) -> str:
    """실험 세트를 JavaScript 코드로 변환합니다."""
    code = textwrap.dedent(f"""
    /**
     * {experiment_set.name} - A/B Testing Code
     * {"=" * 50}
     * Description: {experiment_set.description or 'No description provided'}
     * Created from LLMNightRun Export
     */
    
    const OpenAI = require('openai');
    const Anthropic = require('anthropic');
    const fs = require('fs');
    
    // 클라이언트 설정
    const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
    
    // OpenAI 모델 실행 함수
    async function runOpenAIExperiment(name, model, prompt, params) {{
        const temperature = params.temperature ?? 0.7;
        const maxTokens = params.max_tokens ?? 1000;
        const topP = params.top_p ?? 1.0;
        const frequencyPenalty = params.frequency_penalty ?? 0.0;
        const presencePenalty = params.presence_penalty ?? 0.0;
        
        const startTime = Date.now();
        
        const response = await openai.chat.completions.create({{
            model,
            messages: [{{ role: 'user', content: prompt }}],
            temperature,
            max_tokens: maxTokens,
            top_p: topP,
            frequency_penalty: frequencyPenalty,
            presence_penalty: presencePenalty
        }});
        
        const endTime = Date.now();
        const executionTime = (endTime - startTime) / 1000;
        
        const output = response.choices[0].message.content;
        const tokenUsage = {{
            promptTokens: response.usage.prompt_tokens,
            completionTokens: response.usage.completion_tokens,
            totalTokens: response.usage.total_tokens
        }};
        
        return {{
            name,
            model,
            output,
            executionTime,
            tokenUsage
        }};
    }}
    
    // Anthropic 모델 실행 함수
    async function runAnthropicExperiment(name, model, prompt, params) {{
        const temperature = params.temperature ?? 0.7;
        const maxTokens = params.max_tokens ?? 1000;
        
        const startTime = Date.now();
        
        const response = await anthropic.messages.create({{
            model,
            messages: [{{ role: 'user', content: prompt }}],
            temperature,
            max_tokens: maxTokens
        }});
        
        const endTime = Date.now();
        const executionTime = (endTime - startTime) / 1000;
        
        const output = response.content[0].text;
        
        // Anthropic API는 현재 토큰 사용량을 제공하지 않음
        const tokenUsage = {{
            promptTokens: 0,
            completionTokens: 0,
            totalTokens: 0
        }};
        
        return {{
            name,
            model,
            output,
            executionTime,
            tokenUsage
        }};
    }}
    
    // 실험 실행 함수
    async function runExperiment(name, model, prompt, params) {{
        if (model.includes('gpt')) {{
            return await runOpenAIExperiment(name, model, prompt, params);
        }} else if (model.includes('claude')) {{
            return await runAnthropicExperiment(name, model, prompt, params);
        }} else {{
            throw new Error(`Unsupported model: ${{model}}`);
        }}
    }}
    
    // 모든 실험 실행
    async function runAllExperiments() {{
        const results = [];
        
        // 실험 정의
    """)
    
    # 각 실험 추가
    for i, experiment in enumerate(experiments):
        model_params = json.dumps(experiment.params, indent=4, ensure_ascii=False) if experiment.params else "{}"
        
        # JavaScript 형식에 맞게 프롬프트 처리
        prompt = experiment.prompt.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        
        code += textwrap.dedent(f"""
        // 실험 {i+1}: {experiment.name}
        const experiment{i+1} = {{
            name: "{experiment.name}",
            model: "{experiment.model}",
            prompt: `{prompt}`,
            params: {model_params}
        }};
        
        console.log(`실험 {i+1} ({experiment.name}) 시작...`);
        const result{i+1} = await runExperiment(
            experiment{i+1}.name,
            experiment{i+1}.model,
            experiment{i+1}.prompt,
            experiment{i+1}.params
        );
        results.push(result{i+1});
        console.log(`실험 {i+1} ({experiment.name}) 완료`);
        """)
    
    # 메인 실행 코드 추가
    code += textwrap.dedent("""
    
        return results;
    }
    
    // 결과 비교 및 분석
    function compareResults(results) {
        console.log("\n결과 비교:");
        console.log("-".repeat(50));
        
        results.forEach((result, i) => {
            console.log(`\n실험 ${i+1}: ${result.name} (모델: ${result.model})`);
            console.log(`실행 시간: ${result.executionTime.toFixed(2)}초`);
            console.log(`토큰 사용량:`, result.tokenUsage);
            
            const displayOutput = result.output.length > 500 
                ? result.output.substring(0, 500) + "..." 
                : result.output;
            console.log("\n출력:");
            console.log(displayOutput);
        });
        
        // 실행 시간 비교
        const minTime = results.reduce((min, r) => r.executionTime < min.executionTime ? r : min, results[0]);
        console.log("\n가장 빠른 모델:", minTime.name, `(${minTime.executionTime.toFixed(2)}초)`);
        
        // 토큰 사용량 비교 (OpenAI 모델만)
        const openaiResults = results.filter(r => r.model.includes('gpt'));
        if (openaiResults.length > 0) {
            const minTokens = openaiResults.reduce(
                (min, r) => (r.tokenUsage.totalTokens < min.tokenUsage.totalTokens) ? r : min, 
                openaiResults[0]
            );
            console.log("가장 적은 토큰 사용:", minTokens.name, `(${minTokens.tokenUsage.totalTokens}개)`);
        }
    }
    
    // 결과 저장
    function saveResults(results, filename = "ab_test_results.json") {
        fs.writeFileSync(filename, JSON.stringify(results, null, 2));
        console.log(`결과가 ${filename}에 저장되었습니다.`);
    }
    
    // 메인 실행
    async function main() {
        try {
            console.log("A/B 테스트 실행 중...");
            const results = await runAllExperiments();
            
            compareResults(results);
            saveResults(results);
            
            console.log("\nA/B 테스트 완료!");
        } catch (error) {
            console.error("오류 발생:", error);
        }
    }
    
    main();
    """)
    
    return code.strip()


def generate_typescript_code(
    experiment_set: models.ExperimentSet,
    experiments: List[models.Experiment]
) -> str:
    """실험 세트를 TypeScript 코드로 변환합니다."""
    code = textwrap.dedent(f"""
    /**
     * {experiment_set.name} - A/B Testing Code
     * {"=" * 50}
     * Description: {experiment_set.description or 'No description provided'}
     * Created from LLMNightRun Export
     */
    
    import OpenAI from 'openai';
    import Anthropic from 'anthropic';
    import * as fs from 'fs';
    
    // 결과 타입 정의
    interface TokenUsage {{
        promptTokens: number;
        completionTokens: number;
        totalTokens: number;
    }}
    
    interface ExperimentResult {{
        name: string;
        model: string;
        output: string;
        executionTime: number;
        tokenUsage: TokenUsage;
    }}
    
    interface ExperimentConfig {{
        name: string;
        model: string;
        prompt: string;
        params: Record<string, any>;
    }}
    
    // 클라이언트 설정
    const openai = new OpenAI({{ apiKey: process.env.OPENAI_API_KEY }});
    const anthropic = new Anthropic({{ apiKey: process.env.ANTHROPIC_API_KEY }});
    
    // OpenAI 모델 실행 함수
    async function runOpenAIExperiment(
        name: string,
        model: string,
        prompt: string,
        params: Record<string, any>
    ): Promise<ExperimentResult> {{
        const temperature = params.temperature ?? 0.7;
        const maxTokens = params.max_tokens ?? 1000;
        const topP = params.top_p ?? 1.0;
        const frequencyPenalty = params.frequency_penalty ?? 0.0;
        const presencePenalty = params.presence_penalty ?? 0.0;
        
        const startTime = Date.now();
        
        const response = await openai.chat.completions.create({{
            model,
            messages: [{{ role: 'user', content: prompt }}],
            temperature,
            max_tokens: maxTokens,
            top_p: topP,
            frequency_penalty: frequencyPenalty,
            presence_penalty: presencePenalty
        }});
        
        const endTime = Date.now();
        const executionTime = (endTime - startTime) / 1000;
        
        const output = response.choices[0].message.content ?? '';
        const tokenUsage: TokenUsage = {{
            promptTokens: response.usage?.prompt_tokens ?? 0,
            completionTokens: response.usage?.completion_tokens ?? 0,
            totalTokens: response.usage?.total_tokens ?? 0
        }};
        
        return {{
            name,
            model,
            output,
            executionTime,
            tokenUsage
        }};
    }}
    
    // Anthropic 모델 실행 함수
    async function runAnthropicExperiment(
        name: string,
        model: string,
        prompt: string,
        params: Record<string, any>
    ): Promise<ExperimentResult> {{
        const temperature = params.temperature ?? 0.7;
        const maxTokens = params.max_tokens ?? 1000;
        
        const startTime = Date.now();
        
        const response = await anthropic.messages.create({{
            model,
            messages: [{{ role: 'user', content: prompt }}],
            temperature,
            max_tokens: maxTokens
        }});
        
        const endTime = Date.now();
        const executionTime = (endTime - startTime) / 1000;
        
        const output = response.content[0].text;
        
        // Anthropic API는 현재 토큰 사용량을 제공하지 않음
        const tokenUsage: TokenUsage = {{
            promptTokens: 0,
            completionTokens: 0,
            totalTokens: 0
        }};
        
        return {{
            name,
            model,
            output,
            executionTime,
            tokenUsage
        }};
    }}
    
    // 실험 실행 함수
    async function runExperiment(config: ExperimentConfig): Promise<ExperimentResult> {{
        const {{ name, model, prompt, params }} = config;
        
        if (model.includes('gpt')) {{
            return await runOpenAIExperiment(name, model, prompt, params);
        }} else if (model.includes('claude')) {{
            return await runAnthropicExperiment(name, model, prompt, params);
        }} else {{
            throw new Error(`Unsupported model: ${{model}}`);
        }}
    }}
    
    // 모든 실험 실행
    async function runAllExperiments(): Promise<ExperimentResult[]> {{
        const results: ExperimentResult[] = [];
        
        // 실험 정의
    """)
    
    # 각 실험 추가
    for i, experiment in enumerate(experiments):
        model_params = json.dumps(experiment.params, indent=4, ensure_ascii=False) if experiment.params else "{}"
        
        # TypeScript 형식에 맞게 프롬프트 처리
        prompt = experiment.prompt.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        
        code += textwrap.dedent(f"""
        // 실험 {i+1}: {experiment.name}
        const experiment{i+1}: ExperimentConfig = {{
            name: "{experiment.name}",
            model: "{experiment.model}",
            prompt: `{prompt}`,
            params: {model_params}
        }};
        
        console.log(`실험 {i+1} ({experiment.name}) 시작...`);
        const result{i+1} = await runExperiment(experiment{i+1});
        results.push(result{i+1});
        console.log(`실험 {i+1} ({experiment.name}) 완료`);
        """)
    
    # 메인 실행 코드 추가
    code += textwrap.dedent("""
    
        return results;
    }
    
    // 결과 비교 및 분석
    function compareResults(results: ExperimentResult[]): void {
        console.log("\n결과 비교:");
        console.log("-".repeat(50));
        
        results.forEach((result, i) => {
            console.log(`\n실험 ${i+1}: ${result.name} (모델: ${result.model})`);
            console.log(`실행 시간: ${result.executionTime.toFixed(2)}초`);
            console.log(`토큰 사용량:`, result.tokenUsage);
            
            const displayOutput = result.output.length > 500 
                ? result.output.substring(0, 500) + "..." 
                : result.output;
            console.log("\n출력:");
            console.log(displayOutput);
        });
        
        // 실행 시간 비교
        const minTime = results.reduce((min, r) => r.executionTime < min.executionTime ? r : min, results[0]);
        console.log("\n가장 빠른 모델:", minTime.name, `(${minTime.executionTime.toFixed(2)}초)`);
        
        // 토큰 사용량 비교 (OpenAI 모델만)
        const openaiResults = results.filter(r => r.model.includes('gpt'));
        if (openaiResults.length > 0) {
            const minTokens = openaiResults.reduce(
                (min, r) => (r.tokenUsage.totalTokens < min.tokenUsage.totalTokens) ? r : min, 
                openaiResults[0]
            );
            console.log("가장 적은 토큰 사용:", minTokens.name, `(${minTokens.tokenUsage.totalTokens}개)`);
        }
    }
    
    // 결과 저장
    function saveResults(results: ExperimentResult[], filename: string = "ab_test_results.json"): void {
        fs.writeFileSync(filename, JSON.stringify(results, null, 2));
        console.log(`결과가 ${filename}에 저장되었습니다.`);
    }
    
    // 메인 실행
    async function main(): Promise<void> {
        try {
            console.log("A/B 테스트 실행 중...");
            const results = await runAllExperiments();
            
            compareResults(results);
            saveResults(results);
            
            console.log("\nA/B 테스트 완료!");
        } catch (error) {
            console.error("오류 발생:", error);
        }
    }
    
    main();
    """)
    
    return code.strip()
