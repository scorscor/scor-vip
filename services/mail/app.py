"""Shared HTTP mail gateway. SMTP acceptance is not inbox delivery."""
import hashlib
import hmac
import json
import os
import re
import smtplib
import sqlite3
import ssl
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, jsonify, request


def send_smtp(config, payload, message_id):
    mail = EmailMessage()
    mail['From'] = config['SMTP_FROM']
    mail['To'] = payload['to']
    mail['Subject'] = payload['subject']
    mail['Message-ID'] = message_id
    if payload.get('reply_to'):
        mail['Reply-To'] = payload['reply_to']
    mail.set_content(payload['text'])
    if payload.get('html'):
        mail.add_alternative(payload['html'], subtype='html')
    with smtplib.SMTP_SSL(config['SMTP_HOST'], int(config['SMTP_PORT']),
                          timeout=15, context=ssl.create_default_context()) as smtp:
        smtp.login(config['SMTP_USERNAME'], config['SMTP_PASSWORD'])
        smtp.send_message(mail)


def create_app(config=None, transport=None):
    app = Flask(__name__)
    app.config.update(
        MAX_CONTENT_LENGTH=131072,
        DATABASE=os.getenv('MAIL_DATABASE', 'data/mail.sqlite3'),
        API_KEYS=os.getenv('MAIL_API_KEYS', '{}'),
        DAILY_LIMIT=int(os.getenv('MAIL_DAILY_LIMIT', '100')),
        SMTP_HOST=os.getenv('SMTP_HOST', 'smtp.qcloudmail.com'),
        SMTP_PORT=os.getenv('SMTP_PORT', '465'),
        SMTP_USERNAME=os.getenv('SMTP_USERNAME', ''),
        SMTP_PASSWORD=os.getenv('SMTP_PASSWORD', ''),
        SMTP_FROM=os.getenv('SMTP_FROM', 'token@scor.vip'),
    )
    app.config.update(config or {})
    keys = app.config['API_KEYS']
    if isinstance(keys, str):
        keys = json.loads(keys)
    if not isinstance(keys, dict) or not keys or any(
        not isinstance(k, str) or not isinstance(v, str) or len(v) < 32
        for k, v in keys.items()
    ) or len(set(keys.values())) != len(keys):
        raise ValueError('MAIL_API_KEYS must map app names to unique keys of at least 32 characters')
    if not app.config['SMTP_USERNAME'] or not app.config['SMTP_PASSWORD']:
        raise ValueError('SMTP credentials are required')
    if app.config['DAILY_LIMIT'] < 1:
        raise ValueError('MAIL_DAILY_LIMIT must be positive')
    db_path = Path(app.config['DATABASE'])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect():
        db = sqlite3.connect(db_path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY, app TEXT NOT NULL, idem TEXT NOT NULL,
            fingerprint TEXT NOT NULL, status TEXT NOT NULL,
            created TEXT NOT NULL, error TEXT, UNIQUE(app, idem))''')
    deliver = transport or send_smtp

    def authorize():
        header = request.headers.get('Authorization', '')
        supplied = header[7:] if header.startswith('Bearer ') else ''
        for name, key in keys.items():
            if hmac.compare_digest(supplied.encode(), key.encode()):
                return name
        return None

    def result(row):
        return {'id': row['id'], 'status': row['status'],
                'created': row['created'], 'error': row['error']}

    @app.errorhandler(413)
    def too_large(_):
        return jsonify(error='request_too_large'), 413

    @app.get('/health')
    def health():
        with connect() as db:
            db.execute('SELECT 1')
        return jsonify(status='ok')

    @app.get('/v1/emails/<mail_id>')
    def status(mail_id):
        caller = authorize()
        if not caller:
            return jsonify(error='unauthorized'), 401
        with connect() as db:
            row = db.execute('SELECT * FROM messages WHERE id=? AND app=?',
                             (mail_id, caller)).fetchone()
        return (jsonify(result(row)), 200) if row else (jsonify(error='not_found'), 404)

    @app.post('/v1/emails')
    def send():
        caller = authorize()
        if not caller:
            return jsonify(error='unauthorized'), 401
        idem = request.headers.get('Idempotency-Key', '')
        if not re.fullmatch(r'[A-Za-z0-9._:-]{1,128}', idem):
            return jsonify(error='invalid_idempotency_key'), 400
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or set(payload) - {'to', 'subject', 'text', 'html', 'reply_to'}:
            return jsonify(error='invalid_payload'), 400
        for field, limit in [('to', 254), ('subject', 200), ('text', 50000),
                             ('html', 50000), ('reply_to', 254)]:
            value = payload.get(field, '')
            if not isinstance(value, str) or len(value) > limit:
                return jsonify(error='invalid_' + field), 400
            if field in ('to', 'subject', 'text') and not value.strip():
                return jsonify(error='invalid_' + field), 400
            if field in ('to', 'subject', 'reply_to') and any(c in value for c in '\r\n\x00'):
                return jsonify(error='invalid_' + field), 400
        for field in ('to', 'reply_to'):
            value = payload.get(field, '')
            if value and not re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}', value):
                return jsonify(error='invalid_' + field), 400
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat()
        mail_id = str(uuid.uuid4())
        with connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM messages WHERE app=? AND idem=?', (caller, idem)).fetchone()
            if old:
                if old['fingerprint'] != fingerprint:
                    return jsonify(error='idempotency_conflict'), 409
                return jsonify(result(old)), 200
            count = db.execute('SELECT COUNT(*) FROM messages WHERE created>=?', (now[:10],)).fetchone()[0]
            if count >= app.config['DAILY_LIMIT']:
                return jsonify(error='daily_limit_reached'), 429
            db.execute('INSERT INTO messages VALUES (?,?,?,?,?,?,?)',
                       (mail_id, caller, idem, fingerprint, 'sending', now, None))
        # Reserve before contacting SMTP. A crash or ambiguous network error must
        # never cause an automatic resend of a potentially accepted message.
        state, error, code = 'accepted', None, 200
        try:
            deliver(app.config, payload, '<' + mail_id + '@scor.vip>')
        except (smtplib.SMTPResponseException, smtplib.SMTPRecipientsRefused):
            state, error, code = 'failed', 'smtp_rejected', 502
        except Exception:
            state, error, code = 'unknown', 'smtp_result_unknown', 502
        with connect() as db:
            db.execute('UPDATE messages SET status=?, error=? WHERE id=?', (state, error, mail_id))
            row = db.execute('SELECT * FROM messages WHERE id=?', (mail_id,)).fetchone()
        return jsonify(result(row)), code

    return app
