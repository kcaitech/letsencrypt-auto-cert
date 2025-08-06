FROM python:3.9-slim

# 安装基础工具
RUN apt-get update && \
    apt-get install -y \
    certbot \
    openssl \
    cron \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 创建证书存储目录和日志目录
RUN mkdir -p /etc/letsencrypt && \
    touch /var/log/cert_renew.log

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 复制项目文件
COPY scripts/ .
# 设置脚本权限
RUN chmod +x auth-hook.sh cleanup-hook.sh entrypoint.sh
# 安装Python依赖
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 设置入口点
ENTRYPOINT ["/app/entrypoint.sh"]