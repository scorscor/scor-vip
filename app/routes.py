from flask import Blueprint, jsonify, request, render_template
from app.models import db, Message, Project, Skill, Admin
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

main = Blueprint('main', __name__)


def admin_required(f):
    """管理员认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 简单的基本认证检查
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return jsonify({'error': '需要认证'}), 401

        admin = Admin.query.filter_by(username=auth.username).first()
        if not admin or not check_password_hash(admin.password_hash, auth.password):
            return jsonify({'error': '认证失败'}), 401

        return f(*args, **kwargs)
    return decorated_function


@main.route('/')
def index():
    """渲染主页"""
    return render_template('index.html')


@main.route('/api/messages', methods=['POST'])
def submit_message():
    """提交联系表单"""
    data = request.get_json()

    if not data or not data.get('name') or not data.get('contact') or not data.get('content'):
        return jsonify({'error': '请填写所有必填字段'}), 400

    contact_type = data.get('contact_type', 'email')
    if contact_type not in ['wechat', 'phone', 'email']:
        return jsonify({'error': '无效的联系方式类型'}), 400

    message = Message(
        name=data.get('name'),
        contact_type=contact_type,
        contact=data.get('contact'),
        content=data.get('content')
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({'message': '发送成功！我会尽快回复您。', 'success': True}), 201


@main.route('/api/messages', methods=['GET'])
@admin_required
def get_messages():
    """获取所有消息（管理用）"""
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return jsonify([msg.to_dict() for msg in messages])


@main.route('/api/messages/<int:id>', methods=['PUT'])
@admin_required
def mark_message_read(id):
    """标记消息为已读"""
    message = Message.query.get_or_404(id)
    message.is_read = True
    db.session.commit()
    return jsonify(message.to_dict())


@main.route('/api/messages/<int:id>', methods=['DELETE'])
@admin_required
def delete_message(id):
    """删除消息"""
    message = Message.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()
    return jsonify({'message': '删除成功', 'success': True})


@main.route('/api/projects', methods=['GET'])
def get_projects():
    """获取所有项目"""
    projects = Project.query.order_by(Project.order).all()
    return jsonify([proj.to_dict() for proj in projects])


@main.route('/api/projects', methods=['POST'])
@admin_required
def create_project():
    """创建新项目"""
    data = request.get_json()

    project = Project(
        title=data.get('title'),
        category=data.get('category'),
        description=data.get('description'),
        image_url=data.get('image_url'),
        project_url=data.get('project_url'),
        order=data.get('order', 0),
        is_offset=data.get('is_offset', False)
    )

    db.session.add(project)
    db.session.commit()

    return jsonify(project.to_dict()), 201


@main.route('/api/projects/<int:id>', methods=['PUT'])
@admin_required
def update_project(id):
    """更新项目"""
    project = Project.query.get_or_404(id)
    data = request.get_json()

    if data.get('title'):
        project.title = data.get('title')
    if data.get('category'):
        project.category = data.get('category')
    if data.get('description'):
        project.description = data.get('description')
    if data.get('image_url'):
        project.image_url = data.get('image_url')
    if data.get('project_url') is not None:
        project.project_url = data.get('project_url')
    if data.get('order') is not None:
        project.order = data.get('order')
    if data.get('is_offset') is not None:
        project.is_offset = data.get('is_offset')

    db.session.commit()
    return jsonify(project.to_dict())


@main.route('/api/projects/<int:id>', methods=['DELETE'])
@admin_required
def delete_project(id):
    """删除项目"""
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({'message': '删除成功', 'success': True})


@main.route('/api/skills', methods=['GET'])
def get_skills():
    """获取所有技能"""
    skills = Skill.query.order_by(Skill.category, Skill.order).all()
    return jsonify([skill.to_dict() for skill in skills])


@main.route('/api/skills', methods=['POST'])
@admin_required
def create_skill():
    """创建新技能"""
    data = request.get_json()

    skill = Skill(
        name=data.get('name'),
        category=data.get('category'),
        order=data.get('order', 0)
    )

    db.session.add(skill)
    db.session.commit()

    return jsonify(skill.to_dict()), 201


@main.route('/api/skills/<int:id>', methods=['DELETE'])
@admin_required
def delete_skill(id):
    """删除技能"""
    skill = Skill.query.get_or_404(id)
    db.session.delete(skill)
    db.session.commit()
    return jsonify({'message': '删除成功', 'success': True})


@main.route('/api/admin/register', methods=['POST'])
def register_admin():
    """注册管理员（仅首次使用）"""
    # 检查是否已有管理员
    if Admin.query.first():
        return jsonify({'error': '管理员已存在'}), 400

    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': '请提供用户名和密码'}), 400

    admin = Admin(
        username=data.get('username'),
        password_hash=generate_password_hash(data.get('password'))
    )

    db.session.add(admin)
    db.session.commit()

    return jsonify({'message': '注册成功', 'success': True}), 201


@main.route('/api/init-data', methods=['POST'])
def init_data():
    """初始化默认数据"""
    # 初始化项目
    projects_data = [
        {
            'title': 'Sphere Finance',
            'category': 'UI/UX 设计',
            'description': '面向新一代投资者的高保真财富管理平台',
            'image_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuD1htco-xwkCOvnY3etuwsb2W_4jZTqmLbQsWQu9EIMr8RhmScGoCSVe7_JxZbCS6G2wGJBO6sqsl5iHbQALLPmdxvkkW0KTZsc0VENs3TTFGh_h8pSWrCH4cTkd0ZqHC0zQ3Wh5Z0N9-n8PU4D2nXjtxts2-LNV9EahjPCIfSGbUz5ITp2nI4dATaDribM8cGX3C_8jWFDuh4VqZI873YcPw7p6ZysJz61lqE7-NS0UXnkP91eaoFdWP-uUeOGZcNZwHpia9mLXqqB',
            'order': 1,
            'is_offset': False
        },
        {
            'title': 'Neo-Lithe',
            'category': '品牌识别',
            'description': '可持续建筑集体的编辑优先品牌设计',
            'image_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuBWvwStc-jiYCs-QwPBE2kPVSO4M8DcAjEjJdpu0YxEYC3BHuhRw2Q6l3gk9GSgkqJlK3QINoQavdOOugMw48uboVuCmgMM5F_Q2AivD7zXtN-35-Y64AEuxL5oADT2ndOt_JzThf36VM-ibaMSGW2zxPWtkdd6Ke98qtZ-fFetVVMEgBIjV1t1nULNNEP1b9lC_l7YRl9wL-z-QouksrFSiP83xu-TZyVbRuJnabiH8oeShKQJ7tVSaoj5gCC24IPl9Yki660UU-qs',
            'order': 2,
            'is_offset': True
        },
        {
            'title': 'Gradient Logic',
            'category': '视觉艺术',
            'description': '探索生成艺术与用户界面动效的交汇点',
            'image_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuAfw0xTkpzFQuwMQntXmGlTCMrA85M26CfxAzCE37knbJoXKHkIIfVm59pabsbO9xteFsFcIYSXwaiSSgC2JFp9eM2WIoCaJzotIiC_2tlyvuZDaM7HBuW2nVoEBFKuALBu4WtGUx1CjKjXpdBjkU6gG8raOiju7usqnhtbkzRiVexdag5gevji6AKUwklpkQYDWa5U8438UMszrZXOXuspmZpPUDkZZqoSAQhOLFjCjXL-To5ZK26GKGriwRXiSuU9XWayRc7qZ4lL',
            'order': 3,
            'is_offset': False
        },
        {
            'title': 'Atelier Mono',
            'category': 'Web 开发',
            'description': '为创意机构打造的高性能作品集引擎',
            'image_url': 'https://lh3.googleusercontent.com/aida-public/AB6AXuDXhmDTf0_RbwMBwZ-NUFVd8eP3pnisUGVg_JBTKWCYgQh-evqQfENULvMi3NfOcmcvL5zmmALxhSfZb96KwC5L8DErWMl8owEc7LaeP4SVTZ6w_TWA7DQGklCDGnFGiN8tosbJGeROqp3w4g6QauH0FqhEE2nXm4JgESq4yjajrvXMRV6DwHaYoLSF3sXfC_9oiejLP2Lu5ENTmp97Su47Y3RQi_UzecJJ8wMa95S62q2ejEBcip5x90ZM3FrpClG6Oo_R7Xetjy6X',
            'order': 4,
            'is_offset': True
        }
    ]

    for proj_data in projects_data:
        existing = Project.query.filter_by(title=proj_data['title']).first()
        if not existing:
            project = Project(**proj_data)
            db.session.add(project)

    # 初始化技能
    skills_data = [
        {'name': 'Figma', 'category': 'design', 'order': 1},
        {'name': 'Principle', 'category': 'design', 'order': 2},
        {'name': 'Webflow', 'category': 'design', 'order': 3},
        {'name': 'Tailwind', 'category': 'development', 'order': 1},
        {'name': 'React', 'category': 'development', 'order': 2},
        {'name': 'GSAP', 'category': 'development', 'order': 3},
        {'name': '策略规划', 'category': 'soft', 'order': 1},
        {'name': '设计指导', 'category': 'soft', 'order': 2},
        {'name': '咨询顾问', 'category': 'soft', 'order': 3},
    ]

    for skill_data in skills_data:
        existing = Skill.query.filter_by(name=skill_data['name']).first()
        if not existing:
            skill = Skill(**skill_data)
            db.session.add(skill)

    db.session.commit()

    return jsonify({'message': '数据初始化完成', 'success': True})
