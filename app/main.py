from fastapi import FastAPI

# 初始化 FastAPI 实例，定义项目元数据
app = FastAPI(
    title="DocBridge AI API",
    description="多语境商业情报中枢 - 异步接入网关",
    version="1.0.0"
)

# 定义根路由 (Root Router)
@app.get("/")
async def root_gateway():
    """
    系统探针：用于验证网关是否在线
    """
    return {
        "status": "online",
        "system": "DocBridge AI Gateway",
        "location": "Nizhny Novgorod",
        "message": "统帅，认知管线网关已在此坐标点火运行！"
    }