# -*- coding: utf-8 -*-
"""
AI 代理路由
代理前端对 AI 服务的请求，避免 CORS 跨域问题
"""
import httpx
from sanic import Blueprint
from sanic.response import json
from sanic_ext import openapi
from sanic.log import logger

from apps.utils.auth_middleware import auth_required


# 创建 AI 代理蓝图
ai_proxy = Blueprint('ai_proxy', url_prefix='/api/ai')

# 请求超时时间（秒）
REQUEST_TIMEOUT = 30


def _build_models_url(base_url: str) -> str:
    """
    构建获取模型列表的 URL
    
    规则：
    - 如果 URL 以 /chat/completions 结尾，替换为 /models
    - 如果 URL 已包含 /models，直接使用
    - 如果 URL 以 / 结尾（如 https://b.xyz/），拼接 models → https://b.xyz/models
    - 如果 URL 不以 / 结尾（如 https://a.com），拼接 /v1/models → https://a.com/v1/models
    
    Args:
        base_url: API 基础 URL
        
    Returns:
        str: 完整的 models API URL
    """
    # 处理 /chat/completions 结尾
    if base_url.endswith('/chat/completions'):
        return base_url.replace('/chat/completions', '/models')
    
    # 已经是 models 接口
    if '/models' in base_url:
        return base_url
    
    # 处理末尾斜杠的情况
    # 有末尾 / → 用户已指定路径前缀，只需加 models
    # 无末尾 / → 需要加完整的 /v1/models
    if base_url.endswith('/'):
        return f"{base_url}models"
    else:
        return f"{base_url}/v1/models"


def _build_chat_url(base_url: str) -> str:
    """
    构建 chat completions URL
    
    规则：
    - 如果 URL 已以 /chat/completions 结尾，直接使用
    - 如果 URL 以 / 结尾（如 https://b.xyz/），拼接 chat/completions
    - 如果 URL 不以 / 结尾（如 https://a.com），拼接 /v1/chat/completions
    
    Args:
        base_url: API 基础 URL
        
    Returns:
        str: 完整的 chat completions URL
    """
    if base_url.endswith('/chat/completions'):
        return base_url
    
    if '/chat/completions' in base_url:
        return base_url
    
    if base_url.endswith('/'):
        return f"{base_url}chat/completions"
    else:
        return f"{base_url}/v1/chat/completions"


@ai_proxy.post('/models')
@auth_required
@openapi.summary("获取 AI 模型列表")
@openapi.description("通过后端代理获取 AI 服务的模型列表，避免 CORS 问题")
@openapi.secured("BearerAuth")
@openapi.body({"application/json": {
    "base_url": openapi.String(description="AI 服务基础 URL", required=True),
    "api_key": openapi.String(description="API Key", required=True),
    "provider_type": openapi.String(description="提供商类型: openai/anthropic/google", required=True),
}})
@openapi.response(200, {"application/json": {
    "code": int,
    "data": dict
}})
async def get_models(request):
    """
    获取 AI 模型列表（代理请求）
    
    支持的提供商类型：
    - openai: OpenAI 兼容接口
    - anthropic: Anthropic Claude
    - google: Google Gemini
    """
    try:
        data = request.json
        # 注意：不要 rstrip('/')，因为末尾的 / 用于判断是否需要拼接 /v1
        base_url = data.get('base_url', '').strip()
        api_key = data.get('api_key', '')
        provider_type = data.get('provider_type', 'openai')
        
        if not base_url or not api_key:
            return json({
                'code': 400,
                'message': '缺少必要参数: base_url 和 api_key'
            })
        
        # 根据提供商类型获取模型列表
        if provider_type == 'openai':
            models = await _fetch_openai_models(base_url, api_key)
        elif provider_type == 'anthropic':
            models = await _fetch_anthropic_models(base_url, api_key)
        elif provider_type == 'google':
            models = await _fetch_google_models(base_url, api_key)
        else:
            # 默认使用 OpenAI 兼容接口
            models = await _fetch_openai_models(base_url, api_key)
        
        return json({
            'code': 200,
            'data': {
                'models': models
            }
        })
        
    except httpx.TimeoutException:
        logger.error(f'❌ 获取模型列表超时')
        return json({
            'code': 504,
            'message': '请求超时，请检查网络或 API 地址'
        })
    except httpx.RequestError as e:
        logger.error(f'❌ 获取模型列表网络错误: {e}')
        return json({
            'code': 502,
            'message': f'网络请求失败: {str(e)}'
        })
    except Exception as e:
        logger.error(f'❌ 获取模型列表失败: {e}')
        return json({
            'code': 500,
            'message': f'获取失败: {str(e)}'
        })


