"""
数据库初始化脚本
"""
from app import create_app
from app.models import db, Message, Project, Skill, Admin
from werkzeug.security import generate_password_hash
import os


def init_database():
    app = create_app()

    with app.app_context():
        # 创建所有表
        db.create_all()
        print("[成功] 数据库表创建完成")

        # 询问是否初始化默认数据
        init_data = input("\n是否初始化默认项目数据？(y/n): ").strip().lower()

        if init_data == 'y':
            # 检查是否已有数据
            if Project.query.first() is None:
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
                    project = Project(**proj_data)
                    db.session.add(project)

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
                    skill = Skill(**skill_data)
                    db.session.add(skill)

                db.session.commit()
                print("[成功] 默认数据初始化完成")
            else:
                print("[信息] 数据已存在，跳过初始化")

        # 询问是否创建管理员账户
        create_admin = input("\n是否创建管理员账户？(y/n): ").strip().lower()

        if create_admin == 'y':
            if Admin.query.first() is None:
                username = input("设置用户名：").strip()
                password = input("设置密码：").strip()

                if username and password:
                    admin = Admin(
                        username=username,
                        password_hash=generate_password_hash(password)
                    )
                    db.session.add(admin)
                    db.session.commit()
                    print("[成功] 管理员账户创建完成")
                else:
                    print("[错误] 用户名或密码不能为空")
            else:
                print("[信息] 管理员账户已存在")

        print("\n[完成] 数据库初始化完成")


if __name__ == '__main__':
    init_database()
