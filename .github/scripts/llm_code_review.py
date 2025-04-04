#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import requests
from typing import List, Dict, Any, Optional

# API 클라이언트 설정
try:
    import openai
    import anthropic
    
    # OpenAI API 키 설정
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    
    # PR 정보 가져오기
    PR_NUMBER = os.environ.get("PR_NUMBER")
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    REPO = os.environ.get("GITHUB_REPOSITORY")  # 예: owner/repo
    
    # 변경된 파일 목록
    CHANGED_FILES = os.environ.get("CHANGED_FILES", "").split(",")
except ImportError:
    print("필요한 라이브러리를 설치하세요: pip install openai anthropic")
    sys.exit(1)
except KeyError:
    print("필요한 환경 변수가 설정되지 않았습니다.")
    sys.exit(1)

# GitHub API URL
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}"

def get_file_diff(file_path: str) -> str:
    """지정된 파일의 diff를 가져옵니다."""
    try:
        result = subprocess.run(
            ["git", "diff", "origin/main", "--", file_path], 
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting diff for {file_path}: {e}")
        return ""

def get_file_content(file_path: str) -> str:
    """현재 브랜치의 파일 내용을 가져옵니다."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def get_openai_review(code_diff: str, file_path: str) -> str:
    """OpenAI GPT를 사용하여 코드 리뷰를 수행합니다."""
    try:
        file_extension = os.path.splitext(file_path)[1]
        
        prompt = f"""
        아래는 PR의 일부로 변경된 코드의 diff입니다. 파일: {file_path}
        
        ```{file_extension}
        {code_diff}
        ```
        
        이 코드 변경사항을 분석하고 다음 사항에 중점을 두어 리뷰해주세요:
        1. 잠재적인 버그나 오류
        2. 코드 품질과 가독성 향상을 위한 제안
        3. 성능 최적화 가능성
        4. 보안 취약점
        5. 테스트 가능성
        
        중요한 문제점만 지적하고, 트리비얼한 스타일 이슈는 무시하세요.
        GitHub PR 코멘트로 사용될 수 있도록 마크다운 형식으로 응답해주세요.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 경험이 풍부한 소프트웨어 엔지니어로, 코드 리뷰를 수행하고 있습니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 오류: {e}")
        return f"OpenAI를 사용한 코드 리뷰 중 오류가 발생했습니다: {str(e)}"

def post_github_comment(review_content: str, file_path: str) -> None:
    """GitHub PR에 리뷰 코멘트를 작성합니다."""
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "body": f"## LLM 코드 리뷰: `{file_path}`\n\n{review_content}\n\n*이 리뷰는 자동으로 생성되었습니다.*"
        }
        
        response = requests.post(
            f"{GITHUB_API_URL}/issues/{PR_NUMBER}/comments",
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            print(f"파일에 대한 리뷰 코멘트 작성 성공: {file_path}")
        else:
            print(f"GitHub API 오류: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"GitHub 코멘트 게시 중 오류 발생: {e}")

def main():
    """메인 함수: 변경된 파일을 확인하고 LLM 코드 리뷰를 수행합니다."""
    print("LLM 코드 리뷰 시작")
    
    review_count = 0
    
    for file_path in CHANGED_FILES:
        # 빈 파일이거나 지원하지 않는 형식은 건너뜁니다
        if not file_path or file_path.strip() == "":
            continue
            
        # 코드 파일만 리뷰합니다
        supported_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.java', '.c', '.cpp', '.go']
        if not any(file_path.endswith(ext) for ext in supported_extensions):
            print(f"지원하지 않는 파일 형식, 건너뜁니다: {file_path}")
            continue
            
        print(f"파일 처리 중: {file_path}")
        
        # 파일 diff 가져오기
        diff = get_file_diff(file_path)
        
        # diff가 너무 작거나 없으면 건너뜁니다
        if len(diff) < 50:
            print(f"변경 사항이 너무 작습니다, 건너뜁니다: {file_path}")
            continue
            
        # OpenAI를 사용한 코드 리뷰
        review = get_openai_review(diff, file_path)
        
        # PR에 코멘트 작성
        post_github_comment(review, file_path)
        
        review_count += 1
        
        # API 비용 절감을 위해 최대 5개 파일로 제한
        if review_count >= 5:
            print("최대 파일 수 제한에 도달했습니다")
            break
    
    print(f"LLM 코드 리뷰 완료: {review_count}개 파일 처리됨")

if __name__ == "__main__":
    main()