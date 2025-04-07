"""
데이터베이스 열거형 업데이트 스크립트

데이터베이스의 열거형 타입에 새로운 값을 추가합니다.
"""

import os
import sys
import sqlite3

# 프로젝트 루트 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def update_llm_type_enum():
    """
    LLMTypeEnum에 local_llm 추가
    """
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'llmnightrun.db'))
    
    # 데이터베이스 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # SQLite에는 ALTER TYPE이 없으므로, 직접 값을 추가
        # 기존 enum 값 확인
        cursor.execute("PRAGMA table_info(responses)")
        columns_info = cursor.fetchall()
        
        for column in columns_info:
            if column[1] == 'llm_type':
                check_constraint = column[5]  # CHECK 제약조건
                if 'local_llm' not in check_constraint:
                    print("[*] 기존 LLMTypeEnum 확인:", check_constraint)
                    # 새로운 enum 값을 포함하는 제약조건 생성
                    new_constraint = check_constraint.replace("'manual')", "'manual', 'local_llm')")
                    
                    # 테이블 구조 변경
                    # 1. 임시 테이블 생성
                    cursor.execute("""
                    CREATE TABLE responses_new (
                        id INTEGER PRIMARY KEY, 
                        question_id INTEGER,
                        llm_type TEXT CHECK(llm_type IN ('openai_api', 'openai_web', 'claude_api', 'claude_web', 'local_llm', 'manual')),
                        content TEXT NOT NULL,
                        created_at TIMESTAMP
                    )
                    """)
                    
                    # 2. 데이터 복사
                    cursor.execute("""
                    INSERT INTO responses_new
                    SELECT id, question_id, llm_type, content, created_at
                    FROM responses
                    """)
                    
                    # 3. 기존 테이블 삭제
                    cursor.execute("DROP TABLE responses")
                    
                    # 4. 새 테이블 이름 변경
                    cursor.execute("ALTER TABLE responses_new RENAME TO responses")
                    
                    # 5. 외래 키 제약 조건 재생성
                    cursor.execute("""
                    CREATE INDEX ix_responses_id ON responses (id)
                    """)
                    
                    print("[+] LLMTypeEnum에 'local_llm' 값이 추가되었습니다.")
                else:
                    print("[*] LLMTypeEnum에 이미 'local_llm' 값이 있습니다.")
                break
        
        # 변경사항 저장
        conn.commit()
        print("[+] 데이터베이스 업데이트가 완료되었습니다.")
        
    except Exception as e:
        conn.rollback()
        print(f"[!] 오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("[*] 데이터베이스 열거형 업데이트 시작...")
    update_llm_type_enum()
    print("[*] 작업 완료.")
