/**
 * api/legal.ts - 法务 AI 咨询 API 客户端
 */
import http from './request'

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface ChatResult {
  reply: string
  usage: { prompt_tokens: number; completion_tokens: number; total_tokens: number }
  model: string
  latency_ms: number
}

export interface UsageInfo {
  enabled: boolean
  free_limit: number
  message: string
}

export interface Scenario {
  key: string
  title: string
  prompt: string
}

/** 发送聊天（单轮） */
export function legalChat(
  messages: ChatMessage[],
  user_id?: string,
  session_id?: string,
) {
  return http.post<ChatResult>('/api/legal/chat', {
    messages,
    user_id,
    session_id,
  })
}

/** 查询服务状态 + 免费次数提示 */
export function legalUsage() {
  return http.get<UsageInfo>('/api/legal/usage')
}

/** 常见场景快速入口 */
export function legalScenarios() {
  return http.get<Scenario[]>('/api/legal/scenarios')
}

// ============ 本地 quota 管理（localStorage）============

const QUOTA_KEY = 'xinceutong_legal_free_used'
const USER_ID_KEY = 'xinceutong_legal_user_id'

/** 获取或生成 device_id（用于追踪） */
export function getOrCreateUserId(): string {
  let uid = uni.getStorageSync(USER_ID_KEY)
  if (!uid) {
    uid = `u_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    uni.setStorageSync(USER_ID_KEY, uid)
  }
  return uid
}

/** 获取已用免费次数 */
export function getFreeUsed(): number {
  return uni.getStorageSync(QUOTA_KEY) || 0
}

/** 记录用了 1 次免费 */
export function incFreeUsed(): number {
  const n = getFreeUsed() + 1
  uni.setStorageSync(QUOTA_KEY, n)
  return n
}

/** 重置（测试用） */
export function resetFreeUsed() {
  uni.removeStorageSync(QUOTA_KEY)
}
