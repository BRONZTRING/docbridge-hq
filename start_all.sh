#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}  DocBridge AI 情报中枢 - 全维阵列启动程序 ${NC}"
echo -e "${GREEN}===========================================${NC}"

# 建立战报存放营帐
mkdir -p logs

echo -e "${GREEN}[1/3] 激活 Python 隔离区...${NC}"
source venv/bin/activate

echo -e "${GREEN}[2/3] 点火 FastAPI 战略网关 (战报记录于 logs/gateway.log)...${NC}"
uvicorn app.main:app --reload --port 8000 > logs/gateway.log 2>&1 &
UVICORN_PID=$!

echo -e "${GREEN}[3/3] 唤醒 Celery 异步劳工 (战报记录于 logs/worker.log)...${NC}"
celery -A app.worker.celery_app worker --loglevel=info > logs/worker.log 2>&1 &
CELERY_PID=$!

echo -e "${GREEN}[准备] 展开 Vue3 战术大屏 (战报记录于 logs/frontend.log)...${NC}"
cd frontend && npm run dev > ../logs/frontend.log 2>&1 &
VITE_PID=$!
cd ..

echo -e "${GREEN}===========================================${NC}"
echo -e "${GREEN}✅ 三路大军已就位！${NC}"
echo -e "${GREEN}🌐 前端雷达: http://localhost:5173${NC}"
echo -e "${GREEN}📖 查看劳工战报: 请新开一个终端执行 ${RED}tail -f logs/worker.log${GREEN} ${NC}"
echo -e "${RED}⚠️  按 Ctrl + C 收兵 ${NC}"
echo -e "${GREEN}===========================================${NC}"

trap "echo -e '\n${RED}>>> 统帅下令收兵！正在清理战场...${NC}'; kill $UVICORN_PID $CELERY_PID $VITE_PID; exit" SIGINT SIGTERM
wait