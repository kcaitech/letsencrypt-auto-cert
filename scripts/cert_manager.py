#!/usr/bin/env python3
import os
import logging
import subprocess
import smtplib
import yaml
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkcdn.request.v20180510.SetDomainServerCertificateRequest import SetDomainServerCertificateRequest
from aliyunsdkalidns.request.v20150109.AddDomainRecordRequest import AddDomainRecordRequest
from aliyunsdkalidns.request.v20150109.DeleteDomainRecordRequest import DeleteDomainRecordRequest
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CertManager:
    def __init__(self, config_path='config.yaml'):
        # 加载配置文件
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # 初始化阿里云客户端
        self.acs_client = AcsClient(
            self.config['aliyun']['access_key_id'],
            self.config['aliyun']['access_key_secret'],
            self.config['aliyun']['region']
        )
        
        # 设置域名
        self.domains = self.config['domains']['cert_domains']
        self.cdn_domains = self.config['domains'].get('cdn_domains', self.domains)
        
        # 设置邮件配置
        self.email_config = self.config['email']
        
        # 设置证书配置
        self.cert_config = self.config['cert']
        
        self.certbot_path = '/usr/bin/certbot'
        self.dns_records = {}

    def send_notification(self, subject, message):
        """发送邮件通知"""
        try:
            smtp_config = self.email_config['smtp']
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = smtp_config['user']
            msg['To'] = self.email_config['to']

            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                server.starttls()
                server.login(smtp_config['user'], smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"通知邮件发送成功: {subject}")
        except Exception as e:
            logger.error(f"发送通知邮件失败: {str(e)}")

    def check_cert_expiry(self):
        """检查证书是否即将过期（30天内）"""
        try:
            # 获取主域名列表
            main_domains = self._get_main_domains(self.domains)
            if not main_domains:
                logger.error("无法确定主域名，请检查域名列表")
                return True
                
            # 只检查主域名的证书
            for domain in main_domains:
                cert_path = f"/etc/letsencrypt/live/{domain}/fullchain.pem"
                if not os.path.exists(cert_path):
                    return True
                
                result = subprocess.run(
                    ['openssl', 'x509', '-enddate', '-noout', '-in', cert_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    logger.error(f"检查证书过期时间失败: {result.stderr}")
                    return True
                
                # 解析证书过期时间
                expiry_str = result.stdout.split('=')[1].strip()
                expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                
                # 如果证书在30天内过期，需要更新
                if expiry_date - datetime.now() < timedelta(days=30):
                    logger.info(f"域名 {domain} 的证书将在30天内过期，需要更新")
                    return True
                
            return False
        except Exception as e:
            logger.error(f"检查证书过期时间出错: {str(e)}")
            return True

    def add_dns_record(self, domain, record_type, record_value):
        """添加DNS记录"""
        try:
            main_domain = self._get_main_domain(domain)
            subdomain = domain[:-len(main_domain)-1] if domain.endswith(main_domain) else domain
            
            request = AddDomainRecordRequest()
            request.set_accept_format('json')
            request.set_DomainName(main_domain)
            request.set_RR(f"_acme-challenge.{subdomain}" if subdomain else "_acme-challenge")
            request.set_Type(record_type)
            request.set_Value(record_value)
            
            response = self.acs_client.do_action_with_exception(request)
            record_id = response.get('RecordId')
            self.dns_records[domain] = record_id
            logger.info(f"已添加DNS记录: {domain}")
            
            # 等待DNS记录生效
            time.sleep(self.cert_config['dns_wait_time'])
            return True
        except Exception as e:
            logger.error(f"添加DNS记录失败: {str(e)}")
            return False

    def remove_dns_record(self, domain):
        """删除DNS记录"""
        try:
            record_id = self.dns_records.get(domain)
            if not record_id:
                return True
                
            request = DeleteDomainRecordRequest()
            request.set_accept_format('json')
            request.set_RecordId(record_id)
            
            self.acs_client.do_action_with_exception(request)
            del self.dns_records[domain]
            logger.info(f"已删除DNS记录: {domain}")
            return True
        except Exception as e:
            logger.error(f"删除DNS记录失败: {str(e)}")
            return False

    def get_certificate(self):
        """获取或更新证书"""
        try:
            # 检查证书是否需要更新
            if not self.check_cert_expiry():
                logger.info("证书未过期，无需更新")
                return False

            # 按主域名分组申请证书
            main_domains = self._get_main_domains(self.domains)
            for main_domain in main_domains:
                related_domains = [d for d in self.domains if d == main_domain or d.endswith('.' + main_domain)]
                
                cmd = [
                    self.certbot_path,
                    'certonly',
                    '--manual',
                    '--preferred-challenges', 'dns',
                    '--manual-auth-hook', '/app/auth-hook.sh',
                    '--manual-cleanup-hook', '/app/cleanup-hook.sh',
                    '--email', self.email_config['to'],
                    '--agree-tos',
                    '--no-eff-email',
                ]
                
                # 添加相关域名
                for domain in related_domains:
                    cmd.extend(['-d', domain])
                
                logger.info(f"正在为主域名 {main_domain} 申请证书，包含域名: {', '.join(related_domains)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    error_msg = f"主域名 {main_domain} 证书获取失败: {result.stderr}"
                    logger.error(error_msg)
                    self.send_notification(
                        "SSL证书更新失败",
                        f"域名: {', '.join(related_domains)}\n\n错误信息:\n{error_msg}"
                    )
                    return False
                else:
                    logger.info(f"主域名 {main_domain} 证书获取成功")
            
            return True
        except Exception as e:
            error_msg = f"证书获取过程出错: {str(e)}"
            logger.error(error_msg)
            self.send_notification(
                "SSL证书更新出错",
                f"域名: {', '.join(self.domains)}\n\n错误信息:\n{error_msg}"
            )
            return False

    def _get_main_domain(self, domain):
        """获取主域名"""
        parts = domain.split('.')
        if len(parts) > 2:
            return '.'.join(parts[-2:])
        return domain

    def _get_main_domains(self, domains):
        """根据域名列表确定主域名"""
        if not domains:
            return []
            
        # 按域名长度排序
        sorted_domains = sorted(domains, key=len)
        main_domains = []
        
        for domain in sorted_domains:
            for main_domain in main_domains:
                if domain.endswith('.' + main_domain):
                    break
            else:
                main_domains.append(domain)

        return main_domains

    def _get_cert_path(self, domain):
        """获取证书路径，处理多域名证书的情况"""
        # 首先检查域名自己的目录
        direct_path = f"/etc/letsencrypt/live/{domain}"
        if os.path.exists(direct_path):
            return direct_path
            
        # 如果不存在，查找可能的主域名目录
        main_domains = self._get_main_domains(self.domains)
        for main_domain in main_domains:
            if domain == main_domain or domain.endswith('.' + main_domain):
                path = f"/etc/letsencrypt/live/{main_domain}"
                if os.path.exists(path):
                    return path
        
        return None

    def update_cdn_certificate(self):
        """更新CDN证书"""
        success = True
        errors = []
        
        if not self.cdn_domains:
            logger.info("未配置CDN域名，跳过CDN证书更新")
            return True
            
        main_domains = self._get_main_domains(self.domains)
        if not main_domains:
            error_msg = "无法确定主域名，请检查域名列表"
            logger.error(error_msg)
            errors.append(error_msg)
            return False
            
        logger.info(f"使用以下主域名更新 CDN: {', '.join(main_domains)}")
            
        # 创建域名到主域名的映射
        domain_to_main = {}
        for cdn_domain in self.cdn_domains:
            for main_domain in main_domains:
                if cdn_domain == main_domain or cdn_domain.endswith('.' + main_domain):
                    domain_to_main[cdn_domain] = main_domain
                    break
            else:
                error_msg = f"CDN域名 {cdn_domain} 不在证书覆盖范围内"
                logger.error(error_msg)
                errors.append(error_msg)
                success = False

        # 更新每个CDN域名的证书
        for cdn_domain in self.cdn_domains:
            try:
                cert_path = self._get_cert_path(cdn_domain)
                if not cert_path:
                    error_msg = f"域名 {cdn_domain} 的证书文件不存在"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
                
                cert_file = f"{cert_path}/fullchain.pem"
                key_file = f"{cert_path}/privkey.pem"
                
                if not os.path.exists(cert_file) or not os.path.exists(key_file):
                    error_msg = f"域名 {cdn_domain} 的证书文件不完整"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
                    
                with open(cert_file, 'r') as f:
                    cert_content = f.read()
                with open(key_file, 'r') as f:
                    key_content = f.read()

                try:
                    request = SetDomainServerCertificateRequest()
                    request.set_accept_format('json')
                    request.set_DomainName(cdn_domain)
                    request.set_CertType('upload')
                    request.set_ServerCertificateStatus('on')
                    request.set_ServerCertificate(cert_content)
                    request.set_PrivateKey(key_content)

                    response = self.acs_client.do_action_with_exception(request)
                    logger.info(f"域名 {cdn_domain} CDN证书更新成功: {response}")
                except (ClientException, ServerException) as e:
                    error_msg = f"域名 {cdn_domain} CDN证书更新失败: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    success = False
                except Exception as e:
                    error_msg = f"域名 {cdn_domain} CDN证书更新过程出错: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    success = False
            except Exception as e:
                error_msg = f"读取证书文件失败: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                success = False
        
        if not success:
            self.send_notification(
                "CDN证书更新失败",
                f"域名: {', '.join(self.cdn_domains)}\n\n错误信息:\n" + "\n".join(errors)
            )
                
        return success

    def run(self):
        """运行证书管理流程"""
        try:
            if self.get_certificate():
                self.update_cdn_certificate()
        except Exception as e:
            error_msg = f"运行过程出错: {str(e)}"
            logger.error(error_msg)
            self.send_notification(
                "证书管理流程出错",
                f"域名: {', '.join(self.domains)}\n\n错误信息:\n{error_msg}"
            )
            exit(1)

if __name__ == "__main__":
    cert_manager = CertManager()
    cert_manager.run() 