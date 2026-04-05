"""
数据库迁移脚本 - 将 Message 表的 email 字段迁移为 contact_type 和 contact 字段
使用原生 SQLite 命令直接修改数据库
"""
import sqlite3
import os

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'portfolio.db')


def migrate_message_table():
    """迁移 Message 表结构"""
    if not os.path.exists(DB_PATH):
        print(f"数据库文件不存在：{DB_PATH}")
        return
    
    print(f"连接数据库：{DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查当前表结构
        print("\n检查当前表结构...")
        cursor.execute("PRAGMA table_info(messages)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"当前列：{column_names}")
        
        if 'contact_type' in column_names:
            print("\n[信息] 数据库已经是新结构，无需迁移")
            return
        
        if 'email' not in column_names:
            print("\n[错误] 找不到 email 列")
            return
        
        # 备份数据
        print("\n备份旧数据...")
        cursor.execute("SELECT * FROM messages")
        old_data = cursor.fetchall()
        print(f"已备份 {len(old_data)} 条消息记录")
        
        # 重命名旧表
        print("重命名旧表为 messages_backup...")
        cursor.execute("ALTER TABLE messages RENAME TO messages_backup")
        conn.commit()
        
        # 创建新表
        print("创建新表...")
        cursor.execute("""
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                contact_type VARCHAR(20) NOT NULL DEFAULT 'email',
                contact VARCHAR(120) NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME,
                is_read BOOLEAN DEFAULT 0
            )
        """)
        conn.commit()
        
        # 恢复数据
        print("恢复数据...")
        for row in old_data:
            # 旧表结构：id, name, email, content, created_at, is_read
            old_id, name, email, content, created_at, is_read = row
            cursor.execute("""
                INSERT INTO messages (id, name, contact_type, contact, content, created_at, is_read)
                VALUES (?, ?, 'email', ?, ?, ?, ?)
            """, (old_id, name, email, content, created_at, is_read))
        
        conn.commit()
        print(f"已恢复 {len(old_data)} 条消息记录")
        
        # 删除备份表
        print("删除备份表...")
        cursor.execute("DROP TABLE messages_backup")
        conn.commit()
        
        print("\n[成功] 数据库迁移完成！")
        print("  - 原 'email' 字段已迁移到 'contact' 字段")
        print("  - 所有旧记录的 'contact_type' 设置为 'email'")
        
    except Exception as e:
        print(f"\n[错误] 迁移失败：{e}")
        conn.rollback()
        # 如果有备份表，尝试恢复
        try:
            cursor.execute("DROP TABLE IF EXISTS messages_backup")
            conn.commit()
        except:
            pass
    finally:
        conn.close()


if __name__ == '__main__':
    print("=== Message 表迁移脚本 ===")
    print("此脚本将把 Message 表从旧的 email 字段迁移到新的 contact_type + contact 字段")
    print()
    confirm = input("是否继续？(y/n): ").strip().lower()
    if confirm == 'y':
        migrate_message_table()
    else:
        print("已取消迁移")