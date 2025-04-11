from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# 사용자 모델
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계 정의
    questions = relationship("Question", back_populates="user")
    responses = relationship("Response", back_populates="user")
    repositories = relationship("GitHubRepository", back_populates="owner")
    prompt_templates = relationship("PromptTemplate", back_populates="user")


# 질문 모델
class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    tags = Column(ARRAY(String), default=list)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 외래 키 및 관계 정의
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="questions")
    responses = relationship("Response", back_populates="question")


# 응답 모델
class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    llm_type = Column(String)  # 'openai', 'claude', 'local', 등
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 외래 키 및 관계 정의
    user_id = Column(Integer, ForeignKey("users.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    user = relationship("User", back_populates="responses")
    question = relationship("Question", back_populates="responses")


# GitHub 저장소 모델
class GitHubRepository(Base):
    __tablename__ = "github_repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    is_private = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 외래 키 및 관계 정의
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="repositories")


# 프롬프트 템플릿 모델
class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    content = Column(Text)
    system_prompt = Column(Text, nullable=True)  # 시스템 프롬프트 필드 추가
    description = Column(Text, nullable=True)
    category = Column(String, default="일반")
    tags = Column(ARRAY(String), default=list)
    template_variables = Column(ARRAY(String), default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 외래 키 및 관계 정의
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="prompt_templates")
