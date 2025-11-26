# YPrompt

AI通过对话挖掘用户需求，并自动生成专业的提示词，支持系统/用户提示词优化、效果对比，版本管理和支持即时渲染的操练场

## 功能特性

- AI引导对话挖掘用户需求后生成专业系统提示词
- 系统/用户(支持构建对话上下文)优化、效果对比
- 提示词版本管理与历史回滚
- 操练场支持多种输出类型即时渲染，效果看得见
- 双认证：本地用户名密码 、 `Linux.do OAuth`
- 双数据库：SQLite（默认）+ MySQL（可选）
- 响应式设计（桌面/移动端）

## 界面

![](imgs/1.gif)
![](imgs/2.gif)
![](imgs/3.gif)
![](imgs/4.gif)
![](imgs/5.gif)
![](imgs/6.gif)
![](imgs/7.gif)
![](imgs/8.gif)
![](imgs/9.gif)
![](imgs/10.gif)
![](imgs/11.gif)
![](imgs/12.gif)
![](imgs/13.gif)
![](imgs/14.gif)
![](imgs/15.gif)

## 系统架构

```
YPrompt/
├── frontend/                  # Vue 3 + TypeScript 前端
│   └── dist/                 # 构建产物
├── backend/                   # Sanic Python 后端（同时服务静态文件）
│   ├── apps/                 # 应用代码
│   ├── config/               # 配置文件
│   └── migrations/           # 数据库脚本
├── data/                      # 数据目录（持久化）
│   ├── yprompt.db            # SQLite数据库
│   └── logs/                 # 日志文件
├── Dockerfile                 # Docker镜像（多阶段构建）
├── docker-compose.yml         # Docker Compose配置（Traefik）
├── docker-compose.local.yml   # 本地开发配置（直接暴露端口）
└── start.sh                   # 容器启动脚本
```

## 快速启动

### 方式一：使用 Traefik 反向代理（推荐生产环境）

**前提条件**：已部署 Traefik 并创建 `traefik-network` 网络

1. 创建环境变量文件：

```bash
cp env.example .env
# 编辑 .env 文件，配置域名和密钥
```

2. 启动服务：

```bash
docker-compose up -d
```

3. 访问：`https://your-domain.com`

### 方式二：本地开发/测试（直接暴露端口）

```bash
# 构建并启动
docker-compose -f docker-compose.local.yml up -d --build

# 访问
http://localhost:8888
```

### 方式三：Docker Run（简单部署）

```bash
docker run -d \
  --name yprompt \
  -p 8888:8888 \
  -v ./data:/app/data \
  -e SECRET_KEY=your-random-secret-key \
  -e ADMIN_USERNAME=admin \
  -e ADMIN_PASSWORD=your-password \
  ghcr.io/fish2018/yprompt:latest
```

## Traefik 配置示例

### docker-compose.yml

```yaml
version: '3.8'

services:
  yprompt:
    image: ghcr.io/fish2018/yprompt:latest
    container_name: yprompt
    restart: unless-stopped
    volumes:
      - ./data:/app/data
    environment:
      - SECRET_KEY=your-secret-key
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD=your-password
      # Linux.do OAuth（可选）
      - LINUX_DO_CLIENT_ID=your_client_id
      - LINUX_DO_CLIENT_SECRET=your_client_secret
      - LINUX_DO_REDIRECT_URI=https://yourdomain.com/auth/callback
    labels:
      - "traefik.enable=true"
      # HTTP
      - "traefik.http.routers.yprompt.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.yprompt.entrypoints=web"
      # HTTPS
      - "traefik.http.routers.yprompt-secure.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.yprompt-secure.entrypoints=websecure"
      - "traefik.http.routers.yprompt-secure.tls=true"
      - "traefik.http.routers.yprompt-secure.tls.certresolver=letsencrypt"
      # 服务端口
      - "traefik.http.services.yprompt.loadbalancer.server.port=8888"
    networks:
      - traefik-network

networks:
  traefik-network:
    external: true
```

## 环境变量说明

### 必需参数

| 变量 | 说明 | 示例 |
|------|------|------|
| `SECRET_KEY` | JWT密钥（至少32位随机字符） | `a1b2c3d4e5f6...` |

### 服务器配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `YPROMPT_HOST` | `0.0.0.0` | 监听地址 |
| `YPROMPT_PORT` | `8888` | 监听端口 |
| `DOMAIN` | `localhost` | 域名（Traefik 路由用） |

### 数据库配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_TYPE` | `sqlite` | 数据库类型：`sqlite` 或 `mysql` |
| `SQLITE_DB_PATH` | `/app/data/yprompt.db` | SQLite数据库文件路径 |
| `DB_HOST` | `localhost` | MySQL主机地址 |
| `DB_USER` | `root` | MySQL用户名 |
| `DB_PASS` | - | MySQL密码 |
| `DB_NAME` | `yprompt` | MySQL数据库名 |
| `DB_PORT` | `3306` | MySQL端口 |

### `Linux.do OAuth`配置（可选）

| 变量 | 说明 | 示例 |
|------|------|------|
| `LINUX_DO_CLIENT_ID` | 应用Client ID | `WMYxs1aE2NOdBkj1le...` |
| `LINUX_DO_CLIENT_SECRET` | 应用Client Secret | `QGl30etmvXbLM0d...` |
| `LINUX_DO_REDIRECT_URI` | OAuth回调地址 | `https://yourdomain.com/auth/callback` |

申请地址：https://connect.linux.do/my/preferences/apps

### 本地认证配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ADMIN_USERNAME` | `admin` | 默认管理员用户名 |
| `ADMIN_PASSWORD` | `admin123` | 默认管理员密码 |

### Traefik 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TRAEFIK_NETWORK` | `traefik-network` | Traefik 网络名称 |
| `CERT_RESOLVER` | `letsencrypt` | SSL证书解析器 |

## GitHub Actions 自动构建

项目已配置 GitHub Actions 工作流，在以下情况自动构建 Docker 镜像：

- 推送到 `main`/`master` 分支
- 创建版本标签（如 `v1.0.0`）
- 手动触发

镜像会自动推送到 GitHub Container Registry：

```bash
# 拉取最新镜像
docker pull ghcr.io/your-username/yprompt:latest

# 拉取指定版本
docker pull ghcr.io/your-username/yprompt:v1.0.0
```

## 本地开发

### 前端开发

```bash
cd frontend
npm install
npm run dev
```

### 后端开发

```bash
cd backend
pip install -r requirements.txt
python run.py
```

## 许可证

MIT License
