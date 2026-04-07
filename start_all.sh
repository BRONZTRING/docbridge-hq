#!/bin/bash

echo "==========================================="
echo "  DocBridge AI 情报中枢 - 全维阵列启动程序 "
echo "==========================================="

# 【新增：自动化战前清场】
# || true 的意思是：就算没找到对应的进程也不报错，继续往下执行
echo "[0/3] 执行战前清场，斩杀潜伏的僵尸进程..."
pkill -9 -f uvicorn || true
pkill -9 -f celery || true
sleep 1

# 确保日志目录存在
mkdir -p logs

echo "[1/3] 激活 Python 隔离区..."
source venv/bin/activate

echo "[2/3] 点火 FastAPI 战略网关 (战报记录于 logs/gateway.log)..."
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/gateway.log 2>&1 &

echo "[3/3] 唤醒 Celery 异步劳工 (战报记录于 logs/worker.log)..."
# 【关键防线：--pool=solo 强制单兵作战，彻底规避异步时空错乱】
nohup celery -A app.worker worker --pool=solo --loglevel=info > logs/worker.log 2>&1 &

echo "[准备] 展开 Vue3 战术大屏 (战报记录于 logs/frontend.log)..."
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
cd ..

echo "==========================================="
echo "✅ 三路大军已就位！"
echo "🌐 前端雷达: http://localhost:5173"
echo "📖 查看劳工战报: 请新开一个终端执行 tail -f logs/worker.log "
echo "⚠️  按 Ctrl + C 收兵"
echo "==========================================="

# 保持脚本运行
wait