#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart, MIMEBase
from email.utils import parseaddr, formataddr
import smtplib


def _format_address(s):
    name, address = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), address))


def send_email(from_address, password, to_address, smtp_server):
    msg = MIMEText('<html><body><h1>Hello</h1>' + '<p>send by <a href="http://www.python.org">Python</a>...</p>' +
                   '</body></html>', 'html', 'utf-8')
    msg['From'] = _format_address('Python爱好者 <%s>' % from_address)
    msg['To'] = _format_address('管理员 <%s>' % to_address)
    msg['Subject'] = Header('来自SMTP的问候……', 'utf-8').encode()

    server = smtplib.SMTP(smtp_server, 25)
    server.set_debuglevel(1)
    server.login(from_address, password)
    server.sendmail(from_address, [to_address], msg.as_string())
    server.quit()


def send_email_with_attachment(from_address, password, to_address, smtp_server):
    # 邮件对象:
    msg = MIMEMultipart()
    msg['From'] = _format_address('Python爱好者 <%s>' % from_address)
    msg['To'] = _format_address('管理员 <%s>' % to_address)
    msg['Subject'] = Header('来自SMTP的问候……', 'utf-8').encode()

    # 邮件正文是MIMEText:
    msg.attach(MIMEText('<html><body><h1>Hello</h1>' + '<p><img src="cid:0"></p>' + '</body></html>', 'html', 'utf-8'))

    # 添加附件就是加上一个MIMEBase，从本地读取一个图片:
    with open('/Users/myzle/desktop/1.jpg', 'rb') as f:
        # 设置附件的MIME和文件名，这里是png类型:
        mime = MIMEBase('image', 'jpg', filename='1.jpg')
        # 加上必要的头信息:
        mime.add_header('Content-Disposition', 'attachment', filename='1.jpg')
        mime.add_header('Content-ID', '<0>')
        mime.add_header('X-Attachment-Id', '0')
        # 把附件的内容读进来:
        mime.set_payload(f.read())
        # 用Base64编码:
        encoders.encode_base64(mime)
        # 添加到MIMEMultipart:
        msg.attach(mime)

    server = smtplib.SMTP(smtp_server, 25)
    server.set_debuglevel(1)
    server.login(from_address, password)
    server.sendmail(from_address, [to_address], msg.as_string())
    server.quit()


if __name__ == '__main__':

    # send_email('myzle@yeah.net', 'Hb2:)sophie', 'myzle@yeah.net', 'smtp.yeah.net')
    send_email_with_attachment('myzle@yeah.net', 'Hb2:)sophie', 'myzle@yeah.net', 'smtp.yeah.net')
