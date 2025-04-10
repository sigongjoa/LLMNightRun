"""
데이터베이스 마이그레이션 스크립트: 사용자 시스템 추가

이 스크립트는 사용자 관리 및 GitHub 저장소 관리를 위한 새로운 테이블을 추가합니다.
기존 GitHub 저장소 테이블을 새로운 스키마에 맞게 업데이트합니다.
"""

import logging
from sqlalchemy import create_engine, text, Table, Column, Integer, String, ForeignKey
from sqlalchemy.sql import select, update
from datetime import datetime

# 로거 설정
logger = logging.getLogger(__name__)

def upgrade(connection_string):
    """
    마이그레이션 업그레이드 함수
    
    Args:
        connection_string: 데이터베이스 연결 문자열
    """
    try:
        # 데이터베이스 엔진 생성
        engine = create_engine(connection_string)
        conn = engine.connect()
        
        logger.info("마이그레이션 시작: 사용자 시스템 추가")
        
        # 트랜잭션 시작
        trans = conn.begin()
        
        try:
            # 1. admin 사용자 생성 (임시 비밀번호: admin123)
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                is_active BOOLEAN DEFAULT TRUE,
                is_admin BOOLEAN DEFAULT FALSE,
                profile_image VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
            """))
            
            # 관리자 사용자 추가
            admin_exists = conn.execute(text("SELECT id FROM users WHERE username = 'admin'")).fetchone()
            if not admin_exists:
                # hashed_password는 실제 구현에서는 적절한 해싱 알고리즘으로 암호화해야 함
                # 여기서는 예시를 위해 간단히 'admin123'으로 설정
                conn.execute(text("""
                INSERT INTO users (username, email, hashed_password, is_admin, created_at, updated_at)
                VALUES ('admin', 'admin@example.com', 'admin123', TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """))
                logger.info("관리자 사용자 생성 완료")
            
            # 2. 사용자 설정 테이블 생성
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                openai_api_key VARCHAR(255),
                claude_api_key VARCHAR(255),
                github_token VARCHAR(255),
                default_github_repo VARCHAR(255),
                default_github_username VARCHAR(255),
                theme VARCHAR(20) DEFAULT 'light',
                language VARCHAR(10) DEFAULT 'ko',
                notification_enabled BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """))
            
            # 3. API 키 테이블 생성
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key_name VARCHAR(50) NOT NULL,
                key_value VARCHAR(255) NOT NULL UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """))
            
            # 4. OAuth 계정 테이블 생성
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS oauth_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider VARCHAR(20) NOT NULL,
                provider_user_id VARCHAR(100) NOT NULL,
                access_token VARCHAR(255) NOT NULL,
                refresh_token VARCHAR(255),
                expires_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (provider, provider_user_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """))
            
            # 5. 프로젝트 테이블 업데이트 (owner_id, is_public 필드 추가)
            # 먼저 projects 테이블이 있는지 확인
            projects_exists = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")).fetchone()
            
            if projects_exists:
                # owner_id 컬럼이 없는지 확인
                owner_id_exists = conn.execute(text("PRAGMA table_info(projects)")).fetchall()
                has_owner_id = any(col[1] == 'owner_id' for col in owner_id_exists)
                has_is_public = any(col[1] == 'is_public' for col in owner_id_exists)
                
                # 필요한 컬럼 추가
                if not has_owner_id:
                    conn.execute(text("ALTER TABLE projects ADD COLUMN owner_id INTEGER"))
                    # 관리자를 기본 소유자로 설정
                    admin_id = conn.execute(text("SELECT id FROM users WHERE username = 'admin'")).fetchone()[0]
                    conn.execute(text(f"UPDATE projects SET owner_id = {admin_id}"))
                    # 외래 키 제약 조건 추가는 SQLite에서는 불가능하므로 새 테이블로 마이그레이션 필요
                
                if not has_is_public:
                    conn.execute(text("ALTER TABLE projects ADD COLUMN is_public BOOLEAN DEFAULT FALSE"))
            
            # 6. 프로젝트 협업자 테이블 생성
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS project_collaborators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role VARCHAR(20) DEFAULT 'editor',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (project_id, user_id),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """))
            
            # 7. GitHub 저장소 테이블 업데이트
            # GitHub 저장소 테이블이 있는지 확인
            github_repos_exists = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='github_repositories'")).fetchone()
            
            if github_repos_exists:
                # 필요한 컬럼들이 있는지 확인
                columns = conn.execute(text("PRAGMA table_info(github_repositories)")).fetchall()
                col_names = [col[1] for col in columns]
                
                # user_id 컬럼이 없으면 추가
                if 'user_id' not in col_names:
                    conn.execute(text("ALTER TABLE github_repositories ADD COLUMN user_id INTEGER"))
                    # 관리자를 기본 소유자로 설정
                    admin_id = conn.execute(text("SELECT id FROM users WHERE username = 'admin'")).fetchone()[0]
                    conn.execute(text(f"UPDATE github_repositories SET user_id = {admin_id}"))
                
                # owner 컬럼을 github_owner로 변경할 수 없으므로 두 컬럼을 모두 유지
                if 'github_owner' not in col_names:
                    conn.execute(text("ALTER TABLE github_repositories ADD COLUMN github_owner VARCHAR(255)"))
                    conn.execute(text("UPDATE github_repositories SET github_owner = owner"))
                
                # 추가 필드들 추가
                for field in ['webhook_id', 'webhook_secret', 'sync_enabled', 'last_synced_at']:
                    if field not in col_names:
                        field_type = 'BOOLEAN DEFAULT FALSE' if field == 'sync_enabled' else 'VARCHAR(100)'
                        field_type = 'DATETIME' if field == 'last_synced_at' else field_type
                        conn.execute(text(f"ALTER TABLE github_repositories ADD COLUMN {field} {field_type}"))
            
            # 8. GitHub 커밋 히스토리 테이블 생성
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS github_commits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_id INTEGER NOT NULL,
                commit_hash VARCHAR(40) NOT NULL,
                author VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                commit_date DATETIME NOT NULL,
                files_changed INTEGER DEFAULT 0,
                additions INTEGER DEFAULT 0,
                deletions INTEGER DEFAULT 0,
                commit_data JSON DEFAULT '{}',
                related_question_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (repository_id, commit_hash),
                FOREIGN KEY (repository_id) REFERENCES github_repositories(id) ON DELETE CASCADE,
                FOREIGN KEY (related_question_id) REFERENCES questions(id) ON DELETE SET NULL
            )
            """))
            
            # 9. GitHub 웹훅 이벤트 테이블 생성
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS github_webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_id INTEGER NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                payload JSON NOT NULL,
                processed BOOLEAN DEFAULT FALSE,
                processed_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (repository_id) REFERENCES github_repositories(id) ON DELETE CASCADE
            )
            """))
            
            # 10. 사용자 활동 로그 테이블 생성
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type VARCHAR(50) NOT NULL,
                description TEXT,
                ip_address VARCHAR(45),
                user_agent VARCHAR(255),
                meta_data JSON DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """))
            
            # 11. 백그라운드 작업 테이블 생성
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS background_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id VARCHAR(36) NOT NULL UNIQUE,
                user_id INTEGER,
                task_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                progress FLOAT DEFAULT 0.0,
                result JSON,
                error TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                started_at DATETIME,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
            """))
            
            # 12. 알림 테이블 생성
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                category VARCHAR(50) NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                action_url VARCHAR(255),
                meta_data JSON DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """))
            
            # 13. GitHub 저장소 파일 테이블 생성
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS github_repository_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repository_id INTEGER NOT NULL,
                path VARCHAR(255) NOT NULL,
                name VARCHAR(100) NOT NULL,
                size INTEGER,
                sha VARCHAR(40),
                last_commit_hash VARCHAR(40),
                last_updated DATETIME,
                is_directory BOOLEAN DEFAULT FALSE,
                content_type VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (repository_id, path, name),
                FOREIGN KEY (repository_id) REFERENCES github_repositories(id) ON DELETE CASCADE
            )
            """))
            
            # 기존 Settings 테이블에서 데이터 가져와서 관리자 사용자 설정에 복사
            settings_exists = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")).fetchone()
            
            if settings_exists:
                settings = conn.execute(text("SELECT * FROM settings LIMIT 1")).fetchone()
                if settings:
                    admin_id = conn.execute(text("SELECT id FROM users WHERE username = 'admin'")).fetchone()[0]
                    
                    # 기존 사용자 설정이 있는지 확인
                    user_settings_exists = conn.execute(text(f"SELECT id FROM user_settings WHERE user_id = {admin_id}")).fetchone()
                    
                    if not user_settings_exists:
                        # settings 테이블 컬럼 이름 가져오기
                        settings_columns = conn.execute(text("PRAGMA table_info(settings)")).fetchall()
                        col_names = [col[1] for col in settings_columns]
                        
                        # 공통 필드들 매핑
                        common_fields = {}
                        for field in ['openai_api_key', 'claude_api_key', 'github_token', 'github_repo', 'github_username']:
                            if field in col_names:
                                idx = col_names.index(field)
                                if settings[idx] is not None:  # None 값 제외
                                    github_field = field
                                    if field == 'github_repo':
                                        github_field = 'default_github_repo'
                                    elif field == 'github_username':
                                        github_field = 'default_github_username'
                                    common_fields[github_field] = settings[idx]
                        
                        # 관리자의 사용자 설정 생성
                        fields_str = ', '.join(['user_id'] + list(common_fields.keys()))
                        values_str = ', '.join([str(admin_id)] + [f"'{val}'" for val in common_fields.values()])
                        
                        conn.execute(text(f"""
                        INSERT INTO user_settings ({fields_str}, created_at, updated_at)
                        VALUES ({values_str}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """))
                        
                        logger.info("관리자 사용자 설정을 기존 설정값으로 초기화했습니다.")
            
            # 트랜잭션 커밋
            trans.commit()
            logger.info("마이그레이션 완료: 사용자 시스템 추가")
            
        except Exception as e:
            # 오류 발생 시 롤백
            trans.rollback()
            logger.error(f"마이그레이션 실패: {str(e)}")
            raise
        
        finally:
            # 연결 종료
            conn.close()
    
    except Exception as e:
        logger.error(f"마이그레이션 오류: {str(e)}")
        raise

def downgrade(connection_string):
    """
    마이그레이션 다운그레이드 함수 (롤백)
    
    Args:
        connection_string: 데이터베이스 연결 문자열
    """
    try:
        # 데이터베이스 엔진 생성
        engine = create_engine(connection_string)
        conn = engine.connect()
        
        logger.info("마이그레이션 롤백 시작: 사용자 시스템 제거")
        
        # 트랜잭션 시작
        trans = conn.begin()
        
        try:
            # 추가한 테이블 삭제 (역순으로)
            tables_to_drop = [
                "github_repository_files",
                "notifications",
                "background_tasks",
                "user_activities",
                "github_webhook_events",
                "github_commits",
                "project_collaborators",
                "oauth_accounts",
                "api_keys",
                "user_settings",
            ]
            
            for table in tables_to_drop:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
            
            # Projects 테이블에서 추가한 컬럼 제거
            # SQLite는 컬럼 삭제를 직접 지원하지 않으므로, 실제 운영 시에는 테이블 재생성 필요
            # 여기서는 롤백을 위한 예시로 남겨둠
            
            # GitHub Repositories 테이블에서 추가한 컬럼 제거
            # SQLite는 컬럼 삭제를 직접 지원하지 않으므로, 실제 운영 시에는 테이블 재생성 필요
            
            # users 테이블을 마지막으로 삭제
            conn.execute(text("DROP TABLE IF EXISTS users"))
            
            # 트랜잭션 커밋
            trans.commit()
            logger.info("마이그레이션 롤백 완료: 사용자 시스템 제거")
            
        except Exception as e:
            # 오류 발생 시 롤백
            trans.rollback()
            logger.error(f"마이그레이션 롤백 실패: {str(e)}")
            raise
        
        finally:
            # 연결 종료
            conn.close()
    
    except Exception as e:
        logger.error(f"마이그레이션 롤백 오류: {str(e)}")
        raise
