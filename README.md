🌐 DocBridge AI 情报中枢 (v1.0 MVP)

核心定位：中、日、俄、英四语商业与国际关系情报中枢
战术目标：利用数学底盘与国关视野，将复杂的法律、金融、学术卷宗转化为可行动的决策指令，解决跨国协作中的合规与信任鸿沟。

本项目是一个基于大语言模型（LLM）与检索增强生成（RAG）技术构建的跨语言智能文档分析平台，专为跨境贸易合同、法律卷宗及外语长文本提供自动化解析与精准问答服务。

【核心功能展示】

多模态与多语种解析：支持中、俄、英、日等多语种的PDF、Word及图片扫描件摄入。集成底层OCR引擎，无惧复杂跨国合同排版，精准提取西里尔字母及多语种混合文本。

智能风控与摘要生成：利用大模型对长文本进行跨条款逻辑推理，自动生成核心简报，并精准提取潜在的法律风险与违约陷阱。

全局向量检索 (RAG)：基于 pgvector 向量数据库，支持用户通过自然语言进行跨文档、跨语种的语义级对话。大模型回答可精准溯源至原文件的物理切片（来源定位）。

高并发异步架构：引入 Celery + Redis 处理耗时的文件解析与向量化任务，配合 WebSocket 实现前端日志的实时双向通讯与状态映射。

【我在本项目中的角色与贡献】
我作为独立全栈开发者与AI应用工程师，主导了从底层架构设计到前后端开发的全流程：

算法优化：结合自身的数学与应用数学专业背景，摒弃暴力的文本截断，设计了基于自然语义与标点符号的切分规则（Semantic Chunking），显著提升了高维向量余弦相似度检索的召回准确率。

跨语种NLP调优：依托自身的语文学硕士背景及多年俄语、日语（N1水平）的翻译与本地化经验，针对俄语黏着语特性与西里尔语系的复杂实体（如税务号、俄罗斯企业全称）进行了深度处理，解决了传统正则表达式在多语种隐私脱敏与信息提取中的盲区。

【技术栈检索关键词】
Vue3, FastAPI, Celery, Redis, PostgreSQL, pgvector, Docker容器化, RAG架构, LLM大语言模型接入, OCR文本识别, 异步队列, 多语种NLP处理, 俄文/日文文档解析, 全栈开发。

⚔️ 核心阵法与兵器谱 (Tech Stack)

1. 混合双擎认知管线 (AI Core)

文本主炮 (LLM)：SiliconFlow Qwen2.5-7B-Instruct (云端无限火力，精通四语种推理)

高维折叠枪 (Embedding)：paraphrase-multilingual-mpnet-base-v2 (1.1GB 本地完全私有化部署，768维数学坐标转换)

2. 战术大本营 (Backend)

战略网关：FastAPI (全异步非阻塞 API)

实时雷达：WebSocket (底层 tail -f 实时映射劳工战报至前端)

异步劳工营：Celery + Redis (开启 --pool=solo 单兵护甲，防御 PyTorch 时空错乱)

高维记忆矩阵：PostgreSQL + pgvector (768维向量相似度检索) + SQLAlchemy (异步 NullPool 用完即毁连接池)

3. 全息战术大屏 (Frontend)

框架：Vue 3 + Vite + Element Plus

特色组件：多页签 RAG 审讯弹窗、右下角悬浮 WebSocket 实时终端日志视窗。

🚀 启动大阵 (Quick Start)

1. 环境整备

# 建立 Python 隔离区
python3 -m venv venv
source venv/bin/activate

# 补充弹药
pip install -r requirements.txt


2. 隐秘兵符配置

在根目录创建 .env 文件，注入硅基流动 API 密钥（该文件已被 gitignore 保护）：

SILICONFLOW_API_KEY=sk-your-api-key-here


3. 物理清洗与建库

# 拉起 Postgres 与 Redis 容器
docker-compose up -d

# 执行魔法阵，构建 768 维向量表 (自动加载 vector 扩展)
alembic upgrade head


4. 一键点火

# 赋予执行权限并启动
chmod +x start_all.sh
./start_all.sh


前端大屏将自动在 http://localhost:5173 展开。

🗺️ 战略路线图 (Roadmap)

[x] Week 1: 基础架构闭环 (FastAPI 网关、PostgreSQL+pgvector、Redis 队列、Vue3 基础大屏)

[x] Week 1.5: 混合双擎改造 (突破谷歌封锁，实装硅基流动 Qwen2.5 与本地 MPNet 768维模型)

[x] Week 2: 核心认知管线 (异步 PDF 穿透、RAG 向量检索、全局 WebSocket 实时战报视窗)

[ ] Week 2.5: 多模态深水区 (图片与表格解析增强、多轮对话记忆矩阵)

[ ] Week 3: 合规与部署 (正则安全脱敏拦截网、Docker 终极全容器化、云端服务器实装)

“在数据洪流中，建立秩序；在语言壁垒前，架设桥梁。”
