"""
파일 통계 분석기

파일 내용에 대한 통계 정보를 분석합니다.
"""

from typing import Dict, Any

from core.logging import get_logger
from ..language_utils import get_language_from_extension

logger = get_logger("github_docs.analyzers.file_stats")

def get_file_content_stats(file_path: str) -> Dict[str, Any]:
    """
    파일 내용 통계 추출
    
    Args:
        file_path: 파일 경로
    
    Returns:
        파일 내용 통계 딕셔너리
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 기본 통계
        lines = content.splitlines()
        stats = {
            "path": file_path,
            "size_bytes": len(content),
            "lines_total": len(lines),
            "lines_code": 0,
            "lines_comment": 0,
            "lines_blank": 0,
            "characters": len(content),
            "words": len(content.split())
        }
        
        # 언어 확인
        language = get_language_from_extension(file_path)
        stats["language"] = language
        
        # 언어별 코드/주석/빈 줄 분석
        if language:
            analyze_language_stats(language, lines, stats)
        else:
            # 기본 분석 (빈 줄만 카운트)
            for line in lines:
                if not line.strip():
                    stats["lines_blank"] += 1
                else:
                    stats["lines_code"] += 1
        
        return stats
    
    except Exception as e:
        logger.error(f"파일 내용 통계 추출 중 오류 발생: {file_path} - {str(e)}")
        
        # 기본 정보만 반환
        return {
            "path": file_path,
            "error": str(e)
        }

def analyze_language_stats(language: str, lines: list, stats: Dict[str, Any]) -> None:
    """
    언어별 통계 분석
    
    Args:
        language: 프로그래밍 언어
        lines: 파일 내용 라인 목록
        stats: 통계 정보를 저장할 딕셔너리
    """
    if language == "python":
        analyze_python_stats(lines, stats)
    elif language in ["javascript", "typescript", "java", "c", "cpp", "go"]:
        analyze_c_style_stats(lines, stats)
    elif language in ["html", "xml"]:
        analyze_markup_stats(lines, stats)
    elif language in ["css", "scss", "sass", "less"]:
        analyze_css_stats(lines, stats)
    else:
        # 기본 분석 (빈 줄만 카운트)
        for line in lines:
            if not line.strip():
                stats["lines_blank"] += 1
            else:
                stats["lines_code"] += 1

def analyze_python_stats(lines: list, stats: Dict[str, Any]) -> None:
    """
    Python 파일 통계 분석
    
    Args:
        lines: 파일 내용 라인 목록
        stats: 통계 정보를 저장할 딕셔너리
    """
    in_multiline_comment = False
    comment_marker = "#"
    docstring_markers = ['"""', "'''"]
    
    for line in lines:
        line = line.strip()
        
        if not line:
            stats["lines_blank"] += 1
        elif line.startswith(comment_marker):
            stats["lines_comment"] += 1
        elif any(marker in line for marker in docstring_markers):
            # 간단한 docstring 계산 (완전하지 않음)
            stats["lines_comment"] += 1
            
            # 멀티라인 주석 상태 토글
            for marker in docstring_markers:
                if line.count(marker) % 2 == 1:
                    in_multiline_comment = not in_multiline_comment
                    break
        elif in_multiline_comment:
            stats["lines_comment"] += 1
        else:
            stats["lines_code"] += 1

def analyze_c_style_stats(lines: list, stats: Dict[str, Any]) -> None:
    """
    C 스타일 언어 (JavaScript, Java, C, C++, Go 등) 파일 통계 분석
    
    Args:
        lines: 파일 내용 라인 목록
        stats: 통계 정보를 저장할 딕셔너리
    """
    in_multiline_comment = False
    
    for line in lines:
        line = line.strip()
        
        if not line:
            stats["lines_blank"] += 1
        elif in_multiline_comment:
            stats["lines_comment"] += 1
            if "*/" in line:
                in_multiline_comment = False
        elif line.startswith("//"):
            stats["lines_comment"] += 1
        elif "/*" in line:
            stats["lines_comment"] += 1
            if "*/" not in line[line.find("/*") + 2:]:
                in_multiline_comment = True
        else:
            stats["lines_code"] += 1

def analyze_markup_stats(lines: list, stats: Dict[str, Any]) -> None:
    """
    마크업 언어 (HTML, XML 등) 파일 통계 분석
    
    Args:
        lines: 파일 내용 라인 목록
        stats: 통계 정보를 저장할 딕셔너리
    """
    in_comment = False
    
    for line in lines:
        line = line.strip()
        
        if not line:
            stats["lines_blank"] += 1
        elif in_comment:
            stats["lines_comment"] += 1
            if "-->" in line:
                in_comment = False
        elif "<!--" in line:
            stats["lines_comment"] += 1
            if "-->" not in line[line.find("<!--") + 4:]:
                in_comment = True
        else:
            stats["lines_code"] += 1

def analyze_css_stats(lines: list, stats: Dict[str, Any]) -> None:
    """
    CSS 파일 통계 분석
    
    Args:
        lines: 파일 내용 라인 목록
        stats: 통계 정보를 저장할 딕셔너리
    """
    in_comment = False
    
    for line in lines:
        line = line.strip()
        
        if not line:
            stats["lines_blank"] += 1
        elif in_comment:
            stats["lines_comment"] += 1
            if "*/" in line:
                in_comment = False
        elif "/*" in line:
            stats["lines_comment"] += 1
            if "*/" not in line[line.find("/*") + 2:]:
                in_comment = True
        else:
            stats["lines_code"] += 1
