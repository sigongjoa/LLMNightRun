"""
AI 환경 설정 생성기

분석 결과를 바탕으로 GitHub 저장소에 적합한 AI 환경 설정을 생성합니다.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

# 로깅 설정
logger = logging.getLogger("github_ai_setup.generator")


class AISetupGenerator:
    """
    AI 환경 설정 생성 클래스
    
    GitHub 저장소에 필요한 AI 관련 구성 파일과 스크립트를 생성합니다.
    """
    
    def __init__(self, repo_analysis: Dict[str, Any]):
        """
        생성기 초기화
        
        Args:
            repo_analysis: 저장소 분석 결과
        """
        self.repo_analysis = repo_analysis
        self.repo_id = repo_analysis.get("repo_id", "unknown")
        self.language_stats = repo_analysis.get("language_stats", {})
        self.frameworks = repo_analysis.get("frameworks", [])
        self.dependencies = repo_analysis.get("dependencies", {})
        
        # 주요 언어 결정
        self.primary_language = self._determine_primary_language()
        
        logger.info(f"AI 환경 설정 생성기 초기화: {self.repo_id} (주 언어: {self.primary_language})")
    
    def _determine_primary_language(self) -> str:
        """
        주요 언어 결정
        
        Returns:
            주요 프로그래밍 언어
        """
        if not self.language_stats:
            return "Python"  # 기본값
        
        # 사용 비율이 가장 높은 언어 선택
        return max(self.language_stats.items(), key=lambda x: x[1])[0]
    
    async def generate_setup(self) -> Dict[str, Any]:
        """
        AI 환경 설정 생성
        
        Returns:
            생성된 설정 정보
        """
        try:
            logger.info(f"AI 환경 설정 생성 시작: {self.repo_id}")
            
            # 필요한 구성 파일 생성
            config_files = await self.generate_config_files()
            
            # 설치 스크립트 생성
            setup_scripts = await self.generate_setup_scripts()
            
            # GitHub Actions 워크플로우 생성
            workflows = await self.generate_workflows()
            
            # 문서 생성
            documentation = await self.generate_documentation()
            
            # 결과 종합
            result = {
                "repo_id": self.repo_id,
                "config_files": config_files,
                "setup_scripts": setup_scripts,
                "workflows": workflows,
                "documentation": documentation
            }
            
            logger.info(f"AI 환경 설정 생성 완료: {self.repo_id}")
            return result
            
        except Exception as e:
            logger.error(f"AI 환경 설정 생성 오류: {str(e)}")
            return {
                "error": str(e),
                "repo_id": self.repo_id
            }
    
    async def generate_config_files(self) -> List[Dict[str, Any]]:
        """
        구성 파일 생성
        
        Returns:
            구성 파일 목록
        """
        config_files = []
        
        # 주요 언어에 따라 다른 구성 파일 생성
        if self.primary_language == "Python":
            # requirements-ai.txt
            ai_requirements = await self._generate_python_requirements()
            config_files.append({
                "path": "requirements-ai.txt",
                "content": ai_requirements,
                "description": "AI 관련 Python 종속성"
            })
            
            # pyproject.toml 업데이트 (있는 경우)
            pyproject = await self._generate_pyproject_update()
            if pyproject:
                config_files.append({
                    "path": "pyproject.toml",
                    "content": pyproject,
                    "description": "Python 프로젝트 설정 업데이트"
                })
                
        elif self.primary_language == "JavaScript" or self.primary_language == "TypeScript":
            # package.json 업데이트
            package_json = await self._generate_package_json_update()
            config_files.append({
                "path": "package.json.update",
                "content": package_json,
                "description": "package.json 업데이트 내용"
            })
        
        # .env.example 파일 (공통)
        env_example = await self._generate_env_example()
        config_files.append({
            "path": ".env.example",
            "content": env_example,
            "description": "AI 환경 변수 예시"
        })
        
        # .gitignore 업데이트 (공통)
        gitignore = await self._generate_gitignore_update()
        config_files.append({
            "path": ".gitignore.append",
            "content": gitignore,
            "description": ".gitignore에 추가할 내용"
        })
        
        # Docker 지원이 필요한 경우
        if self._needs_docker():
            dockerfile = await self._generate_dockerfile()
            config_files.append({
                "path": "Dockerfile.ai",
                "content": dockerfile,
                "description": "AI 지원 Dockerfile"
            })
            
            docker_compose = await self._generate_docker_compose()
            config_files.append({
                "path": "docker-compose.ai.yml",
                "content": docker_compose,
                "description": "AI 서비스 docker-compose 구성"
            })
        
        return config_files
    
    async def generate_setup_scripts(self) -> List[Dict[str, Any]]:
        """
        설치 스크립트 생성
        
        Returns:
            설치 스크립트 목록
        """
        setup_scripts = []
        
        # 환경 설정 스크립트
        if self.primary_language == "Python":
            setup_script = await self._generate_python_setup_script()
            setup_scripts.append({
                "path": "scripts/setup_ai_env.py",
                "content": setup_script,
                "description": "AI 환경 설정 스크립트"
            })
            
            # 모델 다운로드 스크립트
            download_script = await self._generate_model_download_script()
            setup_scripts.append({
                "path": "scripts/download_models.py",
                "content": download_script,
                "description": "AI 모델 다운로드 스크립트"
            })
            
        elif self.primary_language == "JavaScript" or self.primary_language == "TypeScript":
            setup_script = await self._generate_js_setup_script()
            setup_scripts.append({
                "path": "scripts/setup-ai-env.js",
                "content": setup_script,
                "description": "AI 환경 설정 스크립트"
            })
        
        # 공통 - 설치 지원 셸 스크립트
        if "Linux" in self._get_target_platforms() or "macOS" in self._get_target_platforms():
            shell_script = await self._generate_shell_setup_script()
            setup_scripts.append({
                "path": "scripts/setup-ai-env.sh",
                "content": shell_script,
                "description": "Unix/Linux용 AI 환경 설정 스크립트"
            })
        
        if "Windows" in self._get_target_platforms():
            batch_script = await self._generate_batch_setup_script()
            setup_scripts.append({
                "path": "scripts/setup-ai-env.bat",
                "content": batch_script,
                "description": "Windows용 AI 환경 설정 스크립트"
            })
        
        return setup_scripts
    
    async def generate_workflows(self) -> List[Dict[str, Any]]:
        """
        GitHub Actions 워크플로우 생성
        
        Returns:
            워크플로우 파일 목록
        """
        workflows = []
        
        # CI 워크플로우 (테스트, 린트 등)
        ci_workflow = await self._generate_ci_workflow()
        workflows.append({
            "path": ".github/workflows/ai-ci.yml",
            "content": ci_workflow,
            "description": "AI 구성요소 CI 워크플로우"
        })
        
        # 모델 훈련 워크플로우
        training_workflow = await self._generate_training_workflow()
        workflows.append({
            "path": ".github/workflows/model-training.yml",
            "content": training_workflow,
            "description": "모델 훈련 워크플로우"
        })
        
        # 모델 배포 워크플로우
        deployment_workflow = await self._generate_deployment_workflow()
        workflows.append({
            "path": ".github/workflows/model-deployment.yml",
            "content": deployment_workflow,
            "description": "모델 배포 워크플로우"
        })
        
        return workflows
    
    async def generate_documentation(self) -> Dict[str, Any]:
        """
        문서 생성
        
        Returns:
            문서 정보
        """
        # AI 통합 가이드
        integration_guide = await self._generate_integration_guide()
        
        return {
            "path": "docs/ai_integration.md",
            "content": integration_guide,
            "description": "AI 통합 가이드"
        }
    
    # Helper methods
    def _needs_docker(self) -> bool:
        """Docker 지원이 필요한지 확인"""
        # 실제 구현에서는 여러 요소 고려
        return True
    
    def _get_target_platforms(self) -> List[str]:
        """지원할 타겟 플랫폼 목록"""
        # 실제 구현에서는 프로젝트 구성 분석
        return ["Linux", "macOS", "Windows"]
    
    # 파일 생성 메서드들
    async def _generate_python_requirements(self) -> str:
        """Python AI 요구사항 파일 생성"""
        requirements = [
            "# AI 환경을 위한 Python 패키지",
            "numpy>=1.21.0",
            "pandas>=1.3.0",
            "scikit-learn>=1.0.0",
            "tensorflow>=2.8.0",
            "torch>=1.10.0",
            "transformers>=4.18.0",
            "huggingface-hub>=0.4.0",
            "matplotlib>=3.4.0",
            "seaborn>=0.11.0",
            "fastapi>=0.75.0",
            "uvicorn>=0.17.0",
            "pytest>=6.2.5",
        ]
        return "\n".join(requirements)
    
    async def _generate_pyproject_update(self) -> Optional[str]:
        """pyproject.toml 업데이트 내용 생성"""
        # 실제 구현에서는 기존 파일 내용 분석 후 업데이트
        return None
    
    async def _generate_package_json_update(self) -> str:
        """package.json 업데이트 내용 생성"""
        # 실제 구현에서는 기존 파일 내용 분석 후 업데이트
        return json.dumps({
            "dependencies": {
                "@tensorflow/tfjs": "^3.18.0",
                "ml5": "^0.7.1",
                "brain.js": "^2.0.0"
            },
            "devDependencies": {
                "@types/tensorflow__tfjs": "^3.0.0"
            },
            "scripts": {
                "train-model": "node scripts/train-model.js",
                "serve-model": "node scripts/serve-model.js"
            }
        }, indent=2)
    
    async def _generate_env_example(self) -> str:
        """환경 변수 예시 파일 생성"""
        env_vars = [
            "# AI 환경 변수",
            "MODEL_PATH=./models",
            "DEFAULT_MODEL=efficientnet_b0",
            "INFERENCE_TIMEOUT=30",
            "TF_ENABLE_ONEDNN_OPTS=1",
            "TF_CPP_MIN_LOG_LEVEL=2",
            "CUDA_VISIBLE_DEVICES=0",
            "",
            "# API 키(안전한 방식으로 관리하세요)",
            "# OPENAI_API_KEY=your_key_here",
            "# HUGGINGFACE_API_KEY=your_key_here",
        ]
        return "\n".join(env_vars)
    
    async def _generate_gitignore_update(self) -> str:
        """gitignore 업데이트 내용 생성"""
        gitignore_content = [
            "# AI 관련 파일",
            "models/",
            "*.onnx",
            "*.h5",
            "*.tflite",
            "*.pt",
            "*.pth",
            "*.bin",
            "cached_models/",
            "runs/",
            "logs/",
            "mlruns/",
            ".vectordb/",
            ".env.ai",
        ]
        return "\n".join(gitignore_content)
    
    async def _generate_dockerfile(self) -> str:
        """AI 지원 Dockerfile 생성"""
        if self.primary_language == "Python":
            dockerfile = [
                "FROM python:3.9-slim",
                "",
                "WORKDIR /app",
                "",
                "# 시스템 종속성 설치",
                "RUN apt-get update && apt-get install -y --no-install-recommends \\",
                "    build-essential \\",
                "    && rm -rf /var/lib/apt/lists/*",
                "",
                "# Python 종속성 설치",
                "COPY requirements.txt requirements-ai.txt /app/",
                "RUN pip install --no-cache-dir -r requirements.txt -r requirements-ai.txt",
                "",
                "# 애플리케이션 복사",
                "COPY . /app/",
                "",
                "# 모델 다운로드",
                "RUN python scripts/download_models.py",
                "",
                "EXPOSE 8000",
                "",
                "CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]",
            ]
        elif self.primary_language == "JavaScript" or self.primary_language == "TypeScript":
            dockerfile = [
                "FROM node:16-slim",
                "",
                "WORKDIR /app",
                "",
                "# 종속성 설치",
                "COPY package*.json /app/",
                "RUN npm install",
                "",
                "# 애플리케이션 복사",
                "COPY . /app/",
                "",
                "# 모델 다운로드",
                "RUN node scripts/download-models.js",
                "",
                "EXPOSE 3000",
                "",
                "CMD [\"npm\", \"start\"]",
            ]
        else:
            dockerfile = [
                "# 기본 Dockerfile",
                "FROM python:3.9-slim",
                "",
                "WORKDIR /app",
                "",
                "COPY . /app/",
                "",
                "RUN pip install --no-cache-dir -r requirements.txt",
                "",
                "EXPOSE 8000",
                "",
                "CMD [\"python\", \"app.py\"]",
            ]
        
        return "\n".join(dockerfile)
    
    async def _generate_docker_compose(self) -> str:
        """AI 지원 docker-compose 구성 생성"""
        compose = [
            "version: '3'",
            "",
            "services:",
            "  app:",
            "    build:",
            "      context: .",
            "      dockerfile: Dockerfile.ai",
            "    ports:",
            "      - \"8000:8000\"",
            "    volumes:",
            "      - ./:/app",
            "      - model-cache:/app/models",
            "    env_file:",
            "      - .env",
            "    environment:",
            "      - TF_ENABLE_ONEDNN_OPTS=1",
            "      - CUDA_VISIBLE_DEVICES=0",
            "",
            "volumes:",
            "  model-cache:",
            "    driver: local",
        ]
        return "\n".join(compose)
    
    async def _generate_python_setup_script(self) -> str:
        """Python AI 환경 설정 스크립트 생성"""
        script = [
            "#!/usr/bin/env python",
            "\"\"\"",
            "AI 환경 설정 스크립트",
            "",
            "이 스크립트는 AI 개발 및 배포에 필요한 환경을 설정합니다.",
            "\"\"\"",
            "",
            "import os",
            "import sys",
            "import subprocess",
            "import platform",
            "import argparse",
            "from pathlib import Path",
            "",
            "",
            "def setup_environment(args):",
            "    \"\"\"AI 환경 설정\"\"\"",
            "    print(\"AI 환경 설정을 시작합니다...\")",
            "    ",
            "    # 현재 디렉토리",
            "    current_dir = Path().absolute()",
            "    ",
            "    # 필요한 디렉토리 생성",
            "    os.makedirs(\"models\", exist_ok=True)",
            "    os.makedirs(\"logs\", exist_ok=True)",
            "    ",
            "    # 종속성 설치",
            "    print(\"종속성을 설치하는 중...\")",
            "    subprocess.check_call([sys.executable, \"-m\", \"pip\", \"install\", \"-r\", \"requirements-ai.txt\"])",
            "    ",
            "    # 환경 변수 설정",
            "    if not os.path.exists(\".env\"):",
            "        print(\".env 파일을 생성하는 중...\")",
            "        with open(\".env.example\", \"r\") as example, open(\".env\", \"w\") as env:",
            "            env.write(example.read())",
            "    ",
            "    # 모델 다운로드",
            "    if args.download_models:",
            "        print(\"모델을 다운로드하는 중...\")",
            "        subprocess.check_call([sys.executable, \"scripts/download_models.py\"])",
            "    ",
            "    print(\"AI 환경 설정이 완료되었습니다!\")",
            "",
            "",
            "def main():",
            "    \"\"\"메인 함수\"\"\"",
            "    parser = argparse.ArgumentParser(description=\"AI 환경 설정 스크립트\")",
            "    parser.add_argument(\"--download-models\", action=\"store_true\", help=\"모델 다운로드 실행\")",
            "    args = parser.parse_args()",
            "    ",
            "    setup_environment(args)",
            "",
            "",
            "if __name__ == \"__main__\":",
            "    main()",
        ]
        return "\n".join(script)
    
    async def _generate_model_download_script(self) -> str:
        """모델 다운로드 스크립트 생성"""
        script = [
            "#!/usr/bin/env python",
            "\"\"\"",
            "AI 모델 다운로드 스크립트",
            "",
            "이 스크립트는 필요한 AI 모델을 다운로드합니다.",
            "\"\"\"",
            "",
            "import os",
            "import sys",
            "import argparse",
            "from pathlib import Path",
            "",
            "# 가능하면 tqdm 사용",
            "try:",
            "    from tqdm import tqdm",
            "    has_tqdm = True",
            "except ImportError:",
            "    has_tqdm = False",
            "",
            "# 가능하면 huggingface_hub 사용",
            "try:",
            "    from huggingface_hub import hf_hub_download, snapshot_download",
            "    has_hf = True",
            "except ImportError:",
            "    has_hf = False",
            "",
            "",
            "def download_models(args):",
            "    \"\"\"필요한 모델 다운로드\"\"\"",
            "    print(\"AI 모델 다운로드를 시작합니다...\")",
            "    ",
            "    # 모델 저장 디렉토리",
            "    model_dir = Path(args.output_dir)",
            "    os.makedirs(model_dir, exist_ok=True)",
            "    ",
            "    if has_hf:",
            "        print(\"Hugging Face Hub에서 모델을 다운로드하는 중...\")",
            "        # 예시 모델 다운로드",
            "        models_to_download = [",
            "            {\"repo_id\": \"google/vit-base-patch16-224\", \"filename\": \"pytorch_model.bin\"},",
            "            {\"repo_id\": \"microsoft/resnet-50\", \"filename\": \"pytorch_model.bin\"}",
            "        ]",
            "        ",
            "        for model in models_to_download:",
            "            try:",
            "                print(f\"다운로드 중: {model['repo_id']}\")",
            "                hf_hub_download(",
            "                    repo_id=model['repo_id'],",
            "                    filename=model['filename'],",
            "                    cache_dir=model_dir",
            "                )",
            "            except Exception as e:",
            "                print(f\"모델 다운로드 오류: {e}\")",
            "    else:",
            "        print(\"경고: huggingface_hub가 설치되지 않았습니다. 'pip install huggingface_hub'를 실행하세요.\")",
            "    ",
            "    print(\"모델 다운로드가 완료되었습니다!\")",
            "",
            "",
            "def main():",
            "    \"\"\"메인 함수\"\"\"",
            "    parser = argparse.ArgumentParser(description=\"AI 모델 다운로드 스크립트\")",
            "    parser.add_argument(\"--output-dir\", default=\"./models\", help=\"모델을 저장할 디렉토리\")",
            "    args = parser.parse_args()",
            "    ",
            "    download_models(args)",
            "",
            "",
            "if __name__ == \"__main__\":",
            "    main()",
        ]
        return "\n".join(script)
    
    async def _generate_js_setup_script(self) -> str:
        """JavaScript AI 환경 설정 스크립트 생성"""
        script = [
            "#!/usr/bin/env node",
            "/**",
            " * AI 환경 설정 스크립트",
            " *",
            " * 이 스크립트는 AI 개발 및 배포에 필요한 환경을 설정합니다.",
            " */",
            "",
            "const fs = require('fs');",
            "const path = require('path');",
            "const { execSync } = require('child_process');",
            "const os = require('os');",
            "",
            "// 명령줄 인수 파싱",
            "const args = process.argv.slice(2);",
            "const downloadModels = args.includes('--download-models');",
            "",
            "/**",
            " * AI 환경 설정",
            " */",
            "function setupEnvironment() {",
            "  console.log('AI 환경 설정을 시작합니다...');",
            "",
            "  // 필요한 디렉토리 생성",
            "  if (!fs.existsSync('models')) {",
            "    fs.mkdirSync('models', { recursive: true });",
            "  }",
            "",
            "  if (!fs.existsSync('logs')) {",
            "    fs.mkdirSync('logs', { recursive: true });",
            "  }",
            "",
            "  // 종속성 설치",
            "  console.log('종속성을 설치하는 중...');",
            "  execSync('npm install', { stdio: 'inherit' });",
            "",
            "  // 환경 변수 설정",
            "  if (!fs.existsSync('.env')) {",
            "    console.log('.env 파일을 생성하는 중...');",
            "    const envExample = fs.readFileSync('.env.example', 'utf8');",
            "    fs.writeFileSync('.env', envExample);",
            "  }",
            "",
            "  // 모델 다운로드",
            "  if (downloadModels) {",
            "    console.log('모델을 다운로드하는 중...');",
            "    execSync('node scripts/download-models.js', { stdio: 'inherit' });",
            "  }",
            "",
            "  console.log('AI 환경 설정이 완료되었습니다!');",
            "}",
            "",
            "// 스크립트 실행",
            "setupEnvironment();",
        ]
        return "\n".join(script)
    
    async def _generate_shell_setup_script(self) -> str:
        """Unix/Linux 셸 설정 스크립트 생성"""
        script = [
            "#!/bin/bash",
            "",
            "# AI 환경 설정 스크립트",
            "",
            "set -e",
            "",
            "echo \"AI 환경 설정을 시작합니다...\"",
            "",
            "# 필요한 디렉토리 생성",
            "mkdir -p models logs",
            "",
            "# Python 프로젝트인 경우",
            "if [ -f \"requirements.txt\" ] || [ -f \"requirements-ai.txt\" ]; then",
            "    echo \"Python 종속성을 설치하는 중...\"",
            "    if [ -f \"requirements-ai.txt\" ]; then",
            "        pip install -r requirements-ai.txt",
            "    fi",
            "fi",
            "",
            "# Node.js 프로젝트인 경우",
            "if [ -f \"package.json\" ]; then",
            "    echo \"Node.js 종속성을 설치하는 중...\"",
            "    npm install",
            "fi",
            "",
            "# 환경 변수 설정",
            "if [ ! -f \".env\" ] && [ -f \".env.example\" ]; then",
            "    echo \".env 파일을 생성하는 중...\"",
            "    cp .env.example .env",
            "fi",
            "",
            "# 모델 다운로드",
            "if [ \"$1\" == \"--download-models\" ]; then",
            "    echo \"모델을 다운로드하는 중...\"",
            "    if [ -f \"scripts/download_models.py\" ]; then",
            "        python scripts/download_models.py",
            "    elif [ -f \"scripts/download-models.js\" ]; then",
            "        node scripts/download-models.js",
            "    fi",
            "fi",
            "",
            "echo \"AI 환경 설정이 완료되었습니다!\"",
        ]
        return "\n".join(script)
    
    async def _generate_batch_setup_script(self) -> str:
        """Windows 배치 설정 스크립트 생성"""
        script = [
            "@echo off",
            "",
            "echo AI 환경 설정을 시작합니다...",
            "",
            ":: 필요한 디렉토리 생성",
            "if not exist models mkdir models",
            "if not exist logs mkdir logs",
            "",
            ":: Python 프로젝트인 경우",
            "if exist requirements-ai.txt (",
            "    echo Python 종속성을 설치하는 중...",
            "    pip install -r requirements-ai.txt",
            ")",
            "",
            ":: Node.js 프로젝트인 경우",
            "if exist package.json (",
            "    echo Node.js 종속성을 설치하는 중...",
            "    npm install",
            ")",
            "",
            ":: 환경 변수 설정",
            "if not exist .env (",
            "    if exist .env.example (",
            "        echo .env 파일을 생성하는 중...",
            "        copy .env.example .env",
            "    )",
            ")",
            "",
            ":: 모델 다운로드",
            "if \"%1\"==\"--download-models\" (",
            "    echo 모델을 다운로드하는 중...",
            "    if exist scripts\\download_models.py (",
            "        python scripts\\download_models.py",
            "    ) else (",
            "        if exist scripts\\download-models.js (",
            "            node scripts\\download-models.js",
            "        )",
            "    )",
            ")",
            "",
            "echo AI 환경 설정이 완료되었습니다!",
        ]
        return "\n".join(script)
    
    async def _generate_ci_workflow(self) -> str:
        """CI 워크플로우 생성"""
        workflow = [
            "name: AI CI",
            "",
            "on:",
            "  push:",
            "    branches: [ main, dev ]",
            "    paths:",
            "      - '**.py'",
            "      - '**.js'",
            "      - 'requirements*.txt'",
            "      - 'package*.json'",
            "  pull_request:",
            "    branches: [ main ]",
            "",
            "jobs:",
            "  test:",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - uses: actions/checkout@v2",
            "",
            "      - name: Set up Python",
            "        uses: actions/setup-python@v2",
            "        with:",
            "          python-version: '3.9'",
            "",
            "      - name: Install dependencies",
            "        run: |",
            "          python -m pip install --upgrade pip",
            "          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi",
            "          if [ -f requirements-ai.txt ]; then pip install -r requirements-ai.txt; fi",
            "          pip install pytest pytest-cov",
            "",
            "      - name: Run tests",
            "        run: |",
            "          pytest --cov=. --cov-report=xml",
            "",
            "      - name: Upload coverage to Codecov",
            "        uses: codecov/codecov-action@v1",
        ]
        return "\n".join(workflow)
    
    async def _generate_training_workflow(self) -> str:
        """훈련 워크플로우 생성"""
        workflow = [
            "name: Model Training",
            "",
            "on:",
            "  workflow_dispatch:",
            "    inputs:",
            "      model_type:",
            "        description: '훈련할 모델 유형'",
            "        required: true",
            "        default: 'default'",
            "        type: choice",
            "        options:",
            "          - default",
            "          - large",
            "          - custom",
            "      epochs:",
            "        description: '훈련 에폭 수'",
            "        required: true",
            "        default: '10'",
            "      use_gpu:",
            "        description: 'GPU 사용 여부'",
            "        type: boolean",
            "        default: true",
            "",
            "jobs:",
            "  train:",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - uses: actions/checkout@v2",
            "",
            "      - name: Set up Python",
            "        uses: actions/setup-python@v2",
            "        with:",
            "          python-version: '3.9'",
            "",
            "      - name: Install dependencies",
            "        run: |",
            "          python -m pip install --upgrade pip",
            "          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi",
            "          if [ -f requirements-ai.txt ]; then pip install -r requirements-ai.txt; fi",
            "",
            "      - name: Train model",
            "        run: |",
            "          python scripts/train_model.py --model-type=${{ github.event.inputs.model_type }} --epochs=${{ github.event.inputs.epochs }} ${{ github.event.inputs.use_gpu && '--gpu' || '' }}",
            "",
            "      - name: Upload model artifacts",
            "        uses: actions/upload-artifact@v2",
            "        with:",
            "          name: trained-model",
            "          path: models/",
        ]
        return "\n".join(workflow)
    
    async def _generate_deployment_workflow(self) -> str:
        """배포 워크플로우 생성"""
        workflow = [
            "name: Model Deployment",
            "",
            "on:",
            "  workflow_dispatch:",
            "    inputs:",
            "      environment:",
            "        description: '배포 환경'",
            "        required: true",
            "        default: 'staging'",
            "        type: choice",
            "        options:",
            "          - staging",
            "          - production",
            "      model_version:",
            "        description: '모델 버전'",
            "        required: true",
            "        default: 'latest'",
            "",
            "jobs:",
            "  deploy:",
            "    runs-on: ubuntu-latest",
            "    environment: ${{ github.event.inputs.environment }}",
            "    steps:",
            "      - uses: actions/checkout@v2",
            "",
            "      - name: Set up Docker Buildx",
            "        uses: docker/setup-buildx-action@v1",
            "",
            "      - name: Login to Docker Hub",
            "        uses: docker/login-action@v1",
            "        with:",
            "          username: ${{ secrets.DOCKER_HUB_USERNAME }}",
            "          password: ${{ secrets.DOCKER_HUB_TOKEN }}",
            "",
            "      - name: Build and push",
            "        uses: docker/build-push-action@v2",
            "        with:",
            "          context: .",
            "          file: ./Dockerfile.ai",
            "          push: true",
            "          tags: ${{ secrets.DOCKER_HUB_USERNAME }}/ai-model:${{ github.event.inputs.model_version }}",
            "",
            "      - name: Deploy model",
            "        run: |",
            "          echo \"Deploying model to ${{ github.event.inputs.environment }}...\"",
            "          if [ \"${{ github.event.inputs.environment }}\" == \"production\" ]; then",
            "            # 프로덕션 배포 명령",
            "            echo \"Production deployment command here\"",
            "          else",
            "            # 스테이징 배포 명령",
            "            echo \"Staging deployment command here\"",
            "          fi",
        ]
        return "\n".join(workflow)
    
    async def _generate_integration_guide(self) -> str:
        """통합 가이드 생성"""
        guide = [
            "# AI 통합 가이드",
            "",
            "이 가이드는 프로젝트에 AI 기능을 통합하는 방법을 설명합니다.",
            "",
            "## 목차",
            "",
            "1. [시작하기](#시작하기)",
            "2. [환경 설정](#환경-설정)",
            "3. [모델 사용하기](#모델-사용하기)",
            "4. [모델 훈련하기](#모델-훈련하기)",
            "5. [배포하기](#배포하기)",
            "6. [문제 해결](#문제-해결)",
            "",
            "## 시작하기",
            "",
            "이 프로젝트는 다음과 같은 AI 기능을 포함하고 있습니다:",
            "",
            "- 이미지 분류",
            "- 텍스트 생성",
            "- 감정 분석",
            "",
            "## 환경 설정",
            "",
            "### 종속성 설치",
            "",
            "```bash",
            "# Python 프로젝트",
            "pip install -r requirements-ai.txt",
            "",
            "# 또는 JavaScript 프로젝트",
            "npm install",
            "```",
            "",
            "### 설정 스크립트 실행",
            "",
            "```bash",
            "# Unix/Linux/macOS",
            "./scripts/setup-ai-env.sh",
            "",
            "# Windows",
            ".\\scripts\\setup-ai-env.bat",
            "",
            "# 모델 다운로드 포함",
            "./scripts/setup-ai-env.sh --download-models",
            "```",
            "",
            "## 모델 사용하기",
            "",
            "### 예시 코드",
            "",
            "```python",
            "from app.models import load_model",
            "",
            "# 모델 로드",
            "model = load_model('image_classifier')",
            "",
            "# 예측 수행",
            "result = model.predict(image_data)",
            "```",
            "",
            "## 모델 훈련하기",
            "",
            "### 로컬 훈련",
            "",
            "```bash",
            "python scripts/train_model.py --model-type=default --epochs=10",
            "```",
            "",
            "### GitHub Actions 사용",
            "",
            "1. GitHub 저장소의 'Actions' 탭으로 이동",
            "2. 'Model Training' 워크플로우 선택",
            "3. 'Run workflow' 버튼 클릭",
            "4. 필요한 매개변수 입력 후 실행",
            "",
            "## 배포하기",
            "",
            "### Docker로 배포",
            "",
            "```bash",
            "docker-compose -f docker-compose.ai.yml up -d",
            "```",
            "",
            "### GitHub Actions로 배포",
            "",
            "1. GitHub 저장소의 'Actions' 탭으로 이동",
            "2. 'Model Deployment' 워크플로우 선택",
            "3. 'Run workflow' 버튼 클릭",
            "4. 배포 환경과 모델 버전 선택 후 실행",
            "",
            "## 문제 해결",
            "",
            "### 일반적인 오류",
            "",
            "- **ModuleNotFoundError**: `pip install -r requirements-ai.txt`를 실행했는지 확인",
            "- **CUDA 오류**: GPU 설정과 CUDA 호환성 확인",
            "- **메모리 부족**: 배치 크기 감소 또는 더 작은 모델 사용",
            "",
            "### 지원 받기",
            "",
            "문제가 지속되면 이슈를 제출하거나 기술 지원팀에 문의하세요.",
        ]
        return "\n".join(guide)


async def generate_ai_setup(repo_id: str, repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI 환경 설정 생성 함수
    
    Args:
        repo_id: 저장소 ID
        repo_analysis: 저장소 분석 결과
        
    Returns:
        생성된 AI 환경 설정
    """
    generator = AISetupGenerator(repo_analysis)
    setup = await generator.generate_setup()
    
    return setup
