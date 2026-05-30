#!/usr/bin/env bash
# 启动脚本 - 使用 Gunicorn 运行智能问答系统

APP_NAME="智能问答系统"
APP_MODULE="app:app"
HOST="0.0.0.0"
PORT="8080"
WORKERS=4

echo "🚀 启动 $APP_NAME..."
echo "📡 服务地址: http://$HOST:$PORT"
echo "🔧 管理后台: http://$HOST:$PORT/admin"
echo "👷 工作进程数: $WORKERS"
echo ""

gunicorn -w $WORKERS -b $HOST:$PORT $APP_MODULE