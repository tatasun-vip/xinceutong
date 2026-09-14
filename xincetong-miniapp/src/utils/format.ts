/**
 * utils/format.ts - 格式化工具
 * v11：额度展示从"X.X 万"改为纯元数 + 3 位千分位（50000 → "50,000 元"）
 */

/** 元 -> "12,345"（千分位，不带单位） */
export function formatMoney(yuan: number | string | null | undefined, digits = 0): string {
  if (yuan === null || yuan === undefined || yuan === '') return '0'
  const n = Number(yuan)
  if (Number.isNaN(n)) return '0'
  return n.toFixed(digits).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/**
 * 元 -> "50,000 元"（带千分位 + 元）
 * 用户决策（2026-09-14）：评估额度统一用纯元数展示，3 位千分位 + 元
 */
export function formatYuan(yuan: number | string | null | undefined): string {
  return formatMoney(yuan, 0) + ' 元'
}

/**
 * 元 -> "¥ 50,000"（千分位 + ¥）
 * 卡片标题/重要数字用，¥ 在前
 */
export function formatYuanWithSign(yuan: number | string | null | undefined): string {
  return '¥ ' + formatMoney(yuan, 0)
}

/**
 * 兼容旧调用：formatMoneyWan 直接返回元（不再 /10000 折万）
 * v11 起等效 formatYuan；保留函数名避免全仓批量重命名
 */
export function formatMoneyWan(yuan: number | null | undefined): string {
  return formatYuan(yuan)
}

/**
 * 额度区间 → "50,000~100,000 元"（千分位 + 元）
 * v11 新增：替换原来 /10000 + toFixed + "万" 的拼接
 * @param min 最小额度（元，可为 0）
 * @param max 最大额度（元，可为 0）
 */
export function formatLimit(min?: number, max?: number): string {
  if (!min && !max) return '—'
  const fmt = (n: number) =>
    Math.round(n).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  if (min && max) {
    if (min === max) return `${fmt(min)} 元`
    return `${fmt(min)}~${fmt(max)} 元`
  }
  if (max) return `${fmt(max)} 元`
  return `${fmt(min || 0)} 元`
}

/** 手机号脱敏 138****1234 */
export function maskPhone(phone: string | null | undefined): string {
  if (!phone || phone.length < 11) return phone || ''
  return phone.slice(0, 3) + '****' + phone.slice(-4)
}

/** 姓名脱敏 张* / 张** */
export function maskName(name: string | null | undefined): string {
  if (!name) return ''
  if (name.length === 1) return name
  if (name.length === 2) return name[0] + '*'
  return name[0] + '*'.repeat(name.length - 2) + name.slice(-1)
}

/** 身份证号脱敏（前端只显示后 4 位） */
export function maskIdCard(id: string | null | undefined): string {
  if (!id || id.length < 8) return ''
  return id.slice(0, 4) + '*'.repeat(id.length - 8) + id.slice(-4)
}

/** 日期格式化 */
export function formatDate(d: Date | string | number | null | undefined, withTime = true): string {
  if (!d) return ''
  const date = d instanceof Date ? d : new Date(d)
  const pad = (n: number) => (n < 10 ? '0' + n : '' + n)
  const ymd = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
  if (!withTime) return ymd
  return `${ymd} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

/** 数字补 0 */
export function pad2(n: number): string {
  return n < 10 ? '0' + n : '' + n
}

export default { formatMoney, formatMoneyWan, formatYuan, formatYuanWithSign, formatLimit, maskPhone, maskName, maskIdCard, formatDate, pad2 }
