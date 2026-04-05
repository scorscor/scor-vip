# Gunicorn 配置文件

bind = "0.0.0.0:5003"
workers = 2
worker_class = "sync"
threads = 4
worker_connections = 1000
keepalive = 5
timeout = 30

# 日志
accesslog = "-"
errorlog = "-"
loglevel = "info"

# 进程命名
proc_name = "scor-vip-portfolio"

# 重启
max_requests = 1000
max_requests_jitter = 50
