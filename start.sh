#!/bin/bash

echo "========================================"
echo "  Scor-Vip Portfolio - 启动脚本"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "[信息] 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "[信息] 创建虚拟环境..."
    python3 -m venv venv
    echo "[成功] 虚拟环境创建完成"
else
    echo "[信息] 虚拟环境已存在"
fi

echo ""
echo "[信息] 激活虚拟环境..."
source venv/bin/activate

echo ""
echo "[信息] 安装依赖..."
pip install -r requirements.txt

echo ""
echo "[信息] 创建数据库..."
python init_db.py

echo ""
echo "========================================"
echo "  启动 Flask 开发服务器"
echo "  访问地址：http://localhost:5003"
echo "  按 Ctrl+C 停止服务器"
echo "========================================"
echo ""

python run.py
