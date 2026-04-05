from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
import os

from app.models import db, Message, Project, Skill, Admin

migrate = Migrate()


def _build_default_sqlite_uri(instance_dir):
    db_path = os.path.join(instance_dir, 'portfolio.db')
    return f"sqlite:///{db_path}"


def _normalize_database_uri(database_url, root_dir, instance_dir):
    database_url = (database_url or '').strip()
    if not database_url:
        return _build_default_sqlite_uri(instance_dir)

    if database_url.startswith('postgres://'):
        return database_url.replace('postgres://', 'postgresql://', 1)

    if database_url.startswith('mysql://'):
        return database_url.replace('mysql://', 'mysql+pymysql://', 1)

    if not database_url.startswith('sqlite:///') or database_url.startswith('sqlite:////'):
        return database_url

    sqlite_path = database_url.replace('sqlite:///', '', 1)
    if os.path.isabs(sqlite_path):
        return database_url

    return f"sqlite:///{os.path.join(root_dir, sqlite_path)}"


def create_app():
    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='../static'
    )

    root_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
    instance_dir = os.path.join(root_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = _normalize_database_uri(
        os.environ.get('DATABASE_URL'),
        root_dir,
        instance_dir
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
    }

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    from app.routes import main
    app.register_blueprint(main)

    from app.admin import admin_bp, init_login_manager
    app.register_blueprint(admin_bp)
    init_login_manager(app)

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV', 'development') == 'development')
