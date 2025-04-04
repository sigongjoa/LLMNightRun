#!/usr/bin/env python3
import os
import json
import glob
import requests
import xml.etree.ElementTree as ET

# API 클라이언트 설정
try:
    import openai
    
    # OpenAI API 키 설정
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    
    # 환경 변수
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    WORKFLOW_NAME = os.environ.get("WORKFLOW_NAME")
    REPO_OWNER = os.environ.get("REPO_OWNER")
    REPO_NAME = os.environ.get("REPO_NAME")
    RUN_ID = os.environ.get("RUN_ID")
    REPO = f"{REPO_OWNER}/{REPO_NAME}"
    
except ImportError:
    print("필요한 라이브러리를 설치하세요: pip install openai requests")
    exit(1)
except KeyError:
    print("필요한 환경 변수가 설정되지 않았습니다.")
    exit(1)

# GitHub API URL
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}"

def parse_junit_xml(file_path):
    """
    JUnit XML 테스트 결과 파일을 파싱하여 실패한 테스트 정보를 추출합니다.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        failures = []
        
        # 테스트 케이스 반복
        for testsuite in root.findall(".//testsuite"):
            for testcase in testsuite.findall("testcase"):
                failure = testcase.find("failure")
                error = testcase.find("error")
                
                if failure is not None or error is not None:
                    # 실패 정보 추출
                    failure_element = failure if failure is not None else error
                    failure_message = failure_element.get("message", "알 수 없는 오류")
                    failure_text = failure_element.text or "세부 정보 없음"
                    
                    failures.append({
                        "class": testcase.get("classname", "Unknown"),
                        "name": testcase.get("name", "Unknown"),
                        "message": failure_message,
                        "details": failure_text
                    })
        
        return failures
    except Exception as e:
        print(f"XML 파싱 오류: {e}")
        return []

def parse_json_results(file_path):
    """
    JSON 형식의 테스트 결과 파일을 파싱합니다.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        failures = []
        
        # Jest 또는 다른 JSON 형식의 결과 파싱
        if "testResults" in data:
            for test_suite in data["testResults"]:
                for test_result in test_suite.get("assertionResults", []):
                    if test_result.get("status") == "failed":
                        failures.append({
                            "class": test_suite.get("name", "Unknown"),
                            "name": test_result.get("title", "Unknown"),
                            "message": test_result.get("failureMessages", ["알 수 없는 오류"])[0],
                            "details": "\n".join(test_result.get("failureMessages", []))
                        })
        return failures
    except Exception as e:
        print(f"JSON 파싱 오류: {e}")
        return []

def get_test_failures():
    """
    테스트 결과 디렉토리에서 모든 테스트 실패 정보를 수집합니다.
    """
    failures = []
    
    # XML 파일 검색
    for xml_file in glob.glob("test-results/**/*.xml", recursive=True):
        failures.extend(parse_junit_xml(xml_file))
    
    # JSON 파일 검색
    for json_file in glob.glob("test-results/**/*.json", recursive=True):
        failures.extend(parse_json_results(json_file))
    
    return failures

def analyze_failures_with_llm(failures):
    """
    LLM을 사용하여 테스트 실패 원인과 해결 방안을 분석합니다.
    """
    if not failures:
        return "테스트 실패 정보가 없습니다."
    
    # 실패 정보 포맷팅
    failures_text = ""
    for i, failure in enumerate(failures, 1):
        failures_text += f"\n{i}. 테스트: {failure['name']} ({failure['class']})\n"
        failures_text += f"   실패 메시지: {failure['message']}\n"
        failures_text += f"   세부 정보: {failure['details'][:500]}...(생략)\n"
    
    # GPT-4를 사용한 분석
    try:
        prompt = f"""
        다음은 CI 파이프라인에서 실패한 테스트 목록입니다:
        
        {failures_text}
        
        각 테스트 실패에 대해 다음 정보를 제공해주세요:
        1. 가능한 실패 원인
        2. 해결책 제안
        3. 코드 수정 예시 (적절한 경우)
        
        마크다운 형식으로 명확하고 간결하게 응답해주세요.
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "당신은 소프트웨어 테스트 및 디버깅 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API 오류: {e}")
        return f"테스트 실패 분석 중 오류가 발생했습니다: {str(e)}"

def create_github_issue(analysis):
    """
    GitHub에 테스트 실패 분석 이슈를 생성합니다.
    """
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        workflow_url = f"https://github.com/{REPO}/actions/runs/{RUN_ID}"
        
        data = {
            "title": f"테스트 실패 분석: {WORKFLOW_NAME}",
            "body": f"""
# 테스트 실패 자동 분석

## 워크플로우 정보
- **워크플로우**: [{WORKFLOW_NAME}]({workflow_url})
- **실행 ID**: {RUN_ID}

## 분석 결과

{analysis}

---
*이 이슈는 자동으로 생성되었습니다.*
            """,
            "labels": ["test-failure", "automated", "ci-cd"]
        }
        
        response = requests.post(
            f"{GITHUB_API_URL}/issues",
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            print(f"GitHub 이슈 생성 성공: {response.json()['html_url']}")
        else:
            print(f"GitHub API 오류: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"GitHub 이슈 생성 중 오류 발생: {e}")

def main():
    """
    메인 함수: 테스트 실패를 분석하고 GitHub 이슈를 생성합니다.
    """
    print("테스트 실패 분석 시작")
    
    # 테스트 실패 정보 수집
    failures = get_test_failures()
    print(f"{len(failures)}개의 테스트 실패를 발견했습니다.")
    
    if not failures:
        print("분석할 테스트 실패가 없습니다.")
        return
    
    # LLM을 사용한 분석
    analysis = analyze_failures_with_llm(failures)
    print("분석 완료")
    
    # GitHub 이슈 생성
    create_github_issue(analysis)
    print("처리 완료")

if __name__ == "__main__":
    main()