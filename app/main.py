import os
import aiofiles
from fastapi import FastAPI, UploadFile, File, HTTPException

# 初始化 FastAPI 实例
app = FastAPI(
    title="DocBridge AI API",
    description="多语境商业情报中枢 - 异步接入网关",
    version="1.0.0"
)

# 划定物理存储隔离区（在根目录下自动创建 uploads 文件夹）
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
    流式文件上传接口 (异步解耦，内存保护)
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="未检测到文件名")

    # 确立文件最终落地的物理坐标
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # 施展流式异步写入阵法
    try:
        # 'wb' 意为以二进制写入模式打开
        async with aiofiles.open(file_path, 'wb') as out_file:
            # 每次仅将 1MB (1024*1024 bytes) 吸入内存，写完再吸，防线坚不可摧！
            while content := await file.read(1024 * 1024):
                await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件写入失败: {str(e)}")

    return {
        "status": "success",
        "filename": file.filename,
        "saved_path": file_path,
        "message": "统帅，文件流式接收完毕，内存防线稳固！"
    }