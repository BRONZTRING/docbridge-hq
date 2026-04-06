import asyncio
import pdfplumber
from celery import Celery
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .ai_core import build_summary_chain, build_risk_chain, get_embeddings
from .database import AsyncSessionLocal
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

async def update_doc_status(document_id: int, status: str, summary: str = None, risk_points: str = None):
    async with AsyncSessionLocal() as session:
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

# 【全新法术】：将切碎的文本及其高维坐标，批量存入 PostgreSQL
async def save_chunks_and_vectors(document_id: int, chunks: list[str], vectors: list[list[float]]):
    async with AsyncSessionLocal() as session:
        for i, (text_chunk, vector) in enumerate(zip(chunks, vectors)):
            doc_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=i,
                text_content=text_chunk,
                embedding=vector # 1536维数组直接存入 pgvector 字段！
            )
            session.add(doc_chunk)
        await session.commit()

@celery_app.task(name="analyze_document_task")
def analyze_document_task(file_path: str, document_id: int):
    # 1. 物理穿透 PDF
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

    # 2. 宏观认知 (取前 3000 字做摘要，防止超长文档撑爆摘要模型)
    text_chunk_for_summary = text_content[:3000]
    try:
        summary_res = build_summary_chain().invoke({"text": text_chunk_for_summary})
        risk_res = build_risk_chain().invoke({"text": text_chunk_for_summary})
    except Exception as e:
        asyncio.run(update_doc_status(document_id, "failed_auth"))
        return {"status": "error", "message": f"认知链阻断: {str(e)}"}

    # ==========================================
    # 3. 【向量觉醒核心阶段】：千刀万剐与高维折叠
    # ==========================================
    try:
        # 定义碎纸机规则：每 1000 个字符切一刀，相邻两刀保留 100 字符重叠(防断句断意)
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_text(text_content)
        
        # 调用大模型，将切出来的文字块化作数学坐标 (由于是并发网络请求，可能会稍耗时)
        embed_model = get_embeddings()
        vectors = embed_model.embed_documents(chunks)
        
        # 召唤异步函数，将坐标与文字封存入库
        asyncio.run(save_chunks_and_vectors(document_id, chunks, vectors))
        
    except Exception as e:
        # 向量化若失败（比如网络抖动），不阻断总体流程，仅记录报错
        print(f"⚠️ [警告] 文档 {document_id} 向量化折叠失败: {str(e)}")

    # 4. 全部大捷，标记完工
    asyncio.run(update_doc_status(document_id, "completed", summary_res, risk_res))
    return {"status": "success", "summary": summary_res, "risk_points": risk_res}