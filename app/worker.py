import asyncio
import pdfplumber
from celery import Celery
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
# 引入“用完即毁”连接池，彻底阻断异步时空错乱
from sqlalchemy.pool import NullPool

from .ai_core import build_summary_chain, build_risk_chain, get_embeddings
from .database import SQLALCHEMY_DATABASE_URL
from .models import Document, AnalysisResult, DocumentChunk

celery_app = Celery(
    "docbridge_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=True,
)

# 【核心防线】：为劳工单独配置 NullPool 引擎
worker_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, poolclass=NullPool)
WorkerSessionLocal = sessionmaker(worker_engine, class_=AsyncSession, expire_on_commit=False)

async def update_doc_status(document_id: int, status: str, summary: str = None, risk_points: str = None):
    async with WorkerSessionLocal() as session:
        doc = await session.get(Document, document_id)
        if doc:
            doc.status = status
            if status == "completed":
                result = AnalysisResult(
                    document_id=document_id,
                    summary=summary,
                    risk_points={"raw_report": risk_points}
                )
                session.add(result)
            await session.commit()
    # 彻底销毁当前引擎痕迹
    await worker_engine.dispose()

async def save_chunks_and_vectors(document_id: int, chunks: list[str], vectors: list[list[float]]):
    async with WorkerSessionLocal() as session:
        for i, (text_chunk, vector) in enumerate(zip(chunks, vectors)):
            doc_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                text_content=text_chunk,
                embedding=vector
            )
            session.add(doc_chunk)
        await session.commit()
    await worker_engine.dispose()

@celery_app.task(name="analyze_document_task")
def analyze_document_task(file_path: str, document_id: int):
    text_content = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content += extracted + "\n"
    except Exception as e:
        asyncio.run(update_doc_status(document_id, "failed"))
        return {"status": "error", "message": f"物理穿透 PDF 失败: {str(e)}"}

    if not text_content.strip():
        asyncio.run(update_doc_status(document_id, "failed"))
        return {"status": "error", "message": "未能提取到有效文本"}

    text_chunk_for_summary = text_content[:3000]
    try:
        summary_res = build_summary_chain().invoke({"text": text_chunk_for_summary})
        risk_res = build_risk_chain().invoke({"text": text_chunk_for_summary})
    except Exception as e:
        asyncio.run(update_doc_status(document_id, "failed_auth"))
        return {"status": "error", "message": f"认知链阻断: {str(e)}"}

    try:
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_text(text_content)
        
        embed_model = get_embeddings()
        vectors = embed_model.embed_documents(chunks)
        
        # 写入 768 维坐标
        asyncio.run(save_chunks_and_vectors(document_id, chunks, vectors))
    except Exception as e:
        asyncio.run(update_doc_status(document_id, "failed_auth"))
        return {"status": "error", "message": f"向量化写入失败: {str(e)}"}

    asyncio.run(update_doc_status(document_id, "completed", summary_res, risk_res))
    return {"status": "success", "summary": summary_res, "risk_points": risk_res}