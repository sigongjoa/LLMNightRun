import os
import re
import logging
import fnmatch
import hashlib
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import traceback

import numpy as np
from openai import OpenAI
import httpx
from sqlalchemy.orm import Session

from backend.models import IndexingStatus, IndexingFrequency
from backend.database.operations import (
    get_indexing_settings,
    create_or_update_indexing_settings,
    create_indexing_run,
    update_indexing_run,
    get_indexing_runs,
    get_latest_indexing_run,
    create_code_embedding,
    update_code_embedding,
    get_file_embeddings,
    delete_file_embeddings,
    get_codebase_embeddings_stats,
    get_codebase_files,
    get_codebases
)
from backend.database.connection import SessionLocal
from backend.database import models

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodebaseIndexingManager:
    """코드베이스 인덱싱 관리 클래스"""
    
    def __init__(self):
        """인덱싱 관리자 초기화"""
        self.db = SessionLocal()
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.current_runs = {}  # 현재 실행 중인 인덱싱 작업 (codebase_id: run_id)
    
    def __del__(self):
        """객체 소멸 시 DB 연결 닫기"""
        if self.db:
            self.db.close()
    
    async def initialize_indexing_settings(self, codebase_id: int) -> models.CodebaseIndexingSettings:
        """
        코드베이스의 인덱싱 설정을 초기화합니다.
        
        Args:
            codebase_id: 코드베이스 ID
            
        Returns:
            생성된 인덱싱 설정
        """
        # 기존 설정 확인
        settings = get_indexing_settings(self.db, codebase_id)
        if settings:
            return settings
        
        # 코드베이스 정보 확인
        codebase = get_codebases(self.db, codebase_id=codebase_id, single=True)
        if not codebase:
            raise ValueError(f"코드베이스 ID {codebase_id}을(를) 찾을 수 없습니다.")
        
        # 언어별 기본 설정 초기화
        default_settings = {
            "is_enabled": True,
            "frequency": "on_commit",
            "excluded_patterns": self._get_default_excluded_patterns(codebase.language),
            "priority_patterns": self._get_default_priority_patterns(codebase.language),
            "embedding_model": "openai/text-embedding-ada-002",
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "include_comments": True,
            "max_files_per_run": 100
        }
        
        # 설정 생성
        return create_or_update_indexing_settings(self.db, codebase_id, default_settings)
    
    def _get_default_excluded_patterns(self, language: str) -> List[str]:
        """
        언어별 기본 제외 패턴을 반환합니다.
        
        Args:
            language: 프로그래밍 언어
            
        Returns:
            제외 패턴 목록
        """
        # 공통 제외 패턴
        common_patterns = [
            "*.log", "*.md", "*.txt", 
            "*.json", "*.yaml", "*.yml",
            "*.min.js", "*.min.css",
            ".git/*", ".github/*", ".gitignore",
            "LICENSE", "README*",
            "node_modules/*", "dist/*", "build/*",
            "*.pyc", "__pycache__/*",
            ".DS_Store", "Thumbs.db"
        ]
        
        # 언어별 추가 패턴
        language_patterns = {
            "python": ["venv/*", "env/*", "*.egg-info/*", "*.egg", "*.whl"],
            "javascript": ["package-lock.json", "yarn.lock", "coverage/*"],
            "typescript": ["package-lock.json", "yarn.lock", "coverage/*", "*.d.ts"],
            "java": [
                "target/*", "build/*", "gradle/*", ".gradle/*", 
                "*.class", "*.jar", "out/*", ".idea/*"
            ],
            "csharp": ["obj/*", "bin/*", "packages/*", ".vs/*"],
            "go": ["vendor/*", "go.sum"],
            "rust": ["target/*", "Cargo.lock"],
            "php": ["vendor/*", "composer.lock"],
            "ruby": ["Gemfile.lock", "vendor/*"]
        }
        
        return common_patterns + language_patterns.get(language.lower(), [])
    
    def _get_default_priority_patterns(self, language: str) -> List[str]:
        """
        언어별 기본 우선순위 패턴을 반환합니다.
        
        Args:
            language: 프로그래밍 언어
            
        Returns:
            우선순위 패턴 목록
        """
        # 언어별 주요 파일 패턴
        language_patterns = {
            "python": ["src/*.py", "main.py", "__init__.py"],
            "javascript": ["src/*.js", "index.js", "app.js"],
            "typescript": ["src/*.ts", "index.ts", "app.ts"],
            "java": ["src/main/java/*.java", "src/main/*/Main.java"],
            "csharp": ["src/*.cs", "Program.cs"],
            "go": ["*.go", "main.go"],
            "rust": ["src/*.rs", "main.rs", "lib.rs"],
            "php": ["src/*.php", "index.php"],
            "ruby": ["lib/*.rb", "app.rb"]
        }
        
        return language_patterns.get(language.lower(), ["src/*"])
    
    async def update_indexing_settings(
        self, 
        codebase_id: int, 
        settings: Dict[str, Any]
    ) -> models.CodebaseIndexingSettings:
        """
        코드베이스의 인덱싱 설정을 업데이트합니다.
        
        Args:
            codebase_id: 코드베이스 ID
            settings: 업데이트할 설정
            
        Returns:
            업데이트된 인덱싱 설정
        """
        # 기존 설정 확인
        existing_settings = get_indexing_settings(self.db, codebase_id)
        if not existing_settings:
            # 설정 초기화 후 업데이트
            existing_settings = await self.initialize_indexing_settings(codebase_id)
        
        # 설정 업데이트
        return create_or_update_indexing_settings(self.db, codebase_id, settings)
    
    async def get_indexing_status(self, codebase_id: int) -> Dict[str, Any]:
        """
        코드베이스의 인덱싱 상태를 조회합니다.
        
        Args:
            codebase_id: 코드베이스 ID
            
        Returns:
            인덱싱 상태 정보
        """
        # 설정 확인
        settings = get_indexing_settings(self.db, codebase_id)
        if not settings:
            settings = await self.initialize_indexing_settings(codebase_id)
        
        # 최근 실행 정보 조회
        recent_runs = get_indexing_runs(self.db, codebase_id, limit=5)
        latest_run = None if not recent_runs else recent_runs[0]
        
        # 임베딩 통계 조회
        embedding_stats = get_codebase_embeddings_stats(self.db, codebase_id)
        
        # 현재 실행 중인지 확인
        is_indexing_now = codebase_id in self.current_runs
        
        return {
            "settings": {
                "is_enabled": settings.is_enabled,
                "frequency": settings.frequency.value,
                "excluded_patterns": settings.excluded_patterns,
                "priority_patterns": settings.priority_patterns,
                "embedding_model": settings.embedding_model,
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "include_comments": settings.include_comments,
                "max_files_per_run": settings.max_files_per_run,
                "last_updated": settings.updated_at.isoformat() if settings.updated_at else None
            },
            "status": {
                "is_indexing_now": is_indexing_now,
                "current_run_id": self.current_runs.get(codebase_id),
                "last_run": {
                    "id": latest_run.id if latest_run else None,
                    "status": latest_run.status.value if latest_run else None,
                    "start_time": latest_run.start_time.isoformat() if latest_run and latest_run.start_time else None,
                    "end_time": latest_run.end_time.isoformat() if latest_run and latest_run.end_time else None,
                    "files_processed": latest_run.files_processed if latest_run else 0,
                    "files_indexed": latest_run.files_indexed if latest_run else 0,
                    "files_skipped": latest_run.files_skipped if latest_run else 0,
                    "error_message": latest_run.error_message if latest_run else None
                },
                "recent_runs": [
                    {
                        "id": run.id,
                        "status": run.status.value,
                        "start_time": run.start_time.isoformat() if run.start_time else None,
                        "end_time": run.end_time.isoformat() if run.end_time else None,
                        "is_full_index": run.is_full_index,
                        "files_indexed": run.files_indexed
                    }
                    for run in recent_runs
                ] if recent_runs else []
            },
            "statistics": embedding_stats
        }
    
    async def trigger_indexing(
        self, 
        codebase_id: int, 
        is_full_index: bool = False,
        priority_files: Optional[List[int]] = None,
        triggered_by: str = "manual"
    ) -> Dict[str, Any]:
        """
        코드베이스 인덱싱을 트리거합니다.
        
        Args:
            codebase_id: 코드베이스 ID
            is_full_index: 전체 인덱싱 여부
            priority_files: 우선적으로 인덱싱할 파일 ID 목록
            triggered_by: 트리거 소스
            
        Returns:
            인덱싱 트리거 결과
        """
        # 이미 실행 중인지 확인
        if codebase_id in self.current_runs:
            return {
                "success": False,
                "message": "이미 인덱싱이 실행 중입니다.",
                "run_id": self.current_runs[codebase_id]
            }
        
        # 설정 확인
        settings = get_indexing_settings(self.db, codebase_id)
        if not settings:
            settings = await self.initialize_indexing_settings(codebase_id)
        
        # 인덱싱 비활성화 상태인지 확인
        if not settings.is_enabled:
            return {
                "success": False,
                "message": "인덱싱이 비활성화되어 있습니다.",
                "run_id": None
            }
        
        # 새 인덱싱 실행 생성
        indexing_run = create_indexing_run(
            self.db,
            codebase_id,
            is_full_index=is_full_index,
            triggered_by=triggered_by
        )
        
        # 비동기로 인덱싱 프로세스 시작
        asyncio.create_task(self._run_indexing_process(
            codebase_id, 
            indexing_run.id, 
            is_full_index, 
            priority_files
        ))
        
        return {
            "success": True,
            "message": "인덱싱이 시작되었습니다.",
            "run_id": indexing_run.id
        }
    
    async def _run_indexing_process(
        self, 
        codebase_id: int, 
        run_id: int, 
        is_full_index: bool,
        priority_files: Optional[List[int]] = None
    ):
        """
        인덱싱 프로세스를 실행합니다.
        
        Args:
            codebase_id: 코드베이스 ID
            run_id: 인덱싱 실행 ID
            is_full_index: 전체 인덱싱 여부
            priority_files: 우선적으로 인덱싱할 파일 ID 목록
        """
        # 현재 실행 중인 작업으로 등록
        self.current_runs[codebase_id] = run_id
        
        try:
            # 실행 상태 업데이트
            update_indexing_run(self.db, run_id, {
                "status": models.IndexingStatusEnum.in_progress,
                "start_time": datetime.utcnow()
            })
            
            # 설정 가져오기
            settings = get_indexing_settings(self.db, codebase_id)
            
            # 파일 목록 가져오기
            all_files = get_codebase_files(self.db, codebase_id, is_directory=False)
            
            # 제외 패턴에 따라 파일 필터링
            files_to_process = self._filter_files_by_patterns(
                all_files, 
                settings.excluded_patterns, 
                settings.priority_patterns
            )
            
            # 우선 처리 파일 추가
            if priority_files:
                priority_file_objects = [f for f in all_files if f.id in priority_files]
                # 중복 제거하여 맨 앞으로 추가
                seen_ids = set()
                final_file_list = []
                
                # 우선 처리 파일 먼저 추가
                for file in priority_file_objects:
                    if file.id not in seen_ids and not file.is_directory:
                        seen_ids.add(file.id)
                        final_file_list.append(file)
                
                # 나머지 파일 추가
                for file in files_to_process:
                    if file.id not in seen_ids:
                        seen_ids.add(file.id)
                        final_file_list.append(file)
                
                files_to_process = final_file_list
            
            # 최대 파일 수 제한
            files_to_process = files_to_process[:settings.max_files_per_run]
            
            # 전체 인덱싱이 아닌 경우 이미 인덱싱된 파일은 건너뛰기
            if not is_full_index:
                files_to_process = self._filter_already_indexed_files(
                    files_to_process,
                    codebase_id
                )
            
            # 파일 처리 결과 초기화
            processed_count = 0
            indexed_count = 0
            skipped_count = 0
            
            # 각 파일 처리
            for file in files_to_process:
                processed_count += 1
                
                try:
                    # 전체 인덱싱이면 기존 임베딩 삭제
                    if is_full_index:
                        delete_file_embeddings(self.db, file.id)
                    
                    # 파일 내용 청크로 분할
                    chunks = self._split_file_into_chunks(
                        file.content,
                        settings.chunk_size,
                        settings.chunk_overlap,
                        settings.include_comments,
                        file.path
                    )
                    
                    # 각 청크의 임베딩 생성
                    for chunk_id, chunk_content in chunks:
                        embedding = await self._generate_embedding(
                            chunk_content,
                            settings.embedding_model
                        )
                        
                        if embedding:
                            # 메타데이터 생성
                            metadata = self._generate_chunk_metadata(
                                file.path, 
                                chunk_id, 
                                chunk_content
                            )
                            
                            # 임베딩 저장
                            create_code_embedding(
                                self.db,
                                codebase_id,
                                file.id,
                                chunk_id,
                                chunk_content,
                                embedding=embedding,
                                metadata=metadata,
                                run_id=run_id
                            )
                            
                            indexed_count += 1
                        else:
                            skipped_count += 1
                    
                    # 실행 상태 주기적 업데이트
                    if processed_count % 10 == 0:
                        update_indexing_run(self.db, run_id, {
                            "files_processed": processed_count,
                            "files_indexed": indexed_count,
                            "files_skipped": skipped_count
                        })
                    
                except Exception as e:
                    logger.error(f"파일 {file.path} 인덱싱 중 오류 발생: {str(e)}")
                    skipped_count += 1
                    continue
            
            # 완료 상태 업데이트
            update_indexing_run(self.db, run_id, {
                "status": models.IndexingStatusEnum.completed,
                "end_time": datetime.utcnow(),
                "files_processed": processed_count,
                "files_indexed": indexed_count,
                "files_skipped": skipped_count
            })
            
            logger.info(f"코드베이스 {codebase_id} 인덱싱 완료. "
                       f"처리: {processed_count}, 인덱싱: {indexed_count}, 건너뜀: {skipped_count}")
            
        except Exception as e:
            # 오류 상태 업데이트
            error_message = f"인덱싱 중 오류 발생: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            
            update_indexing_run(self.db, run_id, {
                "status": models.IndexingStatusEnum.failed,
                "end_time": datetime.utcnow(),
                "error_message": error_message
            })
        
        finally:
            # 현재 실행 중인 작업에서 제거
            if codebase_id in self.current_runs:
                del self.current_runs[codebase_id]
    
    def _filter_files_by_patterns(
        self, 
        files: List[models.CodebaseFile], 
        excluded_patterns: List[str], 
        priority_patterns: List[str]
    ) -> List[models.CodebaseFile]:
        """
        패턴에 따라 파일을 필터링합니다.
        
        Args:
            files: 파일 목록
            excluded_patterns: 제외 패턴 목록
            priority_patterns: 우선순위 패턴 목록
            
        Returns:
            필터링된 파일 목록
        """
        # 디렉토리 제외
        non_directory_files = [f for f in files if not f.is_directory]
        
        # 제외 패턴에 맞는 파일 필터링
        filtered_files = []
        for file in non_directory_files:
            # 제외 패턴 확인
            excluded = False
            for pattern in excluded_patterns:
                if fnmatch.fnmatch(file.path, pattern):
                    excluded = True
                    break
            
            if not excluded:
                filtered_files.append(file)
        
        # 우선순위 패턴에 맞는 파일 먼저 정렬
        def get_priority(file):
            for i, pattern in enumerate(priority_patterns):
                if fnmatch.fnmatch(file.path, pattern):
                    return i
            return len(priority_patterns)
        
        return sorted(filtered_files, key=get_priority)
    
    def _filter_already_indexed_files(
        self, 
        files: List[models.CodebaseFile], 
        codebase_id: int
    ) -> List[models.CodebaseFile]:
        """
        이미 인덱싱된 파일을 필터링합니다.
        
        Args:
            files: 파일 목록
            codebase_id: 코드베이스 ID
            
        Returns:
            필터링된 파일 목록 (인덱싱되지 않은 파일)
        """
        # 이미 인덱싱된 파일의 ID 조회
        indexed_file_ids = set()
        for file in files:
            embeddings = get_file_embeddings(self.db, file.id)
            if embeddings:
                indexed_file_ids.add(file.id)
        
        # 인덱싱되지 않은 파일만 반환
        return [f for f in files if f.id not in indexed_file_ids]
    
    def _split_file_into_chunks(
        self, 
        content: str, 
        chunk_size: int, 
        chunk_overlap: int, 
        include_comments: bool, 
        file_path: str
    ) -> List[Tuple[str, str]]:
        """
        파일 내용을 청크로 분할합니다.
        
        Args:
            content: 파일 내용
            chunk_size: 청크 크기
            chunk_overlap: 청크 간 겹침 정도
            include_comments: 주석 포함 여부
            file_path: 파일 경로
            
        Returns:
            (청크 ID, 청크 내용) 튜플 목록
        """
        if not content:
            return []
        
        # 주석 제거 (옵션)
        if not include_comments:
            content = self._remove_comments(content, file_path)
        
        # 줄 단위로 분할
        lines = content.splitlines()
        
        # 결과 청크 목록
        chunks = []
        
        # 라인 기반 청킹
        current_chunk = []
        current_size = 0
        chunk_number = 0
        
        for i, line in enumerate(lines):
            line_len = len(line)
            
            if current_size + line_len > chunk_size and current_chunk:
                # 청크 완성
                chunk_content = "\n".join(current_chunk)
                chunk_id = f"{file_path}:{chunk_number}"
                chunks.append((chunk_id, chunk_content))
                
                # 다음 청크 준비 (겹침 적용)
                overlap_lines = current_chunk[-chunk_overlap:] if chunk_overlap > 0 else []
                current_chunk = overlap_lines + [line]
                current_size = sum(len(l) for l in current_chunk)
                chunk_number += 1
            else:
                # 현재 청크에 라인 추가
                current_chunk.append(line)
                current_size += line_len
        
        # 마지막 청크 추가
        if current_chunk:
            chunk_content = "\n".join(current_chunk)
            chunk_id = f"{file_path}:{chunk_number}"
            chunks.append((chunk_id, chunk_content))
        
        return chunks
    
    def _remove_comments(self, content: str, file_path: str) -> str:
        """
        코드에서 주석을 제거합니다.
        
        Args:
            content: 코드 내용
            file_path: 파일 경로
            
        Returns:
            주석이 제거된 코드
        """
        # 파일 확장자 추출
        _, ext = os.path.splitext(file_path.lower())
        
        # 언어별 주석 패턴
        if ext in ['.py']:
            # Python 주석
            # 한 줄 주석 제거
            content = re.sub(r'#.*import os
import re
import logging
import fnmatch
import hashlib
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import traceback

import numpy as np
from openai import OpenAI
import httpx
from sqlalchemy.orm import Session

from backend.models import IndexingStatus, IndexingFrequency
from backend.database.operations import (
    get_indexing_settings,
    create_or_update_indexing_settings,
    create_indexing_run,
    update_indexing_run,
    get_indexing_runs,
    get_latest_indexing_run,
    create_code_embedding,
    update_code_embedding,
    get_file_embeddings,
    delete_file_embeddings,
    get_codebase_embeddings_stats,
    get_codebase_files,
    get_codebases
)
from backend.database.connection import SessionLocal
from backend.database import models

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodebaseIndexingManager:
    """코드베이스 인덱싱 관리 클래스"""
    
    def __init__(self):
        """인덱싱 관리자 초기화"""
        self.db = SessionLocal()
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.current_runs = {}  # 현재 실행 중인 인덱싱 작업 (codebase_id: run_id)
    
    def __del__(self):
        """객체 소멸 시 DB 연결 닫기"""
        if self.db:
            self.db.close()
    
    async def initialize_indexing_settings(self, codebase_id: int) -> models.CodebaseIndexingSettings:
        """
        코드베이스의 인덱싱 설정을 초기화합니다.
        
        Args:
            codebase_id: 코드베이스 ID
            
        Returns:
            생성된 인덱싱 설정
        """
        # 기존 설정 확인
        settings = get_indexing_settings(self.db, codebase_id)
        if settings:
            return settings
        
        # 코드베이스 정보 확인
        codebase = get_codebases(self.db, codebase_id=codebase_id, single=True)
        if not codebase:
            raise ValueError(f"코드베이스 ID {codebase_id}을(를) 찾을 수 없습니다.")
        
        # 언어별 기본 설정 초기화
        default_settings = {
            "is_enabled": True,
            "frequency": "on_commit",
            "excluded_patterns": self._get_default_excluded_patterns(codebase.language),
            "priority_patterns": self._get_default_priority_patterns(codebase.language),
            "embedding_model": "openai/text-embedding-ada-002",
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "include_comments": True,
            "max_files_per_run": 100
        }
        
        # 설정 생성
        return create_or_update_indexing_settings(self.db, codebase_id, default_settings)
    
    def _get_default_excluded_patterns(self, language: str) -> List[str]:
        """
        언어별 기본 제외 패턴을 반환합니다.
        
        Args:
            language: 프로그래밍 언어
            
        Returns:
            제외 패턴 목록
        """
        # 공통 제외 패턴
        common_patterns = [
            "*.log", "*.md", "*.txt", 
            "*.json", "*.yaml", "*.yml",
            "*.min.js", "*.min.css",
            ".git/*", ".github/*", ".gitignore",
            "LICENSE", "README*",
            "node_modules/*", "dist/*", "build/*",
            "*.pyc", "__pycache__/*",
            ".DS_Store", "Thumbs.db"
        ]
        
        # 언어별 추가 패턴
        language_patterns = {
            "python": ["venv/*", "env/*", "*.egg-info/*", "*.egg", "*.whl"],
            "javascript": ["package-lock.json", "yarn.lock", "coverage/*"],
            "typescript": ["package-lock.json", "yarn.lock", "coverage/*", "*.d.ts"],
            "java":, '', content, flags=re.MULTILINE)
            # 여러 줄 주석 제거
            content = re.sub(r'"""[\s\S]*?"""', '', content)
            content = re.sub(r"'''[\s\S]*?'''", '', content)
        
        elif ext in ['.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.cs', '.php']:
            # C-스타일 주석
            # 한 줄 주석 제거
            content = re.sub(r'//.*import os
import re
import logging
import fnmatch
import hashlib
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import traceback

import numpy as np
from openai import OpenAI
import httpx
from sqlalchemy.orm import Session

from backend.models import IndexingStatus, IndexingFrequency
from backend.database.operations import (
    get_indexing_settings,
    create_or_update_indexing_settings,
    create_indexing_run,
    update_indexing_run,
    get_indexing_runs,
    get_latest_indexing_run,
    create_code_embedding,
    update_code_embedding,
    get_file_embeddings,
    delete_file_embeddings,
    get_codebase_embeddings_stats,
    get_codebase_files,
    get_codebases
)
from backend.database.connection import SessionLocal
from backend.database import models

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodebaseIndexingManager:
    """코드베이스 인덱싱 관리 클래스"""
    
    def __init__(self):
        """인덱싱 관리자 초기화"""
        self.db = SessionLocal()
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.current_runs = {}  # 현재 실행 중인 인덱싱 작업 (codebase_id: run_id)
    
    def __del__(self):
        """객체 소멸 시 DB 연결 닫기"""
        if self.db:
            self.db.close()
    
    async def initialize_indexing_settings(self, codebase_id: int) -> models.CodebaseIndexingSettings:
        """
        코드베이스의 인덱싱 설정을 초기화합니다.
        
        Args:
            codebase_id: 코드베이스 ID
            
        Returns:
            생성된 인덱싱 설정
        """
        # 기존 설정 확인
        settings = get_indexing_settings(self.db, codebase_id)
        if settings:
            return settings
        
        # 코드베이스 정보 확인
        codebase = get_codebases(self.db, codebase_id=codebase_id, single=True)
        if not codebase:
            raise ValueError(f"코드베이스 ID {codebase_id}을(를) 찾을 수 없습니다.")
        
        # 언어별 기본 설정 초기화
        default_settings = {
            "is_enabled": True,
            "frequency": "on_commit",
            "excluded_patterns": self._get_default_excluded_patterns(codebase.language),
            "priority_patterns": self._get_default_priority_patterns(codebase.language),
            "embedding_model": "openai/text-embedding-ada-002",
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "include_comments": True,
            "max_files_per_run": 100
        }
        
        # 설정 생성
        return create_or_update_indexing_settings(self.db, codebase_id, default_settings)
    
    def _get_default_excluded_patterns(self, language: str) -> List[str]:
        """
        언어별 기본 제외 패턴을 반환합니다.
        
        Args:
            language: 프로그래밍 언어
            
        Returns:
            제외 패턴 목록
        """
        # 공통 제외 패턴
        common_patterns = [
            "*.log", "*.md", "*.txt", 
            "*.json", "*.yaml", "*.yml",
            "*.min.js", "*.min.css",
            ".git/*", ".github/*", ".gitignore",
            "LICENSE", "README*",
            "node_modules/*", "dist/*", "build/*",
            "*.pyc", "__pycache__/*",
            ".DS_Store", "Thumbs.db"
        ]
        
        # 언어별 추가 패턴
        language_patterns = {
            "python": ["venv/*", "env/*", "*.egg-info/*", "*.egg", "*.whl"],
            "javascript": ["package-lock.json", "yarn.lock", "coverage/*"],
            "typescript": ["package-lock.json", "yarn.lock", "coverage/*", "*.d.ts"],
            "java":, '', content, flags=re.MULTILINE)
            # 여러 줄 주석 제거
            content = re.sub(r'/\*[\s\S]*?\*/', '', content)
        
        elif ext in ['.rb']:
            # Ruby 주석
            # 한 줄 주석 제거
            content = re.sub(r'#.*import os
import re
import logging
import fnmatch
import hashlib
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import traceback

import numpy as np
from openai import OpenAI
import httpx
from sqlalchemy.orm import Session

from backend.models import IndexingStatus, IndexingFrequency
from backend.database.operations import (
    get_indexing_settings,
    create_or_update_indexing_settings,
    create_indexing_run,
    update_indexing_run,
    get_indexing_runs,
    get_latest_indexing_run,
    create_code_embedding,
    update_code_embedding,
    get_file_embeddings,
    delete_file_embeddings,
    get_codebase_embeddings_stats,
    get_codebase_files,
    get_codebases
)
from backend.database.connection import SessionLocal
from backend.database import models

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodebaseIndexingManager:
    """코드베이스 인덱싱 관리 클래스"""
    
    def __init__(self):
        """인덱싱 관리자 초기화"""
        self.db = SessionLocal()
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.current_runs = {}  # 현재 실행 중인 인덱싱 작업 (codebase_id: run_id)
    
    def __del__(self):
        """객체 소멸 시 DB 연결 닫기"""
        if self.db:
            self.db.close()
    
    async def initialize_indexing_settings(self, codebase_id: int) -> models.CodebaseIndexingSettings:
        """
        코드베이스의 인덱싱 설정을 초기화합니다.
        
        Args:
            codebase_id: 코드베이스 ID
            
        Returns:
            생성된 인덱싱 설정
        """
        # 기존 설정 확인
        settings = get_indexing_settings(self.db, codebase_id)
        if settings:
            return settings
        
        # 코드베이스 정보 확인
        codebase = get_codebases(self.db, codebase_id=codebase_id, single=True)
        if not codebase:
            raise ValueError(f"코드베이스 ID {codebase_id}을(를) 찾을 수 없습니다.")
        
        # 언어별 기본 설정 초기화
        default_settings = {
            "is_enabled": True,
            "frequency": "on_commit",
            "excluded_patterns": self._get_default_excluded_patterns(codebase.language),
            "priority_patterns": self._get_default_priority_patterns(codebase.language),
            "embedding_model": "openai/text-embedding-ada-002",
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "include_comments": True,
            "max_files_per_run": 100
        }
        
        # 설정 생성
        return create_or_update_indexing_settings(self.db, codebase_id, default_settings)
    
    def _get_default_excluded_patterns(self, language: str) -> List[str]:
        """
        언어별 기본 제외 패턴을 반환합니다.
        
        Args:
            language: 프로그래밍 언어
            
        Returns:
            제외 패턴 목록
        """
        # 공통 제외 패턴
        common_patterns = [
            "*.log", "*.md", "*.txt", 
            "*.json", "*.yaml", "*.yml",
            "*.min.js", "*.min.css",
            ".git/*", ".github/*", ".gitignore",
            "LICENSE", "README*",
            "node_modules/*", "dist/*", "build/*",
            "*.pyc", "__pycache__/*",
            ".DS_Store", "Thumbs.db"
        ]
        
        # 언어별 추가 패턴
        language_patterns = {
            "python": ["venv/*", "env/*", "*.egg-info/*", "*.egg", "*.whl"],
            "javascript": ["package-lock.json", "yarn.lock", "coverage/*"],
            "typescript": ["package-lock.json", "yarn.lock", "coverage/*", "*.d.ts"],
            "java":, '', content, flags=re.MULTILINE)
            # 여러 줄 주석 제거
            content = re.sub(r'=begin[\s\S]*?=end', '', content)
        
        elif ext in ['.html', '.xml']:
            # HTML/XML 주석
            content = re.sub(r'<!--[\s\S]*?-->', '', content)
        
        # 빈 줄 여러 개를 하나로 압축
        content = re.sub(r'\n\s*\n', '\n\n', content)
        
        return content
    
    async def _generate_embedding(
        self, 
        text: str, 
        model: str
    ) -> Optional[List[float]]:
        """
        텍스트의 임베딩을 생성합니다.
        
        Args:
            text: 임베딩할 텍스트
            model: 임베딩 모델
            
        Returns:
            임베딩 벡터 또는 None (실패 시)
        """
        if not text.strip():
            return None
        
        try:
            # OpenAI API를 통한 임베딩 생성
            if model.startswith("openai/"):
                model_name = model.replace("openai/", "")
                response = self.openai_client.embeddings.create(
                    input=text,
                    model=model_name
                )
                return response.data[0].embedding
            
            # 다른 임베딩 모델 지원 (추가 가능)
            else:
                logger.warning(f"지원되지 않는 임베딩 모델: {model}")
                return None
        
        except Exception as e:
            logger.error(f"임베딩 생성 중 오류 발생: {str(e)}")
            return None
    
    def _generate_chunk_metadata(
        self, 
        file_path: str, 
        chunk_id: str, 
        chunk_content: str
    ) -> Dict[str, Any]:
        """
        청크의 메타데이터를 생성합니다.
        
        Args:
            file_path: 파일 경로
            chunk_id: 청크 ID
            chunk_content: 청크 내용
            
        Returns:
            메타데이터
        """
        # 파일 확장자 추출
        file_name = os.path.basename(file_path)
        _, ext = os.path.splitext(file_path.lower())
        ext = ext[1:] if ext else ""
        
        # 주요 기능/클래스/메서드 추출 시도
        code_elements = self._extract_code_elements(chunk_content, ext)
        
        # 토큰 수 계산 (간단한 근사치)
        token_count = len(chunk_content.split())
        
        # 청크 해시 생성
        content_hash = hashlib.md5(chunk_content.encode()).hexdigest()
        
        return {
            "file_name": file_name,
            "file_path": file_path,
            "chunk_id": chunk_id,
            "extension": ext,
            "language": ext,
            "code_elements": code_elements,
            "char_count": len(chunk_content),
            "token_count": token_count,
            "content_hash": content_hash,
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _extract_code_elements(
        self, 
        content: str, 
        language: str
    ) -> Dict[str, List[str]]:
        """
        코드에서 주요 요소(함수, 클래스 등)를 추출합니다.
        
        Args:
            content: 코드 내용
            language: 프로그래밍 언어
            
        Returns:
            코드 요소 정보
        """
        result = {
            "classes": [],
            "functions": [],
            "variables": []
        }
        
        try:
            # Python 코드 분석
            if language == "py":
                # 클래스 추출
                class_matches = re.finditer(r'class\s+(\w+)(?:\(.*\))?:', content)
                result["classes"] = [m.group(1) for m in class_matches]
                
                # 함수 추출
                func_matches = re.finditer(r'def\s+(\w+)\s*\(', content)
                result["functions"] = [m.group(1) for m in func_matches]
                
                # 변수 추출 (상수/클래스 변수 위주)
                var_matches = re.finditer(r'^([A-Z][A-Z0-9_]*)\s*=', content, re.MULTILINE)
                result["variables"] = [m.group(1) for m in var_matches]
            
            # JavaScript/TypeScript 코드 분석
            elif language in ["js", "ts"]:
                # 클래스 추출
                class_matches = re.finditer(r'class\s+(\w+)', content)
                result["classes"] = [m.group(1) for m in class_matches]
                
                # 함수 추출 (함수 선언과 화살표 함수)
                func_matches = re.finditer(r'function\s+(\w+)\s*\(', content)
                result["functions"] = [m.group(1) for m in func_matches]
                
                arrow_func_matches = re.finditer(r'(const|let|var)\s+(\w+)\s*=\s*\(.*\)\s*=>', content)
                result["functions"].extend([m.group(2) for m in arrow_func_matches])
                
                # 변수 추출 (상수 위주)
                var_matches = re.finditer(r'const\s+([A-Z][A-Z0-9_]*)\s*=', content)
                result["variables"] = [m.group(1) for m in var_matches]
            
            # Java 코드 분석
            elif language == "java":
                # 클래스 추출
                class_matches = re.finditer(r'(class|interface|enum)\s+(\w+)', content)
                result["classes"] = [m.group(2) for m in class_matches]
                
                # 메서드 추출
                func_matches = re.finditer(r'(public|private|protected)?\s*(\w+)\s+(\w+)\s*\(', content)
                result["functions"] = [m.group(3) for m in func_matches if m.group(3) not in ["if", "for", "while", "switch"]]
                
                # 상수 추출
                var_matches = re.finditer(r'(public|private|protected)?\s*(static\s+final|final\s+static)\s+\w+\s+([A-Z][A-Z0-9_]*)\s*=', content)
                result["variables"] = [m.group(3) for m in var_matches]
            
            # 기타 언어는 간단히 처리
            else:
                # 정규식 기반 간단 추출 (언어별 상세 구현 필요)
                pass
        
        except Exception as e:
            logger.error(f"코드 요소 추출 중 오류 발생: {str(e)}")
        
        return result
    
    async def search_code(
        self, 
        codebase_id: int, 
        query: str, 
        limit: int = 10, 
        threshold: float = 0.5,
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        코드베이스에서 코드를 검색합니다.
        
        Args:
            codebase_id: 코드베이스 ID
            query: 검색 쿼리
            limit: 최대 결과 수
            threshold: 유사도 임계값
            file_patterns: 검색할 파일 패턴
            exclude_patterns: 제외할 파일 패턴
            
        Returns:
            검색 결과 목록
        """
        # 설정 확인
        settings = get_indexing_settings(self.db, codebase_id)
        if not settings:
            settings = await self.initialize_indexing_settings(codebase_id)
        
        # 쿼리 임베딩 생성
        query_embedding = await self._generate_embedding(query, settings.embedding_model)
        if not query_embedding:
            return []
        
        # 모든 임베딩 가져오기 (실제로import os
import re
import logging
import fnmatch
import hashlib
import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import traceback

import numpy as np
from openai import OpenAI
import httpx
from sqlalchemy.orm import Session

from backend.models import IndexingStatus, IndexingFrequency
from backend.database.operations import (
    get_indexing_settings,
    create_or_update_indexing_settings,
    create_indexing_run,
    update_indexing_run,
    get_indexing_runs,
    get_latest_indexing_run,
    create_code_embedding,
    update_code_embedding,
    get_file_embeddings,
    delete_file_embeddings,
    get_codebase_embeddings_stats,
    get_codebase_files,
    get_codebases
)
from backend.database.connection import SessionLocal
from backend.database import models

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodebaseIndexingManager:
    """코드베이스 인덱싱 관리 클래스"""
    
    def __init__(self):
        """인덱싱 관리자 초기화"""
        self.db = SessionLocal()
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.current_runs = {}  # 현재 실행 중인 인덱싱 작업 (codebase_id: run_id)
    
    def __del__(self):
        """객체 소멸 시 DB 연결 닫기"""
        if self.db:
            self.db.close()
    
    async def initialize_indexing_settings(self, codebase_id: int) -> models.CodebaseIndexingSettings:
        """
        코드베이스의 인덱싱 설정을 초기화합니다.
        
        Args:
            codebase_id: 코드베이스 ID
            
        Returns:
            생성된 인덱싱 설정
        """
        # 기존 설정 확인
        settings = get_indexing_settings(self.db, codebase_id)
        if settings:
            return settings
        
        # 코드베이스 정보 확인
        codebase = get_codebases(self.db, codebase_id=codebase_id, single=True)
        if not codebase:
            raise ValueError(f"코드베이스 ID {codebase_id}을(를) 찾을 수 없습니다.")
        
        # 언어별 기본 설정 초기화
        default_settings = {
            "is_enabled": True,
            "frequency": "on_commit",
            "excluded_patterns": self._get_default_excluded_patterns(codebase.language),
            "priority_patterns": self._get_default_priority_patterns(codebase.language),
            "embedding_model": "openai/text-embedding-ada-002",
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "include_comments": True,
            "max_files_per_run": 100
        }
        
        # 설정 생성
        return create_or_update_indexing_settings(self.db, codebase_id, default_settings)
    
    def _get_default_excluded_patterns(self, language: str) -> List[str]:
        """
        언어별 기본 제외 패턴을 반환합니다.
        
        Args:
            language: 프로그래밍 언어
            
        Returns:
            제외 패턴 목록
        """
        # 공통 제외 패턴
        common_patterns = [
            "*.log", "*.md", "*.txt", 
            "*.json", "*.yaml", "*.yml",
            "*.min.js", "*.min.css",
            ".git/*", ".github/*", ".gitignore",
            "LICENSE", "README*",
            "node_modules/*", "dist/*", "build/*",
            "*.pyc", "__pycache__/*",
            ".DS_Store", "Thumbs.db"
        ]
        
        # 언어별 추가 패턴
        language_patterns = {
            "python": ["venv/*", "env/*", "*.egg-info/*", "*.egg", "*.whl"],
            "javascript": ["package-lock.json", "yarn.lock", "coverage/*"],
            "typescript": ["package-lock.json", "yarn.lock", "coverage/*", "*.d.ts"],
            "java":