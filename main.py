import ssl
import json
import time
import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
import toml
from urllib3 import Retry
import smtplib  # 引入 smtplib 库
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

def init_session(proxy):
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    s.proxies = {} if proxy == "" else {"http": proxy, "https": proxy}
    return s


def send_mails(smtp_info, from_email, to, subject, content):
    try:
        # 创建 MIME 对象
        msg = MIMEMultipart()
        msg.attach(MIMEText(content, 'html', 'utf-8'))
        msg['From'] = Header(from_email)  # 发件人邮箱
        msg['To'] = Header(';'.join(to))  # 收件人邮箱列表
        msg['Subject'] = Header(subject, 'utf-8')  # 邮件主题

        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT')

        # 连接到 SMTP 服务器
        with smtplib.SMTP_SSL(smtp_info["server"], smtp_info["port"], context=context) as server:
            server.login(smtp_info["username"], smtp_info["password"])  # 登录认证
            server.sendmail(from_email, to, msg.as_string())  # 发送邮件
            print("发件成功")
            return True
    except Exception as e:
        print(f"发件失败，错误信息：{e}")
        return False


if __name__ == "__main__":
    try:
        config = toml.load("config.toml")
    except FileNotFoundError:
        print("配置文件config.toml不存在")
        exit()

    smtp_info = {
        "server": config["smtp"]["server"],
        "port": config["smtp"]["port"],
        "username": config["smtp"]["username"],
        "password": config["smtp"]["password"]
    }
    from_email = config["smtp"]["from_email"]

    # 其他设置读取，如邮件列表和邮件内容文件
    emails = []
    try:
        emails_file = open(config['setting']['email_list'], "r", encoding="utf-8")
    except FileNotFoundError:
        print("读取邮箱列表失败")
        exit()
    else:
        for line in emails_file.readlines():
            if line.strip() != "":
                emails.append(line.strip())
        emails_file.close()
        if len(emails) == 0:
            print("邮箱列表为空")
            exit()

    try:
        html_file = open(config["setting"]["email_content"], "r", encoding="utf-8")
    except FileNotFoundError:
        print("读取邮件内容失败")
        exit()
    else:
        html = html_file.read()
        html_file.close()

    if input("确认发送？(y/n)") != "y":
        exit()

    delay = (60 / config["setting"]["limit"]) if config["setting"]["limit"] != 0 else 0
    total_emails = len(emails)
    print(f"延迟{delay}秒发送，共{total_emails}封邮件")

    for i, address in enumerate(tqdm(emails, desc="发送邮件进度"), start=1):
        try:
            # 注意这里传入的参数改为了 smtp_info 而非 session 和其他 API 相关信息
            send_mails(smtp_info, from_email, [address], config["setting"]["subject"], html)
        except Exception as e:
            print(f"发件失败，错误信息：{e}")
        if i != total_emails:
            time.sleep(delay)
