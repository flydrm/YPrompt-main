import { BaseProvider } from './BaseProvider'
import type { ChatMessage, AIResponse, StreamChunk, MessageContent } from '../types'
import { AnthropicAttachmentHandler } from '../multimodal/AnthropicAttachmentHandler'
import { ResponseCleaner } from '../utils/ResponseCleaner'

/**
 * Anthropic Claude API 提供商实现
 * 支持 Claude 系列模型和多模态内容
 * 
 * 默认通过后端代理调用，避免 CORS 跨域问题
 */
export class AnthropicProvider extends BaseProvider {
  /**
   * 调用 Anthropic API（通过后端代理，解决 CORS 问题）
   * @param messages 聊天消息列表
   * @param stream 是否使用流式响应
   * @returns Promise<AIResponse | ReadableStream<Uint8Array>>
   */
  async callAPI(messages: ChatMessage[], stream: boolean): Promise<AIResponse | ReadableStream<Uint8Array>> {
    if (!this.config.baseUrl) {
      throw new Error('API URL 未配置')
    }

    // 分离系统消息和对话消息
    const systemMessage = this.extractSystemMessageText(messages)
    const conversationMessages = messages.filter(m => m.role !== 'system')
    
    const modelId = this.modelId
    
    // 构建消息列表
    const formattedMessages = conversationMessages.map(msg => ({
      role: msg.role === 'assistant' ? 'assistant' : 'user',
      content: this.hasMultimodalContent(msg) 
        ? this.convertToMultimodalContent(msg)
        : (typeof msg.content === 'string' ? msg.content : (Array.isArray(msg.content) ? msg.content[0]?.text || '' : String(msg.content)))
    }))
    
    // 通过后端代理调用（解决 CORS 问题）
    const proxyUrl = '/api/ai/chat'
    
    // 对于思考模型使用更长的超时时间
    const isThinkingModel = modelId.includes('claude-3') || modelId.includes('thinking') || modelId.includes('sonnet')
    const timeoutMs = isThinkingModel ? 600000 : 300000 // 思考模型10分钟，普通模型5分钟
    
    // 获取认证 Token
    const token = localStorage.getItem('yprompt_token')

    const response = await this.fetchWithTimeout(proxyUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: JSON.stringify({
        base_url: this.config.baseUrl.trim(),
        api_key: this.config.apiKey,
        model: modelId,
        messages: formattedMessages,
        stream: stream,
        provider_type: 'anthropic',
        system_message: systemMessage,
        max_tokens: 60000
      })
    }, timeoutMs)

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      const error = new Error(`API error: ${response.status} ${errorData.message || response.statusText}`)
      ;(error as any).error = errorData
      ;(error as any).status = response.status
      throw error
    }

    if (stream) {
      return response.body as ReadableStream<Uint8Array>
    } else {
      const data = await response.json()
      
      // 处理后端代理的响应格式
      const responseData = data.data || data
      const result = responseData.content?.[0]?.text
      
      if (!result || result.trim() === '') {
        throw new Error('API返回空内容')
      }
      
      // 清理think标签内容
      const cleanedResult = ResponseCleaner.cleanThinkTags(result)
      
      return {
        content: cleanedResult,
        finishReason: responseData.stop_reason
      }
    }
  }

  /**
   * 解析 Anthropic 流式响应块
   * @param data SSE 数据字符串
   * @returns 解析后的流式块或 null
   */
  parseStreamChunk(data: string): StreamChunk | null {
    if (!data.trim()) {
      return null
    }

    try {
      const parsed = JSON.parse(data)
      
      if (parsed.type === 'content_block_delta') {
        const content = parsed.delta?.text
        if (content) {
          return {
            content,
            done: false
          }
        }
      } else if (parsed.type === 'message_stop') {
        return {
          content: '',
          done: true
        }
      }
      
      return null
    } catch (e) {
      // JSON解析错误，返回null
      return null
    }
  }

  /**
   * 提取系统消息文本的辅助方法
   * @param messages 消息列表
   * @returns 系统消息文本
   */
  private extractSystemMessageText(messages: ChatMessage[]): string {
    const systemMsg = messages.find(m => m.role === 'system')
    if (!systemMsg) return ''
    if (typeof systemMsg.content === 'string') return systemMsg.content
    if (Array.isArray(systemMsg.content)) {
      // 如果是MessageContent[]，提取所有文本内容
      return systemMsg.content.map(c => c.text || '').join(' ')
    }
    return ''
  }

  /**
   * 检查消息是否包含多模态内容
   * @param message 聊天消息
   * @returns 是否包含附件
   */
  private hasMultimodalContent(message: ChatMessage): boolean {
    return !!(message.attachments && message.attachments.length > 0)
  }

  /**
   * 将消息转换为多模态内容格式
   * @param message 聊天消息
   * @returns 多模态内容数组
   */
  private convertToMultimodalContent(message: ChatMessage): MessageContent[] {
    const content: MessageContent[] = []
    
    // 添加文本内容
    if (typeof message.content === 'string' && message.content.trim()) {
      content.push({ type: 'text', text: message.content })
    }
    
    // 添加附件内容
    if (message.attachments && message.attachments.length > 0) {
      const anthropicAttachments = AnthropicAttachmentHandler.convertAttachments(message.attachments)
      content.push(...anthropicAttachments)
    }
    
    return content
  }
}
