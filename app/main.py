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
from .ai_core import build_qa_chain, get_embeddings, PrivacyShield

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

class ChatRequest(BaseModel): 
    query: str
    history: Optional[List[Dict[str, str]]] = []
    document_id: Optional[int] = None  # 如果为 None，则是全局搜索！

@app.post("/api/v1/chat")
async def unified_chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        q_vec = get_embeddings().embed_query(request.query)
        
        # ==========================================
        # 🌐 战术丙：支持全局跨文档检索
        # ==========================================
        stmt = select(DocumentChunk).order_by(DocumentChunk.embedding.cosine_distance(q_vec)).limit(4)
        if request.document_id: # 局部检索
            stmt = stmt.where(DocumentChunk.document_id == request.document_id)
            
        top_chunks = (await db.execute(stmt)).scalars().all()
        if not top_chunks: return {"status": "success", "answer": "雷达未能扫过相关物理切片。"}
        
        raw_context = "\n\n".join([f"[片段来源 DocID:{c.document_id}] {c.text_content}" for c in top_chunks])
        
        # 组装记忆矩阵
        formatted_history = ""
        for msg in request.history[-6:]:
            role = "统帅" if msg.get("role") == "user" else "AI 参谋"
            formatted_history += f"[{role}]: {msg.get('content')}\n"
        if not formatted_history: formatted_history = "暂无历史对话。"

        # ==========================================
        # 🛡️ 战术乙应用：拦截敏感词
        # ==========================================
        shield = PrivacyShield()
        masked_context = shield.mask(raw_context)
        masked_query = shield.mask(request.query)

        # 呼叫云端 (此时金额已被替换为 [绝密金额_1] 等)
        masked_answer = await build_qa_chain().ainvoke({
            "context": masked_context, 
            "chat_history": formatted_history,
            "question": masked_query
        })
        
        # 收回后还原绝密数据
        final_answer = shield.unmask(masked_answer)

        return {"status": "success", "answer": final_answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))