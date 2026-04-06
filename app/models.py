from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector  # 【新增】引入高维向量装甲

from .database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    filename = Column(String(255))
    file_path = Column(String(500))
    language = Column(String(50), default="unknown")
    status = Column(String(50), default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 建立与分析结果、以及切片的级联关系
    analysis = relationship("AnalysisResult", back_populates="document", uselist=False, cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), unique=True)
    summary = Column(Text)
    risk_points = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="analysis")

# 【全新法阵】：文档切片与向量坐标表
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer, comment="切片序号")
    text_content = Column(Text, comment="切片物理文本")
    
    # 核心武器：存储 1536 维度的浮点数坐标 (适配 OpenAI 的 text-embedding-3-small 模型)
    embedding = Column(Vector(1536), comment="高维数学坐标")

    document = relationship("Document", back_populates="chunks")