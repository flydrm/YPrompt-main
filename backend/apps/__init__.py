# -*- coding: utf-8 -*-

"""
初始化app及各种相关配置，扩展插件，中间件，蓝图等
"""
import os
import pkgutil
import importlib
import logging.config

from sanic import Sanic, Blueprint
from sanic.response import html, file as file_response
from sanic_ext import Extend
from sanic.log import logger

from apps.utils.db_utils import DB
from apps.utils.jwt_utils import JWTUtil
from config.settings import Config

def configure_extensions(sanic_app):
    # cors
    sanic_app.config.CORS_ORIGINS = "*"
    Extend(sanic_app)
    # mysql
    DB(sanic_app)
    # jwt
    JWTUtil.init_app(sanic_app)

def configure_blueprints(sanic_app):
    """注册蓝图 - 自动发现机制"""
    app_dict = {}
    
    # 自动发现并注册 apps/modules 下的所有蓝图
    for _, modname, ispkg in pkgutil.walk_packages(["apps/modules"]):
        try:
            module = importlib.import_module(f"apps.modules.{modname}.views")
            attr = getattr(module, modname)
            if isinstance(attr, Blueprint):
                if app_dict.get(modname) is None:
                    app_dict[modname] = attr
                    sanic_app.blueprint(attr)
        except AttributeError:
            pass  # 模块没有对应的Blueprint，跳过
        except Exception as e:
            logger.error(f"❌ 注册蓝图失败 [{modname}]: {e}")


# 全局标记，防止静态文件配置被重复调用
_static_files_configured = False

def configure_static_files(sanic_app):
    """配置前端静态文件服务（用于 Docker 部署，Traefik 反代场景）"""
    global _static_files_configured
    
    # 防止重复配置
    if _static_files_configured:
        logger.debug("静态文件服务已配置，跳过重复配置")
        return
    
    # 获取静态文件目录，默认为 /app/frontend/dist
    static_path = os.environ.get('STATIC_PATH', '/app/frontend/dist')
    
    # 检查静态文件目录是否存在
    if not os.path.exists(static_path):
        logger.warning(f"⚠️  静态文件目录不存在: {static_path}，跳过静态文件配置")
        return
    
    index_file = os.path.join(static_path, 'index.html')
    if not os.path.exists(index_file):
        logger.warning(f"⚠️  index.html 不存在: {index_file}，跳过静态文件配置")
        return
    
    logger.info(f"✅ 配置静态文件服务: {static_path}")
    
    # 标记已配置
    _static_files_configured = True
    
    # 注册静态文件目录（用于 js/css/images 等资源）
    try:
        sanic_app.static('/assets', os.path.join(static_path, 'assets'), name='assets')
    except Exception as e:
        logger.debug(f"静态资源目录可能已注册: {e}")
    
    # 处理 favicon.ico
    favicon_path = os.path.join(static_path, 'favicon.ico')
    if os.path.exists(favicon_path):
        try:
            sanic_app.static('/favicon.ico', favicon_path, name='favicon')
        except Exception as e:
            logger.debug(f"favicon 可能已注册: {e}")
    
    # SPA 路由处理：所有非 API 请求返回 index.html
    # 注意：Sanic v23.3+ 不允许重复路由名称，需要分开定义
    
    @sanic_app.route('/', methods=['GET'], name='spa_index')
    async def serve_spa_index(request):
        """处理根路径请求"""
        return await file_response(index_file)
    
    @sanic_app.route('/<path:path>', methods=['GET'], name='spa_catch_all')
    async def serve_spa_path(request, path):
        """处理其他所有路径请求（SPA 路由）"""
        # 跳过 API 请求
        if path.startswith('api/') or path.startswith('docs') or path.startswith('openapi'):
            return
        
        # 检查是否是静态资源请求
        full_path = os.path.join(static_path, path)
        if os.path.isfile(full_path):
            return await file_response(full_path)
        
        # 其他所有请求返回 index.html（SPA 路由）
        return await file_response(index_file)


def create_app(env=None,name=None):
    """
    create an app with config file
    """
    # init a sanic app
    name = name if name else __name__
    app = Sanic(name)
    # 配置日志
    logging.config.dictConfig(Config.BASE_LOGGING)
    # 加载sanic的配置内容
    app.config.update_config(Config)
    # 配置插件扩展
    configure_extensions(app)
    # 配置蓝图
    configure_blueprints(app)
    # 配置静态文件服务（Docker 部署时使用）
    configure_static_files(app)
    return app

