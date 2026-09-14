<script setup lang="ts">
// App.vue - 应用入口
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { useUserStore } from '@/store/user'

onLaunch(() => {
  console.log('[信测通] App Launch')

  // 系统信息
  try {
    const sys = uni.getSystemInfoSync()
    uni.setStorageSync('systemInfo', sys)
  } catch (e) {
    console.error('getSystemInfoSync 失败', e)
  }

  // 恢复登录态
  const userStore = useUserStore()
  userStore.restoreFromStorage()

  // 解析启动参数
  const launchOptions = uni.getLaunchOptionsSync()
  const query = (launchOptions?.query || {}) as Record<string, string>
  if (query.share_code)     uni.setStorageSync('share_code',     query.share_code)
  if (query.promoter_code)  uni.setStorageSync('promoter_code',  query.promoter_code)
})

onShow((options) => {
  const q = (options?.query || {}) as Record<string, string>
  if (q.share_code)    uni.setStorageSync('share_code',    q.share_code)
  if (q.promoter_code) uni.setStorageSync('promoter_code', q.promoter_code)
})

onHide(() => {
  console.log('[信测通] App Hide')
})
</script>

<style lang="scss">
/* 全局样式（无需 scoped，因为是全局注入） */
@import '@/utils/styles/common.scss';

page {
  background: $bg;
  color: $text-main;
  font-size: $font-md;
  line-height: 1.6;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
}
</style>
