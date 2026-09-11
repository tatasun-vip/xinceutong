/**
 * composables/useShare.ts - 分享配置
 *
 * 用法：
 *   useShare({ title: '...', path: '/pages/...' })
 */
import { onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'

interface ShareOptions {
  title: string
  path: string
  imageUrl?: string
}

export function useShare(opts: ShareOptions): void {
  onShareAppMessage(() => ({
    title: opts.title,
    path: opts.path,
    imageUrl: opts.imageUrl || '',
  }))
  onShareTimeline(() => ({
    title: opts.title,
    query: '',
  }))
}
