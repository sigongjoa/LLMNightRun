from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .connection import Base

class LLMTypeEnum(enum.Enum):
    openai_api = "openai_api"
    openai_web = "openai_web"
    claude_api = "claude_api"
    claude_web = "claude_web"
    manual = "manual"

class CodeLanguageEnum(enum.Enum):
    python = "python"
    javascript = "javascript"
    typescript = "typescript"
    java = "java"
    csharp = "csharp"
    cpp = "cpp"
    go = "go"
    rust = "rust"
    php = "php"
    ruby = "ruby"
    swift = "swift"
    kotlin = "kotlin"
    other = "other"

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 정의
    responses = relationship("Response", back_populates="question")
    code_snippets = relationship("CodeSnippet", back_populates="question")

class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    llm_type = Column(Enum(LLMTypeEnum), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 정의
    question = relationship("Question", back_populates="responses")
    code_snippets = relationship("CodeSnippet", back_populates="response")

class CodeSnippet(Base):
    __tablename__ = "code_snippets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    language = Column(Enum(CodeLanguageEnum), nullable=False)
    tags = Column(JSON, default=list)
    source_llm = Column(Enum(LLMTypeEnum), nullable=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    response_id = Column(Integer, ForeignKey("responses.id"), nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    question = relationship("Question", back_populates="code_snippets")
    response = relationship("Response", back_populates="code_snippets")
    parent_id = Column(Integer, ForeignKey("code_snippets.id"), nullable=True)
    children = relationship("CodeSnippet")

class CodeTemplate(Base):
    __tablename__ = "code_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    language = Column(Enum(CodeLanguageEnum), nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    openai_api_key = Column(String(255), nullable=True)
    claude_api_key = Column(String(255), nullable=True)
    github_token = Column(String(255), nullable=True)
    github_repo = Column(String(255), nullable=True)
    github_username = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)