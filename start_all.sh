#!/bin/bash

# 全栈游民的一键启停阵法
# 颜色配置
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}  DocBridge AI 情报中枢 - 全维阵列启动程序 ${NC}"
echo -e "${GREEN}===========================================${NC}"

# 1. 唤醒虚拟环境
echo -e "${GREEN}[1/3] 激活 Python 隔离区...${NC}"
source venv/bin/activate

# 2. 点火 FastAPI 网关 (后台运行)
echo -e "${GREEN}[2/3] 点火 FastAPI 战略网关...${NC}"
uvicorn app.main:app --reload --port 8000 > /dev/null 2>&1 &
UVICORN_PID=$!

# 3. 点火 Celery 劳工 (后台运行)
echo -e "${GREEN}[3/3] 唤醒 Celery 异步劳工...${NC}"
celery -A app.worker.celery_app worker --loglevel=info > /dev/null 2>&1 &
CELERY_PID=$!

# 4. 点火 Vue3 前端 (后台运行)
echo -e "${GREEN}[准备] 展开 Vue3 战术大屏...${NC}"
cd frontend && npm run dev > /dev/null 2>&1 &
VITE_PID=$!

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}✅ 统帅，三路大军已全部在后台潜行就绪！${NC}"
echo -e "${GREEN}🌐 前端雷达: http://localhost:5173${NC}"
echo -e "${GREEN}🛠️ 后端网关: http://localhost:8000/docs${NC}"
echo -e "${RED}⚠️  若要收兵，请在此窗口按下 Ctrl + C ${NC}"
echo -e "${GREEN}===========================================${NC}"

# 捕获 Ctrl+C 信号 (SIGINT)，一旦按下，立刻将三个后台进程全部斩杀
trap "echo -e '\n${RED}>>> 统帅下令收兵！正在关闭网关、劳工与雷达...${NC}'; kill $UVICORN_PID $CELERY_PID $VITE_PID; exit" SIGINT SIGTERM

# 挂起当前脚本，使其不退出，直到统帅按下 Ctrl+C
wait