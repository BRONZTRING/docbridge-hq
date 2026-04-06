import os
import aiofiles
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from celery.result import AsyncResult

from .database import get_db
# 【补充导入】：加上 AnalysisResult
from .models import Document, AnalysisResult
from .worker import analyze_document_task, celery_app

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

    new_doc = Document(
        title=file.filename,
        filename=file.filename,
        file_path=file_path,
        status="processing"
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)

    task = analyze_document_task.delay(file_path, new_doc.id)

    return {
        "status": "success",
        "document_id": new_doc.id,
        "task_id": task.id,
        "message": "统帅，文件落盘且已登记入库，劳工正在全速解析！"
    }

@app.get("/api/v1/task/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else "劳工仍在奋力解析中..."
    }

@app.get("/api/v1/documents/")
async def get_all_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return {
        "status": "success",
        "data": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "language": doc.language,
                "status": doc.status,
                "created_at": doc.created_at.strftime("%Y-%m-%d %H:%M:%S") if doc.created_at else None
            }
            for doc in docs
        ]
    }

# 【新增兵器】：专门提取具体某一份卷宗的 AI 认知结果
@app.get("/api/v1/documents/{document_id}/result")
async def get_document_result(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AnalysisResult).where(AnalysisResult.document_id == document_id))
    analysis = result.scalars().first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="尚无认知结果，可能仍在解析或解析失败。")
        
    return {
        "status": "success",
        "summary": analysis.summary,
        "risk_points": analysis.risk_points
    }