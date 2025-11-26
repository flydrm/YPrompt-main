# -*- coding: utf-8 -*-
"""
全局AI设置路由
- 获取设置：所有登录用户可用
- 修改设置：仅管理员可用
"""
from sanic import Blueprint
from sanic.response import json
from sanic_ext import openapi
from sanic.log import logger

from apps.utils.auth_middleware import auth_required
from .services import GlobalAISettingsService, UserService


# 创建设置蓝图
settings = Blueprint('settings', url_prefix='/api/settings')


@settings.get('/ai')
@auth_required
@openapi.summary("获取全局AI设置")
@openapi.description("获取管理员配置的全局AI提供商设置（所有用户可用）")
@openapi.secured("BearerAuth")
@openapi.response(200, {"application/json": {
    "code": int,
    "data": dict
}})
async def get_ai_settings(request):
    """获取全局AI设置（所有用户可用）"""
    try:
        user_id = request.ctx.user_id
        
        # 获取设置
        settings_service = GlobalAISettingsService(request.app.ctx.db)
        settings_data = await settings_service.get_settings()
        
        # 检查当前用户是否为管理员
        user_service = UserService(request.app.ctx.db)
        is_admin = await user_service.is_admin(user_id)
        
        # 添加管理员标识
        settings_data['is_admin'] = is_admin
        
        return json({
            'code': 200,
            'data': settings_data
        })
        
    except Exception as e:
        logger.error(f'❌ 获取AI设置失败: {e}')
        return json({
            'code': 500,
            'message': f'获取失败: {str(e)}'
        })


@settings.post('/ai')
@auth_required
@openapi.summary("保存全局AI设置")
@openapi.description("保存AI提供商配置（仅管理员可用）")
@openapi.secured("BearerAuth")
@openapi.body({"application/json": dict})
@openapi.response(200, {"application/json": {"code": int, "message": str}})
@openapi.response(403, {"application/json": {"code": int, "message": str}})
async def save_ai_settings(request):
    """保存全局AI设置（仅管理员可用）"""
    try:
        user_id = request.ctx.user_id
        
        # 检查管理员权限
        user_service = UserService(request.app.ctx.db)
        is_admin = await user_service.is_admin(user_id)
        
        if not is_admin:
            return json({
                'code': 403,
                'message': '权限不足，仅管理员可修改AI设置'
            })
        
        data = request.json
        
        # 保存设置
        settings_service = GlobalAISettingsService(request.app.ctx.db)
        await settings_service.save_settings(user_id, data)
        
        return json({
            'code': 200,
            'message': '保存成功'
        })
        
    except Exception as e:
        logger.error(f'❌ 保存AI设置失败: {e}')
        return json({
            'code': 500,
            'message': f'保存失败: {str(e)}'
        })


@settings.delete('/ai')
@auth_required
@openapi.summary("重置全局AI设置")
@openapi.description("重置AI提供商配置为默认值（仅管理员可用）")
@openapi.secured("BearerAuth")
@openapi.response(200, {"application/json": {"code": int, "message": str}})
@openapi.response(403, {"application/json": {"code": int, "message": str}})
async def reset_ai_settings(request):
    """重置全局AI设置（仅管理员可用）"""
    try:
        user_id = request.ctx.user_id
        
        # 检查管理员权限
        user_service = UserService(request.app.ctx.db)
        is_admin = await user_service.is_admin(user_id)
        
        if not is_admin:
            return json({
                'code': 403,
                'message': '权限不足，仅管理员可重置AI设置'
            })
        
        # 重置设置
        settings_service = GlobalAISettingsService(request.app.ctx.db)
        await settings_service.reset_settings(user_id)
        
        return json({
            'code': 200,
            'message': '重置成功'
        })
        
    except Exception as e:
        logger.error(f'❌ 重置AI设置失败: {e}')
        return json({
            'code': 500,
            'message': f'重置失败: {str(e)}'
        })
