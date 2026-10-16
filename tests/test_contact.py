import os
import io
import json
import smtplib
import unittest
from unittest.mock import patch

from app import create_app
from app.models import db, Message


class ContactTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            'DATABASE_URL': 'sqlite://',
            'CONTACT_NOTIFY_EMAIL': '',
            'SMTP_HOST': '',
            'MAIL_API_URL': '',
            'MAIL_API_KEY': '',
        })
        self.env.start()
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.payload = dict(name='测试访客', contact_type='email', contact='visitor@example.com', content='私密咨询内容')

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()
        self.env.stop()

    def test_private_message_saved_without_mail_configuration(self):
        response = self.client.post('/api/messages', json=self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.query.one().content, self.payload['content'])
        self.assertEqual(self.client.get('/api/messages').status_code, 401)
        self.assertEqual(self.client.get('/admin/messages').status_code, 302)
        self.assertNotIn(self.payload['content'], self.client.get('/').get_data(as_text=True))

    def test_all_contact_types(self):
        for kind, value in [('wechat', 'visitor_wechat'), ('phone', '+86 13800138000')]:
            response = self.client.post('/api/messages', json={**self.payload, 'contact_type': kind, 'contact': value})
            self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.query.count(), 2)

    def test_invalid_inputs_not_saved(self):
        for payload in [[], {'name': 'test'}, {**self.payload, 'name': '   '},
                        {**self.payload, 'content': 'a' * 5001},
                        {**self.payload, 'contact': 'invalid-email'},
                        {**self.payload, 'contact': 'x@example.com\nBcc: other@example.com'},
                        {**self.payload, 'contact_type': 'other'},
                        {**self.payload, 'content': ['not text']}]:
            self.assertEqual(self.client.post('/api/messages', json=payload).status_code, 400)
        self.assertEqual(Message.query.count(), 0)

    @patch('app.mail.smtplib.SMTP')
    def test_notification_uses_configured_recipient(self, smtp_class):
        with patch.dict(os.environ, {'SMTP_HOST': 'smtp.example.com', 'SMTP_FROM': 'site@example.com',
                                    'CONTACT_NOTIFY_EMAIL': 'owner@example.com', 'SMTP_SECURITY': 'starttls',
                                    'SMTP_PORT': '587', 'SMTP_USERNAME': 'site', 'SMTP_PASSWORD': 'test-only'}):
            self.assertEqual(self.client.post('/api/messages', json=self.payload).status_code, 201)
        smtp = smtp_class.return_value.__enter__.return_value
        smtp.starttls.assert_called_once()
        smtp.login.assert_called_once_with('site', 'test-only')
        email = smtp.send_message.call_args.args[0]
        self.assertEqual(email['To'], 'owner@example.com')
        self.assertEqual(email['Reply-To'], 'visitor@example.com')
        self.assertIn(self.payload['content'], email.get_content())

    @patch('app.mail.smtplib.SMTP', side_effect=smtplib.SMTPException('unavailable'))
    def test_mail_failure_does_not_lose_message(self, smtp_class):
        with patch.dict(os.environ, {'SMTP_HOST': 'smtp.example.com', 'SMTP_FROM': 'site@example.com',
                                    'CONTACT_NOTIFY_EMAIL': 'owner@example.com', 'SMTP_SECURITY': 'starttls'}):
            response = self.client.post('/api/messages', json=self.payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.query.count(), 1)

    @patch('app.mail.urlopen')
    def test_shared_mail_api_uses_owner_recipient(self, urlopen):
        urlopen.return_value.__enter__.return_value = io.BytesIO(b'{"status":"accepted"}')
        with patch.dict(os.environ, {'MAIL_API_URL': 'https://mail.example.com',
                                    'MAIL_API_KEY': 'test-key',
                                    'CONTACT_NOTIFY_EMAIL': 'chenjiwei@moorechipsea.com'}):
            self.assertEqual(self.client.post('/api/messages', json=self.payload).status_code, 201)
        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(request.full_url, 'https://mail.example.com/v1/emails')
        self.assertEqual(payload['to'], 'chenjiwei@moorechipsea.com')
        self.assertEqual(payload['reply_to'], 'visitor@example.com')
        self.assertIn(self.payload['content'], payload['text'])
        self.assertEqual(request.get_header('Idempotency-key'), 'scor.vip:contact:1')
        self.assertEqual(request.get_header('Authorization'), 'Bearer test-key')

    @patch('app.mail.urlopen', side_effect=TimeoutError('unavailable'))
    @patch('app.mail.smtplib.SMTP')
    def test_api_timeout_preserves_message_without_smtp_resend(self, smtp, urlopen):
        with patch.dict(os.environ, {'MAIL_API_URL': 'https://mail.example.com',
                                    'MAIL_API_KEY': 'test-key',
                                    'CONTACT_NOTIFY_EMAIL': 'chenjiwei@moorechipsea.com'}):
            self.assertEqual(self.client.post('/api/messages', json=self.payload).status_code, 201)
        self.assertEqual(Message.query.count(), 1)
        smtp.assert_not_called()


if __name__ == '__main__':
    unittest.main()
