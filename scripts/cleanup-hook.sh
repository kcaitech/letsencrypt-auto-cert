#!/bin/bash

# 从环境变量获取域名
DOMAIN="$CERTBOT_DOMAIN"

# 调用Python脚本删除DNS记录
python3 - << EOF
from cert_manager import CertManager

cert_manager = CertManager()
cert_manager.remove_dns_record("$DOMAIN")
EOF 