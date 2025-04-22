"""
JavaScript 코드 분석기

JavaScript 코드를 분석하여 함수, 클래스 등의 정보를 추출합니다.
"""

import re
from typing import Dict, Any, List, Set, Optional

from core.logging import get_logger

logger = get_logger("github_docs.analyzers.javascript")

def analyze_javascript_file(file_path: str, relative_path: str) -> Dict[str, Any]:
    """
    JavaScript 파일 분석
    
    Args:
        file_path: 파일 경로
        relative_path: 저장소 루트로부터의 상대 경로
    
    Returns:
        분석 결과 딕셔너리
    """
    result = {
        "path": relative_path,
        "language": "javascript",
        "imports": set(),
        "exports": set(),
        "functions": [],
        "classes": []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 모듈 이름 추출
        module_name = relative_path.replace('/', '.').replace('\\', '.')
        if module_name.endswith('.js') or module_name.endswith('.jsx') or \
           module_name.endswith('.ts') or module_name.endswith('.tsx'):
            module_name = '.'.join(module_name.split('.')[:-1])
        result["module_name"] = module_name
        
        # 모듈 문서 문자열 추출 (JSDoc)
        module_doc = extract_jsdoc_comment(content, 0)
        if module_doc:
            result["module_doc"] = module_doc
        
        # 임포트 문 추출
        extract_js_imports(content, result["imports"])
        
        # 내보내기 문 추출
        extract_js_exports(content, result["exports"])
        
        # 함수 추출
        extract_js_functions(content, module_name, result["functions"])
        
        # 클래스 추출
        extract_js_classes(content, module_name, result["classes"])
        
        # Set을 리스트로 변환
        result["imports"] = list(result["imports"])
        result["exports"] = list(result["exports"])
        
        logger.debug(f"JavaScript 파일 분석 완료: {relative_path}")
        return result
    
    except Exception as e:
        logger.error(f"JavaScript 파일 분석 중 오류 발생: {file_path} - {str(e)}")
        
        # 기본 정보만 반환
        result["imports"] = list(result["imports"])
        result["exports"] = list(result["exports"])
        result["error"] = str(e)
        return result

def extract_jsdoc_comment(content: str, start_pos: int = 0) -> Optional[str]:
    """
    JSDoc 주석 추출
    
    Args:
        content: 파일 내용
        start_pos: 검색 시작 위치
    
    Returns:
        JSDoc 주석 문자열 또는 None
    """
    # JSDoc 주석 패턴 (/** ... */)
    jsdoc_pattern = r'/\*\*(.*?)\*/'
    match = re.search(jsdoc_pattern, content[start_pos:], re.DOTALL)
    
    if match:
        # 주석 내용 추출 및 정리
        comment = match.group(1)
        
        # 각 줄에서 선행 공백과 * 제거
        lines = []
        for line in comment.split('\n'):
            line = line.strip()
            if line.startswith('*'):
                line = line[1:].strip()
            lines.append(line)
        
        return '\n'.join(lines).strip()
    
    return None

def extract_js_imports(content: str, imports_set: Set[str]) -> None:
    """
    JavaScript 파일에서 임포트 문 추출
    
    Args:
        content: 파일 내용
        imports_set: 임포트 문자열을 저장할 세트
    """
    # import 문 패턴
    import_patterns = [
        r'import\s+(\{[^}]+\}|\*\s+as\s+[a-zA-Z0-9_$]+|[a-zA-Z0-9_$]+)\s+from\s+[\'"]([^\'"]+)[\'"]',
        r'import\s+[\'"]([^\'"]+)[\'"]',
        r'require\([\'"]([^\'"]+)[\'"]\)'
    ]
    
    for pattern in import_patterns:
        for match in re.finditer(pattern, content):
            if len(match.groups()) > 1:
                imports_set.add(match.group(2))
            else:
                imports_set.add(match.group(1))

def extract_js_exports(content: str, exports_set: Set[str]) -> None:
    """
    JavaScript 파일에서 내보내기 문 추출
    
    Args:
        content: 파일 내용
        exports_set: 내보내기 문자열을 저장할 세트
    """
    # export 문 패턴
    export_patterns = [
        r'export\s+(?:default\s+)?(?:function|class|const|let|var)\s+([a-zA-Z0-9_$]+)',
        r'export\s+\{([^}]+)\}',
        r'module\.exports\s*=\s*([a-zA-Z0-9_$]+)',
        r'exports\.([a-zA-Z0-9_$]+)\s*='
    ]
    
    for pattern in export_patterns:
        for match in re.finditer(pattern, content):
            # 중괄호 안의 내용이면 쉼표로 구분된 여러 항목일 수 있음
            exports = match.group(1).split(',')
            for export in exports:
                export = export.strip()
                if export:
                    exports_set.add(export)

def extract_js_functions(content: str, module_name: str, functions: List[Dict[str, Any]]) -> None:
    """
    JavaScript 파일에서 함수 추출
    
    Args:
        content: 파일 내용
        module_name: 모듈 이름
        functions: 함수 정보를 저장할 리스트
    """
    # 함수 선언 패턴
    function_patterns = [
        # 일반 함수 선언
        r'function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)',
        # 화살표 함수(const/let/var 변수 할당)
        r'(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:\([^)]*\)|\s*[a-zA-Z0-9_$,\s]*)\s*=>\s*[{(]',
        # 메서드 정의
        r'([a-zA-Z0-9_$]+)\s*\(([^)]*)\)\s*\{'
    ]
    
    for pattern in function_patterns:
        for match in re.finditer(pattern, content):
            func_name = match.group(1)
            
            # 함수 위치 근처의 JSDoc 주석 찾기
            func_pos = match.start()
            docstring = extract_jsdoc_comment(content[:func_pos])
            
            # 괄호 내용으로 매개변수 추출
            args = []
            if len(match.groups()) > 1:
                args_str = match.group(2)
                if args_str:
                    args = [arg.strip() for arg in args_str.split(',')]
            
            functions.append({
                "name": func_name,
                "module": module_name,
                "docstring": docstring or "",
                "arguments": args,
                "line_number": content[:func_pos].count('\n') + 1
            })

def extract_js_classes(content: str, module_name: str, classes: List[Dict[str, Any]]) -> None:
    """
    JavaScript 파일에서 클래스 추출
    
    Args:
        content: 파일 내용
        module_name: 모듈 이름
        classes: 클래스 정보를 저장할 리스트
    """
    # 클래스 선언 패턴
    class_pattern = r'class\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+([a-zA-Z0-9_$.]+))?\s*\{'
    
    for match in re.finditer(class_pattern, content):
        class_name = match.group(1)
        base_class = match.group(2) if len(match.groups()) > 1 and match.group(2) else ""
        
        class_pos = match.start()
        
        # 클래스 위치 근처의 JSDoc 주석 찾기
        docstring = extract_jsdoc_comment(content[:class_pos])
        
        # 메서드 찾기
        class_content = find_class_content(content, match.end())
        methods = []
        
        # 메서드 추출
        if class_content:
            method_pattern = r'(?:async\s+)?([a-zA-Z0-9_$]+)\s*\(([^)]*)\)\s*\{'
            for method_match in re.finditer(method_pattern, class_content):
                method_name = method_match.group(1)
                
                # 생성자나 특수 메서드가 아닌 경우만 추가
                if method_name not in ['constructor', 'render', 'if', 'for', 'while', 'switch']:
                    method_pos = class_pos + method_match.start()
                    method_docstring = extract_jsdoc_comment(content[:method_pos])
                    
                    args_str = method_match.group(2)
                    args = [arg.strip() for arg in args_str.split(',')] if args_str else []
                    
                    methods.append({
                        "name": method_name,
                        "docstring": method_docstring or "",
                        "arguments": args,
                        "line_number": content[:method_pos].count('\n') + 1
                    })
        
        classes.append({
            "name": class_name,
            "module": module_name,
            "docstring": docstring or "",
            "methods": methods,
            "line_number": content[:class_pos].count('\n') + 1,
            "base_classes": [base_class] if base_class else []
        })

def find_class_content(content: str, start_pos: int) -> Optional[str]:
    """
    클래스 내용 찾기
    
    Args:
        content: 파일 내용
        start_pos: 클래스 선언 이후 시작 위치
    
    Returns:
        클래스 내용 또는 None
    """
    brace_count = 1
    end_pos = start_pos
    
    while brace_count > 0 and end_pos < len(content):
        if content[end_pos] == '{':
            brace_count += 1
        elif content[end_pos] == '}':
            brace_count -= 1
        end_pos += 1
    
    if brace_count == 0:
        return content[start_pos:end_pos-1]
    
    return None
