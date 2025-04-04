#!/usr/bin/env python3
import os
import re
import glob
import json
import subprocess
from datetime import datetime

# API 클라이언트 설정
try:
    import openai
    
    # OpenAI API 키 설정
    openai.api_key = os.environ.get("OPENAI_API_KEY")
except ImportError:
    print("필요한 라이브러리를 설치하세요: pip install openai")
    exit(1)

def get_changed_files():
    """
    최근 커밋에서 변경된 파일 목록을 가져옵니다.
    """
    try:
        # 기준 브랜치 (main 또는 develop)
        base_branch = "origin/main"
        current_branch = subprocess.getoutput("git rev-parse --abbrev-ref HEAD")
        
        if current_branch == "develop":
            base_branch = "origin/develop"
        
        # 변경된 파일 가져오기
        result = subprocess.run(
            ["git", "diff", "--name-only", base_branch, "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 파일 목록 반환
        return [f for f in result.stdout.splitlines() if os.path.exists(f)]
    except subprocess.CalledProcessError:
        # 이전 커밋이 없는 경우 (새 저장소)
        return glob.glob("**/*.*", recursive=True)

def filter_source_files(files):
    """
    문서화할 소스 파일만 필터링합니다.
    """
    source_extensions = ['.py', '.tsx', '.ts', '.js', '.jsx']
    excluded_dirs = ['node_modules', 'venv', '__pycache__', '.git']
    
    filtered_files = []
    for file in files:
        # 제외할 디렉토리 체크
        if any(excluded_dir in file for excluded_dir in excluded_dirs):
            continue
        
        # 확장자 체크
        ext = os.path.splitext(file)[1]
        if ext in source_extensions:
            filtered_files.append(file)
    
    return filtered_files

def get_file_content(file_path):
    """
    파일 내용을 가져옵니다.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"파일 읽기 오류 ({file_path}): {e}")
        return ""

def generate_file_documentation(file_path, content):
    """
    LLM을 사용하여 파일 문서를 생성합니다.
    """
    try:
        # 파일 유형 및 경로 정보
        file_ext = os.path.splitext(file_path)[1]
        file_type = {
            '.py': 'Python',
            '.tsx': 'TypeScript React',
            '.ts': 'TypeScript',
            '.js': 'JavaScript',
            '.jsx': 'JavaScript React'
        }.get(file_ext, 'Unknown')
        
        prompt = f"""
        다음은 '{file_path}' 파일의 내용입니다. 이 파일은 {file_type} 코드입니다.

        ```{file_ext}
        {content[:10000]}  # 내용이 너무 길면 앞부분만 사용
        ```

        이 파일에 대한 간결하고 명확한 마크다운 문서를 작성해주세요. 다음 내용을 포함해야 합니다:

        1. 파일의 주요 목적 및 책임
        2. 주요 클래스, 함수, 컴포넌트에 대한 설명
        3. 관련 모듈이나 의존성
        4. 사용 방법이나 중요한 참고 사항

        응답은 마크다운 형식이어야 하며, 코드 샘플은 포함하지 마세요.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 소프트웨어 문서 작성 전문가입니다. 명확하고 간결하게 기술적 문서를 작성합니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"문서 생성 오류 ({file_path}): {e}")
        return f"# {os.path.basename(file_path)}\n\n문서 생성 중 오류가 발생했습니다: {str(e)}"

def update_readme(changed_files):
    """
    README.md 파일을 업데이트합니다.
    """
    readme_path = "README.md"
    
    if os.path.exists(readme_path):
        readme_content = get_file_content(readme_path)
    else:
        readme_content = f"# {os.path.basename(os.getcwd())}\n\n프로젝트 설명이 필요합니다."
    
    try:
        # 최근 업데이트 정보 추가
        update_section = f"""
## 최근 업데이트
*마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

최근 변경된 파일:
"""
        
        # 변경된 파일 목록 추가
        for file in changed_files[:10]:  # 최대 10개만 표시
            update_section += f"- `{file}`\n"
        
        if len(changed_files) > 10:
            update_section += f"- *외 {len(changed_files) - 10}개 파일*\n"
        
        # README에 최근 업데이트 섹션 추가 또는 업데이트
        if "## 최근 업데이트" in readme_content:
            # 기존 섹션 업데이트
            pattern = r"## 최근 업데이트[\s\S]*?(?=##|$)"
            readme_content = re.sub(pattern, update_section, readme_content)
        else:
            # 새 섹션 추가
            readme_content += "\n" + update_section
        
        # 파일 저장
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
            
        print(f"README.md 업데이트 완료")
        return True
    except Exception as e:
        print(f"README 업데이트 오류: {e}")
        return False

def generate_module_documentation(files):
    """
    모듈별 문서를 생성합니다.
    """
    # 기존 문서 디렉토리 확인 또는 생성
    docs_dir = "docs"
    os.makedirs(docs_dir, exist_ok=True)
    
    # 생성된 문서 목록
    generated_docs = []
    
    # 모듈별 그룹화
    modules = {}
    for file in files:
        # 모듈 이름 추출 (첫 번째 디렉토리)
        parts = file.split('/')
        if len(parts) > 1:
            module = parts[0]
            if module not in modules:
                modules[module] = []
            modules[module].append(file)
    
    # 모듈별 문서 생성
    for module, module_files in modules.items():
        module_doc_path = os.path.join(docs_dir, f"{module}.md")
        
        # 모듈 문서 헤더
        module_doc = f"# {module.title()} 모듈 문서\n\n"
        module_doc += f"*생성일: {datetime.now().strftime('%Y-%m-%d')}*\n\n"
        module_doc += f"## 개요\n\n{module} 모듈은 다음 파일들로 구성되어 있습니다:\n\n"
        
        # 파일 목록
        for file in module_files:
            module_doc += f"- [{file}](#{file.replace('/', '-').replace('.', '-')})\n"
        
        module_doc += "\n## 파일별 설명\n\n"
        
        # 파일별 문서 생성
        for file in module_files:
            print(f"'{file}' 파일 문서 생성 중...")
            content = get_file_content(file)
            file_doc = generate_file_documentation(file, content)
            
            file_anchor = file.replace('/', '-').replace('.', '-')
            module_doc += f"<a id='{file_anchor}'></a>\n"
            module_doc += f"### {file}\n\n"
            module_doc += file_doc
            module_doc += "\n\n---\n\n"
        
        # 파일 저장
        with open(module_doc_path, 'w', encoding='utf-8') as f:
            f.write(module_doc)
        
        generated_docs.append(module_doc_path)
        print(f"'{module_doc_path}' 문서 생성 완료")
    
    return generated_docs

def main():
    """
    메인 함수: 변경된 파일을 감지하고 문서를 생성합니다.
    """
    print("자동 문서 생성 시작")
    
    # 변경된 파일 가져오기
    all_changed_files = get_changed_files()
    print(f"{len(all_changed_files)}개의 변경된 파일 감지")
    
    # 소스 파일 필터링
    source_files = filter_source_files(all_changed_files)
    print(f"{len(source_files)}개의 소스 파일 문서화 대상")
    
    if not source_files:
        print("문서화할 파일이 없습니다.")
        return
    
    # README.md 업데이트
    update_readme(all_changed_files)
    
    # 모듈별 문서 생성
    generated_docs = generate_module_documentation(source_files)
    print(f"{len(generated_docs)}개의 문서 파일 생성 완료")

if __name__ == "__main__":
    main()