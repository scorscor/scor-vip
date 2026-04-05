"""
数据库迁移脚本 - 为 projects 表添加 project_url 字段
"""
import sqlite3
import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'portfolio.db')


def migrate_projects_table():
    """为 projects 表添加 project_url 字段"""
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在：{DB_PATH}")
        return
    
    print(f"连接数据库：{DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查当前表结构
        print("\n检查当前表结构...")
        cursor.execute("PRAGMA table_info(projects)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"当前列：{column_names}")
        
        if 'project_url' in column_names:
            print("\n[信息] 数据库已经有 project_url 字段，无需迁移")
            return
        
        # 添加新字段
        print("\n添加 project_url 字段...")
        cursor.execute("ALTER TABLE projects ADD COLUMN project_url VARCHAR(500)")
        conn.commit()
        
        print("\n[成功] 数据库迁移完成！")
        print("  - 已添加 'project_url' 字段到 projects 表")
        
    except Exception as e:
        print(f"\n[错误] 迁移失败：{e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    print("=== Projects 表迁移脚本 ===")
    print("此脚本将为 projects 表添加 project_url 字段")
    print()
    confirm = input("是否继续？(y/n): ").strip().lower()
    if confirm == 'y':
        migrate_projects_table()
    else:
        print("已取消迁移")