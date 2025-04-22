"""
코드 분석 모듈

GitHub 저장소의 코드를 분석하여 구조, 함수, 클래스 등의 정보를 추출합니다.
"""

import os
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict

from core.logging import get_logger
from .language_utils import get_language_from_extension, FILE_EXTENSIONS
from .analyzers.python_analyzer import analyze_python_file
from .analyzers.javascript_analyzer import analyze_javascript_file
from .analyzers.file_stats import get_file_content_stats

logger = get_logger("github_docs.code_analyzer")

def analyze_repository(repo_path: str) -> Dict[str, Any]:
    """
    저장소 코드 분석
    
    Args:
        repo_path: 저장소 경로
    
    Returns:
        분석 결과 딕셔너리
    """
    logger.info(f"저장소 분석 중: {repo_path}")
    
    # 결과 딕셔너리
    result = {
        "repo_path": repo_path,
        "file_count": 0,
        "language_stats": defaultdict(int),
        "file_stats": [],
        "modules": [],
        "functions": [],
        "classes": [],
        "dependencies": set()
    }
    
    # 파일 목록 가져오기
    for root, dirs, files in os.walk(repo_path):
        # .git 디렉토리 건너뛰기
        if ".git" in dirs:
            dirs.remove(".git")
        
        # 가상 환경 디렉토리 건너뛰기
        venv_dirs = [d for d in dirs if d in ["venv", "env", "__pycache__", "node_modules"]]
        for d in venv_dirs:
            if d in dirs:
                dirs.remove(d)
        
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, repo_path)
            
            # 파일 언어 확인
            language = get_language_from_extension(file_path)
            
            if language:
                result["language_stats"][language] += 1
                result["file_count"] += 1
                
                # 파일 정보
                file_info = {
                    "path": relative_path,
                    "language": language,
                    "size": os.path.getsize(file_path)
                }
                
                # 언어별 분석
                if language == "python":
                    python_info = analyze_python_file(file_path, relative_path)
                    file_info.update(python_info)
                    
                    # 모듈, 함수, 클래스 정보 추가
                    if "module_name" in python_info:
                        result["modules"].append(python_info)
                    
                    if "functions" in python_info:
                        result["functions"].extend(python_info["functions"])
                    
                    if "classes" in python_info:
                        result["classes"].extend(python_info["classes"])
                    
                    # 의존성 추가
                    if "imports" in python_info:
                        result["dependencies"].update(python_info["imports"])
                
                elif language == "javascript":
                    js_info = analyze_javascript_file(file_path, relative_path)
                    file_info.update(js_info)
                    
                    # 함수, 클래스 정보 추가
                    if "functions" in js_info:
                        result["functions"].extend(js_info["functions"])
                    
                    if "classes" in js_info:
                        result["classes"].extend(js_info["classes"])
                
                # 기타 언어 분석은 필요에 따라 추가
                
                result["file_stats"].append(file_info)
    
    # Set을 리스트로 변환 (JSON 직렬화를 위해)
    result["dependencies"] = list(result["dependencies"])
    
    # 언어 통계를 딕셔너리로 변환
    result["language_stats"] = dict(result["language_stats"])
    
    logger.info(f"저장소 분석 완료: {result['file_count']} 파일")
    return result

def get_repository_structure(repo_path: str) -> Dict[str, Any]:
    """
    저장소 구조 정보 추출
    
    Args:
        repo_path: 저장소 경로
    
    Returns:
        저장소 구조 딕셔너리
    """
    def create_node(name):
        return {"name": name, "type": "directory", "children": []}
    
    root = create_node(os.path.basename(repo_path))
    
    # 스택을 사용한 디렉토리 트리 구축
    for current_dir, dirs, files in os.walk(repo_path):
        # .git 디렉토리 건너뛰기
        if ".git" in dirs:
            dirs.remove(".git")
        
        # 가상 환경 디렉토리 건너뛰기
        venv_dirs = [d for d in dirs if d in ["venv", "env", "__pycache__", "node_modules"]]
        for d in venv_dirs:
            if d in dirs:
                dirs.remove(d)
        
        # 현재 경로에서 저장소 루트 이후의 상대 경로 계산
        relative_path = os.path.relpath(current_dir, repo_path)
        if relative_path == ".":
            current_node = root
        else:
            # 상대 경로의 각 부분으로 노드 검색
            path_parts = relative_path.split(os.sep)
            current_node = root
            
            for part in path_parts:
                found = False
                for child in current_node["children"]:
                    if child["name"] == part and child["type"] == "directory":
                        current_node = child
                        found = True
                        break
                
                if not found:
                    # 없으면 새 노드 생성
                    new_node = create_node(part)
                    current_node["children"].append(new_node)
                    current_node = new_node
        
        # 파일 노드 추가
        for file in files:
            file_type = "file"
            file_path = os.path.join(current_dir, file)
            language = get_language_from_extension(file_path)
            size = os.path.getsize(file_path)
            
            file_node = {
                "name": file,
                "type": file_type,
                "size": size
            }
            
            if language:
                file_node["language"] = language
            
            current_node["children"].append(file_node)
    
    return root

def find_entry_points(repo_path: str) -> List[str]:
    """
    저장소의 주요 진입점 찾기
    
    Args:
        repo_path: 저장소 경로
    
    Returns:
        진입점 파일 경로 목록
    """
    entry_points = []
    
    # 일반적인 진입점 파일 이름
    common_entry_points = [
        "main.py", "app.py", "server.py", "run.py", "start.py", "cli.py",
        "index.js", "server.js", "app.js", "main.js",
        "Main.java", "App.java", "Application.java",
        "main.go", "app.go"
    ]
    
    # setup.py 또는 package.json 확인
    setup_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file in common_entry_points:
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                entry_points.append(rel_path)
            
            if file in ["setup.py", "package.json", "pom.xml", "build.gradle", "Makefile"]:
                rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                setup_files.append(rel_path)
    
    # 루트 디렉토리의 파일 확인
    root_files = [f for f in os.listdir(repo_path) if os.path.isfile(os.path.join(repo_path, f))]
    
    # README 파일 추가
    readme_files = [f for f in root_files if f.lower().startswith("readme")]
    if readme_files:
        entry_points.extend(readme_files)
    
    # 설정 파일 추가
    entry_points.extend(setup_files)
    
    return entry_points
