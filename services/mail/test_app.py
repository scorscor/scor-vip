import smtplib
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

from app import create_app


class MailTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.transport = Mock()
        self.config = dict(DATABASE=str(Path(self.temp.name) / 'mail.db'),
                           API_KEYS={'scor': 'a' * 40, 'snap': 'b' * 40},
                           SMTP_USERNAME='sender@example.com', SMTP_PASSWORD='test',
                           DAILY_LIMIT=100, TESTING=True)
        self.app = create_app(self.config, self.transport)
        self.client = self.app.test_client()
        self.payload = dict(to='recipient@example.com', subject='测试', text='正文')
        self.headers = {'Authorization': 'Bearer ' + 'a' * 40, 'Idempotency-Key': 'contact:123'}

    def send(self, **kwargs):
        return self.client.post('/v1/emails', json=kwargs.get('payload', self.payload),
                                headers=kwargs.get('headers', self.headers))

    def test_auth_and_validation_do_not_send(self):
        self.assertEqual(self.send(headers={}).status_code, 401)
        for payload in [[], {**self.payload, 'to': 'bad\r\nBcc: victim@example.com'},
                        {**self.payload, 'from': 'arbitrary@example.com'},
                        {**self.payload, 'text': ''}]:
            self.assertEqual(self.send(payload=payload).status_code, 400)
        self.transport.assert_not_called()

    def test_success_repeat_and_conflict(self):
        first = self.send()
        self.assertEqual(first.json['status'], 'accepted')
        self.assertEqual(first.json, self.send().json)
        self.assertEqual(self.send(payload={**self.payload, 'subject': 'changed'}).status_code, 409)
        self.transport.assert_called_once()
        # Idempotency survives a new application process.
        client = create_app(self.config, self.transport).test_client()
        self.assertEqual(client.post('/v1/emails', json=self.payload, headers=self.headers).json, first.json)
        self.transport.assert_called_once()

    def test_status_is_scoped_to_caller(self):
        mail_id = self.send().json['id']
        path = '/v1/emails/' + mail_id
        self.assertEqual(self.client.get(path, headers=self.headers).status_code, 200)
        self.assertEqual(self.client.get(path, headers={'Authorization': 'Bearer ' + 'b' * 40}).status_code, 404)
        self.assertEqual(self.client.get(path).status_code, 401)

    def test_daily_limit_is_global(self):
        self.app.config['DAILY_LIMIT'] = 1
        self.send()
        response = self.send(headers={'Authorization': 'Bearer ' + 'b' * 40, 'Idempotency-Key': '2'})
        self.assertEqual(response.status_code, 429)
        self.transport.assert_called_once()

    def test_unknown_is_not_resent(self):
        self.transport.side_effect = TimeoutError('secret must not appear')
        response = self.send()
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json['status'], 'unknown')
        self.assertNotIn('secret', response.get_data(as_text=True))
        self.assertEqual(self.send().json, response.json)
        self.transport.assert_called_once()

    def test_rejection(self):
        self.transport.side_effect = smtplib.SMTPAuthenticationError(535, b'secret')
        self.assertEqual(self.send().json['status'], 'failed')

    def test_concurrent_repeat_sends_once(self):
        def post(_):
            with self.app.test_client() as client:
                return client.post('/v1/emails', json=self.payload, headers=self.headers)
        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(post, range(4)))
        self.assertEqual(len({r.json['id'] for r in responses}), 1)
        self.transport.assert_called_once()

    def test_rejects_insecure_configuration(self):
        with self.assertRaises(ValueError):
            create_app({**self.config, 'API_KEYS': {'scor': 'short'}})


if __name__ == '__main__':
    unittest.main()
