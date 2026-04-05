FROM python:3.11-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建实例目录和数据卷
RUN mkdir -p instance
VOLUME ["/app/instance"]

# 暴露端口
EXPOSE 5003

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5003/')" || exit 1

# 启动命令
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5003", "--workers", "2", "--threads", "4", "app:create_app()"]
