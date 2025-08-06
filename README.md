# Let's Encrypt DNS Verification Certificate Application

For automatic Let's Encrypt certificate application and renewal when using Alibaba Cloud CDN

## Features

- Apply for Let's Encrypt certificates using DNS verification method
- Support wildcard domain certificate applications
- Automatically update Alibaba Cloud CDN certificate configuration
- Email notification functionality
- Scheduled certificate checking and renewal
- Docker containerized deployment

## Configuration

### 1. Configuration File Structure

The project uses `config.yaml` (mounted at `/app/config.yaml` in container) as the configuration file, containing the following main configuration items:

```yaml
# Alibaba Cloud configuration
aliyun:
  access_key_id: "your_access_key_id"
  access_key_secret: "your_access_key_secret"
  region: "cn-hangzhou"

# Domain configuration
domains:
  cert_domains:
    - "example.com"
    - "*.example.com"
  cdn_domains:
    - "www.example.com"
    - "api.example.com"

# Email notification configuration
email:
  to: "your-email@example.com"
  smtp:
    host: "smtp.gmail.com"
    port: 587
    user: "your-smtp-user@gmail.com"
    password: "your-smtp-password"

# Certificate configuration
cert:
  check_interval: 15
  dns_wait_time: 20
```

### 2. Detailed Configuration

#### Alibaba Cloud Configuration (aliyun)
- `access_key_id`: Alibaba Cloud Access Key ID
- `access_key_secret`: Alibaba Cloud Access Key Secret
- `region`: Alibaba Cloud region, such as `cn-hangzhou`

#### Domain Configuration (domains)
- `cert_domains`: List of domains for certificate application
  - Supports wildcard domains, such as `*.example.com`
  - Supports multiple domains
- `cdn_domains`: CDN domain list (optional)
  - If not set, will use `cert_domains` as CDN domains
  - Used for automatically updating Alibaba Cloud CDN certificate configuration

#### Email Notification Configuration (email)
- `to`: Email address to receive notifications
- `smtp`: SMTP server configuration
  - `host`: SMTP server address
  - `port`: SMTP port
  - `user`: SMTP username
  - `password`: SMTP password

#### Certificate Configuration (cert)
- `check_interval`: Interval in days for checking certificate updates (default 15 days)
- `dns_wait_time`: DNS record propagation wait time (seconds, default 20 seconds)

## Important Notes

1. **Alibaba Cloud Permissions**: Ensure AccessKey has DNS resolution and CDN management permissions
2. **Domain Ownership**: Ensure domains are configured in Alibaba Cloud DNS resolution service
3. **SMTP Configuration**: If using Gmail, you need to use an app-specific password
4. **Certificate Limits**: Let's Encrypt has rate limits for certificate applications, recommend setting reasonable check intervals
5. **DNS Propagation**: Different DNS providers have different propagation times, may need to adjust `dns_wait_time`

## Troubleshooting

### Common Issues

1. **DNS Verification Failed**
   - Check Alibaba Cloud AccessKey permissions
   - Confirm domains are configured in Alibaba Cloud DNS resolution
   - Increase `dns_wait_time` value

2. **Email Sending Failed**
   - Check SMTP configuration
   - Confirm email password is correct
   - Check firewall settings

3. **CDN Update Failed**
   - Check CDN domain configuration
   - Confirm AccessKey has CDN management permissions

## License

MIT License
