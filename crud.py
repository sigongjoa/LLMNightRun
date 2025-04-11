from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models
import schemas

# 비밀번호 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 사용자 관련 CRUD 함수
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 질문 관련 CRUD 함수
def get_questions(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Question).filter(models.Question.user_id == user_id).offset(skip).limit(limit).all()

def get_question(db: Session, question_id: int):
    return db.query(models.Question).filter(models.Question.id == question_id).first()

def create_question(db: Session, question: schemas.QuestionCreate, user_id: int):
    db_question = models.Question(**question.dict(), user_id=user_id)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

# 응답 관련 CRUD 함수
def get_responses(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Response).filter(models.Response.user_id == user_id).offset(skip).limit(limit).all()

def get_response(db: Session, response_id: int):
    return db.query(models.Response).filter(models.Response.id == response_id).first()

def create_response(db: Session, response: schemas.ResponseCreate, user_id: int):
    db_response = models.Response(**response.dict(), user_id=user_id)
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

# GitHub 저장소 관련 CRUD 함수
def get_github_repository(db: Session, repo_id: int):
    return db.query(models.GitHubRepository).filter(models.GitHubRepository.id == repo_id).first()

def get_user_github_repositories(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.GitHubRepository).filter(
        models.GitHubRepository.owner_id == user_id
    ).offset(skip).limit(limit).all()

def create_github_repository(db: Session, repository: schemas.GitHubRepositoryCreate, user_id: int):
    db_repo = models.GitHubRepository(
        name=repository.name,
        url=repository.url,
        description=repository.description,
        is_private=repository.is_private,
        owner_id=user_id
    )
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    return db_repo

def update_github_repository(db: Session, repo_id: int, repository: schemas.GitHubRepositoryCreate):
    db_repo = get_github_repository(db, repo_id=repo_id)
    if db_repo:
        db_repo.name = repository.name
        db_repo.url = repository.url
        db_repo.description = repository.description
        db_repo.is_private = repository.is_private
        db.commit()
        db.refresh(db_repo)
    return db_repo

def delete_github_repository(db: Session, repo_id: int):
    db_repo = get_github_repository(db, repo_id=repo_id)
    if db_repo:
        db.delete(db_repo)
        db.commit()
    return db_repo
