"""Optional SMTP notifications for private contact messages."""
import os
import json
import smtplib
import ssl
from email.message import EmailMessage
from urllib.request import Request, urlopen

from flask import current_app


def notify_contact_message(message):
    host = os.environ.get('SMTP_HOST', '').strip()
    recipient = os.environ.get('CONTACT_NOTIFY_EMAIL', '').strip()
    sender = os.environ.get('SMTP_FROM', '').strip()
    api_url = os.environ.get('MAIL_API_URL', '').strip().rstrip('/')
    api_key = os.environ.get('MAIL_API_KEY', '').strip()
    if not recipient or not (api_url or (host and sender)):
        return False

    try:
        contact_label = {'email': '邮箱', 'phone': '电话', 'wechat': '微信'}[message.contact_type]
        subject = f'scor.vip 新留言 #{message.id}'
        text = (
            f'姓名：{message.name}\n{contact_label}：{message.contact}\n\n'
            f'{message.content}\n\n后台查看：https://scor.vip/admin/messages\n'
        )
        if api_url:
            if not api_key:
                raise ValueError('MAIL_API_KEY is required')
            payload = {'to': recipient, 'subject': subject, 'text': text}
            if message.contact_type == 'email':
                payload['reply_to'] = message.contact
            api_request = Request(api_url + '/v1/emails',
                                  data=json.dumps(payload).encode('utf-8'),
                                  headers={'Content-Type': 'application/json',
                                           'Authorization': 'Bearer ' + api_key,
                                           'Idempotency-Key': f'scor.vip:contact:{message.id}'},
                                  method='POST')
            with urlopen(api_request, timeout=20) as response:
                result = json.load(response)
            if result.get('status') != 'accepted':
                raise RuntimeError('Mail API did not confirm acceptance')
            return True
        security = os.environ.get('SMTP_SECURITY', 'starttls').lower()
        if security not in ('ssl', 'starttls'):
            raise ValueError('SMTP_SECURITY must be ssl or starttls')
        port = int(os.environ.get('SMTP_PORT') or (465 if security == 'ssl' else 587))
        email = EmailMessage()
        email['Subject'] = subject
        email['From'] = sender
        email['To'] = recipient
        if message.contact_type == 'email':
            email['Reply-To'] = message.contact
        email.set_content(text)
        context = ssl.create_default_context()
        if security == 'ssl':
            connection = smtplib.SMTP_SSL(host, port, timeout=8, context=context)
        else:
            connection = smtplib.SMTP(host, port, timeout=8)
        with connection as smtp:
            if security == 'starttls':
                smtp.starttls(context=context)
            username = os.environ.get('SMTP_USERNAME', '')
            if username:
                smtp.login(username, os.environ.get('SMTP_PASSWORD', ''))
            smtp.send_message(email)
        return True
    except Exception as exc:
        # Keep message contents and mail credentials out of application logs.
        current_app.logger.warning('Contact email failed for message %s (%s)', message.id, type(exc).__name__)
        return False
