#!/bin/bash

# 乾坤量化交易系统 - 一键启动脚本 (macOS)
# 同时启动后端和前端服务

echo "=========================================="
echo "  乾坤量化交易系统 - 启动中..."
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  警告: 端口 $port 已被占用"
        read -p "是否要关闭占用该端口的进程? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            lsof -ti:$port | xargs kill -9
            echo "✅ 已关闭占用端口 $port 的进程"
            sleep 1
        else
            echo "❌ 启动取消"
            exit 1
        fi
    fi
}

# 检查后端端口 (8000)
check_port 8000

# 检查前端端口 (5173)
check_port 5173

# 创建日志目录
mkdir -p logs

echo ""
echo "1️⃣  启动后端服务..."
echo "----------------------------------------"

# 检查后端依赖
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ 错误: 找不到 backend/requirements.txt"
    exit 1
fi

# ==========================================
# 智能虚拟环境检测
# ==========================================
# 虚拟环境检测说明：
# 1. 如果当前已在虚拟环境中（如手动激活的venv），直接使用
# 2. 如果项目中存在 backend/venv，激活并使用
# 3. 如果都不存在，创建新的虚拟环境
# ==========================================

VENV_EXISTS=false
NEED_INSTALL_DEPS=false

# 检测是否已在虚拟环境中
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ 检测到已在虚拟环境中: $VIRTUAL_ENV"
    echo "📦 使用当前虚拟环境"
    VENV_EXISTS=true
# 检测项目中是否已有虚拟环境
elif [ -d "backend/venv" ]; then
    echo "✅ 检测到项目虚拟环境: backend/venv"
    echo "🔄 激活虚拟环境..."
    source backend/venv/bin/activate
    VENV_EXISTS=true
# 创建新的虚拟环境
else
    echo "📦 未检测到虚拟环境，创建新环境..."
    python3 -m venv backend/venv
    source backend/venv/bin/activate
    VENV_EXISTS=true
    NEED_INSTALL_DEPS=true
    echo "📦 安装后端依赖..."
    pip install -q -r backend/requirements.txt
    echo "✅ 后端依赖安装完成"
fi

# 检查依赖是否需要更新（仅当虚拟环境已存在且不是新建时）
if [ "$VENV_EXISTS" = true ] && [ "$NEED_INSTALL_DEPS" = false ]; then
    # 通过比较requirements.txt修改时间和标记文件来判断
    DEPS_MARKER=".deps_installed"
    if [ ! -f "$DEPS_MARKER" ] || [ "backend/requirements.txt" -nt "$DEPS_MARKER" ]; then
        echo "📦 检测到依赖变更,更新后端依赖..."
        pip install -q -r backend/requirements.txt
        touch "$DEPS_MARKER"
        echo "✅ 后端依赖更新完成"
    else
        echo "✅ 后端依赖已就绪(跳过安装)"
    fi
fi

# 启动后端
cd backend
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
echo "   - 地址: http://localhost:8000"
echo "   - 日志: logs/backend.log"

# 等待后端启动
echo "⏳ 等待后端服务就绪..."
sleep 3

echo ""
echo "2️⃣  启动前端服务..."
echo "----------------------------------------"

# 检查前端依赖
cd frontend
FRONTEND_DEPS_MARKER="../.frontend_deps_installed"
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行: 安装前端依赖..."
    npm install
    touch "$FRONTEND_DEPS_MARKER"
    echo "✅ 前端依赖安装完成"
elif [ ! -f "$FRONTEND_DEPS_MARKER" ] || [ "package.json" -nt "$FRONTEND_DEPS_MARKER" ]; then
    echo "📦 检测到依赖变更,更新前端依赖..."
    npm install
    touch "$FRONTEND_DEPS_MARKER"
    echo "✅ 前端依赖更新完成"
else
    echo "✅ 前端依赖已就绪(跳过安装)"
fi

# 启动前端
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
echo "   - 地址: http://localhost:5173"
echo "   - 日志: logs/frontend.log"

# 保存PID到文件，方便后续关闭
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo ""
echo "=========================================="
echo "  ✅ 启动完成！"
echo "=========================================="
echo ""
echo "📊 前端访问地址: http://localhost:5173"
echo "🔧 后端API地址:  http://localhost:8000"
echo "📖 API文档地址:  http://localhost:8000/docs"
echo ""
echo "💡 提示:"
echo "   - 查看后端日志: tail -f logs/backend.log"
echo "   - 查看前端日志: tail -f logs/frontend.log"
echo "   - 停止服务:    ./stop.sh"
echo ""
echo "⏳ 等待服务完全启动..."
sleep 3

# 自动打开浏览器（可选）
read -p "是否在浏览器中打开系统? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open http://localhost:5173
fi

echo ""
echo "✨ 系统已就绪，按 Ctrl+C 不会关闭服务"
echo "   使用 ./stop.sh 脚本来停止服务"
echo ""