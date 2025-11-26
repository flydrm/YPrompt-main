import type { ProviderConfig } from '@/stores/settingsStore'
import { post } from '@/services/apiService'

/**
 * 模型列表获取器
 * 
 * 通过后端代理获取模型列表，避免 CORS 跨域问题
 */
export class ModelFetcher {
  /**
   * 获取模型列表（通过后端代理）
   */
  static async getModels(provider: ProviderConfig, apiType?: 'openai' | 'anthropic' | 'google'): Promise<string[]> {
    const type = apiType || provider.type
    
    // Anthropic 没有公开的 models API，直接返回预设列表
    if (type === 'anthropic') {
      return this.getAnthropicModels()
    }
    
    // 其他提供商通过后端代理获取
    try {
      const response = await post<{
        code: number
        data?: { models: Array<{ id: string; name: string }> }
        message?: string
      }>('/api/ai/models', {
        base_url: provider.baseUrl,
        api_key: provider.apiKey,
        provider_type: type || 'openai'
      })
      
      if (response.code === 200 && response.data?.models) {
        return response.data.models.map(m => m.id).sort()
      }
      
      throw new Error(response.message || '获取模型列表失败')
    } catch (error: any) {
      console.error('获取模型列表失败:', error)
      throw new Error(error.message || '获取模型列表失败')
    }
  }

  /**
   * Anthropic 预设模型列表（没有公开的 models API）
   */
  private static getAnthropicModels(): string[] {
    return [
      'claude-opus-4-1-20250805',
      'claude-opus-4-20250514',
      'claude-sonnet-4-20250514',
      'claude-3-7-sonnet-20250219',
      'claude-3-5-sonnet-20241022',
      'claude-3-5-haiku-20241022',
      'claude-3-opus-20240229',
      'claude-3-sonnet-20240229',
      'claude-3-haiku-20240307'
    ].sort()
  }
}
