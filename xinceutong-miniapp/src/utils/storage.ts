/**
 * utils/storage.ts - 跨端存储封装
 */

export function setStorage(key: string, value: unknown): void {
  try {
    uni.setStorageSync(key, value)
  } catch (e) {
    console.error(`storage.set ${key} 失败`, e)
  }
}

export function getStorage<T = unknown>(key: string, defaultValue?: T): T | undefined {
  try {
    const v = uni.getStorageSync(key)
    if (v === '' || v === undefined || v === null) return defaultValue
    return v as T
  } catch {
    return defaultValue
  }
}

export function removeStorage(key: string): void {
  try { uni.removeStorageSync(key) } catch { /* ignore */ }
}

export function clearStorage(): void {
  try { uni.clearStorageSync() } catch { /* ignore */ }
}
