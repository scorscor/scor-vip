@echo off
echo ========================================
echo   Scor-Vip Portfolio - 启动脚本
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [信息] 检查虚拟环境...
if not exist "venv" (
    echo [信息] 创建虚拟环境...
    python -m venv venv
    echo [成功] 虚拟环境创建完成
) else (
    echo [信息] 虚拟环境已存在
)

echo.
echo [信息] 激活虚拟环境...
call venv\Scripts\activate.bat

echo.
echo [信息] 安装依赖...
pip install -r requirements.txt

echo.
echo [信息] 创建数据库...
python init_db.py

echo.
echo ========================================
echo   启动 Flask 开发服务器
echo   访问地址：http://localhost:5003
echo   按 Ctrl+C 停止服务器
echo ========================================
echo.

python run.py

pause
