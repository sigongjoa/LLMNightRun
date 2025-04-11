import requests
import json

def test_get_templates():
    try:
        response = requests.get("http://localhost:8000/prompt-templates/")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def test_create_template():
    try:
        template_data = {
            "name": "테스트 템플릿",
            "content": "{{name}}님, 안녕하세요! {{topic}}에 대해 설명해 주세요.",
            "system_prompt": "당신은 친절한 AI 비서입니다. 한국어로 상세하게 답변해 주세요.",
            "description": "테스트 용 템플릿입니다.",
            "category": "테스트",
            "tags": ["테스트", "안내"],
            "template_variables": ["name", "topic"]
        }
        
        response = requests.post(
            "http://localhost:8000/prompt-templates/", 
            json=template_data
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code in (200, 201):
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

def test_get_template(template_id):
    try:
        response = requests.get(f"http://localhost:8000/prompt-templates/{template_id}")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    print("----- GET 템플릿 목록 테스트 -----")
    test_get_templates()
    
    print("\n----- POST 템플릿 생성 테스트 -----")
    test_create_template()
    
    print("\n----- GET 템플릿 목록 테스트 (생성 후) -----")
    test_get_templates()
    
    print("\n----- GET 템플릿 상세 조회 테스트 -----")
    test_get_template(1)
