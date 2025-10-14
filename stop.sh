#!/bin/bash

# 乾坤量化交易系统 - 停止脚本 (macOS)
# 停止前端和后端服务

echo "=========================================="
echo "  乾坤量化交易系统 - 停止服务中..."
echo "=========================================="

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 停止服务
stop_service() {
    local name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            echo "🛑 停止${name}服务 (PID: $PID)..."
            kill $PID
            sleep 1
            # 如果进程还在，强制kill
            if ps -p $PID > /dev/null 2>&1; then
                kill -9 $PID
            fi
            rm -f "$pid_file"
            echo "✅ ${name}服务已停止"
        else
            echo "⚠️  ${name}服务未在运行"
            rm -f "$pid_file"
        fi
    else
        echo "⚠️  找不到${name}服务的PID文件"
        # 尝试通过端口查找并关闭
        if [ "$name" == "后端" ]; then
            PORT_PID=$(lsof -ti:8000)
            if [ ! -z "$PORT_PID" ]; then
                echo "🔍 通过端口找到${name}进程 (PID: $PORT_PID)，正在停止..."
                kill -9 $PORT_PID
                echo "✅ ${name}服务已停止"
            fi
        elif [ "$name" == "前端" ]; then
            PORT_PID=$(lsof -ti:5173)
            if [ ! -z "$PORT_PID" ]; then
                echo "🔍 通过端口找到${name}进程 (PID: $PORT_PID)，正在停止..."
                kill -9 $PORT_PID
                echo "✅ ${name}服务已停止"
            fi
        fi
    fi
}

# 停止后端
stop_service "后端" "logs/backend.pid"

# 停止前端
stop_service "前端" "logs/frontend.pid"

echo ""
echo "=========================================="
echo "  ✅ 所有服务已停止"
echo "=========================================="
echo ""