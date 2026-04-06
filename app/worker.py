import asyncio
import pdfplumber
from celery import Celery

from .ai_core import build_summary_chain, build_risk_chain
from .database import AsyncSessionLocal
from .models import Document, AnalysisResult

celery_app = Celery(
    "docbridge_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=True,
)

# 【三才阵归位 2】：专为劳工定制的数据库写入法阵
async def update_doc_status(document_id: int, status: str, summary: str = None, risk_points: str = None):
    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, document_id)
        if doc:
            doc.status = status
            if status == "completed":
                # 将情报存入 AnalysisResult 表
                result = AnalysisResult(
                    document_id=document_id,
                    summary=summary,
                    # models.py 中 risk_points 是 JSON 类型，所以包一层字典
                    risk_points={"raw_report": risk_points}
                )
                session.add(result)
            await session.commit()

@celery_app.task(name="analyze_document_task")
# 【核心升级】：接收 document_id
def analyze_document_task(file_path: str, document_id: int):
    text_content = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content += extracted + "\n"
    except Exception as e:
        asyncio.run(update_doc_status(document_id, "failed"))
        return {"status": "error", "message": f"物理穿透 PDF 失败: {str(e)}"}

    if not text_content.strip():
        asyncio.run(update_doc_status(document_id, "failed"))
        return {"status": "error", "message": "未能提取到有效文本"}

    text_chunk = text_content[:3000]

    try:
        summary_chain = build_summary_chain()
        risk_chain = build_risk_chain()

        summary_res = summary_chain.invoke({"text": text_chunk})
        risk_res = risk_chain.invoke({"text": text_chunk})

        # 【大捷落盘】：如果真密钥跑通了，将战果写入 PostgreSQL
        asyncio.run(update_doc_status(document_id, "completed", summary_res, risk_res))

        return {"status": "success", "summary": summary_res, "risk_points": risk_res}
        
    except Exception as e:
        # 假密钥必定会走到这里，我们将数据库状态标记为 failed_auth
        asyncio.run(update_doc_status(document_id, "failed_auth"))
        return {"status": "error", "message": f"认知链阻断 (等待真实密钥): {str(e)}"}