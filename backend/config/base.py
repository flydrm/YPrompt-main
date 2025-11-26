# -*- coding: utf-8 -*-

class BaseConfig(object):
    """配置基类"""

    DEBUG = True

    # JWT秘钥
    SECRET_KEY = 'intramirror'
    
    # Linux.do OAuth配置
    LINUX_DO_CLIENT_ID = ''
    LINUX_DO_CLIENT_SECRET = ''
    LINUX_DO_REDIRECT_URI = ''
    
    # ==========================================
    # 数据库配置
    # ==========================================
    # 数据库类型: 'sqlite' 或 'mysql'
    DB_TYPE = 'sqlite'
    
    # SQLite配置
    SQLITE_DB_PATH = '../data/yprompt.db'
    
    # MySQL配置（当DB_TYPE='mysql'时使用）
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASS = ''
    DB_NAME = 'yprompt'
    DB_PORT = 3306
    
    # ==========================================
    # 默认管理员账号配置（仅首次初始化时使用）
    # ==========================================
    DEFAULT_ADMIN_USERNAME = 'admin'
    DEFAULT_ADMIN_PASSWORD = 'admin123'
    DEFAULT_ADMIN_NAME = '管理员'

    ACCESS_LOG = False

    # 服务worker数量
    WORKERS = 1

    # 跨域相关
    # 是否启动跨域功能
    ENABLE_CORS = False
    CORS_SUPPORTS_CREDENTIALS = True

    # redis配置
    REDIS_CON = "redis://127.0.0.1:6379/2"

    # 日志配置，兼容sanic内置log库
    # Docker 环境下只需控制台输出，通过 docker logs 查看
    BASE_LOGGING = {
        'version': 1,
        'loggers': {
            "sanic.root": {"level": "INFO", "handlers": ["console"]},
        },
        'formatters': {
            'default': {
                'format': '%(asctime)s | %(levelname)s | %(message)s',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'default',
            },
        },
    }

    # 告警源和派生表映射关系
    S2T = {
        "apm": "apm",
        "rum": "rum",
        "ckafka": "mid",
        "mongodb": "mid",
        "redis": "mid",
        "cdb": "mid",
        "es": "mid",
        "cvm": "iaas",
        "ecs": "iaas",
        "cos": "iaas",
        "cls": "iaas",
        "sls": "iaas",
        "custom": "custom"
    }

    # 没有对应的分派策略的默认owner
    OWNER_DEFAULT = [{
        'workforceType': 4,
        'watchkeeperId': 833,
        'watchkeeperName': '朱威',
        'dingDingId': 4311207311543872874
    }]
    ARGS_DEFAULT = {
    'status': 0,
    'dingtalk_person': 0,
    'sms': 0,
    'dingtalk_group': 0
    }


    def __init__(self):
        pass
