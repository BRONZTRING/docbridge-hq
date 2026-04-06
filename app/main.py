import os
import aiofiles
from fastapi import FastAPI, UploadFile, File, HTTPException
from .worker import analyze_document_task

# 初始化 FastAPI 实例
app = FastAPI(
    title="DocBridge AI API",
    description="多语境商业情报中枢 - 异步接入网关",
    version="1.0.0"
)

# 划定物理存储隔离区
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root_gateway():
    """系统探针"""
    return {
        "status": "online",
        "system": "DocBridge AI Gateway",
        "location": "Nizhny Novgorod",
        "message": "统帅，认知管线网关在线！"
    }

@app.post("/api/v1/upload/")
async def upload_document(file: UploadFile = File(...)):
    """
    流式文件上传，并全自动触发异步认知链
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="未检测到文件名")

    # 确立文件最终落地的物理坐标
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # 1. 施展流式异步写入阵法
    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件写入失败: {str(e)}")

    # 2. 下达异步指令，唤醒劳工大营 (将物理路径传给 Celery)
    # delay 是 Celery 的法咒，意为“异步发送，不必等它做完”
    task = analyze_document_task.delay(file_path)

    return {
        "status": "success",
        "filename": file.filename,
        "saved_path": file_path,
        "task_id": task.id,
        "message": "统帅，文件落盘完毕。已向劳工大营下达认知解析指令！"
    }