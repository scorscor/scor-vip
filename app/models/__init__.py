from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Message(db.Model):
    """联系表单消息模型"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_type = db.Column(db.String(20), nullable=False, default='email')  # wechat, phone, email
    contact = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_type': self.contact_type,
            'contact': self.contact,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_read': self.is_read
        }


class Project(db.Model):
    """项目作品模型"""
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    project_url = db.Column(db.String(500))  # 项目跳转 URL
    order = db.Column(db.Integer, default=0)
    is_offset = db.Column(db.Boolean, default=False)  # 是否错位显示
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'image_url': self.image_url,
            'project_url': self.project_url,
            'order': self.order,
            'is_offset': self.is_offset,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Skill(db.Model):
    """技能模型"""
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # design, development, soft
    order = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'order': self.order
        }


class Admin(db.Model):
    """管理员用户模型"""
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
