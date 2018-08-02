#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
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


if __name__ == '__main__':

    send_email('myzle@yeah.net', '', 'myzle@yeah.net', 'smtp.yeah.net')
