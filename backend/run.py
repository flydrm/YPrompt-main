import os
from apps import create_app

app = create_app()


if __name__ == '__main__':
    # 从环境变量读取配置
    host = os.environ.get('YPROMPT_HOST', '0.0.0.0')
    port = int(os.environ.get('YPROMPT_PORT', 8888))
    workers = int(os.environ.get('YPROMPT_WORKERS', 1))
    debug = os.environ.get('YPROMPT_DEBUG', 'false').lower() == 'true'
    auto_reload = os.environ.get('YPROMPT_AUTO_RELOAD', 'false').lower() == 'true'
    
    print(f"🚀 启动 YPrompt 后端服务: {host}:{port}")
    app.run(host=host, port=port, workers=workers, auto_reload=auto_reload, debug=debug)
