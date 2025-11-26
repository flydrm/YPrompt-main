import { BaseProvider } from './BaseProvider'
import type { ChatMessage, AIResponse, StreamChunk, MessageContent } from '../types'
import { OpenAIAttachmentHandler } from '../multimodal/OpenAIAttachmentHandler'
import { ResponseCleaner } from '../utils/ResponseCleaner'

/**
 * OpenAI API 提供商实现
 * 支持 GPT 系列模型和多模态内容
 * 
 * 默认通过后端代理调用，避免 CORS 跨域问题
 */
export class OpenAIProvider extends BaseProvider {
  /**
   * 调用 OpenAI API（通过后端代理，解决 CORS 问题）
   * @param messages 聊天消息列表
   * @param stream 是否使用流式响应
   * @returns Promise<AIResponse | ReadableStream<Uint8Array>>
   */
  async callAPI(messages: ChatMessage[], stream: boolean): Promise<AIResponse | ReadableStream<Uint8Array>> {
    if (!this.config.baseUrl) {
      throw new Error('API URL 未配置')
    }
    
    const modelId = this.modelId
    
    // 构建消息列表
    const formattedMessages = messages.map(msg => {
      if (this.hasMultimodalContent(msg)) {
        const multimodalContent = this.convertToMultimodalContent(msg)
        return {
          role: msg.role,
          content: multimodalContent
        }
      } else {
        return {
          role: msg.role,
          content: typeof msg.content === 'string' ? msg.content : msg.content[0]?.text || ''
        }
      }
    })
    
    // 通过后端代理调用（解决 CORS 问题）
    const proxyUrl = '/api/ai/chat'
    
    // 对于思考模型（如gpt-5-high）使用更长的超时时间
    const isThinkingModel = modelId.includes('gpt-5') || modelId.includes('o1') || modelId.includes('thinking')
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
        provider_type: 'openai',
        temperature: 0.7,
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
      
      // 支持多种API响应格式的内容提取
      let result: string | undefined
      
      if (responseData.choices && responseData.choices[0]?.message?.content) {
        // OpenAI 格式: {choices: [{message: {content: "text"}}]}
        result = responseData.choices[0].message.content
      } else if (responseData.candidates && responseData.candidates[0]?.content?.parts) {
        // Gemini 格式: {candidates: [{content: {parts: [{text: "text"}]}}]}
        const parts = responseData.candidates[0].content.parts
        // 查找包含text的部分（过滤掉thought等）
        for (const part of parts) {
          if (part.text && !part.thought) {
            result = part.text
            break
          }
        }
      } else if (responseData.content && typeof responseData.content === 'string') {
        // 直接返回内容格式
        result = responseData.content
      } else if (responseData.text && typeof responseData.text === 'string') {
        // 简单文本格式
        result = responseData.text
      }
      
      if (!result || result.trim() === '') {
        throw new Error('API返回空内容或无法解析响应格式')
      }
      
      // 清理响应内容
      result = ResponseCleaner.cleanResponse(result)
      result = ResponseCleaner.cleanThinkTags(result)
      
      return {
        content: result,
        finishReason: responseData.choices?.[0]?.finish_reason
      }
    }
  }

  /**
   * 解析 OpenAI 流式响应块
   * @param data SSE 数据字符串
   * @returns 解析后的流式块或 null
   */
  parseStreamChunk(data: string): StreamChunk | null {
    if (!data.trim() || data.trim() === '[DONE]') {
      return { content: '', done: true }
    }
    
    // 专门过滤OPENROUTER的处理状态信息
    if (data === ': OPENROUTER PROCESSING') {
      return null
    }
    
    // 过滤其他明显的状态信息（更保守的方法）
    if (data.startsWith(': ') && data.toUpperCase().includes('PROCESSING')) {
      return null
    }
    
    try {
      const parsed = JSON.parse(data)
      let content: string | undefined
      
      // 支持多种流式响应格式
      if (parsed.choices?.[0]?.delta?.content) {
        // OpenAI 流式格式
        content = parsed.choices[0].delta.content
      } else if (parsed.candidates?.[0]?.content?.parts) {
        // Gemini SSE 流式格式
        const parts = parsed.candidates[0].content.parts
        for (const part of parts) {
          if (part.text && !part.thought) {
            content = part.text
            break
          }
        }
      } else if (parsed.delta?.text) {
        // 简化流式格式
        content = parsed.delta.text
      } else if (parsed.text) {
        // 直接文本格式
        content = parsed.text
      }
      
      const finishReason = parsed.choices?.[0]?.finish_reason
      const done = !!(finishReason || parsed.done)
      
      return {
        content: content || '',
        done
      }
    } catch (e) {
      // JSON解析错误，返回null
      return null
    }
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
      const openaiAttachments = OpenAIAttachmentHandler.convertAttachments(message.attachments)
      content.push(...openaiAttachments)
    }
    
    return content
  }
}
