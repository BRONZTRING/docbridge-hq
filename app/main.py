import os
import aiofiles
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from celery.result import AsyncResult

from .database import get_db
from .models import Document
from .worker import analyze_document_task, celery_app

app = FastAPI(
    title="DocBridge AI API",
    description="多语境商业情报中枢 - 异步接入网关",
    version="1.0.0"
)

# 【破壁法阵】：打破跨域结界，允许前端 Vue3 (5173端口) 访问网关
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 统帅大营内部测试，暂且允许所有域访问
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
    """流式文件上传，并全自动触发异步认知链"""
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
    """千里眼：按工单号查询劳工进度"""
    task_result = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else "劳工仍在奋力解析中..."
    }

# 【新增兵器】：提取历史情报卷宗 (供前端列表展示)
@app.get("/api/v1/documents/")
async def get_all_documents(db: AsyncSession = Depends(get_db)):
    """获取数据库中所有的文档卷宗，按时间倒序排列"""
    # 统帅请看：此乃 SQLAlchemy 2.0 的新式阵法 select()
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