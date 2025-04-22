"""
Python 코드 분석기

Python 코드를 분석하여 모듈, 함수, 클래스 등의 정보를 추출합니다.
"""

import ast
from typing import Dict, Any, List, Set

from core.logging import get_logger

logger = get_logger("github_docs.analyzers.python")

def analyze_python_file(file_path: str, relative_path: str) -> Dict[str, Any]:
    """
    Python 파일 분석
    
    Args:
        file_path: 파일 경로
        relative_path: 저장소 루트로부터의 상대 경로
    
    Returns:
        분석 결과 딕셔너리
    """
    result = {
        "path": relative_path,
        "language": "python",
        "imports": set(),
        "functions": [],
        "classes": []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 모듈 이름 추출
        module_path = relative_path.replace('/', '.').replace('\\', '.')
        if module_path.endswith('.py'):
            module_path = module_path[:-3]
        result["module_name"] = module_path
        
        # 모듈 문서 문자열 추출
        module_doc = ""
        if content.startswith('"""') or content.startswith("'''"):
            doc_end = content.find('"""', 3) if content.startswith('"""') else content.find("'''", 3)
            if doc_end > 0:
                module_doc = content[3:doc_end].strip()
        result["module_doc"] = module_doc
        
        # AST 파싱
        try:
            tree = ast.parse(content)
            
            # 임포트 문 분석
            extract_imports(tree, result["imports"])
            
            # 함수 및 클래스 분석
            extract_functions_and_classes(tree, module_path, result)
            
        except SyntaxError as e:
            logger.warning(f"Python 파일 파싱 중 구문 오류: {file_path} - {str(e)}")
            result["syntax_error"] = str(e)
        
        # Set을 리스트로 변환
        result["imports"] = list(result["imports"])
        
        logger.debug(f"Python 파일 분석 완료: {relative_path}")
        return result
    
    except Exception as e:
        logger.error(f"Python 파일 분석 중 오류 발생: {file_path} - {str(e)}")
        
        # 기본 정보만 반환
        result["imports"] = list(result["imports"])
        result["error"] = str(e)
        return result

def extract_imports(tree: ast.Module, imports_set: Set[str]) -> None:
    """
    AST에서 임포트 문 추출
    
    Args:
        tree: AST 트리
        imports_set: 임포트 문자열을 저장할 세트
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports_set.add(name.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for name in node.names:
                    imports_set.add(f"{node.module}.{name.name}")

def extract_functions_and_classes(tree: ast.Module, module_path: str, result: Dict[str, Any]) -> None:
    """
    AST에서 함수 및 클래스 정보 추출
    
    Args:
        tree: AST 트리
        module_path: 모듈 경로
        result: 결과를 저장할 딕셔너리
    """
    for node in tree.body:
        # 함수 정의
        if isinstance(node, ast.FunctionDef):
            func_info = extract_function(node, module_path)
            result["functions"].append(func_info)
        
        # 클래스 정의
        elif isinstance(node, ast.ClassDef):
            class_info = extract_class(node, module_path)
            result["classes"].append(class_info)

def extract_function(node: ast.FunctionDef, module_path: str) -> Dict[str, Any]:
    """
    함수 노드에서 정보 추출
    
    Args:
        node: 함수 정의 노드
        module_path: 모듈 경로
    
    Returns:
        함수 정보 딕셔너리
    """
    return {
        "name": node.name,
        "module": module_path,
        "docstring": ast.get_docstring(node) or "",
        "arguments": [arg.arg for arg in node.args.args],
        "line_number": node.lineno
    }

def extract_class(node: ast.ClassDef, module_path: str) -> Dict[str, Any]:
    """
    클래스 노드에서 정보 추출
    
    Args:
        node: 클래스 정의 노드
        module_path: 모듈 경로
    
    Returns:
        클래스 정보 딕셔너리
    """
    class_info = {
        "name": node.name,
        "module": module_path,
        "docstring": ast.get_docstring(node) or "",
        "methods": [],
        "line_number": node.lineno,
        "base_classes": [base.id if isinstance(base, ast.Name) else "" for base in node.bases]
    }
    
    # 클래스 메서드 분석
    for class_node in node.body:
        if isinstance(class_node, ast.FunctionDef):
            method_info = {
                "name": class_node.name,
                "docstring": ast.get_docstring(class_node) or "",
                "arguments": [arg.arg for arg in class_node.args.args if arg.arg != "self"],
                "line_number": class_node.lineno
            }
            class_info["methods"].append(method_info)
    
    return class_info
