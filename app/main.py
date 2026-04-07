import os
import aiofiles
import asyncio
from typing import List, Dict, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from celery.result import AsyncResult
from pydantic import BaseModel
from .database import get_db
from .models import Document, AnalysisResult, DocumentChunk
from .worker import analyze_document_task, celery_app
from .ai_core import build_qa_chain, get_embeddings

app = FastAPI(title="DocBridge AI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
os.makedirs("uploads", exist_ok=True)

@app.websocket("/api/v1/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        process = await asyncio.create_subprocess_exec("tail", "-n", "50", "-f", "logs/worker.log", stdout=asyncio.subprocess.PIPE)
        while line := await process.stdout.readline():
            await websocket.send_text(line.decode('utf-8').strip())
    except WebSocketDisconnect:
        if 'process' in locals(): process.terminate()
    except Exception:
        if 'process' in locals(): process.terminate()

@app.post("/api/v1/upload/")
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    file_path = os.path.join("uploads", file.filename)
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024): await out_file.write(content)
    new_doc = Document(title=file.filename, filename=file.filename, file_path=file_path, status="processing")
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    task = analyze_document_task.delay(file_path, new_doc.id)
    return {"status": "success", "document_id": new_doc.id, "task_id": task.id}

@app.get("/api/v1/documents/")
async def get_all_documents(db: AsyncSession = Depends(get_db)):
    docs = (await db.execute(select(Document).order_by(Document.created_at.desc()))).scalars().all()
    return {"status": "success", "data": [{"id": d.id, "filename": d.filename, "status": d.status} for d in docs]}

@app.get("/api/v1/documents/{document_id}/result")
async def get_document_result(document_id: int, db: AsyncSession = Depends(get_db)):
    analysis = (await db.execute(select(AnalysisResult).where(AnalysisResult.document_id == document_id))).scalars().first()
    if not analysis: raise HTTPException(status_code=404)
    return {"status": "success", "summary": analysis.summary, "risk_points": analysis.risk_points}

# 【战术升级】：请求体中加入可选的 history 字段
class ChatRequest(BaseModel): 
    query: str
    history: Optional[List[Dict[str, str]]] = []

@app.post("/api/v1/documents/{document_id}/chat")
async def chat_with_document(document_id: int, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        q_vec = get_embeddings().embed_query(request.query)
        top_chunks = (await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.embedding.cosine_distance(q_vec)).limit(3))).scalars().all()
        if not top_chunks: return {"status": "success", "answer": "未找到物理切片。"}
        
        context = "\n\n".join([chunk.text_content for chunk in top_chunks])
        
        # 组装记忆矩阵
        formatted_history = ""
        for msg in request.history[-6:]: # 只保留最近3轮对话（6条），防止上下文爆炸
            role = "统帅" if msg.get("role") == "user" else "AI 参谋"
            formatted_history += f"[{role}]: {msg.get('content')}\n"
        if not formatted_history: formatted_history = "暂无历史对话。"

        answer = await build_qa_chain().ainvoke({
            "context": context, 
            "chat_history": formatted_history,
            "question": request.query
        })
        return {"status": "success", "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))