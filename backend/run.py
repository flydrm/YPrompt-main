#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YPrompt 后端服务启动入口

支持通过环境变量配置：
- YPROMPT_HOST: 监听地址（默认 0.0.0.0）
- YPROMPT_PORT: 监听端口（默认 8888）
- YPROMPT_WORKERS: worker 数量（默认 1）
- YPROMPT_DEBUG: 调试模式（默认 false）
- YPROMPT_AUTO_RELOAD: 自动重载（默认 false）
"""
import os
import sys

# 确保当前目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """主入口函数"""
    from apps import create_app
    
    # 创建应用实例
    app = create_app()
    
    # 从环境变量读取配置
    host = os.environ.get('YPROMPT_HOST', '0.0.0.0')
    port = int(os.environ.get('YPROMPT_PORT', 8888))
    workers = int(os.environ.get('YPROMPT_WORKERS', 1))
    debug = os.environ.get('YPROMPT_DEBUG', 'false').lower() == 'true'
    auto_reload = os.environ.get('YPROMPT_AUTO_RELOAD', 'false').lower() == 'true'
    
    print(f"🚀 启动 YPrompt 后端服务: {host}:{port}")
    print(f"   workers={workers}, debug={debug}, auto_reload={auto_reload}")
    
    # 启动服务
    # 使用 single_process=True 避免多进程导致的重复初始化问题
    # 在 Docker 环境中，使用单进程更简单可靠
    app.run(
        host=host, 
        port=port, 
        workers=workers, 
        auto_reload=auto_reload, 
        debug=debug,
        single_process=True  # 关键：使用单进程模式
    )


if __name__ == '__main__':
    main()
