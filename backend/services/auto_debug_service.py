"""
자동 디버깅 서비스 모듈

코드 오류를 자동으로 분석하고 수정 방안을 제안하는 서비스를 제공합니다.
"""

import os
import re
import ast
import traceback
import importlib
import inspect
import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from sqlalchemy.orm import Session

from ..database.operations.indexing import (
    get_codebase_files,
    get_file_embeddings,
    get_codebase_embeddings_stats
)
from ..services.indexing_service import IndexingService
from ..services.llm_service import LLMService
from ..models.enums import LLMType
from ..exceptions import LLMError, TokenLimitExceeded

# 로거 설정
logger = logging.getLogger(__name__)


class AutoDebugService:
    """자동 디버깅 서비스 클래스"""
    
    def __init__(self, db: Session, llm_type: LLMType = LLMType.OPENAI_API):
        """서비스 초기화"""
        self.db = db
        self.llm_type = llm_type
        self.llm_service = LLMService()
        self.indexing_service = IndexingService(db)
    
    async def analyze_error(
        self, 
        error_message: str, 
        traceback_text: str, 
        codebase_id: int,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        에러 분석 및 수정 방안 제안
        
        Args:
            error_message: 에러 메시지
            traceback_text: 에러 트레이스백
            codebase_id: 코드베이스 ID
            additional_context: 추가 컨텍스트 정보 (선택 사항)
            
        Returns:
            분석 결과 및 수정 방안
        """
        try:
            # 1. 에러 정보 파싱
            error_info = self._parse_error_info(error_message, traceback_text)
            
            # 2. 관련 코드 찾기
            relevant_code = await self._find_relevant_code(error_info, codebase_id)
            
            # 3. LLM에 분석 요청
            analysis_result = await self._analyze_with_llm(error_info, relevant_code, additional_context)
            
            # 4. 결과 정리 및 반환
            return {
                "error_info": error_info,
                "relevant_code": relevant_code,
                "analysis": analysis_result["analysis"],
                "fix_suggestions": analysis_result["fix_suggestions"],
                "confidence": analysis_result["confidence"]
            }
        except Exception as e:
            logger.error(f"에러 분석 중 오류 발생: {str(e)}")
            return {
                "error": str(e),
                "error_info": self._parse_error_info(error_message, traceback_text),
                "analysis": "에러 분석 중 오류가 발생했습니다.",
                "fix_suggestions": []
            }
    
    async def auto_fix_error(
        self, 
        error_message: str, 
        traceback_text: str, 
        codebase_id: int,
        apply_fix: bool = False,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        에러 자동 수정 시도
        
        Args:
            error_message: 에러 메시지
            traceback_text: 에러 트레이스백
            codebase_id: 코드베이스 ID
            apply_fix: 수정 사항 즉시 적용 여부
            additional_context: 추가 컨텍스트 정보 (선택 사항)
            
        Returns:
            수정 결과
        """
        try:
            # 에러 분석
            analysis_result = await self.analyze_error(
                error_message, 
                traceback_text, 
                codebase_id,
                additional_context
            )
            
            if "error" in analysis_result:
                return analysis_result
            
            # 자동 수정 생성
            fix_code = await self._generate_fix(
                analysis_result["error_info"],
                analysis_result["relevant_code"],
                analysis_result["fix_suggestions"]
            )
            
            result = {
                "analysis": analysis_result["analysis"],
                "fix_suggestions": analysis_result["fix_suggestions"],
                "fixed_files": fix_code
            }
            
            # 수정 사항 즉시 적용 (옵션)
            if apply_fix and fix_code:
                applied_fixes = await self._apply_fixes(fix_code)
                result["applied_fixes"] = applied_fixes
            
            return result
        except Exception as e:
            logger.error(f"자동 수정 중 오류 발생: {str(e)}")
            return {
                "error": str(e),
                "analysis": "자동 수정 중 오류가 발생했습니다."
            }
    
    async def debug_import_error(
        self,
        module_name: str,
        error_message: str,
        codebase_id: int
    ) -> Dict[str, Any]:
        """
        모듈 가져오기 오류 디버깅
        
        Args:
            module_name: 가져오기 실패한 모듈 이름
            error_message: 에러 메시지
            codebase_id: 코드베이스 ID
            
        Returns:
            분석 결과 및 수정 방안
        """
        try:
            # 1. 의존성 분석
            dependencies = await self._analyze_module_dependencies(module_name, codebase_id)
            
            # 2. 설치 상태 확인
            installation_status = self._check_module_installation(module_name)
            
            # 3. LLM에 분석 요청
            context = f"""
            모듈 이름: {module_name}
            오류 메시지: {error_message}
            설치 상태: {installation_status['status']}
            관련 파일: {', '.join(dependencies['related_files'])}
            """
            
            analysis_result = await self._get_import_error_solution(module_name, error_message, context)
            
            return {
                "module_name": module_name,
                "error_message": error_message,
                "installation_status": installation_status,
                "dependencies": dependencies,
                "analysis": analysis_result["analysis"],
                "solution": analysis_result["solution"],
                "install_command": analysis_result["install_command"]
            }
        except Exception as e:
            logger.error(f"가져오기 오류 디버깅 중 문제 발생: {str(e)}")
            return {
                "error": str(e),
                "module_name": module_name,
                "analysis": "가져오기 오류 디버깅 중 문제가 발생했습니다."
            }
    
    async def verify_environment(self, codebase_id: int) -> Dict[str, Any]:
        """
        코드베이스의 환경 설정 검증
        
        Args:
            codebase_id: 코드베이스 ID
            
        Returns:
            환경 검증 결과
        """
        try:
            # 1. 환경 설정 파일 찾기
            env_files = await self._find_environment_files(codebase_id)
            
            # 2. 패키지 요구사항 분석
            requirements = await self._analyze_requirements(codebase_id)
            
            # 3. 현재 환경과 비교
            env_analysis = self._compare_with_current_env(requirements)
            
            # 4. 환경 검증 결과 반환
            return {
                "environment_files": env_files,
                "requirements": requirements,
                "environment_analysis": env_analysis,
                "missing_packages": env_analysis["missing_packages"],
                "version_mismatch": env_analysis["version_mismatch"],
                "setup_commands": env_analysis["setup_commands"]
            }
        except Exception as e:
            logger.error(f"환경 검증 중 오류 발생: {str(e)}")
            return {
                "error": str(e),
                "environment_files": [],
                "requirements": {},
                "environment_analysis": {
                    "missing_packages": [],
                    "version_mismatch": [],
                    "setup_commands": []
                }
            }
    
    def _parse_error_info(self, error_message: str, traceback_text: str) -> Dict[str, Any]:
        """
        에러 정보 파싱
        
        Args:
            error_message: 에러 메시지
            traceback_text: 에러 트레이스백
            
        Returns:
            파싱된 에러 정보
        """
        error_info = {
            "error_message": error_message,
            "traceback_text": traceback_text,
            "error_type": "Unknown",
            "error_location": {
                "file": None,
                "line": None,
                "function": None
            },
            "code_lines": []
        }
        
        try:
            # 에러 타입 추출
            error_type_match = re.search(r'([\w\.]+)(?:: |Error: |Exception: )', error_message)
            if error_type_match:
                error_info["error_type"] = error_type_match.group(1)
            
            # 트레이스백에서 파일 및 라인 정보 추출
            file_line_matches = re.findall(r'File "([^"]+)", line (\d+), in ([\w<>\.]+)', traceback_text)
            if file_line_matches:
                # 마지막 항목이 일반적으로 실제 오류 발생 위치
                file_path, line_num, function = file_line_matches[-1]
                error_info["error_location"] = {
                    "file": file_path,
                    "line": int(line_num),
                    "function": function
                }
            
            # 트레이스백에서 코드 라인 추출
            code_lines = []
            for line in traceback_text.split('\n'):
                if line.strip() and not line.strip().startswith('File "'):
                    # 라인 앞에 나오는 공백 및 숫자, 화살표 등을 제거
                    code_line = re.sub(r'^\s*\d*\s*[>\s]*', '', line)
                    if code_line:
                        code_lines.append(code_line)
            
            error_info["code_lines"] = code_lines
        except Exception as e:
            logger.error(f"에러 정보 파싱 중 오류 발생: {str(e)}")
        
        return error_info
    
    async def _find_relevant_code(self, error_info: Dict[str, Any], codebase_id: int) -> Dict[str, Any]:
        """
        에러와 관련된 코드 검색
        
        Args:
            error_info: 파싱된 에러 정보
            codebase_id: 코드베이스 ID
            
        Returns:
            관련 코드 정보
        """
        relevant_code = {
            "error_file": None,
            "error_file_content": None,
            "related_files": [],
            "similar_code": []
        }
        
        try:
            # 에러 발생 파일 찾기
            error_file = error_info["error_location"]["file"]
            if error_file:
                # 코드베이스에서 파일 찾기
                files = get_codebase_files(self.db, codebase_id)
                
                for file in files:
                    if file.path.endswith(os.path.basename(error_file)):
                        relevant_code["error_file"] = file.path
                        relevant_code["error_file_content"] = file.content
                        break
            
            # 유사한 코드 검색
            error_query = f"{error_info['error_type']} {error_info['error_message']}"
            similar_code = await self.indexing_service.search_similar_code(
                query=error_query,
                limit=5,
                threshold=0.5,
                codebase_id=codebase_id
            )
            
            relevant_code["similar_code"] = similar_code
            
            # 관련 파일 추출
            related_files = set()
            if relevant_code["error_file"]:
                related_files.add(relevant_code["error_file"])
            
            for code in similar_code:
                related_files.add(code["file_path"])
            
            relevant_code["related_files"] = list(related_files)
        except Exception as e:
            logger.error(f"관련 코드 검색 중 오류 발생: {str(e)}")
        
        return relevant_code
    
    async def _analyze_with_llm(
        self, 
        error_info: Dict[str, Any], 
        relevant_code: Dict[str, Any],
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        LLM을 사용한 에러 분석
        
        Args:
            error_info: 파싱된 에러 정보
            relevant_code: 관련 코드 정보
            additional_context: 추가 컨텍스트 정보
            
        Returns:
            분석 결과
        """
        try:
            # 프롬프트 구성
            prompt = f"""당신은 파이썬 코드 디버깅 전문가입니다. 다음 에러를 분석하고 해결책을 제시해주세요.

## 에러 정보
에러 타입: {error_info['error_type']}
에러 메시지: {error_info['error_message']}

## 트레이스백
```
{error_info['traceback_text']}
```

## 에러 위치
파일: {error_info['error_location']['file']}
라인: {error_info['error_location']['line']}
함수: {error_info['error_location']['function']}

"""

            # 에러 파일 내용 추가
            if relevant_code["error_file_content"]:
                prompt += f"""
## 에러 발생 파일 내용
```python
{relevant_code["error_file_content"]}
```
"""

            # 유사 코드 추가
            if relevant_code["similar_code"]:
                prompt += "\n## 관련 코드\n"
                for i, code in enumerate(relevant_code["similar_code"][:3]):
                    prompt += f"""
### 파일: {code['file_path']}
```python
{code['content']}
```
"""

            # 추가 컨텍스트 정보
            if additional_context:
                prompt += f"""
## 추가 정보
{additional_context}
"""

            prompt += """
## 요청사항
1. 에러의 원인을 자세히 분석해주세요.
2. 구체적인 수정 방안을 제시해주세요. 가능하면 수정해야 할 코드를 정확히 알려주세요.
3. 코드 수정 제안사항을 다음 JSON 형식으로 제공해주세요:
```json
{
  "analysis": "에러 원인에 대한 상세 분석",
  "fix_suggestions": [
    {
      "file": "수정할 파일 경로",
      "line": 수정할 라인 번호 (정수),
      "original_code": "원본 코드",
      "fixed_code": "수정된 코드",
      "explanation": "수정 내용 설명"
    }
  ],
  "confidence": 0.8  # 0.0에서 1.0 사이의 신뢰도
}
```

JSON 형식으로 응답해주세요.
"""

            # LLM에 요청
            response = await self.llm_service.get_response(self.llm_type, prompt)
            
            # JSON 응답 추출
            json_response = self._extract_json_from_text(response)
            
            if not json_response:
                # JSON이 없는 경우 기본 형식 생성
                return {
                    "analysis": "LLM이 적절한 JSON 형식으로 응답하지 않았습니다. 원본 응답: " + response[:200] + "...",
                    "fix_suggestions": [],
                    "confidence": 0.0
                }
            
            return json_response
        except Exception as e:
            logger.error(f"LLM 분석 중 오류 발생: {str(e)}")
            return {
                "analysis": f"LLM 분석 중 오류가 발생했습니다: {str(e)}",
                "fix_suggestions": [],
                "confidence": 0.0
            }
    
    async def _generate_fix(
        self, 
        error_info: Dict[str, Any], 
        relevant_code: Dict[str, Any],
        fix_suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        수정 코드 생성
        
        Args:
            error_info: 파싱된 에러 정보
            relevant_code: 관련 코드 정보
            fix_suggestions: 수정 제안 목록
            
        Returns:
            수정된 파일 목록
        """
        fixed_files = []
        
        for suggestion in fix_suggestions:
            try:
                file_path = suggestion.get("file")
                if not file_path:
                    continue
                
                original_code = None
                full_content = None
                
                # 파일 내용 가져오기
                if file_path == relevant_code.get("error_file"):
                    full_content = relevant_code.get("error_file_content")
                else:
                    # 다른 파일인 경우 코드베이스에서 찾기
                    for code_info in relevant_code.get("similar_code", []):
                        if code_info.get("file_path") == file_path:
                            full_content = code_info.get("content")
                            break
                
                if not full_content:
                    continue
                
                # 수정할 코드 블록 찾기
                line_num = suggestion.get("line")
                original_code = suggestion.get("original_code")
                fixed_code = suggestion.get("fixed_code")
                
                if not original_code or not fixed_code:
                    continue
                
                # 파일 전체 내용 수정
                updated_content = self._replace_code_in_file(
                    full_content, 
                    original_code, 
                    fixed_code,
                    line_num
                )
                
                fixed_files.append({
                    "file": file_path,
                    "original_content": full_content,
                    "updated_content": updated_content,
                    "modification": {
                        "line": line_num,
                        "original_code": original_code,
                        "fixed_code": fixed_code,
                        "explanation": suggestion.get("explanation", "")
                    }
                })
            except Exception as e:
                logger.error(f"수정 코드 생성 중 오류 발생: {str(e)}")
        
        return fixed_files
    
    async def _apply_fixes(self, fixed_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        수정 사항 적용
        
        Args:
            fixed_files: 수정된 파일 목록
            
        Returns:
            적용 결과 목록
        """
        applied_fixes = []
        
        for file_info in fixed_files:
            try:
                file_path = file_info.get("file")
                updated_content = file_info.get("updated_content")
                
                if not file_path or not updated_content:
                    continue
                
                # 실제 파일 경로 확인
                abs_path = Path(file_path).resolve()
                
                # 파일 존재 여부 확인
                if not abs_path.exists():
                    applied_fixes.append({
                        "file": file_path,
                        "success": False,
                        "message": "파일이 존재하지 않습니다."
                    })
                    continue
                
                # 파일 쓰기
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                applied_fixes.append({
                    "file": file_path,
                    "success": True,
                    "message": "수정 사항이 적용되었습니다."
                })
            except Exception as e:
                applied_fixes.append({
                    "file": file_path if 'file_path' in locals() else "Unknown",
                    "success": False,
                    "message": f"수정 사항 적용 중 오류 발생: {str(e)}"
                })
        
        return applied_fixes
    
    def _replace_code_in_file(
        self, 
        file_content: str, 
        original_code: str, 
        fixed_code: str,
        line_num: Optional[int] = None
    ) -> str:
        """
        파일 내용에서 코드 블록 교체
        
        Args:
            file_content: 파일 전체 내용
            original_code: 원본 코드 블록
            fixed_code: 수정된 코드 블록
            line_num: 코드 라인 번호 (옵션)
            
        Returns:
            수정된 파일 내용
        """
        # 코드 블록 준비 (앞뒤 공백 정규화)
        original_code = original_code.strip()
        fixed_code = fixed_code.strip()
        
        # 라인 번호가 제공된 경우 해당 라인 주변 컨텍스트 사용
        if line_num is not None and line_num > 0:
            lines = file_content.split('\n')
            
            # 라인 번호가 범위 내인지 확인
            if 1 <= line_num <= len(lines):
                # 해당 라인과 주변 5개 라인 검색 (총 11줄)
                start_line = max(1, line_num - 5)
                end_line = min(len(lines), line_num + 5)
                
                # 검색 범위 내에서 원본 코드 찾기
                for i in range(start_line, end_line + 1):
                    search_block = '\n'.join(lines[i-1:min(i+len(original_code.split('\n')), len(lines))])
                    
                    if original_code in search_block:
                        # 원본 코드 교체
                        return file_content.replace(search_block, search_block.replace(original_code, fixed_code))
        
        # 단순 문자열 교체 (라인 번호가 없거나 컨텍스트 검색이 실패한 경우)
        if original_code in file_content:
            return file_content.replace(original_code, fixed_code)
        
        # 정확히 일치하는 코드 블록이 없는 경우, 유사도 기반 검색
        lines = file_content.split('\n')
        best_match = None
        best_similarity = 0
        
        for i in range(len(lines)):
            for j in range(i, min(i + 20, len(lines))):
                candidate = '\n'.join(lines[i:j+1])
                similarity = self._similarity(original_code, candidate)
                
                if similarity > best_similarity and similarity > 0.7:  # 70% 이상 유사한 경우만
                    best_match = candidate
                    best_similarity = similarity
        
        if best_match:
            return file_content.replace(best_match, fixed_code)
        
        # 일치하는 코드 블록을 찾지 못한 경우
        logger.warning(f"원본 코드 블록을 찾을 수 없습니다. 수정이 적용되지 않았습니다.")
        return file_content
    
    def _similarity(self, str1: str, str2: str) -> float:
        """
        두 문자열의 유사도 계산 (0.0 ~ 1.0)
        
        Args:
            str1: 첫 번째 문자열
            str2: 두 번째 문자열
            
        Returns:
            유사도 (0.0 ~ 1.0)
        """
        # 간단한 Jaccard 유사도 계산
        set1 = set(str1.split())
        set2 = set(str2.split())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1) + len(set2) - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        텍스트에서 JSON 추출
        
        Args:
            text: 텍스트
            
        Returns:
            추출된 JSON 데이터 또는 None
        """
        # JSON 블록 추출
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 마크다운 코드 블록이 없는 경우 일반 JSON 찾기
            json_match = re.search(r'({[\s\S]*})', text)
            if json_match:
                json_str = json_match.group(1)
            else:
                return None
        
        try:
            # JSON 파싱
            json_data = json.loads(json_str)
            return json_data
        except json.JSONDecodeError:
            logger.error("JSON 파싱 실패")
            return None
    
    async def _analyze_module_dependencies(self, module_name: str, codebase_id: int) -> Dict[str, Any]:
        """
        모듈 의존성 분석
        
        Args:
            module_name: 모듈 이름
            codebase_id: 코드베이스 ID
            
        Returns:
            의존성 분석 결과
        """
        result = {
            "module_name": module_name,
            "related_files": [],
            "import_patterns": []
        }
        
        try:
            # 코드베이스 파일 조회
            files = get_codebase_files(self.db, codebase_id)
            
            # 각 파일에서 모듈 임포트 패턴 찾기
            for file in files:
                if not file.content or not file.path.endswith('.py'):
                    continue
                
                import_pattern = None
                file_imports_module = False
                
                # 임포트 패턴 확인
                if re.search(fr'\bimport\s+{module_name}\b', file.content):
                    import_pattern = f"import {module_name}"
                    file_imports_module = True
                elif re.search(fr'\bfrom\s+{module_name}\s+import\b', file.content):
                    import_pattern = f"from {module_name} import ..."
                    file_imports_module = True
                elif '.' in module_name:
                    base_module = module_name.split('.')[0]
                    if re.search(fr'\bimport\s+{base_module}\b', file.content):
                        import_pattern = f"import {base_module} (possibly uses {module_name})"
                        file_imports_module = True
                    elif re.search(fr'\bfrom\s+{base_module}\s+import\b', file.content):
                        import_pattern = f"from {base_module} import ... (possibly uses {module_name})"
                        file_imports_module = True
                
                if file_imports_module:
                    result["related_files"].append(file.path)
                    if import_pattern and import_pattern not in result["import_patterns"]:
                        result["import_patterns"].append(import_pattern)
        except Exception as e:
            logger.error(f"모듈 의존성 분석 중 오류 발생: {str(e)}")
        
        return result
    
    def _check_module_installation(self, module_name: str) -> Dict[str, Any]:
        """
        모듈 설치 상태 확인
        
        Args:
            module_name: 모듈 이름
            
        Returns:
            설치 상태 정보
        """
        result = {
            "module_name": module_name,
            "status": "not_found",
            "installed_version": None,
            "installation_path": None,
            "is_standard_library": False
        }
        
        try:
            # 표준 라이브러리인지 확인
            stdlib_modules = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()
            base_module = module_name.split('.')[0]
            
            if base_module in stdlib_modules:
                result["status"] = "standard_library"
                result["is_standard_library"] = True
                return result
            
            # 모듈 임포트 시도
            try:
                if '.' in module_name:
                    base_module = module_name.split('.')[0]
                    mod = importlib.import_module(base_module)
                    
                    # 서브모듈 확인
                    submodules = module_name.split('.')
                    for i in range(1, len(submodules)):
                        sub_path = '.'.join(submodules[:i+1])
                        try:
                            sub_mod = importlib.import_module(sub_path)
                        except ImportError:
                            result["status"] = "partial_import"
                            result["installed_version"] = getattr(mod, '__version__', None)
                            result["installation_path"] = getattr(mod, '__file__', None)
                            return result
                    
                    # 모든 서브모듈이 있는 경우
                    result["status"] = "installed"
                    result["installed_version"] = getattr(mod, '__version__', None)
                    result["installation_path"] = getattr(mod, '__file__', None)
                else:
                    mod = importlib.import_module(module_name)
                    result["status"] = "installed"
                    result["installed_version"] = getattr(mod, '__version__', None)
                    result["installation_path"] = getattr(mod, '__file__', None)
            except ImportError:
                result["status"] = "not_found"
            
            # 추가 정보 수집 (설치는 되었지만 버전이 안 맞는 경우 등)
            if result["status"] == "installed":
                try:
                    import pkg_resources
                    dist = pkg_resources.get_distribution(base_module)
                    result["installed_version"] = dist.version
                except (ImportError, pkg_resources.DistributionNotFound):
                    pass
        except Exception as e:
            logger.error(f"모듈 설치 상태 확인 중 오류 발생: {str(e)}")
        
        return result
    
    async def _get_import_error_solution(
        self, 
        module_name: str, 
        error_message: str, 
        context: str
    ) -> Dict[str, Any]:
        """
        임포트 오류 해결책 생성
        
        Args:
            module_name: 모듈 이름
            error_message: 오류 메시지
            context: 추가 컨텍스트
            
        Returns:
            해결책 정보
        """
        try:
            # 프롬프트 구성
            prompt = f"""당신은 파이썬 패키지와 모듈 문제를 해결하는 전문가입니다. 다음 모듈 가져오기 오류를 분석하고 해결책을 제시해주세요.

## 오류 정보
모듈 이름: {module_name}
오류 메시지: {error_message}

## 추가 컨텍스트
{context}

다음 형식으로 JSON 응답을 제공해주세요:

```json
{{
  "analysis": "오류 원인에 대한 상세 분석",
  "solution": "문제 해결을 위한 단계별 가이드",
  "install_command": "pip install package_name"
}}
```

JSON 형식으로 응답해주세요.
"""

            # LLM에 요청
            response = await self.llm_service.get_response(self.llm_type, prompt)
            
            # JSON 응답 추출
            json_response = self._extract_json_from_text(response)
            
            if not json_response:
                # JSON이 없는 경우 기본 형식 생성
                return {
                    "analysis": "LLM이 적절한 JSON 형식으로 응답하지 않았습니다",
                    "solution": f"추천 해결책: pip install {module_name}",
                    "install_command": f"pip install {module_name}"
                }
            
            return json_response
        except Exception as e:
            logger.error(f"임포트 오류 해결책 생성 중 오류 발생: {str(e)}")
            return {
                "analysis": f"해결책 생성 중 오류가 발생했습니다: {str(e)}",
                "solution": f"pip install {module_name} 명령어로 설치를 시도해보세요.",
                "install_command": f"pip install {module_name}"
            }
    
    async def _find_environment_files(self, codebase_id: int) -> List[Dict[str, Any]]:
        """
        환경 설정 파일 찾기
        
        Args:
            codebase_id: 코드베이스 ID
            
        Returns:
            환경 설정 파일 목록
        """
        env_files = []
        
        try:
            # 코드베이스 파일 조회
            files = get_codebase_files(self.db, codebase_id)
            
            # 환경 설정 파일 패턴
            env_file_patterns = [
                r'requirements\.txt,
                r'setup\.py,
                r'pyproject\.toml,
                r'Pipfile,
                r'environment\.ya?ml,
                r'\.env,
                r'runtime\.txt,
                r'conda_environment\.ya?ml,
                r'docker-compose\.ya?ml,
                r'Dockerfile
            ]
            
            for file in files:
                for pattern in env_file_patterns:
                    if re.search(pattern, file.path, re.IGNORECASE):
                        env_files.append({
                            "file_path": file.path,
                            "file_type": os.path.basename(file.path),
                            "content": file.content
                        })
                        break
        except Exception as e:
            logger.error(f"환경 설정 파일 검색 중 오류 발생: {str(e)}")
        
        return env_files
    
    async def _analyze_requirements(self, codebase_id: int) -> Dict[str, Any]:
        """
        패키지 요구사항 분석
        
        Args:
            codebase_id: 코드베이스 ID
            
        Returns:
            패키지 요구사항 정보
        """
        requirements = {
            "required_packages": [],
            "direct_imports": set(),
            "third_party_imports": {},
            "has_requirements_file": False,
            "has_setup_py": False,
            "detected_python_version": None
        }
        
        try:
            # 환경 설정 파일 찾기
            env_files = await self._find_environment_files(codebase_id)
            
            # requirements.txt 파싱
            for env_file in env_files:
                if 'requirements.txt' in env_file["file_path"].lower():
                    requirements["has_requirements_file"] = True
                    content = env_file["content"]
                    if content:
                        for line in content.splitlines():
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # 버전 요구사항 처리
                                parts = re.split(r'[=<>~]', line)
                                package = parts[0].strip()
                                version_req = line[len(package):].strip()
                                
                                requirements["required_packages"].append({
                                    "name": package,
                                    "version_requirement": version_req if version_req else "any"
                                })
                
                # setup.py 파싱
                elif 'setup.py' in env_file["file_path"].lower():
                    requirements["has_setup_py"] = True
                    content = env_file["content"]
                    
                    # install_requires 검색
                    install_requires_match = re.search(r'install_requires\s*=\s*\[([\s\S]*?)\]', content)
                    if install_requires_match:
                        install_requires = install_requires_match.group(1)
                        # 문자열 패턴 찾기
                        package_matches = re.finditer(r'["\']([^"\']+)["\']', install_requires)
                        
                        for match in package_matches:
                            package_req = match.group(1)
                            parts = re.split(r'[=<>~]', package_req)
                            package = parts[0].strip()
                            version_req = package_req[len(package):].strip()
                            
                            requirements["required_packages"].append({
                                "name": package,
                                "version_requirement": version_req if version_req else "any"
                            })
                
                # Python 버전 검색
                if 'runtime.txt' in env_file["file_path"].lower():
                    content = env_file["content"]
                    if content:
                        python_version_match = re.search(r'python-(\d+\.\d+\.\d+|\d+\.\d+)', content)
                        if python_version_match:
                            requirements["detected_python_version"] = python_version_match.group(1)
                
                # .env 파일에서 환경 변수 검색
                elif '.env' in env_file["file_path"].lower():
                    content = env_file["content"]
                    if content:
                        python_version_match = re.search(r'PYTHON_VERSION\s*=\s*(\d+\.\d+\.\d+|\d+\.\d+)', content)
                        if python_version_match:
                            requirements["detected_python_version"] = python_version_match.group(1)
            
            # 코드베이스에서 import 문 분석
            files = get_codebase_files(self.db, codebase_id)
            stdlib_modules = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()
            
            for file in files:
                if not file.content or not file.path.endswith('.py'):
                    continue
                
                try:
                    # AST를 사용한 import 문 분석
                    tree = ast.parse(file.content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for name in node.names:
                                module_name = name.name.split('.')[0]
                                requirements["direct_imports"].add(module_name)
                                
                                # 표준 라이브러리가 아닌 경우만 기록
                                if module_name not in stdlib_modules:
                                    if module_name not in requirements["third_party_imports"]:
                                        requirements["third_party_imports"][module_name] = []
                                    requirements["third_party_imports"][module_name].append(file.path)
                        
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                module_name = node.module.split('.')[0]
                                requirements["direct_imports"].add(module_name)
                                
                                # 표준 라이브러리가 아닌 경우만 기록
                                if module_name not in stdlib_modules:
                                    if module_name not in requirements["third_party_imports"]:
                                        requirements["third_party_imports"][module_name] = []
                                    requirements["third_party_imports"][module_name].append(file.path)
                except SyntaxError:
                    # 파싱 오류 무시 (다른 버전의 Python 코드일 수 있음)
                    pass
            
            # 직접 가져오기에서 찾은 서드파티 패키지를 요구사항에 추가
            # 단, requirements.txt나 setup.py에 없는 경우에만
            if requirements["third_party_imports"]:
                existing_packages = set(item["name"] for item in requirements["required_packages"])
                
                for package in requirements["third_party_imports"]:
                    if package not in existing_packages:
                        requirements["required_packages"].append({
                            "name": package,
                            "version_requirement": "any",
                            "source": "import_detection"
                        })
            
            # set을 list로 변환 (JSON 직렬화 가능하게)
            requirements["direct_imports"] = list(requirements["direct_imports"])
        except Exception as e:
            logger.error(f"패키지 요구사항 분석 중 오류 발생: {str(e)}")
        
        return requirements
    
    def _compare_with_current_env(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """
        현재 환경과 요구사항 비교
        
        Args:
            requirements: 패키지 요구사항 정보
            
        Returns:
            환경 분석 결과
        """
        result = {
            "missing_packages": [],
            "version_mismatch": [],
            "satisfied_requirements": [],
            "setup_commands": []
        }
        
        try:
            # 가상환경 확인
            in_virtualenv = hasattr(sys, 'real_prefix') or (
                hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
            )
            
            # Python 버전 확인
            current_python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            expected_python_version = requirements.get("detected_python_version")
            
            if expected_python_version and expected_python_version != current_python_version:
                major_minor_match = False
                if expected_python_version.count('.') == 1:  # 메이저.마이너 형식
                    current_major_minor = f"{sys.version_info.major}.{sys.version_info.minor}"
                    if current_major_minor == expected_python_version:
                        major_minor_match = True
                
                if not major_minor_match:
                    result["version_mismatch"].append({
                        "name": "python",
                        "expected_version": expected_python_version,
                        "current_version": current_python_version
                    })
                    
                    result["setup_commands"].append(f"# Python 버전 불일치: 필요 {expected_python_version}, 현재 {current_python_version}")
            
            # 가상환경 생성 명령어 추가
            if not in_virtualenv:
                result["setup_commands"].append("# 가상환경 생성 권장")
                result["setup_commands"].append("python -m venv venv")
                result["setup_commands"].append("# Windows: venv\\Scripts\\activate")
                result["setup_commands"].append("# Linux/Mac: source venv/bin/activate")
            
            # 필수 패키지 확인
            for package_info in requirements.get("required_packages", []):
                package_name = package_info["name"]
                version_req = package_info["version_requirement"]
                
                # 설치 상태 확인
                installation_status = self._check_module_installation(package_name)
                
                if installation_status["status"] == "not_found":
                    result["missing_packages"].append({
                        "name": package_name,
                        "requirement": version_req
                    })
                    
                    if version_req and version_req != "any":
                        result["setup_commands"].append(f"pip install {package_name}{version_req}")
                    else:
                        result["setup_commands"].append(f"pip install {package_name}")
                
                elif installation_status["status"] == "installed":
                    # 버전 요구사항 확인
                    if version_req and version_req != "any" and installation_status["installed_version"]:
                        installed_version = installation_status["installed_version"]
                        
                        # 버전 비교는 복잡하므로 간단한 일치 여부만 확인
                        if "==" in version_req and version_req.split("==")[1].strip() != installed_version:
                            result["version_mismatch"].append({
                                "name": package_name,
                                "expected_version": version_req.split("==")[1].strip(),
                                "current_version": installed_version
                            })
                            
                            result["setup_commands"].append(f"pip install {package_name}{version_req} --upgrade")
                        else:
                            result["satisfied_requirements"].append({
                                "name": package_name,
                                "version": installed_version
                            })
                    else:
                        result["satisfied_requirements"].append({
                            "name": package_name,
                            "version": installation_status["installed_version"]
                        })
            
            # requirements.txt 파일이 있는 경우 설치 명령어 추가
            if requirements.get("has_requirements_file"):
                result["setup_commands"].append("# 모든 의존성 설치")
                result["setup_commands"].append("pip install -r requirements.txt")
            
            # setup.py 파일이 있는 경우 설치 명령어 추가
            elif requirements.get("has_setup_py"):
                result["setup_commands"].append("# 프로젝트 설치")
                result["setup_commands"].append("pip install -e .")
            
            # 누락된 패키지가 많은 경우 일괄 설치 명령어 추가
            if len(result["missing_packages"]) > 3:
                missing_packages = [p["name"] for p in result["missing_packages"]]
                result["setup_commands"].append(f"# 누락된 패키지 일괄 설치")
                result["setup_commands"].append(f"pip install {' '.join(missing_packages)}")
        except Exception as e:
            logger.error(f"환경 비교 중 오류 발생: {str(e)}")
            result["setup_commands"].append(f"# 환경 분석 중 오류 발생: {str(e)}")
        
        return result