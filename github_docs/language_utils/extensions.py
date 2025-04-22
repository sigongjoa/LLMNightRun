"""
파일 확장자 유틸리티

파일 확장자로 프로그래밍 언어를 식별하기 위한 유틸리티 함수들을 제공합니다.
"""

import os
from typing import Optional

# 언어별 파일 확장자
FILE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".jsx", ".ts", ".tsx"],
    "java": [".java"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".hpp", ".cc", ".hh"],
    "go": [".go"],
    "ruby": [".rb"],
    "php": [".php"],
    "html": [".html", ".htm"],
    "css": [".css", ".scss", ".sass", ".less"],
    "markdown": [".md", ".markdown"],
    "json": [".json"],
    "yaml": [".yml", ".yaml"],
    "xml": [".xml"],
    "shell": [".sh", ".bash"]
}

def get_language_from_extension(file_path: str) -> Optional[str]:
    """
    파일 확장자로 프로그래밍 언어 추측
    
    Args:
        file_path: 파일 경로
    
    Returns:
        프로그래밍 언어 또는 None (알 수 없는 경우)
    """
    _, ext = os.path.splitext(file_path.lower())
    
    for language, extensions in FILE_EXTENSIONS.items():
        if ext in extensions:
            return language
    
    return None

def get_language_extensions(language: str) -> list:
    """
    언어에 대한 파일 확장자 목록 가져오기
    
    Args:
        language: 프로그래밍 언어
    
    Returns:
        파일 확장자 목록
    """
    return FILE_EXTENSIONS.get(language.lower(), [])

def is_binary_file(file_path: str) -> bool:
    """
    이진 파일 여부 확인
    
    Args:
        file_path: 파일 경로
    
    Returns:
        이진 파일 여부
    """
    # 일반적인 이진 파일 확장자
    binary_extensions = [
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.exe', '.dll', '.so', '.dylib', '.jar',
        '.pyc', '.class', '.o', '.obj',
        '.ttf', '.woff', '.woff2', '.eot',
        '.mp3', '.mp4', '.wav', '.avi', '.mov'
    ]
    
    _, ext = os.path.splitext(file_path.lower())
    return ext in binary_extensions
