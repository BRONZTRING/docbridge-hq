from celery import Celery

# 初始化 Celery 实例
# 物理坐标：连接本地 Docker 刚刚召唤出的 Redis (端口 6379)
celery_app = Celery(
    "docbridge_worker",
    broker="redis://localhost:6379/0",  # 负责接收指令的信使
    backend="redis://localhost:6379/0"  # 负责存放结果的仓库
)

# 劳工大营法则配置
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # 设为统帅所在的莫斯科时区 (下诺夫哥罗德通用)
    timezone="Europe/Moscow",
    enable_utc=True,
)

# 测试探针任务：验证异步链路是否通畅
@celery_app.task(name="ping_task")
def ping_task(message: str):
    """
    此乃最基础的探针任务，由后台 Worker 执行，绝不阻塞主线程。
    """
    import time
    # 模拟耗时的思考过程（沉睡3秒）
    time.sleep(3)
    return f"【异步回应】统帅，劳工已收到指令: {message}，解析完毕！"

# 引入异步劳工的探针任务
from .worker import ping_task

@app.post("/api/v1/analyze/test_async")
async def trigger_async_analysis(document_name: str):
    """
    测试触发异步认知链 (此接口将瞬间返回，而后台劳工会默默执行任务)
    """
    # 召唤劳工，发放任务 (delay 是 Celery 的法咒，意为“异步发送，不必等它做完”)
    task = ping_task.delay(document_name)
    
    return {
        "status": "success",
        "message": "统帅，已将解析指令暗中发给异步劳工大营！主线程依然畅通无阻！",
        "task_id": task.id  # 返回这个工单号，日后可凭此号去 Redis 查进度
    }