# -*- coding: utf-8 -*-
"""
全局AI设置服务
管理员配置，所有用户共享
"""
import json
from sanic.log import logger


class GlobalAISettingsService:
    """全局AI设置服务类"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_settings(self) -> dict:
        """
        获取全局AI设置（所有用户可调用）
        
        Returns:
            dict: AI设置数据，如果不存在返回默认值
        """
        try:
            sql = "SELECT * FROM global_ai_settings LIMIT 1"
            result = await self.db.get(sql)
            
            if result:
                # 解析 JSON 字段
                settings = {
                    'providers': json.loads(result.get('providers') or '[]'),
                    'default_provider': result.get('default_provider') or '',
                    'default_model': result.get('default_model') or '',
                    'stream_mode': bool(result.get('stream_mode', 1)),
                    'use_slim_rules': bool(result.get('use_slim_rules', 0)),
                }
                return settings
            else:
                # 返回默认值（未配置）
                return {
                    'providers': [],
                    'default_provider': '',
                    'default_model': '',
                    'stream_mode': True,
                    'use_slim_rules': False,
                }
                
        except Exception as e:
            logger.error(f'❌ 获取全局AI设置失败: {e}')
            raise
    
    async def save_settings(self, admin_user_id: int, settings: dict) -> bool:
        """
        保存全局AI设置（仅管理员可调用）
        
        Args:
            admin_user_id: 管理员用户ID
            settings: AI设置数据
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 序列化 JSON 字段
            providers_json = json.dumps(settings.get('providers', []), ensure_ascii=False)
            
            # 检查是否已存在记录
            check_sql = "SELECT id FROM global_ai_settings LIMIT 1"
            existing = await self.db.get(check_sql)
            
            if existing:
                # 更新现有记录
                update_sql = """
                    UPDATE global_ai_settings SET
                        providers = ?,
                        default_provider = ?,
                        default_model = ?,
                        stream_mode = ?,
                        use_slim_rules = ?,
                        updated_by = ?
                    WHERE id = ?
                """
                await self.db.execute(update_sql, (
                    providers_json,
                    settings.get('default_provider', ''),
                    settings.get('default_model', ''),
                    1 if settings.get('stream_mode', True) else 0,
                    1 if settings.get('use_slim_rules', False) else 0,
                    admin_user_id,
                    existing['id']
                ))
            else:
                # 插入新记录
                insert_sql = """
                    INSERT INTO global_ai_settings 
                    (providers, default_provider, default_model, stream_mode, use_slim_rules, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                await self.db.execute(insert_sql, (
                    providers_json,
                    settings.get('default_provider', ''),
                    settings.get('default_model', ''),
                    1 if settings.get('stream_mode', True) else 0,
                    1 if settings.get('use_slim_rules', False) else 0,
                    admin_user_id,
                ))
            
            logger.info(f'✅ 管理员保存全局AI设置成功: admin_id={admin_user_id}')
            return True
            
        except Exception as e:
            logger.error(f'❌ 保存全局AI设置失败: {e}')
            raise
    
    async def reset_settings(self, admin_user_id: int) -> bool:
        """
        重置全局AI设置（仅管理员可调用）
        
        Args:
            admin_user_id: 管理员用户ID
            
        Returns:
            bool: 是否重置成功
        """
        try:
            sql = "DELETE FROM global_ai_settings"
            await self.db.execute(sql)
            
            logger.info(f'✅ 管理员重置全局AI设置成功: admin_id={admin_user_id}')
            return True
            
        except Exception as e:
            logger.error(f'❌ 重置全局AI设置失败: {e}')
            raise


class UserService:
    """用户服务（用于检查管理员权限）"""
    
    def __init__(self, db):
        self.db = db
    
    async def is_admin(self, user_id: int) -> bool:
        """检查用户是否为管理员"""
        try:
            sql = f"SELECT is_admin FROM users WHERE id = {user_id}"
            result = await self.db.get(sql)
            return result and result.get('is_admin', 0) == 1
        except Exception as e:
            logger.error(f'❌ 检查管理员权限失败: {e}')
            return False
