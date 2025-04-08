"""
MCP 채팅 내역 내보내기 기능
"""

import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("mcp.export")

class ExportFunctions:
    """채팅 내역 내보내기 함수 클래스"""
    
    def __init__(self, exports_dir: Optional[str] = None):
        """
        초기화
        
        Args:
            exports_dir: 내보내기 디렉토리 (None인 경우 기본 디렉토리 사용)
        """
        # 기본 내보내기 디렉토리 설정
        if exports_dir is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            exports_dir = os.path.join(project_root, "exports")
        
        self.exports_dir = exports_dir
        
        # 내보내기 디렉토리 생성
        if not os.path.exists(self.exports_dir):
            os.makedirs(self.exports_dir)
            
        logger.info(f"Initialized ExportFunctions with exports_dir: {self.exports_dir}")
    
    def export_chat_history(self, history: List[Dict[str, Any]], format: str = "json", 
                           title: Optional[str] = None) -> Dict[str, Any]:
        """
        채팅 내역 내보내기
        
        Args:
            history: 채팅 내역 목록
            format: 내보내기 형식 (json, markdown, text)
            title: 내보내기 제목 (None인 경우 자동 생성)
            
        Returns:
            Dict[str, Any]: 내보내기 결과
        """
        try:
            if not history:
                return {
                    "success": False,
                    "error": "Chat history is empty"
                }
            
            # 제목이 없으면 자동 생성
            if not title:
                title = f"Chat_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 형식에 따라 처리
            if format.lower() == "json":
                return self._export_as_json(history, title)
            elif format.lower() == "markdown":
                return self._export_as_markdown(history, title)
            elif format.lower() == "text":
                return self._export_as_text(history, title)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format}"
                }
                
        except Exception as e:
            logger.error(f"Error exporting chat history: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _export_as_json(self, history: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        """JSON 형식으로 내보내기"""
        try:
            # 파일 이름 및 경로 생성
            filename = f"{title}.json"
            filepath = os.path.join(self.exports_dir, filename)
            
            # 내보내기 메타데이터 추가
            export_data = {
                "title": title,
                "timestamp": datetime.now().isoformat(),
                "format": "json",
                "messages": history
            }
            
            # JSON 파일로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return {
                "success": True,
                "format": "json",
                "filename": filename,
                "filepath": filepath,
                "message": f"Chat history exported as JSON: {filepath}"
            }
                
        except Exception as e:
            logger.error(f"Error exporting as JSON: {str(e)}")
            return {
                "success": False,
                "error": f"Error exporting as JSON: {str(e)}"
            }
    
    def _export_as_markdown(self, history: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        """Markdown 형식으로 내보내기"""
        try:
            # 파일 이름 및 경로 생성
            filename = f"{title}.md"
            filepath = os.path.join(self.exports_dir, filename)
            
            # Markdown 내용 생성
            content = f"# {title}\n\n"
            content += f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
            
            for message in history:
                role = message.get("role", "unknown")
                content_text = self._extract_message_content(message)
                
                if role == "user":
                    content += f"## User\n\n{content_text}\n\n"
                elif role == "assistant":
                    content += f"## Assistant\n\n{content_text}\n\n"
                elif role == "system":
                    content += f"## System\n\n{content_text}\n\n"
                elif role == "tool":
                    content += f"## Tool\n\n{content_text}\n\n"
                else:
                    content += f"## {role.capitalize()}\n\n{content_text}\n\n"
            
            # Markdown 파일로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "format": "markdown",
                "filename": filename,
                "filepath": filepath,
                "message": f"Chat history exported as Markdown: {filepath}"
            }
                
        except Exception as e:
            logger.error(f"Error exporting as Markdown: {str(e)}")
            return {
                "success": False,
                "error": f"Error exporting as Markdown: {str(e)}"
            }
    
    def _export_as_text(self, history: List[Dict[str, Any]], title: str) -> Dict[str, Any]:
        """일반 텍스트 형식으로 내보내기"""
        try:
            # 파일 이름 및 경로 생성
            filename = f"{title}.txt"
            filepath = os.path.join(self.exports_dir, filename)
            
            # 텍스트 내용 생성
            content = f"{title}\n"
            content += f"Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for message in history:
                role = message.get("role", "unknown")
                content_text = self._extract_message_content(message)
                
                if role == "user":
                    content += f"USER: {content_text}\n\n"
                elif role == "assistant":
                    content += f"ASSISTANT: {content_text}\n\n"
                elif role == "system":
                    content += f"SYSTEM: {content_text}\n\n"
                elif role == "tool":
                    content += f"TOOL: {content_text}\n\n"
                else:
                    content += f"{role.upper()}: {content_text}\n\n"
            
            # 텍스트 파일로 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "format": "text",
                "filename": filename,
                "filepath": filepath,
                "message": f"Chat history exported as Text: {filepath}"
            }
                
        except Exception as e:
            logger.error(f"Error exporting as Text: {str(e)}")
            return {
                "success": False,
                "error": f"Error exporting as Text: {str(e)}"
            }
    
    def _extract_message_content(self, message: Dict[str, Any]) -> str:
        """메시지에서 내용 추출"""
        content = message.get("content", "")
        
        # 문자열인 경우 그대로 반환
        if isinstance(content, str):
            return content
        
        # 리스트인 경우 내용 추출 및 결합
        if isinstance(content, list):
            result = ""
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        result += item.get("text", "")
                    elif item.get("type") == "file":
                        result += f"[FILE: {item.get('name', 'unnamed')}]"
                    elif item.get("type") == "toolCallRequest":
                        tool_call = item.get("toolCallRequest", {})
                        tool_name = tool_call.get("name", "unknown")
                        tool_args = json.dumps(tool_call.get("arguments", {}), ensure_ascii=False)
                        result += f"[TOOL CALL: {tool_name} with args: {tool_args}]"
                    elif item.get("type") == "toolCallResult":
                        result += f"[TOOL RESULT: {item.get('content', '')}]"
                else:
                    result += str(item)
            return result
        
        # 그 외의 경우 JSON 문자열로 변환
        return json.dumps(content, ensure_ascii=False)
    
    def get_exports_list(self) -> Dict[str, Any]:
        """내보내기 목록 조회"""
        try:
            exports = []
            
            for filename in os.listdir(self.exports_dir):
                filepath = os.path.join(self.exports_dir, filename)
                
                if os.path.isfile(filepath):
                    # 파일 정보 추출
                    stat = os.stat(filepath)
                    
                    # 확장자로 형식 추론
                    format = "unknown"
                    if filename.endswith(".json"):
                        format = "json"
                    elif filename.endswith(".md"):
                        format = "markdown"
                    elif filename.endswith(".txt"):
                        format = "text"
                    
                    exports.append({
                        "filename": filename,
                        "filepath": filepath,
                        "format": format,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # 날짜 기준 내림차순 정렬
            exports.sort(key=lambda x: x["modified"], reverse=True)
            
            return {
                "success": True,
                "exports": exports,
                "count": len(exports),
                "directory": self.exports_dir
            }
                
        except Exception as e:
            logger.error(f"Error getting exports list: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_export(self, filename: str) -> Dict[str, Any]:
        """내보내기 삭제"""
        try:
            # 파일 경로 생성 및 보안 검사
            filepath = os.path.join(self.exports_dir, os.path.basename(filename))
            
            if not os.path.exists(filepath):
                return {
                    "success": False,
                    "error": f"File not found: {filename}"
                }
            
            if not os.path.isfile(filepath):
                return {
                    "success": False,
                    "error": f"Path is not a file: {filename}"
                }
            
            # 파일 삭제
            os.remove(filepath)
            
            return {
                "success": True,
                "filename": filename,
                "message": f"Export file deleted: {filename}"
            }
                
        except Exception as e:
            logger.error(f"Error deleting export file: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
