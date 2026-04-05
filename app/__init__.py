from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
import os

# 从 models 导入 db 实例，确保全局唯一
from app.models import db, Message, Project, Skill, Admin

migrate = Migrate()


def create_app():
    app = Flask(__name__,
                template_folder='../templates',
                static_folder='../static')

    # 项目根目录
    root_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
    instance_dir = os.path.join(root_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    # 数据库路径 - 使用绝对路径
    db_path = os.path.join(instance_dir, 'portfolio.db')

    # 配置
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

    # 始终使用绝对路径作为数据库 URI
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # 注册路由
    from app.routes import main
    app.register_blueprint(main)

    # 注册后台管理蓝图
    from app.admin import admin_bp, init_login_manager
    app.register_blueprint(admin_bp)
    init_login_manager(app)

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV', 'development') == 'development')
