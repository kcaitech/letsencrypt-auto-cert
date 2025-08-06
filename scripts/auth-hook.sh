#!/bin/bash

# 从环境变量获取域名和验证值
DOMAIN="$CERTBOT_DOMAIN"
VALIDATION_VALUE="$CERTBOT_VALIDATION"

# 调用Python脚本添加DNS记录
python3 - << EOF
from cert_manager import CertManager

cert_manager = CertManager()
cert_manager.add_dns_record("$DOMAIN", "TXT", "$VALIDATION_VALUE")
EOF 