async def _fetch_openai_models(base_url: str, api_key: str) -> list:
    """
    获取 OpenAI 兼容接口的模型列表
    
    Args:
        base_url: API 基础 URL（如 https://api.openai.com/v1）
        api_key: API Key
        
    Returns:
        list: 模型列表
    """
    # 构建 models 接口 URL
    models_url = _build_models_url(base_url)
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(
            models_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            }
        )
        
        if response.status_code != 200:
            logger.warning(f'⚠️ OpenAI models API 返回: {response.status_code}')
            return []
        
        data = response.json()
        models = data.get('data', [])
        
        # 提取模型 ID 和名称
        result = []
        for model in models:
            model_id = model.get('id', '')
            if model_id:
                result.append({
                    'id': model_id,
                    'name': model_id,
                    'owned_by': model.get('owned_by', ''),
                    'created': model.get('created', 0),
                })
        
        # 按名称排序
        result.sort(key=lambda x: x['name'])
        
        logger.info(f'✅ 获取 OpenAI 模型列表成功: {len(result)} 个模型')
        return result


async def _fetch_anthropic_models(base_url: str, api_key: str) -> list:
    """
    获取 Anthropic Claude 模型列表
    
    注意：Anthropic 没有公开的 models 接口，返回预设列表
    """
    # Anthropic 没有公开的 models API，返回预设列表
    models = [
        {'id': 'claude-opus-4-1-20250805', 'name': 'Claude Opus 4.1'},
        {'id': 'claude-opus-4-20250514', 'name': 'Claude Opus 4.0'},
        {'id': 'claude-sonnet-4-20250514', 'name': 'Claude Sonnet 4.0'},
        {'id': 'claude-3-7-sonnet-20250219', 'name': 'Claude 3.7 Sonnet'},
        {'id': 'claude-3-5-sonnet-20241022', 'name': 'Claude 3.5 Sonnet'},
        {'id': 'claude-3-5-haiku-20241022', 'name': 'Claude 3.5 Haiku'},
        {'id': 'claude-3-opus-20240229', 'name': 'Claude 3 Opus'},
        {'id': 'claude-3-sonnet-20240229', 'name': 'Claude 3 Sonnet'},
        {'id': 'claude-3-haiku-20240307', 'name': 'Claude 3 Haiku'},
    ]
    
    logger.info(f'✅ 返回 Anthropic 预设模型列表: {len(models)} 个模型')
    return models


async def _fetch_google_models(base_url: str, api_key: str) -> list:
    """
    获取 Google Gemini 模型列表
    """
    # 构建 models 接口 URL
    models_url = f"{base_url}/models?key={api_key}"
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(models_url)
        
        if response.status_code != 200:
            logger.warning(f'⚠️ Google models API 返回: {response.status_code}')
            # 返回预设列表
            return [
                {'id': 'gemini-2.0-flash-exp', 'name': 'Gemini 2.0 Flash'},
                {'id': 'gemini-1.5-pro', 'name': 'Gemini 1.5 Pro'},
                {'id': 'gemini-1.5-flash', 'name': 'Gemini 1.5 Flash'},
                {'id': 'gemini-1.0-pro', 'name': 'Gemini 1.0 Pro'},
            ]
        
        data = response.json()
        models = data.get('models', [])
        
        # 提取模型信息
        result = []
        for model in models:
            model_name = model.get('name', '')
            # Google 返回的格式是 "models/gemini-pro"
            model_id = model_name.replace('models/', '') if model_name.startswith('models/') else model_name
            display_name = model.get('displayName', model_id)
            
            if model_id and 'gemini' in model_id.lower():
                result.append({
                    'id': model_id,
                    'name': display_name,
                    'description': model.get('description', ''),
                })
        
        logger.info(f'✅ 获取 Google 模型列表成功: {len(result)} 个模型')
        return result


