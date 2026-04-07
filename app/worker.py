import asyncio
import os
import pdfplumber
import docx  # 战术甲：新增对 Word 的支持
from celery import Celery
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .ai_core import build_summary_chain, build_risk_chain, get_embeddings
from .database import SQLALCHEMY_DATABASE_URL
from .models import Document, AnalysisResult, DocumentChunk

celery_app = Celery("docbridge_worker", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")
celery_app.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"], timezone="Europe/Moscow", enable_utc=True)

worker_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, poolclass=NullPool)
WorkerSessionLocal = sessionmaker(worker_engine, class_=AsyncSession, expire_on_commit=False)

async def update_doc_status(document_id: int, status: str, summary: str = None, risk_points: str = None):
    async with WorkerSessionLocal() as session:
        doc = await session.get(Document, document_id)
        if doc:
            doc.status = status
            if status == "completed":
                session.add(AnalysisResult(document_id=document_id, summary=summary, risk_points={"raw_report": risk_points}))
            await session.commit()
    await worker_engine.dispose()

async def save_chunks_and_vectors(document_id: int, chunks: list[str], vectors: list[list[float]]):
    async with WorkerSessionLocal() as session:
        for i, (text_chunk, vector) in enumerate(zip(chunks, vectors)):
            session.add(DocumentChunk(document_id=document_id, chunk_index=i, text_content=text_chunk, embedding=vector))
        await session.commit()
    await worker_engine.dispose()

@celery_app.task(name="analyze_document_task")
def analyze_document_task(file_path: str, document_id: int):
    text_content = ""
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        # ==========================================
        # 🛠️ 战术甲：全模态与表格穿透
        # ==========================================
        if ext == '.pdf':
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    # 提取纯文本
                    if extracted := page.extract_text(): 
                        text_content += extracted + "\n"
                    # 提取表格并转化为 Markdown 结构
                    for table in page.extract_tables():
                        for row in table:
                            cleaned_row = [str(cell).replace("\n", " ") if cell else "" for cell in row]
                            text_content += " | ".join(cleaned_row) + " |\n"
        elif ext == '.docx':
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text_content += para.text + "\n"
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
            
    except Exception as e:
        asyncio.run(update_doc_status(document_id, "failed"))
        return {"status": "error", "message": f"文件穿透失败: {str(e)}"}

    if not text_content.strip():
        asyncio.run(update_doc_status(document_id, "failed"))
        return {"status": "error", "message": "未能提取有效文本或表格"}

    try:
        summary_res = build_summary_chain().invoke({"text": text_content[:3000]})
        risk_res = build_risk_chain().invoke({"text": text_content[:3000]})
    except Exception as e:
        asyncio.run(update_doc_status(document_id, "failed_auth"))
        return {"status": "error", "message": f"认知链阻断: {str(e)}"}

    try:
        chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100).split_text(text_content)
        vectors = get_embeddings().embed_documents(chunks)
        asyncio.run(save_chunks_and_vectors(document_id, chunks, vectors))
    except Exception as e:
        asyncio.run(update_doc_status(document_id, "failed_auth"))
        return {"status": "error", "message": f"向量化失败: {str(e)}"}

    asyncio.run(update_doc_status(document_id, "completed", summary_res, risk_res))
    return {"status": "success"}