"""
디버깅 스크립트: 환경 설정 과정을 단계별로 디버깅합니다.
"""

import os
import sys
import logging
import traceback

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    try:
        print("\n===== 환경 설정 디버깅 모드 =====\n")
        
        # 테스트할 GitHub 저장소
        repo_url = "https://github.com/karpathy/micrograd"
        
        # GitHubHandler 및 EnvironmentSetup 모듈 가져오기
        from src.utils.github_handler import GitHubHandler
        from src.utils.environment_setup import EnvironmentSetup
        
        # GitHub 핸들러 초기화
        github_config = {"repo_dir": "data/repos"}
        github_handler = GitHubHandler(github_config)
        
        # 저장소가 이미 클론되어 있는지 확인
        repo_name = "karpathy_micrograd"
        repo_path = os.path.join("data/repos", repo_name)
        
        if not os.path.exists(repo_path):
            print(f"저장소를 클론합니다: {repo_url}")
            repo_path = github_handler.clone_repository(repo_url)
        else:
            print(f"이미 클론된 저장소를 사용합니다: {repo_path}")
        
        # 환경 설정 단계별 실행
        try:
            print("\n----- 환경 설정 초기화 -----")
            env_config = {
                "venv_dir": "venv",
                "use_conda": False,
                "python_version": "3.8",
                "force_reinstall": True,  # 기존 환경 강제 재설치
                "detect_gpu": True
            }
            env_setup = EnvironmentSetup(env_config)
            
            print("\n----- 프레임워크 감지 중 -----")
            framework = env_setup._detect_framework(repo_path)
            print(f"감지된 프레임워크: {framework}")
            
            print("\n----- 환경 유형 결정 중 -----")
            env_type = env_setup._determine_env_type(repo_path)
            print(f"결정된 환경 유형: {env_type}")
            
            print("\n----- 요구사항 파일 찾기 중 -----")
            req_file = env_setup._find_requirements_file(repo_path)
            print(f"찾은 요구사항 파일: {req_file}")
            
            print("\n----- 가상 환경 디렉토리 확인 중 -----")
            venv_path = os.path.join(repo_path, env_config["venv_dir"])
            print(f"가상 환경 경로: {venv_path}")
            print(f"가상 환경 존재 여부: {os.path.exists(venv_path)}")
            
            if os.path.exists(venv_path) and env_config["force_reinstall"]:
                print("\n----- 기존 가상 환경 제거 중 -----")
                try:
                    import shutil
                    shutil.rmtree(venv_path)
                    print(f"기존 가상 환경 제거 완료: {venv_path}")
                except Exception as e:
                    print(f"가상 환경 제거 실패: {e}")
            
            print("\n----- 가상 환경 생성 중 -----")
            try:
                print(f"Python 실행 파일: {sys.executable}")
                print(f"명령어: {sys.executable} -m venv {venv_path}")
                
                import subprocess
                result = subprocess.run(
                    [sys.executable, "-m", "venv", venv_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if result.returncode == 0:
                    print("가상 환경 생성 성공")
                else:
                    print(f"가상 환경 생성 실패: {result.stderr}")
                    
            except Exception as e:
                print(f"가상 환경 생성 중 오류: {e}")
                traceback.print_exc()
            
            print("\n----- 환경 설정 경로 확인 -----")
            if os.name == 'nt':  # Windows
                pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
                python_path = os.path.join(venv_path, "Scripts", "python.exe")
            else:  # Linux/macOS
                pip_path = os.path.join(venv_path, "bin", "pip")
                python_path = os.path.join(venv_path, "bin", "python")
                
            pip_path = os.path.normpath(pip_path)
            python_path = os.path.normpath(python_path)
            
            print(f"pip 경로: {pip_path}")
            print(f"python 경로: {python_path}")
            print(f"pip 존재 여부: {os.path.exists(pip_path)}")
            print(f"python 존재 여부: {os.path.exists(python_path)}")
            
            print("\n----- 환경 정보 파일 생성 -----")
            env_info = {
                "type": "venv",
                "path": venv_path,
                "python_path": python_path,
                "pip_path": pip_path,
                "framework": framework,
                "requirements_file": req_file,
                "timestamp": __import__("datetime").datetime.now().isoformat()
            }
            
            env_info_path = os.path.join(repo_path, "env_info.json")
            import json
            with open(env_info_path, 'w', encoding='utf-8') as f:
                json.dump(env_info, f, ensure_ascii=False, indent=2)
                
            print(f"환경 정보 파일 생성 완료: {env_info_path}")
            print("\n환경 설정 디버깅 완료")
            
        except Exception as e:
            print(f"환경 설정 중 오류 발생: {e}")
            traceback.print_exc()
        
    except Exception as e:
        print(f"디버깅 스크립트 실행 중 오류 발생: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