@ai_proxy.post('/test')
@auth_required
@openapi.summary("测试 AI 连接")
@openapi.description("测试 AI 服务连接是否正常")
@openapi.secured("BearerAuth")
@openapi.body({"application/json": {
    "base_url": openapi.String(description="AI 服务基础 URL", required=True),
    "api_key": openapi.String(description="API Key", required=True),
    "model": openapi.String(description="模型 ID", required=True),
    "provider_type": openapi.String(description="提供商类型", required=True),
}})
async def test_connection(request):
    """测试 AI 服务连接"""
    try:
        data = request.json
        # 注意：不要 rstrip('/')，因为末尾的 / 用于判断是否需要拼接 /v1
        base_url = data.get('base_url', '').strip()
        api_key = data.get('api_key', '')
        model = data.get('model', '')
        provider_type = data.get('provider_type', 'openai')
        
        if not all([base_url, api_key, model]):
            return json({
                'code': 400,
                'message': '缺少必要参数'
            })
        
        # 发送简单的测试请求
        if provider_type == 'openai':
            success, message = await _test_openai_connection(base_url, api_key, model)
        elif provider_type == 'anthropic':
            success, message = await _test_anthropic_connection(base_url, api_key, model)
        elif provider_type == 'google':
            success, message = await _test_google_connection(base_url, api_key, model)
        else:
            success, message = await _test_openai_connection(base_url, api_key, model)
        
        if success:
            return json({
                'code': 200,
                'message': '连接成功',
                'data': {'connected': True}
            })
        else:
            return json({
                'code': 400,
                'message': message,
                'data': {'connected': False}
            })
            
    except Exception as e:
        logger.error(f'❌ 测试连接失败: {e}')
        return json({
            'code': 500,
            'message': f'测试失败: {str(e)}',
            'data': {'connected': False}
        })


async def _test_openai_connection(base_url: str, api_key: str, model: str) -> tuple:
    """测试 OpenAI 兼容接口连接"""
    # 构建 chat completions URL
    chat_url = _build_chat_url(base_url)
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(
            chat_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': [{'role': 'user', 'content': 'Hi'}],
                'max_tokens': 5,
            }
        )
        
        if response.status_code == 200:
            return True, '连接成功'
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_msg = error_data.get('error', {}).get('message', response.text[:200])
            return False, f'API 返回错误: {error_msg}'


async def _test_anthropic_connection(base_url: str, api_key: str, model: str) -> tuple:
    """测试 Anthropic 接口连接"""
    if not base_url.endswith('/messages'):
        messages_url = f"{base_url}/v1/messages"
    else:
        messages_url = base_url
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(
            messages_url,
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json',
            },
            json={
                'model': model,
                'messages': [{'role': 'user', 'content': 'Hi'}],
                'max_tokens': 5,
            }
        )
        
        if response.status_code == 200:
            return True, '连接成功'
        else:
            return False, f'API 返回 {response.status_code}'


async def _test_google_connection(base_url: str, api_key: str, model: str) -> tuple:
    """测试 Google Gemini 接口连接"""
    # Google Gemini API 格式
    generate_url = f"{base_url}/models/{model}:generateContent?key={api_key}"
    
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(
            generate_url,
            headers={'Content-Type': 'application/json'},
            json={
                'contents': [{'parts': [{'text': 'Hi'}]}],
                'generationConfig': {'maxOutputTokens': 5}
            }
        )
        
        if response.status_code == 200:
            return True, '连接成功'
        else:
            return False, f'API 返回 {response.status_code}'

