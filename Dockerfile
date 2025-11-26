# ==========================================
# YPrompt Docker 多阶段构建
# 适配 Traefik 反向代理，不使用 Nginx
# ==========================================

# ==========================================
# 阶段1: 构建前端
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制 package.json 和 lock 文件
COPY frontend/package*.json ./

# 安装依赖（使用国内镜像加速）
RUN npm config set registry https://registry.npmmirror.com && \
    npm ci --only=production=false

# 复制前端源代码
COPY frontend/ ./

# 构建前端
RUN npm run build

# ==========================================
# 阶段2: 运行时镜像
# ==========================================
FROM python:3.11-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    # 应用配置
    YPROMPT_PORT=8888 \
    YPROMPT_HOST=0.0.0.0 \
    # 数据库配置
    DB_TYPE=sqlite \
    SQLITE_DB_PATH=/app/data/yprompt.db \
    # 默认管理员账号
    ADMIN_USERNAME=admin \
    ADMIN_PASSWORD=admin123 \
    # 数据目录
    DATA_PATH=/app/data \
    LOG_PATH=/app/data/logs \
    # 前端静态文件目录
    STATIC_PATH=/app/frontend/dist

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# 创建应用目录
WORKDIR /app

# 复制后端依赖文件
COPY backend/requirements.txt /app/backend/

# 安装 Python 依赖（使用国内镜像加速）
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r /app/backend/requirements.txt

# 复制后端代码
COPY backend/ /app/backend/

# 从前端构建阶段复制构建产物
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# 复制启动脚本
COPY start.sh /app/
RUN chmod +x /app/start.sh

# 创建必要的目录
RUN mkdir -p /app/data/logs

# 暴露端口（只需要后端端口，Traefik 会处理）
EXPOSE 8888

# 数据卷
VOLUME ["/app/data"]

# 启动命令
CMD ["/app/start.sh"]
