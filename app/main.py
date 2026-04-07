import os
import aiofiles
import asyncio
from datetime import timedelta
from typing import List, Dict, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from celery.result import AsyncResult
from pydantic import BaseModel

from .database import get_db
from .models import User, Document, AnalysisResult, DocumentChunk
from .worker import analyze_document_task, celery_app
from .ai_core import build_qa_chain, get_embeddings, PrivacyShield
from .auth import get_password_hash, verify_password, create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI(title="DocBridge AI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
os.makedirs("uploads", exist_ok=True)

# ==========================================
# 🔐 身份验证总署
# ==========================================
@app.post("/api/v1/auth/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    existing_user = (await db.execute(select(User).where(User.username == form_data.username))).scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="该代号已被注册")
    new_user = User(username=form_data.username, hashed_password=get_password_hash(form_data.password))
    db.add(new_user)
    await db.commit()
    return {"status": "success", "message": "兵符铸造成功，请持兵符登录"}

@app.post("/api/v1/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.username == form_data.username))).scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="代号或口令错误")
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

# ==========================================
# 📡 战报雷达 (无需Token，暂作开放)
# ==========================================
@app.websocket("/api/v1/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        process = await asyncio.create_subprocess_exec("tail", "-n", "50", "-f", "logs/worker.log", stdout=asyncio.subprocess.PIPE)
        while line := await process.stdout.readline():
            await websocket.send_text(line.decode('utf-8').strip())
    except Exception:
        if 'process' in locals(): process.terminate()

# ==========================================
# 📂 档案与审讯 (全线加装哨兵 current_user)
# ==========================================
@app.post("/api/v1/upload/")
async def upload_document(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    file_path = os.path.join("uploads", f"{current_user.id}_{file.filename}")
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024): await out_file.write(content)
    
    # 刻上主人的烙印
    new_doc = Document(title=file.filename, filename=file.filename, file_path=file_path, status="processing", owner_id=current_user.id)
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    analyze_document_task.delay(file_path, new_doc.id)
    return {"status": "success"}

@app.get("/api/v1/documents/")
async def get_all_documents(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 绝对隔离：只返回属于自己的档案
    docs = (await db.execute(select(Document).where(Document.owner_id == current_user.id).order_by(Document.created_at.desc()))).scalars().all()
    return {"status": "success", "data": [{"id": d.id, "filename": d.filename, "status": d.status} for d in docs]}

@app.get("/api/v1/documents/{document_id}/result")
async def get_document_result(document_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 双重校验：必须是自己的档案
    doc = (await db.execute(select(Document).where(Document.id == document_id, Document.owner_id == current_user.id))).scalars().first()
    if not doc: raise HTTPException(status_code=403, detail="无权调阅此卷宗")
    
    analysis = (await db.execute(select(AnalysisResult).where(AnalysisResult.document_id == document_id))).scalars().first()
    if not analysis: raise HTTPException(status_code=404)
    return {"status": "success", "summary": analysis.summary, "risk_points": analysis.risk_points}

class ChatRequest(BaseModel): 
    query: str
    history: Optional[List[Dict[str, str]]] = []
    document_id: Optional[int] = None

@app.post("/api/v1/chat")
async def unified_chat(request: ChatRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        q_vec = get_embeddings().embed_query(request.query)
        
        # 核心防线：连表查询，全局搜索时也绝不会扫到其他人的切片
        stmt = select(DocumentChunk).join(Document).where(Document.owner_id == current_user.id)
        if request.document_id: 
            stmt = stmt.where(DocumentChunk.document_id == request.document_id)
            
        stmt = stmt.order_by(DocumentChunk.embedding.cosine_distance(q_vec)).limit(4)
        top_chunks = (await db.execute(stmt)).scalars().all()
        
        if not top_chunks: return {"status": "success", "answer": "雷达未能扫过相关物理切片。"}
        
        raw_context = "\n\n".join([f"[片段来源 DocID:{c.document_id}] {c.text_content}" for c in top_chunks])
        
        formatted_history = ""
        for msg in request.history[-6:]:
            role = "统帅" if msg.get("role") == "user" else "AI 参谋"
            formatted_history += f"[{role}]: {msg.get('content')}\n"
        if not formatted_history: formatted_history = "暂无历史对话。"

        shield = PrivacyShield()
        masked_answer = await build_qa_chain().ainvoke({
            "context": shield.mask(raw_context), 
            "chat_history": formatted_history,
            "question": shield.mask(request.query)
        })
        
        return {"status": "success", "answer": shield.unmask(masked_answer)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))