from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    """
    第一层级：用户表 (User)
    记录出海企业或高净值 B 端客户的凭证
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联：一个用户可拥有多个文档
    documents = relationship("Document", back_populates="owner")


class Document(Base):
    """
    第二层级：文档表 (Document)
    承载多语种(中/日/俄/英)的物理文件元数据，记录异步处理状态
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)  # 物理存储的文件名
    file_path = Column(String(500), nullable=False) # 磁盘绝对/相对路径
    language = Column(String(20), default="unknown") # 语种：ru, ja, en, zh
    status = Column(String(50), default="uploaded") # 状态：uploaded, processing, completed, failed
    
    # 外键：归属哪个用户
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联：上下级打通
    owner = relationship("User", back_populates="documents")
    analysis_result = relationship("AnalysisResult", back_populates="document", uselist=False)


class AnalysisResult(Base):
    """
    第三层级：认知结果表 (AnalysisResult)
    承载 LangChain 递归摘要链与风险雷达萃取后的情报
    """
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), unique=True)
    
    summary = Column(Text) # 深度长文档浓缩摘要
    risk_points = Column(JSON) # 风险拦截雷达提取的结构化风险点 (违约责任、管辖地等)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联：归属哪个文档
    document = relationship("Document", back_populates="analysis_result")