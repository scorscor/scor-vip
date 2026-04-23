# Scor-Vip Portfolio - 数字策展人作品集

基于 Flask + SQLite 的个人作品集网站，支持 Docker 部署。

## 技术栈

- **后端**: Flask 3.0 (Python 3.11+)
- **数据库**: SQLite
- **ORM**: SQLAlchemy
- **前端**: TailwindCSS + 原生 JavaScript
- **部署**: Docker / Docker Compose / Gunicorn

## 项目结构

```
scor-vip/
├── app/
│   ├── __init__.py          # 应用工厂
│   ├── routes.py            # 路由和 API 端点
│   ├── admin.py             # 后台管理路由
│   └── models/
│       └── __init__.py      # 数据库模型
├── templates/
│   ├── index.html           # 主页模板
│   └── admin/               # 后台管理模板
├── static/
│   ├── css/                 # 样式文件
│   └── js/                  # JavaScript 文件
├── instance/                # SQLite 数据库文件 (自动生成)
├── .env                     # 环境变量配置
├── .env.example             # 环境变量示例
├── requirements.txt         # Python 依赖
├── Dockerfile               # Docker 镜像配置
├── docker-compose.yml       # Docker Compose 配置
├── init_db.py               # 数据库初始化脚本
├── start.bat                # Windows 启动脚本
└── start.sh                 # Linux/Mac 启动脚本
```

## 快速开始

### 方法一：本地开发

#### Windows

```bash
# 双击运行或在命令行执行
start.bat
```

#### Linux / macOS

```bash
chmod +x start.sh
./start.sh
```

### 方法二：手动安装

```bash
# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库
python init_db.py

# 5. 启动开发服务器
python app/__init__.py
```

访问 http://localhost:5003

## Docker 部署

### 使用 Docker Compose (推荐)

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 仅使用 Docker

```bash
# 构建镜像
docker build -t scor-vip-portfolio .

# 运行容器
docker run -d -p 5003:5003 \
  -e SECRET_KEY=your-secret-key \
  -v $(pwd)/instance/portfolio.db:/app/instance/portfolio.db \
  --name scor-vip \
  scor-vip-portfolio
```

## API 端点

### 公开 API

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/projects` | 获取所有项目 |
| GET | `/api/skills` | 获取所有技能 |
| POST | `/api/messages` | 提交联系表单 |
| POST | `/api/init-data` | 初始化默认数据 |

### 管理 API (需要 HTTP Basic Auth)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/messages` | 获取所有留言 |
| PUT | `/api/messages/<id>` | 标记消息为已读 |
| DELETE | `/api/messages/<id>` | 删除消息 |
| POST | `/api/projects` | 创建项目 |
| PUT | `/api/projects/<id>` | 更新项目 |
| DELETE | `/api/projects/<id>` | 删除项目 |
| POST | `/api/skills` | 创建技能 |
| DELETE | `/api/skills/<id>` | 删除技能 |
| POST | `/api/admin/register` | 注册管理员 |

## 后台管理系统

访问后台管理界面：**http://localhost:5003/admin**

### 默认登录凭据
- 用户名：`admin`
- 密码：`admin123`

### 后台功能
- **仪表板**：查看数据统计和最新留言
- **留言管理**：查看、标记已读、删除留言
- **项目管理**：添加、编辑、删除项目
- **技能管理**：添加、删除技能
- **设置**：修改管理员密码

## 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `SECRET_KEY` | Flask 密钥 | `dev-key-change-in-production` |
| `DATABASE_URL` | 数据库连接 URL | `sqlite:///portfolio.db` |
| `FLASK_ENV` | 运行环境 | `development` |
| `PORT` | 服务端口 | `5003` |

## 数据库模型

### Message (留言)
- id: 主键
- name: 姓名
- email: 邮箱
- content: 内容
- created_at: 创建时间
- is_read: 是否已读

### Project (项目)
- id: 主键
- title: 标题
- category: 分类
- description: 描述
- image_url: 图片 URL
- order: 排序
- is_offset: 是否错位显示
- created_at: 创建时间

### Skill (技能)
- id: 主键
- name: 名称
- category: 分类 (design/development/soft)
- order: 排序

### Admin (管理员)
- id: 主键
- username: 用户名
- password_hash: Base64 编码后的密码
- created_at: 创建时间

## 开发说明

### 添加新依赖

```bash
pip install package-name
pip freeze > requirements.txt
```

### 数据库迁移

项目使用 Flask-Migrate 管理数据库迁移：

```bash
# 初始化迁移 (仅需一次)
flask db init

# 创建迁移脚本
flask db migrate -m "描述"

# 应用迁移
flask db upgrade
```

### 生产环境部署

1. 修改 `.env` 文件，设置生产环境的 `SECRET_KEY`
2. 使用 Docker Compose 部署（推荐）
3. 或配置 Gunicorn + Nginx

## License

MIT
