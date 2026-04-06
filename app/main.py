import os
import aiofiles
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from celery.result import AsyncResult
from pydantic import BaseModel

from .database import get_db
from .models import Document, AnalysisResult, DocumentChunk
from .worker import analyze_document_task, celery_app
from .ai_core import build_summary_chain, build_risk_chain, build_qa_chain, get_embeddings

app = FastAPI(
    title="DocBridge AI API",
    description="多语境商业情报中枢 - 异步接入网关",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root_gateway():
    return {"status": "online", "message": "统帅，认知管线网关在线！"}

@app.post("/api/v1/upload/")
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未检测到文件名")
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件写入失败: {str(e)}")

    new_doc = Document(title=file.filename, filename=file.filename, file_path=file_path, status="processing")
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    task = analyze_document_task.delay(file_path, new_doc.id)
    return {"status": "success", "document_id": new_doc.id, "task_id": task.id, "message": "文件落盘完毕，劳工全速解析中！"}

@app.get("/api/v1/task/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": task_result.status, "result": task_result.result if task_result.ready() else "解析中..."}

@app.get("/api/v1/documents/")
async def get_all_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return {
        "status": "success",
        "data": [{"id": doc.id, "filename": doc.filename, "language": doc.language, "status": doc.status, "created_at": doc.created_at.strftime("%Y-%m-%d %H:%M:%S") if doc.created_at else None} for doc in docs]
    }

@app.get("/api/v1/documents/{document_id}/result")
async def get_document_result(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AnalysisResult).where(AnalysisResult.document_id == document_id))
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(status_code=404, detail="尚无认知结果")
    return {"status": "success", "summary": analysis.summary, "risk_points": analysis.risk_points}

# =========================================================
# 【全新神兵】：RAG 向量狙击与审讯通道
# =========================================================
class ChatRequest(BaseModel):
    query: str

@app.post("/api/v1/documents/{document_id}/chat")
async def chat_with_document(document_id: int, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    query_text = request.query
    if not query_text.strip():
        raise HTTPException(status_code=400, detail="提问不可为空")

    try:
        # 1. 提问向量化 (将统帅的文字化为 768 维坐标)
        embed_model = get_embeddings()
        query_vector = embed_model.embed_query(query_text)

        # 2. 余弦相似度检索 (在 pgvector 中寻找距离最近的 3 个切片)
        stmt = select(DocumentChunk).where(
            DocumentChunk.document_id == document_id
        ).order_by(
            DocumentChunk.embedding.cosine_distance(query_vector)
        ).limit(3)
        
        result = await db.execute(stmt)
        top_chunks = result.scalars().all()

        if not top_chunks:
            return {"status": "success", "answer": "未找到物理切片，该文档可能尚未被成功向量化。"}

        # 3. 拼接上下文
        context = "\n\n---\n\n".join([chunk.text_content for chunk in top_chunks])

        # 4. 召唤大模型作答
        qa_chain = build_qa_chain()
        answer = qa_chain.invoke({"context": context, "question": query_text})

        return {"status": "success", "answer": answer}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审讯回路异常: {str(e)}")