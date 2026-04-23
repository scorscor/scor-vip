from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from app.models import db, Message, Project, Skill, Admin
from app.passwords import check_password, encode_password
from app.utils import process_uploaded_image
import os

# 创建后台管理蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 配置密钥
admin_bp.app = None

# Flask-Login 配置
login_manager = LoginManager()
login_manager.login_view = 'admin.login'
login_manager.login_message = '请先登录'


class AdminUser(UserMixin, Admin):
    """用于 Flask-Login 的用户类"""
    pass


def init_login_manager(app):
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        admin = Admin.query.get(int(user_id))
        if admin:
            user = AdminUser()
            user.id = admin.id
            user.username = admin.username
            return user
        return None


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember')

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password(admin.password_hash, password):
            user = AdminUser()
            user.id = admin.id
            user.username = admin.username
            login_user(user, remember=remember)
            session['username'] = username

            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.dashboard'))

        flash('用户名或密码错误', 'error')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    """管理员登出"""
    logout_user()
    session.pop('username', None)
    flash('已退出登录', 'success')
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@login_required
def dashboard():
    """后台仪表板"""
    # 统计数据
    message_count = Message.query.count()
    unread_count = Message.query.filter_by(is_read=False).count()
    project_count = Project.query.count()
    skill_count = Skill.query.count()

    # 最新留言
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                         message_count=message_count,
                         unread_count=unread_count,
                         project_count=project_count,
                         skill_count=skill_count,
                         recent_messages=recent_messages)


@admin_bp.route('/messages')
@login_required
def messages():
    """留言管理"""
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)


@admin_bp.route('/messages/<int:id>/read', methods=['POST'])
@login_required
def mark_message_read(id):
    """标记留言为已读"""
    message = Message.query.get_or_404(id)
    message.is_read = True
    db.session.commit()
    flash('已标记为已读', 'success')
    return redirect(url_for('admin.messages'))


@admin_bp.route('/messages/<int:id>/delete', methods=['POST'])
@login_required
def delete_message(id):
    """删除留言"""
    message = Message.query.get_or_404(id)
    db.session.delete(message)
    db.session.commit()
    flash('留言已删除', 'success')
    return redirect(url_for('admin.messages'))


@admin_bp.route('/projects')
@login_required
def projects():
    """项目管理"""
    projects = Project.query.order_by(Project.order).all()
    return render_template('admin/projects.html', projects=projects)


@admin_bp.route('/upload', methods=['POST'])
@login_required
def upload_image():
    """图片上传接口"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '未选择图片'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'success': False, 'error': '未选择图片'}), 400

    # 处理图片
    success, result = process_uploaded_image(file)

    if success:
        return jsonify({'success': True, 'url': result})
    else:
        return jsonify({'success': False, 'error': result}), 400


@admin_bp.route('/projects/add', methods=['GET', 'POST'])
@login_required
def add_project():
    """添加项目"""
    if request.method == 'POST':
        project = Project(
            title=request.form.get('title'),
            category=request.form.get('category'),
            description=request.form.get('description'),
            image_url=request.form.get('image_url'),
            project_url=request.form.get('project_url'),
            order=int(request.form.get('order', 0)),
            is_offset=request.form.get('is_offset') == 'on'
        )
        db.session.add(project)
        db.session.commit()
        flash('项目添加成功', 'success')
        return redirect(url_for('admin.projects'))

    return render_template('admin/project_form.html', project=None)


@admin_bp.route('/projects/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(id):
    """编辑项目"""
    project = Project.query.get_or_404(id)

    if request.method == 'POST':
        project.title = request.form.get('title')
        project.category = request.form.get('category')
        project.description = request.form.get('description')
        project.image_url = request.form.get('image_url')
        project.project_url = request.form.get('project_url')
        project.order = int(request.form.get('order', 0))
        project.is_offset = request.form.get('is_offset') == 'on'

        db.session.commit()
        flash('项目更新成功', 'success')
        return redirect(url_for('admin.projects'))

    return render_template('admin/project_form.html', project=project)


@admin_bp.route('/projects/<int:id>/delete', methods=['POST'])
@login_required
def delete_project(id):
    """删除项目"""
    project = Project.query.get_or_404(id)
    db.session.delete(project)
    db.session.commit()
    flash('项目已删除', 'success')
    return redirect(url_for('admin.projects'))


@admin_bp.route('/skills')
@login_required
def skills():
    """技能管理"""
    skills = Skill.query.order_by(Skill.category, Skill.order).all()
    return render_template('admin/skills.html', skills=skills)


@admin_bp.route('/skills/add', methods=['GET', 'POST'])
@login_required
def add_skill():
    """添加技能"""
    if request.method == 'POST':
        skill = Skill(
            name=request.form.get('name'),
            category=request.form.get('category'),
            order=int(request.form.get('order', 0))
        )
        db.session.add(skill)
        db.session.commit()
        flash('技能添加成功', 'success')
        return redirect(url_for('admin.skills'))

    return render_template('admin/skill_form.html', skill=None)


@admin_bp.route('/skills/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_skill(id):
    """编辑技能"""
    skill = Skill.query.get_or_404(id)

    if request.method == 'POST':
        skill.name = request.form.get('name')
        skill.category = request.form.get('category')
        skill.order = int(request.form.get('order', 0))

        db.session.commit()
        flash('技能更新成功', 'success')
        return redirect(url_for('admin.skills'))

    return render_template('admin/skill_form.html', skill=skill)


@admin_bp.route('/skills/<int:id>/delete', methods=['POST'])
@login_required
def delete_skill(id):
    """删除技能"""
    skill = Skill.query.get_or_404(id)
    db.session.delete(skill)
    db.session.commit()
    flash('技能已删除', 'success')
    return redirect(url_for('admin.skills'))


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """系统设置"""
    if request.method == 'POST':
        # 修改密码
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password:
            if new_password != confirm_password:
                flash('两次输入的密码不一致', 'error')
            elif len(new_password) < 6:
                flash('密码长度至少 6 位', 'error')
            else:
                admin = Admin.query.filter_by(username=session.get('username')).first()
                if admin:
                    admin.password_hash = encode_password(new_password)
                    db.session.commit()
                    flash('密码修改成功', 'success')

        return redirect(url_for('admin.settings'))

    return render_template('admin/settings.html')
