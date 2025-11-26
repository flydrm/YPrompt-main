/**
 * API URL构建工具
 */

/**
 * 构建OpenAI聊天API URL
 * 
 * 规则：
 * - 如果 URL 已包含 /chat/completions，直接使用
 * - 如果 URL 以 / 结尾（如 https://b.xyz/），拼接 chat/completions
 * - 如果 URL 不以 / 结尾（如 https://a.com），拼接 /v1/chat/completions
 */
export function buildOpenAIChatUrl(baseUrl: string): string {
  if (!baseUrl) {
    throw new Error('API URL 未配置')
  }

  const apiUrl = baseUrl.trim()

  // 已包含 /chat/completions，直接使用
  if (apiUrl.includes('/chat/completions')) {
    return apiUrl
  }

  // 根据末尾是否有 / 判断是否需要拼接 /v1
  if (apiUrl.endsWith('/')) {
    return `${apiUrl}chat/completions`
  } else {
    return `${apiUrl}/v1/chat/completions`
  }
}

/**
 * 构建OpenAI模型列表URL
 * 
 * 规则：
 * - 如果 URL 已包含 /models，直接使用
 * - 如果 URL 以 / 结尾（如 https://b.xyz/），拼接 models
 * - 如果 URL 不以 / 结尾（如 https://a.com），拼接 /v1/models
 */
export function buildOpenAIModelsUrl(baseUrl: string): string {
  if (!baseUrl) {
    throw new Error('API URL 未配置')
  }

  const apiUrl = baseUrl.trim()

  // 已包含 /models，直接使用
  if (apiUrl.endsWith('/models') || apiUrl.includes('/models?') || apiUrl.includes('/models/')) {
    return apiUrl
  }

  // 根据末尾是否有 / 判断是否需要拼接 /v1
  if (apiUrl.endsWith('/')) {
    return `${apiUrl}models`
  } else {
    return `${apiUrl}/v1/models`
  }
}

/**
 * 构建Anthropic消息API URL
 */
export function buildAnthropicMessagesUrl(baseUrl: string): string {
  if (!baseUrl) {
    throw new Error('API URL 未配置')
  }

  let apiUrl = baseUrl.trim()
  if (!apiUrl.includes('/v1/messages')) {
    apiUrl = apiUrl.replace(/\/+$/, '') + '/v1/messages'
  }
  return apiUrl
}

/**
 * 构建Gemini API URL
 */
export function buildGeminiUrl(baseUrl: string, modelId: string, action: 'generateContent' | 'streamGenerateContent'): string {
  if (!baseUrl) {
    throw new Error('API URL 未配置')
  }

  let apiUrl = baseUrl.trim()

  // 确保以/v1beta结尾
  if (!apiUrl.endsWith('/v1beta')) {
    if (apiUrl.includes('/models/')) {
      apiUrl = apiUrl.split('/models/')[0]
    }
    if (!apiUrl.endsWith('/v1beta')) {
      apiUrl = apiUrl.replace(/\/+$/, '') + '/v1beta'
    }
  }

  return `${apiUrl}/models/${modelId}:${action}`
}

/**
 * 构建Gemini模型列表URL
 */
export function buildGeminiModelsUrl(baseUrl: string): string {
  if (!baseUrl) {
    throw new Error('API URL 未配置')
  }

  let apiUrl = baseUrl.trim()

  if (apiUrl.includes('/models')) {
    return apiUrl
  } else if (apiUrl.includes('/v1beta')) {
    return apiUrl.replace(/\/+$/, '') + '/models'
  } else {
    return apiUrl.replace(/\/+$/, '') + '/v1beta/models'
  }
}
