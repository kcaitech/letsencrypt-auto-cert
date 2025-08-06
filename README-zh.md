# Let's Encrypt DNS验证证书申请

用于使用阿里云CDN时的Let's Encrypt证书自动申请及更新

## 功能特性

- 使用DNS验证方式申请Let's Encrypt证书
- 支持通配符域名证书申请
- 自动更新阿里云CDN证书配置
- 邮件通知功能
- 定时检查和更新证书
- Docker容器化部署

## 配置说明

### 1. 配置文件结构

项目使用 `config.yaml`（挂载到容器内的 `/app/config.yaml`） 作为配置文件，包含以下主要配置项：

```yaml
# 阿里云配置
aliyun:
  access_key_id: "your_access_key_id"
  access_key_secret: "your_access_key_secret"
  region: "cn-hangzhou"

# 域名配置
domains:
  cert_domains:
    - "example.com"
    - "*.example.com"
  cdn_domains:
    - "www.example.com"
    - "api.example.com"

# 邮件通知配置
email:
  to: "your-email@example.com"
  smtp:
    host: "smtp.gmail.com"
    port: 587
    user: "your-smtp-user@gmail.com"
    password: "your-smtp-password"

# 证书配置
cert:
  check_interval: 15
  dns_wait_time: 20
```

### 2. 详细配置说明

#### 阿里云配置 (aliyun)
- `access_key_id`: 阿里云访问密钥ID
- `access_key_secret`: 阿里云访问密钥Secret
- `region`: 阿里云地域，如 `cn-hangzhou`

#### 域名配置 (domains)
- `cert_domains`: 需要申请证书的域名列表
  - 支持通配符域名，如 `*.example.com`
  - 支持多个域名
- `cdn_domains`: CDN域名列表（可选）
  - 如果不设置，将使用 `cert_domains` 作为CDN域名
  - 用于自动更新阿里云CDN的证书配置

#### 邮件通知配置 (email)
- `to`: 接收通知的邮箱地址
- `smtp`: SMTP服务器配置
  - `host`: SMTP服务器地址
  - `port`: SMTP端口
  - `user`: SMTP用户名
  - `password`: SMTP密码

#### 证书配置 (cert)
- `check_interval`: 检查证书更新的间隔天数（默认15天）
- `dns_wait_time`: DNS记录生效等待时间（秒，默认20秒）

## 注意事项

1. **阿里云权限**: 确保AccessKey具有DNS解析和CDN管理权限
2. **域名所有权**: 确保域名已在阿里云DNS解析服务中配置
3. **SMTP配置**: 如果使用Gmail，需要使用应用专用密码
4. **证书限制**: Let's Encrypt对证书申请有频率限制，建议设置合理的检查间隔
5. **DNS传播**: 不同DNS服务商的传播时间不同，可能需要调整 `dns_wait_time`

## 故障排除

### 常见问题

1. **DNS验证失败**
   - 检查阿里云AccessKey权限
   - 确认域名已在阿里云DNS解析
   - 增加 `dns_wait_time` 值

2. **邮件发送失败**
   - 检查SMTP配置
   - 确认邮箱密码正确
   - 检查防火墙设置

3. **CDN更新失败**
   - 检查CDN域名配置
   - 确认AccessKey具有CDN管理权限

## 许可证

MIT License
