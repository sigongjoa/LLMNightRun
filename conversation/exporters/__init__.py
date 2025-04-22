"""
대화 내보내기 모듈

대화 내용을 다양한 형식으로 내보내는 기능을 제공합니다.
"""

from .base import Exporter
from .json_exporter import JsonExporter
from .markdown_exporter import MarkdownExporter
from .text_exporter import TextExporter

# 내보내기 함수
def export_conversation(conversation, format="json", **kwargs):
    """
    형식에 맞는 내보내기 함수 호출
    
    Args:
        conversation: 대화 객체
        format: 내보내기 형식 ('json', 'markdown', 'text')
        **kwargs: 추가 옵션
    
    Returns:
        내보내기 결과 문자열
    """
    if format == "json":
        return JsonExporter(**kwargs).export(conversation)
    elif format == "markdown":
        return MarkdownExporter(**kwargs).export(conversation)
    elif format == "text":
        return TextExporter(**kwargs).export(conversation)
    else:
        raise ValueError(f"지원되지 않는 내보내기 형식: {format}")
