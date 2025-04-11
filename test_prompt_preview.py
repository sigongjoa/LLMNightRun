import requests

def test_prompt_preview():
    try:
        payload = {
            "template": "Hello, my name is {{name}}.",
            "variables": {"name": "John"}
        }
        response = requests.post("http://localhost:8000/prompt-engineering/preview", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing prompt preview...")
    test_prompt_preview()
