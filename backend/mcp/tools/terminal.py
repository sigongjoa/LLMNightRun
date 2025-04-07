"""
LLMNightRun에서 터미널 기능은 비활성화 되었습니다.
"""

class TerminalTool:
    """
    터미널 기능 대체 클래스 (비활성화됨)
    """
    def __init__(self, *args, **kwargs):
        pass
        
    def create_session(self, *args, **kwargs):
        return "dummy-session"
        
    def get_working_directory(self, *args, **kwargs):
        return "D:\\"
        
    def list_sessions(self, *args, **kwargs):
        return []
    
    # 기타 메서드 추가
    def delete_session(self, *args, **kwargs):
        return True
        
    async def execute_command(self, *args, **kwargs):
        return {
            "stdout": "터미널 기능이 비활성화되었습니다.",
            "stderr": "",
            "exit_code": 0,
            "error": None
        }
