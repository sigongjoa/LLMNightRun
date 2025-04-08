"""
코드 분석 모듈

이 모듈은 프로젝트 코드를 분석하여 문서화에 필요한 정보를 추출합니다.
"""

import os
import re
import ast
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set

# 로깅 설정
logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """코드 분석을 위한 클래스"""

    def __init__(self):
        """코드 분석기 초기화"""
        self.analyzers = {
            ".py": self._analyze_python,
            ".js": self._analyze_javascript,
            ".ts": self._analyze_typescript,
            ".tsx": self._analyze_react,
            ".jsx": self._analyze_react,
            ".json": self._analyze_json,
            ".yml": self._analyze_yaml,
            ".yaml": self._analyze_yaml,
            ".md": self._analyze_markdown,
        }
        
    def analyze_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        파일 내용 분석
        
        Args:
            file_path: 파일 경로
            content: 파일 내용
            
        Returns:
            분석 결과를 담은 딕셔너리
        """
        # 기본 분석 결과
        result = {
            "file_path": file_path,
            "type": "unknown",
            "is_router": False,
            "is_model": False,
            "is_database": False,
            "is_test": False,
            "summary": "",
            "imports": [],
            "exports": [],
            "functions": [],
            "classes": [],
            "endpoints": [],
            "models": []
        }
        
        # 파일 유형 감지
        _, ext = os.path.splitext(file_path)
        
        # 파일 명에 따른 특수 처리
        if "/test" in file_path or file_path.endswith("_test.py") or file_path.endswith(".test.ts"):
            result["is_test"] = True
            
        if "/api/" in file_path or "/routes/" in file_path or "router" in file_path.lower():
            result["is_router"] = True
            
        if "/models/" in file_path or "model" in file_path.lower():
            result["is_model"] = True
            
        if "/database/" in file_path or "db" in file_path.lower():
            result["is_database"] = True
            
        # 설정 파일 감지
        if file_path.endswith(".env") or ext.lower() in [".yml", ".yaml", ".json", ".toml", ".ini"]:
            result["type"] = "configuration"
            
        # 파일 확장자별 분석기 호출
        if ext.lower() in self.analyzers:
            try:
                analyzer_result = self.analyzers[ext.lower()](file_path, content)
                result.update(analyzer_result)
            except Exception as e:
                logger.error(f"파일 분석 중 오류 발생 ({file_path}): {str(e)}")
                result["error"] = str(e)
                
        # 요약 생성
        if not result.get("summary"):
            result["summary"] = self._generate_summary(result)
            
        return result
    
    def _analyze_python(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Python 파일 분석
        
        Args:
            file_path: 파일 경로
            content: 파일 내용
            
        Returns:
            분석 결과
        """
        result = {"type": "python"}
        
        try:
            # AST 파싱
            tree = ast.parse(content)
            
            # 클래스 및 함수 추출
            result["classes"] = []
            result["functions"] = []
            result["imports"] = []
            
            for node in ast.walk(tree):
                # 클래스 처리
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "methods": [],
                        "docstring": ast.get_docstring(node) or "",
                        "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                    }
                    
                    # 상속 정보
                    if node.bases:
                        class_info["bases"] = [self._get_name_from_node(base) for base in node.bases]
                    
                    # 메서드 추출
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                "name": item.name,
                                "docstring": ast.get_docstring(item) or "",
                                "params": [arg.arg for arg in item.args.args if arg.arg != 'self'],
                                "decorators": [d.id for d in item.decorator_list if isinstance(d, ast.Name)]
                            }
                            class_info["methods"].append(method_info)
                    
                    result["classes"].append(class_info)
                    
                    # 모델 클래스 감지
                    if any(base in ["BaseModel", "Model", "SQLModel"] for base in class_info.get("bases", [])):
                        result["is_model"] = True
                        model_info = {
                            "name": node.name,
                            "fields": [],
                            "docstring": class_info["docstring"]
                        }
                        
                        # 필드 추출
                        for item in node.body:
                            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                                field_name = item.target.id
                                field_type = ""
                                
                                if item.annotation:
                                    field_type = self._get_name_from_node(item.annotation)
                                    
                                default_value = None
                                if item.value:
                                    if isinstance(item.value, (ast.Str, ast.Num)):
                                        default_value = item.value.s if isinstance(item.value, ast.Str) else item.value.n
                                
                                model_info["fields"].append({
                                    "name": field_name,
                                    "type": field_type,
                                    "default": default_value
                                })
                        
                        if "models" not in result:
                            result["models"] = []
                        result["models"].append(model_info)
                        
                    # FastAPI 라우터 감지
                    if "APIRouter" in class_info.get("bases", []) or "Router" in class_info.get("bases", []):
                        result["is_router"] = True
                
                # 함수 처리
                elif isinstance(node, ast.FunctionDef) and not isinstance(node.parent, ast.ClassDef):
                    func_info = {
                        "name": node.name,
                        "docstring": ast.get_docstring(node) or "",
                        "params": [arg.arg for arg in node.args.args],
                        "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                    }
                    result["functions"].append(func_info)
                    
                    # FastAPI 엔드포인트 감지
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                                method = decorator.func.attr.upper()
                                path = ""
                                
                                # 경로 추출
                                if decorator.args and isinstance(decorator.args[0], ast.Str):
                                    path = decorator.args[0].s
                                
                                endpoint_info = {
                                    "method": method,
                                    "path": path,
                                    "function": node.name,
                                    "summary": ""
                                }
                                
                                # 문서 문자열에서 요약 추출
                                docstring = ast.get_docstring(node) or ""
                                if docstring:
                                    endpoint_info["summary"] = docstring.split('\n')[0]
                                
                                if "endpoints" not in result:
                                    result["endpoints"] = []
                                result["endpoints"].append(endpoint_info)
                                result["is_router"] = True
                
                # 임포트 처리
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        result["imports"].append({"module": name.name, "alias": name.asname})
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for name in node.names:
                        result["imports"].append({
                            "module": f"{module}.{name.name}" if module else name.name,
                            "alias": name.asname,
                            "from_import": True
                        })
                
            # 파일 요약
            docstring = ast.get_docstring(tree)
            if docstring:
                result["summary"] = docstring.split('\n')[0]
            
        except SyntaxError as e:
            logger.error(f"Python 파일 구문 분석 실패 ({file_path}): {str(e)}")
            result["error"] = f"구문 오류: {str(e)}"
            
        except Exception as e:
            logger.error(f"Python 파일 분석 중 예외 발생 ({file_path}): {str(e)}")
            result["error"] = f"분석 실패: {str(e)}"
            
        return result
    
    def _analyze_javascript(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        JavaScript 파일 분석
        
        Args:
            file_path: 파일 경로
            content: 파일 내용
            
        Returns:
            분석 결과
        """
        result = {"type": "javascript"}
        
        # 간단한 정규식 기반 분석
        imports = re.findall(r'import\s+(\{[^}]+\}|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', content)
        result["imports"] = [{"module": imp[1], "items": imp[0]} for imp in imports]
        
        exports = re.findall(r'export\s+(const|let|var|function|class|default)\s+(\w+)', content)
        result["exports"] = [{"type": exp[0], "name": exp[1]} for exp in exports]
        
        # React 컴포넌트 감지
        if 'React' in content or 'react' in content:
            components = re.findall(r'(function|const)\s+(\w+)(?:\s*=\s*(?:\(\)\s*=>|function)|\s*\([^)]*\))\s*(?:=>)?\s*\{', content)
            result["components"] = [comp[1] for comp in components if comp[1][0].isupper()]
            
            if result["components"]:
                result["framework"] = "React"
        
        # NextJS 페이지 감지
        if 'getStaticProps' in content or 'getServerSideProps' in content:
            result["framework"] = "Next.js"
            
        # Express 라우터 감지
        if '.get(' in content or '.post(' in content or '.put(' in content or '.delete(' in content:
            routes = []
            
            # 간단한 라우트 감지
            route_patterns = [
                r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]',
                r'route\s*\.\s*(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
            ]
            
            for pattern in route_patterns:
                for match in re.finditer(pattern, content):
                    method = match.group(1).upper()
                    path = match.group(2)
                    routes.append({"method": method, "path": path})
            
            if routes:
                result["is_router"] = True
                result["endpoints"] = routes
                result["framework"] = "Express"
        
        return result
    
    def _analyze_typescript(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        TypeScript 파일 분석
        
        Args:
            file_path: 파일 경로
            content: 파일 내용
            
        Returns:
            분석 결과
        """
        result = self._analyze_javascript(file_path, content)
        result["type"] = "typescript"
        
        # 인터페이스/타입 추출
        interfaces = re.findall(r'(interface|type)\s+(\w+)', content)
        result["interfaces"] = [{"type": intf[0], "name": intf[1]} for intf in interfaces]
        
        return result
    
    def _analyze_react(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        React 파일 (JSX/TSX) 분석
        
        Args:
            file_path: 파일 경로
            content: 파일 내용
            
        Returns:
            분석 결과
        """
        # .tsx 또는 .jsx 파일
        is_typescript = file_path.endswith(".tsx")
        result = self._analyze_typescript(file_path, content) if is_typescript else self._analyze_javascript(file_path, content)
        result["type"] = "react"
        result["framework"] = "React"
        
        # 컴포넌트 및 훅 감지
        hooks = re.findall(r'use\w+\s*\(', content)
        result["hooks"] = list(set(hook.strip('( ') for hook in hooks))
        
        # JSX/TSX 구문 감지
        jsx_tags = re.findall(r'<(\w+)[^>]*>', content)
        result["jsx_tags"] = list(set(tag for tag in jsx_tags if tag not in ['>', '/']))
        
        return result
    
    def _analyze_json(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        JSON 파일 분석
        
        Args:
            file_path: 파일 경로
            content: 파일 내용
            
        Returns:
            분석 결과
        """
        result = {"type": "json"}
        
        try:
            json_data = json.loads(content)
            result["keys"] = list(json_data.keys()) if isinstance(json_data, dict) else []
            
            # package.json 특별 처리
            if os.path.basename(file_path) == "package.json":
                result["is_package_json"] = True
                
                if "dependencies" in json_data:
                    result["dependencies"] = list(json_data["dependencies"].keys())
                
                if "devDependencies" in json_data:
                    result["dev_dependencies"] = list(json_data["devDependencies"].keys())
                
                if "scripts" in json_data:
                    result["scripts"] = json_data["scripts"]
                
                if "name" in json_data:
                    result["package_name"] = json_data["name"]
                
                if "version" in json_data:
                    result["version"] = json_data["version"]
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패 ({file_path}): {str(e)}")
            result["error"] = f"JSON 파싱 오류: {str(e)}"
        
        return result
    
    def _analyze_yaml(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        YAML 파일 분석
        
        Args:
            file_path: 파일 경로
            content: 파일 내용
            
        Returns:
            분석 결과
        """
        result = {"type": "yaml"}
        
        try:
            import yaml
            yaml_data = yaml.safe_load(content)
            
            if isinstance(yaml_data, dict):
                result["keys"] = list(yaml_data.keys())
                
                # Docker Compose 파일 특별 처리
                if "version" in yaml_data and "services" in yaml_data:
                    result["is_docker_compose"] = True
                    result["services"] = list(yaml_data["services"].keys()) if isinstance(yaml_data["services"], dict) else []
                
                # GitHub Actions 워크플로우 파일 특별 처리
                elif "name" in yaml_data and "on" in yaml_data and "jobs" in yaml_data:
                    result["is_github_workflow"] = True
                    result["workflow_name"] = yaml_data["name"]
                    result["jobs"] = list(yaml_data["jobs"].keys()) if isinstance(yaml_data["jobs"], dict) else []
        
        except ImportError:
            logger.warning("YAML 라이브러리를 사용할 수 없습니다. PyYAML 설치를 권장합니다.")
            result["error"] = "YAML 라이브러리 누락 (PyYAML 설치 필요)"
            
        except Exception as e:
            logger.error(f"YAML 파일 분석 중 예외 발생 ({file_path}): {str(e)}")
            result["error"] = f"YAML 분석 실패: {str(e)}"
            
        return result
    
    def _analyze_markdown(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Markdown 파일 분석
        
        Args:
            file_path: 파일 경로
            content: 파일 내용
            
        Returns:
            분석 결과
        """
        result = {"type": "markdown"}
        
        # 제목 추출
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            result["title"] = title_match.group(1).strip()
            
        # 부제목 추출
        subtitle_match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
        if subtitle_match:
            result["subtitle"] = subtitle_match.group(1).strip()
            
        # 목차 추출
        headings = re.findall(r'^(#+)\s+(.+)$', content, re.MULTILINE)
        if headings:
            result["headings"] = [{
                "level": len(h[0]),
                "text": h[1].strip()
            } for h in headings]
            
        # 코드 블록 추출
        code_blocks = re.findall(r'```(\w*)\n(.*?)```', content, re.DOTALL)
        if code_blocks:
            result["code_blocks"] = [{
                "language": cb[0],
                "length": len(cb[1].split('\n'))
            } for cb in code_blocks]
            
        return result
    
    def _get_name_from_node(self, node: ast.AST) -> str:
        """
        AST 노드에서 이름 정보 추출
        
        Args:
            node: AST 노드
            
        Returns:
            추출된 이름
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name_from_node(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name_from_node(node.value)}[{self._get_name_from_node(node.slice)}]"
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Num):
            return str(node.n)
        elif isinstance(node, ast.NameConstant):
            return str(node.value)
        elif isinstance(node, ast.Call):
            args = []
            if hasattr(node, 'args') and node.args:
                args = [self._get_name_from_node(arg) for arg in node.args]
            return f"{self._get_name_from_node(node.func)}({', '.join(args)})"
        else:
            return str(type(node).__name__)
    
    def _generate_summary(self, analysis_result: Dict[str, Any]) -> str:
        """
        분석 결과에서 요약 생성
        
        Args:
            analysis_result: 파일 분석 결과
            
        Returns:
            요약 문자열
        """
        file_path = analysis_result.get("file_path", "")
        file_type = analysis_result.get("type", "unknown")
        
        summary_parts = []
        
        # 파일 유형별 요약
        if file_type == "python":
            class_count = len(analysis_result.get("classes", []))
            func_count = len(analysis_result.get("functions", []))
            
            if analysis_result.get("is_router", False):
                endpoint_count = len(analysis_result.get("endpoints", []))
                summary_parts.append(f"API 라우터 파일: {endpoint_count}개 엔드포인트")
            elif analysis_result.get("is_model", False):
                model_count = len(analysis_result.get("models", []))
                summary_parts.append(f"모델 정의 파일: {model_count}개 모델")
            elif analysis_result.get("is_database", False):
                summary_parts.append("데이터베이스 관련 파일")
            elif analysis_result.get("is_test", False):
                summary_parts.append("테스트 파일")
            else:
                summary_parts.append(f"Python 모듈: {class_count}개 클래스, {func_count}개 함수")
                
        elif file_type in ["javascript", "typescript"]:
            framework = analysis_result.get("framework", "")
            if framework:
                summary_parts.append(f"{framework} {file_type} 파일")
            else:
                summary_parts.append(f"{file_type} 파일")
                
            if analysis_result.get("is_router", False):
                endpoint_count = len(analysis_result.get("endpoints", []))
                summary_parts.append(f"{endpoint_count}개 라우트 정의")
                
        elif file_type == "react":
            component_count = len(analysis_result.get("components", []))
            summary_parts.append(f"React 컴포넌트 파일: {component_count}개 컴포넌트")
            
        elif file_type == "json":
            if analysis_result.get("is_package_json", False):
                summary_parts.append("NPM 패키지 설정 파일")
            else:
                summary_parts.append("JSON 설정 파일")
                
        elif file_type == "yaml":
            if analysis_result.get("is_docker_compose", False):
                service_count = len(analysis_result.get("services", []))
                summary_parts.append(f"Docker Compose 설정 파일: {service_count}개 서비스")
            elif analysis_result.get("is_github_workflow", False):
                summary_parts.append(f"GitHub Actions 워크플로우: {analysis_result.get('workflow_name', '')}")
            else:
                summary_parts.append("YAML 설정 파일")
                
        elif file_type == "markdown":
            summary_parts.append(f"마크다운 문서: {analysis_result.get('title', '제목 없음')}")
            
        else:
            summary_parts.append(f"{file_type} 파일")
            
        return " - ".join(summary_parts)