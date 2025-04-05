"""
인덱싱 서비스 모듈

코드베이스 인덱싱 및 검색 기능을 제공합니다.
"""

import os
import re
import asyncio
import logging
import json
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..database.operations.indexing import (
    get_indexing_settings, create_or_update_indexing_settings,
    create_indexing_run, update_indexing_run, get_codebase_files,
    create_code_embedding, delete_file_embeddings, 
    get_file_embeddings, get_codebase_embeddings_stats,
    get_latest_indexing_run
)
from ..models.indexing import (
    IndexingStatus, CodeEmbedding, EmbeddingSearchResult,
    CodebaseIndexingRun
)
from ..models.enums import IndexingFrequency
from ..config import settings
from ..exceptions import TokenLimitExceeded

# 로거 설정
logger = logging.getLogger(__name__)


class IndexingService:
    """인덱싱 서비스 클래스"""
    
    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db
    
    async def process_indexing_run(self, run_id: int, is_full_index: bool = False):
        """
        인덱싱 실행 처리
        
        Args:
            run_id: 인덱싱 실행 ID
            is_full_index: 전체 인덱싱 여부
        """
        try:
            # 실행 정보 조회
            run = self.db.query(CodebaseIndexingRun).filter_by(id=run_id).first()
            if not run:
                logger.error(f"인덱싱 실행 ID {run_id}를 찾을 수 없습니다")
                return
            
            # 상태 업데이트
            run = update_indexing_run(
                self.db, 
                run_id, 
                {
                    "status": IndexingStatus.IN_PROGRESS,
                    "start_time": datetime.utcnow()
                }
            )
            
            # 설정 조회
            settings = get_indexing_settings(self.db, run.codebase_id)
            if not settings:
                logger.error(f"코드베이스 ID {run.codebase_id}의 인덱싱 설정을 찾을 수 없습니다")
                update_indexing_run(
                    self.db, 
                    run_id, 
                    {
                        "status": IndexingStatus.FAILED,
                        "end_time": datetime.utcnow(),
                        "error_message": f"코드베이스 ID {run.codebase_id}의 인덱싱 설정을 찾을 수 없습니다"
                    }
                )
                return
            
            # 파일 목록 조회
            files = get_codebase_files(self.db, run.codebase_id, is_directory=False)
            if not files:
                logger.error(f"코드베이스 ID {run.codebase_id}의 파일을 찾을 수 없습니다")
                update_indexing_run(
                    self.db, 
                    run_id, 
                    {
                        "status": IndexingStatus.FAILED,
                        "end_time": datetime.utcnow(),
                        "error_message": f"코드베이스 ID {run.codebase_id}의 파일을 찾을 수 없습니다"
                    }
                )
                return
            
            # 파일 필터링 (제외/우선순위 패턴)
            filtered_files = self._filter_files(files, settings.excluded_patterns, settings.priority_patterns)
            
            # 최대 파일 수 제한
            if len(filtered_files) > settings.max_files_per_run:
                filtered_files = filtered_files[:settings.max_files_per_run]
            
            # 처리 카운터
            files_processed = 0
            files_indexed = 0
            files_skipped = 0
            
            # 파일 처리
            for file in filtered_files:
                try:
                    files_processed += 1
                    
                    # 전체 인덱싱이 아니고 파일이 변경되지 않았으면 건너뛰기
                    if not is_full_index:
                        # 기존 임베딩 확인
                        existing_embeddings = get_file_embeddings(self.db, file.id)
                        if existing_embeddings and self._is_file_unchanged(file, existing_embeddings):
                            files_skipped += 1
                            continue
                    
                    # 기존 임베딩 삭제 (새로 생성)
                    delete_file_embeddings(self.db, file.id)
                    
                    # 파일 내용이 없으면 건너뛰기
                    if not file.content:
                        files_skipped += 1
                        continue
                    
                    # 파일 내용을 청크로 분할
                    chunks = self.chunk_file_content(
                        file.content,
                        settings.chunk_size,
                        settings.chunk_overlap
                    )
                    
                    # 각 청크 처리
                    for i, chunk in enumerate(chunks):
                        # 임베딩 생성
                        embedding = await self.get_embeddings(chunk["content"], settings.embedding_model)
                        
                        # 메타데이터 추출
                        metadata = self._extract_code_metadata(chunk["content"], file.path)
                        
                        # 임베딩 저장
                        create_code_embedding(
                            self.db,
                            codebase_id=run.codebase_id,
                            file_id=file.id,
                            chunk_id=f"{file.path}:{chunk['start_line']}-{chunk['end_line']}",
                            content=chunk["content"],
                            embedding=embedding,
                            metadata=metadata,
                            run_id=run.id
                        )
                    
                    files_indexed += 1
                    
                    # 인덱싱 실행 상태 업데이트 (주기적)
                    if files_processed % 10 == 0:
                        update_indexing_run(
                            self.db, 
                            run_id, 
                            {
                                "files_processed": files_processed,
                                "files_indexed": files_indexed,
                                "files_skipped": files_skipped
                            }
                        )
                
                except Exception as e:
                    logger.error(f"파일 '{file.path}' 인덱싱 중 오류 발생: {str(e)}")
                    files_skipped += 1
            
            # 실행 완료
            update_indexing_run(
                self.db, 
                run_id, 
                {
                    "status": IndexingStatus.COMPLETED,
                    "end_time": datetime.utcnow(),
                    "files_processed": files_processed,
                    "files_indexed": files_indexed,
                    "files_skipped": files_skipped
                }
            )
            
            logger.info(f"인덱싱 완료: 처리 {files_processed}, 인덱싱 {files_indexed}, 건너뛰기 {files_skipped}")
        
        except Exception as e:
            logger.error(f"인덱싱 실행 중 오류 발생: {str(e)}")
            try:
                update_indexing_run(
                    self.db, 
                    run_id, 
                    {
                        "status": IndexingStatus.FAILED,
                        "end_time": datetime.utcnow(),
                        "error_message": str(e)
                    }
                )
            except:
                pass
    
    def chunk_file_content(
        self, 
        content: str, 
        chunk_size: int, 
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """
        파일 내용을 청크로 분할
        
        Args:
            content: 파일 내용
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 간 겹침 정도
            
        Returns:
            청크 목록 (각 청크는 내용, 시작 라인, 끝 라인 포함)
        """
        # 라인 별로 분할
        lines = content.splitlines()
        chunks = []
        
        current_chunk = []
        current_size = 0
        start_line = 1
        
        for i, line in enumerate(lines):
            line_size = len(line)
            
            # 현재 청크가 빈 상태이거나 라인을 추가해도 크기를 초과하지 않는 경우
            if not current_chunk or current_size + line_size <= chunk_size:
                current_chunk.append(line)
                current_size += line_size
            else:
                # 현재 청크 저장
                chunks.append({
                    "content": "\n".join(current_chunk),
                    "start_line": start_line,
                    "end_line": start_line + len(current_chunk) - 1
                })
                
                # 오버랩 계산
                overlap_lines = max(0, int(len(current_chunk) * (chunk_overlap / current_size)))
                
                # 새 청크 시작 (오버랩 고려)
                start_line = start_line + len(current_chunk) - overlap_lines
                current_chunk = current_chunk[-overlap_lines:] if overlap_lines > 0 else []
                current_chunk.append(line)
                current_size = sum(len(l) for l in current_chunk)
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append({
                "content": "\n".join(current_chunk),
                "start_line": start_line,
                "end_line": start_line + len(current_chunk) - 1
            })
        
        return chunks
    
    async def get_embeddings(self, text: str, model: str) -> List[float]:
        """
        텍스트 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
            model: 임베딩 모델
            
        Returns:
            임베딩 벡터
        """
        try:
            # 입력 텍스트가 너무 길면 잘라내기
            if len(text) > 8000:
                text = text[:8000]
            
            # OpenAI API 임베딩
            if model.startswith("openai/"):
                import openai
                
                # API 키 설정
                openai.api_key = settings.llm.openai_api_key
                
                # 모델 이름 추출
                model_name = model.split("/")[1]
                
                # 임베딩 생성
                response = await openai.AsyncOpenAI().embeddings.create(
                    input=text,
                    model=model_name
                )
                
                # 임베딩 벡터 반환
                return response.data[0].embedding
            
            # 기타 모델
            else:
                raise ValueError(f"지원하지 않는 임베딩 모델: {model}")
        
        except Exception as e:
            logger.error(f"임베딩 생성 중 오류 발생: {str(e)}")
            # 오류 발생 시 빈 벡터 반환
            return [0.0] * 1536  # 기본 차원
    
    async def search_similar_code(
        self, 
        query: str, 
        limit: int, 
        threshold: float, 
        codebase_id: int,
        file_patterns: Optional[List[str]] = None
    ) -> List[EmbeddingSearchResult]:
        """
        유사 코드 검색
        
        Args:
            query: 검색 쿼리
            limit: 최대 결과 수
            threshold: 유사도 임계값
            codebase_id: 코드베이스 ID
            file_patterns: 파일 패턴 (선택 사항)
            
        Returns:
            검색 결과
        """
        try:
            # 설정 조회
            settings = get_indexing_settings(self.db, codebase_id)
            if not settings:
                raise HTTPException(
                    status_code=404, 
                    detail=f"코드베이스 ID {codebase_id}의 인덱싱 설정을 찾을 수 없습니다"
                )
            
            # 쿼리 임베딩 생성
            query_embedding = await self.get_embeddings(query, settings.embedding_model)
            
            # 인덱싱된 파일 목록 조회
            # TODO: 실제 구현에서는 벡터 유사도 검색을 위한 최적화된 방식이 필요
            # SQL 데이터베이스에서 직접 모든 임베딩을 가져와 메모리에서 계산하는 방식은 비효율적임
            
            from sqlalchemy import func
            embeddings = []
            
            # 파일 패턴을 이용한 필터링
            files_query = self.db.query(CodeEmbedding)
            files_query = files_query.filter(CodeEmbedding.codebase_id == codebase_id)
            
            if file_patterns:
                # 파일 패턴 필터링 (간단한 구현 - 실제로는 좀 더 효율적인 방법 필요)
                patterns = [pattern.replace('*', '%') for pattern in file_patterns]
                or_conditions = []
                for pattern in patterns:
                    or_conditions.append(CodeEmbedding.chunk_id.like(pattern))
                
                if or_conditions:
                    from sqlalchemy import or_
                    files_query = files_query.filter(or_(*or_conditions))
            
            embeddings_db = files_query.all()
            
            # 유사도 계산 및 결과 구성
            results = []
            for embedding_db in embeddings_db:
                if embedding_db.embedding:
                    # 코사인 유사도 계산
                    similarity = self._cosine_similarity(query_embedding, embedding_db.embedding)
                    
                    # 임계값 이상인 경우에만 결과에 포함
                    if similarity >= threshold:
                        # 파일 정보 조회
                        file = self.db.query(codebase_id).get(embedding_db.file_id)
                        file_path = file.path if file else "Unknown"
                        
                        results.append({
                            "file_id": embedding_db.file_id,
                            "file_path": file_path,
                            "chunk_id": embedding_db.chunk_id,
                            "content": embedding_db.content,
                            "similarity_score": similarity,
                            "metadata": embedding_db.metadata
                        })
            
            # 유사도 기준 정렬 및 제한
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            return results[:limit]
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"코드 검색 중 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"코드 검색 실패: {str(e)}")
    
    def _filter_files(
        self, 
        files: List[Any], 
        excluded_patterns: List[str], 
        priority_patterns: List[str]
    ) -> List[Any]:
        """
        파일 목록을 필터링하고 우선순위 지정
        
        Args:
            files: 파일 목록
            excluded_patterns: 제외 패턴
            priority_patterns: 우선순위 패턴
            
        Returns:
            필터링된 파일 목록
        """
        # 제외 패턴 컴파일
        excluded_regex = []
        for pattern in excluded_patterns:
            try:
                # 와일드카드를 정규식으로 변환
                regex_pattern = pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".")
                excluded_regex.append(re.compile(regex_pattern))
            except:
                pass
        
        # 우선순위 패턴 컴파일
        priority_regex = []
        for pattern in priority_patterns:
            try:
                regex_pattern = pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".")
                priority_regex.append(re.compile(regex_pattern))
            except:
                pass
        
        # 필터링 및 우선순위 점수 할당
        filtered_files = []
        for file in files:
            # 제외 패턴 확인
            excluded = False
            for regex in excluded_regex:
                if regex.match(file.path):
                    excluded = True
                    break
            
            if excluded:
                continue
            
            # 우선순위 점수 계산
            priority_score = 0
            for regex in priority_regex:
                if regex.match(file.path):
                    priority_score += 1
            
            # 파일 및 점수 추가
            filtered_files.append((file, priority_score))
        
        # 우선순위 기준 정렬
        filtered_files.sort(key=lambda x: x[1], reverse=True)
        
        # 파일 객체만 반환
        return [file for file, _ in filtered_files]
    
    def _is_file_unchanged(self, file: Any, embeddings: List[Any]) -> bool:
        """
        파일이 변경되지 않았는지 확인
        
        Args:
            file: 파일 객체
            embeddings: 파일의 임베딩 목록
            
        Returns:
            변경되지 않았으면 True
        """
        # 변경 시간 확인 (첫 번째 임베딩의 생성 시간과 비교)
        if not embeddings:
            return False
        
        first_embedding = embeddings[0]
        if not hasattr(first_embedding, "created_at") or not first_embedding.created_at:
            return False
        
        if not hasattr(file, "updated_at") or not file.updated_at:
            return False
        
        # 파일 수정 시간이 임베딩 생성 시간보다 이후인 경우 변경된 것으로 간주
        return file.updated_at <= first_embedding.created_at
    
    def _extract_code_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """
        코드 내용에서 메타데이터 추출
        
        Args:
            content: 코드 내용
            file_path: 파일 경로
            
        Returns:
            메타데이터
        """
        # 파일 확장자 추출
        _, ext = os.path.splitext(file_path)
        language = ext.lstrip(".").lower() if ext else "unknown"
        
        # 간단한 언어 감지
        if language in ["py", "python"]:
            language = "python"
        elif language in ["js", "jsx"]:
            language = "javascript"
        elif language in ["ts", "tsx"]:
            language = "typescript"
        elif language in ["java"]:
            language = "java"
        elif language in ["cs"]:
            language = "csharp"
        elif language in ["cpp", "cc", "cxx", "c++"]:
            language = "cpp"
        elif language in ["go"]:
            language = "go"
        elif language in ["rs"]:
            language = "rust"
        elif language in ["php"]:
            language = "php"
        elif language in ["rb"]:
            language = "ruby"
        
        # 기본 메타데이터
        metadata = {
            "file_name": os.path.basename(file_path),
            "language": language,
            "code_elements": {
                "functions": [],
                "classes": [],
                "variables": []
            }
        }
        
        # 함수 및 클래스 추출 (간단한 구현)
        try:
            if language == "python":
                metadata["code_elements"]["functions"] = self._extract_python_functions(content)
                metadata["code_elements"]["classes"] = self._extract_python_classes(content)
            elif language in ["javascript", "typescript"]:
                metadata["code_elements"]["functions"] = self._extract_js_functions(content)
                metadata["code_elements"]["classes"] = self._extract_js_classes(content)
            
            # 기타 언어는 필요에 따라 추가 구현
        except Exception as e:
            logger.warning(f"메타데이터 추출 중 오류 발생: {str(e)}")
        
        return metadata
    
    def _extract_python_functions(self, content: str) -> List[str]:
        """Python 함수 이름 추출"""
        pattern = r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
        matches = re.findall(pattern, content)
        return matches
    
    def _extract_python_classes(self, content: str) -> List[str]:
        """Python 클래스 이름 추출"""
        pattern = r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]"
        matches = re.findall(pattern, content)
        return matches
    
    def _extract_js_functions(self, content: str) -> List[str]:
        """JavaScript/TypeScript 함수 이름 추출"""
        # 일반 함수
        pattern1 = r"function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\("
        # 화살표 함수
        pattern2 = r"(const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\([^)]*\)\s*=>"
        # 메서드
        pattern3 = r"([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\([^)]*\)\s*\{"
        
        matches1 = re.findall(pattern1, content)
        matches2 = [m[1] for m in re.findall(pattern2, content)]
        matches3 = re.findall(pattern3, content)
        
        # 중복 제거 및 병합
        all_matches = set(matches1 + matches2 + matches3)
        return list(all_matches)
    
    def _extract_js_classes(self, content: str) -> List[str]:
        """JavaScript/TypeScript 클래스 이름 추출"""
        pattern = r"class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)"
        matches = re.findall(pattern, content)
        return matches
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        두 벡터간의 코사인 유사도 계산
        
        Args:
            vec1: 첫 번째 벡터
            vec2: 두 번째 벡터
            
        Returns:
            코사인 유사도 (-1에서 1 사이의 값)
        """
        try:
            # Numpy 변환
            import numpy as np
            a = np.array(vec1)
            b = np.array(vec2)
            
            # 코사인 유사도 계산
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0
            
            similarity = dot_product / (norm_a * norm_b)
            
            # -1에서 1 사이의 값으로 클립
            return max(-1, min(1, similarity))
        except Exception as e:
            logger.error(f"유사도 계산 중 오류 발생: {str(e)}")
            return 0.0
    
    async def get_stats(self, codebase_id: int) -> Dict[str, Any]:
        """
        코드베이스 인덱싱 통계 조회
        
        Args:
            codebase_id: 코드베이스 ID
            
        Returns:
            통계 정보
        """
        # 설정 조회
        settings = get_indexing_settings(self.db, codebase_id)
        if not settings:
            raise HTTPException(
                status_code=404, 
                detail=f"코드베이스 ID {codebase_id}의 인덱싱 설정을 찾을 수 없습니다"
            )
        
        # 최근 실행 조회
        latest_run = get_latest_indexing_run(self.db, codebase_id)
        
        # 임베딩 통계 조회
        embedding_stats = get_codebase_embeddings_stats(self.db, codebase_id)
        
        # 결과 구성
        return {
            "settings": {
                "is_enabled": settings.is_enabled,
                "frequency": settings.frequency,
                "excluded_patterns": settings.excluded_patterns,
                "priority_patterns": settings.priority_patterns,
                "embedding_model": settings.embedding_model,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "include_comments": settings.include_comments,
                "max_files_per_run": settings.max_files_per_run,
                "last_updated": settings.updated_at
            },
            "status": {
                "is_indexing_now": latest_run is not None and latest_run.status == IndexingStatus.IN_PROGRESS,
                "current_run_id": latest_run.id if latest_run and latest_run.status == IndexingStatus.IN_PROGRESS else None,
                "last_run": self._format_run(latest_run) if latest_run else None,
                "recent_runs": [
                    self._format_run_summary(run) 
                    for run in self.db.query(CodebaseIndexingRun)
                        .filter_by(codebase_id=codebase_id)
                        .order_by(CodebaseIndexingRun.id.desc())
                        .limit(5)
                        .all()
                ]
            },
            "statistics": embedding_stats
        }
    
    def _format_run(self, run: Any) -> Dict[str, Any]:
        """
        인덱싱 실행 정보 포맷팅
        
        Args:
            run: 실행 객체
            
        Returns:
            포맷팅된 실행 정보
        """
        if not run:
            return None
        
        return {
            "id": run.id,
            "status": run.status,
            "start_time": run.start_time,
            "end_time": run.end_time,
            "files_processed": run.files_processed,
            "files_indexed": run.files_indexed,
            "files_skipped": run.files_skipped,
            "error_message": run.error_message,
            "is_full_index": run.is_full_index,
            "triggered_by": run.triggered_by
        }
    
    def _format_run_summary(self, run: Any) -> Dict[str, Any]:
        """
        인덱싱 실행 요약 정보 포맷팅
        
        Args:
            run: 실행 객체
            
        Returns:
            포맷팅된 실행 요약 정보
        """
        if not run:
            return None
        
        return {
            "id": run.id,
            "status": run.status,
            "start_time": run.start_time,
            "end_time": run.end_time,
            "is_full_index": run.is_full_index,
            "files_indexed": run.files_indexed
        }"