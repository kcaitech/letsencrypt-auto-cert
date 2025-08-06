#!/bin/bash

# 创建计划任务 - 每月1号和15号的凌晨执行
echo "0 0 1,15 * * cd /app && python cert_manager.py >> /var/log/cert_renew.log 2>&1" > /etc/cron.d/cert-renew
chmod 0644 /etc/cron.d/cert-renew

# 启动 cron 服务
service cron start

# 首次运行证书申请
python cert_manager.py

# 保持容器运行
tail -f /var/log/cert_renew.log 