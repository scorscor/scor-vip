"""
应用启动入口
"""
from app import create_app, db
from app.models import Message, Project, Skill, Admin

if __name__ == '__main__':
    import os
    app = create_app()
    port = int(os.environ.get('PORT', 5003))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV', 'development') == 'development')
