"""
실행 스크립트 생성 모듈

이 모듈은 모델 실행 스크립트를 자동으로 생성합니다.
"""

import os
import platform
import logging
from typing import Dict, List, Optional, Any, Tuple


logger = logging.getLogger(__name__)


class LauncherGenerator:
    """모델 실행 스크립트를 생성하는 클래스"""
    
    def __init__(self, model_dir: str, model_name: str):
        """
        초기화 함수
        
        Args:
            model_dir: 모델 디렉토리 경로
            model_name: 모델 이름
        """
        self.model_dir = model_dir
        self.model_name = model_name
        self.scripts_dir = os.path.join(model_dir, "scripts")
        self.is_windows = platform.system() == "Windows"
        
        # 스크립트 디렉토리 생성
        os.makedirs(self.scripts_dir, exist_ok=True)
    
    def generate_run_script(self, launch_script: str, script_args: Optional[List[str]] = None) -> Tuple[str, str]:
        """
        실행 스크립트 생성
        
        Args:
            launch_script: 실행할 원본 스크립트 경로 (모델 디렉토리 내 상대 경로)
            script_args: 스크립트 실행 인자 (기본값: None)
            
        Returns:
            Tuple[str, str]: (Windows 배치 파일 경로, Unix 쉘 스크립트 경로)
        """
        if script_args is None:
            script_args = []
        
        # 원본 스크립트 경로 설정 (scripts 디렉토리 내 파일이거나 복사된 파일)
        if os.path.exists(os.path.join(self.scripts_dir, os.path.basename(launch_script))):
            script_path = os.path.join("scripts", os.path.basename(launch_script))
        else:
            script_path = launch_script
        
        # 스크립트 이름에서 확장자 제거
        script_name = os.path.basename(script_path)
        script_name_without_ext = os.path.splitext(script_name)[0]
        
        # Windows 배치 파일 생성
        bat_path = os.path.join(self.scripts_dir, f"run_{script_name_without_ext}.bat")
        with open(bat_path, 'w') as f:
            f.write('@echo off\n')
            f.write(f'cd /d "{self.model_dir}"\n')
            f.write(f'call "{os.path.join(self.model_dir, "venv", "Scripts", "activate.bat")}"\n')
            f.write(f'python "{script_path}" {" ".join(script_args)}\n')
            f.write('if errorlevel 1 (\n')
            f.write('    echo Error occurred while running the script.\n')
            f.write('    pause\n')
            f.write(')\n')
            f.write('echo Script completed.\n')
            f.write('pause\n')
        
        logger.info(f"Generated Windows run script: {bat_path}")
        
        # Unix 쉘 스크립트 생성
        sh_path = os.path.join(self.scripts_dir, f"run_{script_name_without_ext}.sh")
        with open(sh_path, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write(f'cd "{self.model_dir}"\n')
            f.write(f'source "{os.path.join(self.model_dir, "venv", "bin", "activate")}"\n')
            f.write(f'python "{script_path}" {" ".join(script_args)}\n')
            f.write('if [ $? -ne 0 ]; then\n')
            f.write('    echo "Error occurred while running the script."\n')
            f.write('    read -p "Press enter to continue"\n')
            f.write('fi\n')
            f.write('echo "Script completed."\n')
            f.write('read -p "Press enter to exit"\n')
        
        # Unix 파일의 경우 실행 권한 설정
        if not self.is_windows:
            os.chmod(sh_path, 0o755)
        
        logger.info(f"Generated Unix run script: {sh_path}")
        
        return bat_path, sh_path
    
    def generate_universal_launcher(self, scripts: List[str]) -> Tuple[str, str]:
        """
        여러 스크립트를 실행할 수 있는 통합 런처 생성
        
        Args:
            scripts: 실행 가능한 스크립트 목록
            
        Returns:
            Tuple[str, str]: (Windows 배치 파일 경로, Unix 쉘 스크립트 경로)
        """
        # Windows 배치 파일 생성
        bat_path = os.path.join(self.scripts_dir, f"launcher.bat")
        with open(bat_path, 'w') as f:
            f.write('@echo off\n')
            f.write(f'echo {self.model_name} Launcher\n')
            f.write('echo ===========================\n')
            f.write('echo Select a script to run:\n')
            
            for i, script in enumerate(scripts, 1):
                script_name = os.path.basename(script)
                f.write(f'echo {i}. {script_name}\n')
            
            f.write(f'echo {len(scripts) + 1}. Exit\n')
            f.write('echo ===========================\n')
            f.write('set /p choice="Enter your choice (1-%d): "\n' % (len(scripts) + 1))
            
            for i, script in enumerate(scripts, 1):
                script_name = os.path.basename(script)
                script_path = os.path.join("scripts", f"run_{os.path.splitext(script_name)[0]}.bat")
                f.write(f'if "%choice%"=="{i}" call "{script_path}"\n')
            
            f.write(f'if "%choice%"=="{len(scripts) + 1}" exit\n')
            f.write('goto:eof\n')
        
        logger.info(f"Generated Windows universal launcher: {bat_path}")
        
        # Unix 쉘 스크립트 생성
        sh_path = os.path.join(self.scripts_dir, f"launcher.sh")
        with open(sh_path, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write(f'echo "{self.model_name} Launcher"\n')
            f.write('echo "==========================="\n')
            f.write('echo "Select a script to run:"\n')
            
            for i, script in enumerate(scripts, 1):
                script_name = os.path.basename(script)
                f.write(f'echo "{i}. {script_name}"\n')
            
            f.write(f'echo "{len(scripts) + 1}. Exit"\n')
            f.write('echo "==========================="\n')
            f.write('read -p "Enter your choice (1-%d): " choice\n' % (len(scripts) + 1))
            
            f.write('case $choice in\n')
            for i, script in enumerate(scripts, 1):
                script_name = os.path.basename(script)
                script_path = os.path.join("scripts", f"run_{os.path.splitext(script_name)[0]}.sh")
                f.write(f'    {i}) bash "{script_path}" ;;\n')
            
            f.write(f'    {len(scripts) + 1}) exit ;;\n')
            f.write('    *) echo "Invalid choice." ;;\n')
            f.write('esac\n')
        
        # Unix 파일의 경우 실행 권한 설정
        if not self.is_windows:
            os.chmod(sh_path, 0o755)
        
        logger.info(f"Generated Unix universal launcher: {sh_path}")
        
        return bat_path, sh_path
    
    def generate_readme(self, model_info: Dict[str, Any], launch_scripts: List[str]) -> str:
        """
        README 파일 생성
        
        Args:
            model_info: 모델 정보
            launch_scripts: 실행 스크립트 목록
            
        Returns:
            str: README 파일 경로
        """
        readme_path = os.path.join(self.model_dir, "README.md")
        
        with open(readme_path, 'w') as f:
            f.write(f"# {self.model_name}\n\n")
            
            # 모델 정보
            f.write("## 모델 정보\n\n")
            
            if "model_type" in model_info and "primary" in model_info["model_type"]:
                f.write(f"- **모델 유형**: {model_info['model_type']['primary']}\n")
            
            if "repo_url" in model_info:
                f.write(f"- **원본 저장소**: [{model_info['repo_url']}]({model_info['repo_url']})\n")
            
            f.write("\n")
            
            # 설치 방법
            f.write("## 설치 및 실행 방법\n\n")
            f.write("### 환경 설정\n\n")
            f.write("1. 가상 환경 활성화:\n")
            f.write("   - Windows: `scripts\\activate_env.bat`\n")
            f.write("   - Linux/Mac: `source scripts/activate_env.sh`\n\n")
            
            # 실행 방법
            f.write("### 실행 방법\n\n")
            f.write("다음 방법 중 하나로 모델을 실행할 수 있습니다:\n\n")
            
            f.write("1. 통합 런처 사용:\n")
            f.write("   - Windows: `scripts\\launcher.bat`\n")
            f.write("   - Linux/Mac: `bash scripts/launcher.sh`\n\n")
            
            f.write("2. 개별 스크립트 사용:\n")
            for script in launch_scripts:
                script_name = os.path.basename(script)
                script_name_without_ext = os.path.splitext(script_name)[0]
                f.write(f"   - {script_name}:\n")
                f.write(f"     - Windows: `scripts\\run_{script_name_without_ext}.bat`\n")
                f.write(f"     - Linux/Mac: `bash scripts/run_{script_name_without_ext}.sh`\n")
            
            f.write("\n")
            
            # 디렉토리 구조
            f.write("## 디렉토리 구조\n\n")
            f.write("```\n")
            f.write(f"{self.model_name}/\n")
            f.write("├── config/       # 설정 파일\n")
            f.write("├── data/         # 데이터 파일\n")
            f.write("├── scripts/      # 실행 스크립트\n")
            f.write("├── venv/         # 가상 환경\n")
            f.write("└── weights/      # 모델 가중치 파일\n")
            f.write("```\n")
        
        logger.info(f"Generated README at {readme_path}")
        
        return readme_path
