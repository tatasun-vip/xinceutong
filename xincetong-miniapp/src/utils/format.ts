/**
 * utils/format.ts - 格式化工具
 */

/** 元 -> "12,345.00" */
export function formatMoney(yuan: number | string | null | undefined, digits = 2): string {
  if (yuan === null || yuan === undefined || yuan === '') return '0.00'
  const n = Number(yuan)
  if (Number.isNaN(n)) return '0.00'
  return n.toFixed(digits).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

/** 元 -> "12.3 万" */
export function formatMoneyWan(yuan: number | null | undefined): string {
  const n = Number(yuan || 0)
  if (n < 10000) return formatMoney(n) + ' 元'
  return (n / 10000).toFixed(1) + ' 万'
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

export default { formatMoney, formatMoneyWan, maskPhone, maskName, maskIdCard, formatDate, pad2 }
