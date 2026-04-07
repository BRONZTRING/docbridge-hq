# 选用极简且稳定的 Python 3.12 镜像作为底盘
FROM python:3.12-slim-bookworm

# 设置不生成 pyc 文件，强制无缓冲输出日志（方便我们在终端看战报）
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 【重型军火装配】：在 Linux 容器内安装 Tesseract 视觉引擎及中俄英三语包，安装 Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-chi-sim \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# 设定容器内的工作大本营坐标
WORKDIR /app

# 先把弹药清单（requirements.txt）送进去，并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 将项目里的所有后端代码运入集装箱
COPY . .

# 预先挖好存放物理卷宗和战报的地下掩体
RUN mkdir -p uploads logs