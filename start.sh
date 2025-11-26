#!/bin/bash
set -e

# ==========================================
# YPrompt 启动脚本（适配 Traefik 反代）
# ==========================================

# 环境变量默认值
export YPROMPT_PORT=${YPROMPT_PORT:-8888}
export YPROMPT_HOST=${YPROMPT_HOST:-0.0.0.0}
export DATA_PATH=${DATA_PATH:-/app/data}
export STATIC_PATH=${STATIC_PATH:-/app/frontend/dist}

# 数据库配置
export DB_TYPE=${DB_TYPE:-sqlite}
export SQLITE_DB_PATH=${SQLITE_DB_PATH:-/app/data/yprompt.db}

# 默认管理员账号配置
export ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
export ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}

echo "========================================"
echo "正在启动 YPrompt 服务"
echo "========================================"
echo "配置信息："
echo "- 监听地址: ${YPROMPT_HOST}:${YPROMPT_PORT}"
echo "- 数据库类型: ${DB_TYPE}"
echo "- 数据目录: ${DATA_PATH}"
echo "- 静态文件: ${STATIC_PATH}"
echo "- 管理员用户名: ${ADMIN_USERNAME}"
echo "- 日志输出: 控制台 (docker logs 查看)"
echo "========================================"

# 创建必要的目录
mkdir -p ${DATA_PATH}

# 检查前端静态文件
if [ -d "${STATIC_PATH}" ]; then
    echo "✓ 前端静态文件目录存在: ${STATIC_PATH}"
    if [ -f "${STATIC_PATH}/index.html" ]; then
        echo "✓ index.html 存在"
    else
        echo "⚠️  警告: index.html 不存在"
    fi
else
    echo "⚠️  警告: 前端静态文件目录不存在: ${STATIC_PATH}"
fi

# 优雅关闭处理
cleanup() {
    echo ""
    echo "========================================"
    echo "接收到停止信号，正在优雅关闭服务..."
    echo "========================================"
    
    # 停止后端服务
    if [ ! -z "$BACKEND_PID" ]; then
        echo "✓ 停止后端服务 (PID: $BACKEND_PID)"
        kill -TERM $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
    fi
    
    echo "========================================"
    echo "服务已停止"
    echo "========================================"
    exit 0
}

# 注册信号处理
trap cleanup SIGTERM SIGINT SIGQUIT

# 切换到后端目录
cd /app/backend

echo "========================================"
echo "启动 YPrompt 后端服务..."
echo "========================================"

# 启动后端服务（前台运行，让 Docker 可以正确管理进程）
exec python3 run.py
