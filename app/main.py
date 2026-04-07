import os
import aiofiles
import asyncio
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 【新增】：WebSocket 实时读取劳工战报，输送至前端
@app.websocket("/api/v1/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        # 利用系统级 tail 命令，实时截获最后 50 行并追踪
        process = await asyncio.create_subprocess_exec(
            "tail", "-n", "50", "-f", "logs/worker.log",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            await websocket.send_text(line.decode('utf-8').strip())
    except WebSocketDisconnect:
        if 'process' in locals(): process.terminate()
    except Exception as e:
        print(f"战报管线中断: {e}")
        if 'process' in locals(): process.terminate()

@app.get("/")
async def root_gateway():
    return {"status": "online", "message": "统帅，认知管线网关在线！"}

@app.post("/api/v1/upload/")
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未检测到文件名")
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await file.read(1024 * 1024):
            await out_file.write(content)

    new_doc = Document(title=file.filename, filename=file.filename, file_path=file_path, status="processing")
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    task = analyze_document_task.delay(file_path, new_doc.id)
    return {"status": "success", "document_id": new_doc.id, "task_id": task.id}

@app.get("/api/v1/task/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    return {"task_id": task_id, "status": task_result.status, "result": task_result.result if task_result.ready() else "解析中..."}

@app.get("/api/v1/documents/")
async def get_all_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return {"status": "success", "data": [{"id": doc.id, "filename": doc.filename, "status": doc.status} for doc in docs]}

@app.get("/api/v1/documents/{document_id}/result")
async def get_document_result(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AnalysisResult).where(AnalysisResult.document_id == document_id))
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(status_code=404, detail="尚无认知结果")
    return {"status": "success", "summary": analysis.summary, "risk_points": analysis.risk_points}

class ChatRequest(BaseModel):
    query: str

@app.post("/api/v1/documents/{document_id}/chat")
async def chat_with_document(document_id: int, request: ChatRequest, db: AsyncSession = Depends(get_db)):
    try:
        query_vector = get_embeddings().embed_query(request.query)
        stmt = select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.embedding.cosine_distance(query_vector)).limit(3)
        top_chunks = (await db.execute(stmt)).scalars().all()

        if not top_chunks:
            return {"status": "success", "answer": "未找到物理切片。"}

        context = "\n\n".join([chunk.text_content for chunk in top_chunks])
        answer = await build_qa_chain().ainvoke({"context": context, "question": request.query})
        return {"status": "success", "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"审讯异常: {str(e)}")