<!--
  Mine / 我的 - 信测通个人中心
  v3.4 (2026-09-11): 重写
    1. tabBar 页面：移除"返回"按钮（tabBar 上 navigateBack 永远无效）
    2. 完整模块：用户卡 / 数据条 / 功能网格 / 推广员状态 / 关于 / 退出
    3. 沿用 v3.2 编辑感设计：硬边 / 细线 / 8rpx 网格 / 大留白
-->
<template>
  <view class="mine page-bg">
    <ComplianceBar />

    <!-- ========== 1. 用户卡（深海军蓝 + 金线）========== -->
    <view class="user-card">
      <view class="user-card-line" />
      <view class="user-row">
        <view class="user-avatar">
          <text v-if="!userInfo?.avatar" class="user-avatar-text">
            {{ avatarText }}
          </text>
        </view>
        <view class="user-info">
          <view class="user-name-row">
            <text class="user-name">{{ displayName }}</text>
            <text v-if="roleLabel" class="user-role">{{ roleLabel }}</text>
          </view>
          <text class="user-phone">{{ displayPhone }}</text>
        </view>
      </view>
      <view class="user-card-rule" />
      <view class="user-uid-row">
        <text class="user-uid-label">USER ID</text>
        <text class="user-uid">{{ uidDisplay }}</text>
      </view>
    </view>

    <!-- ========== 2. 数据条 ========== -->
    <view class="stats-strip">
      <view class="ss-item" @tap="goHistory">
        <text class="ss-num">{{ totalCount }}</text>
        <text class="ss-rule" />
        <text class="ss-label">测评次数</text>
      </view>
      <view class="ss-item ss-item-mid" @tap="goHistory">
        <text class="ss-num">{{ paidCount }}</text>
        <text class="ss-rule" />
        <text class="ss-label">已解锁报告</text>
      </view>
      <view class="ss-item" @tap="goPromoter">
        <text class="ss-num">{{ shareCount }}</text>
        <text class="ss-rule" />
        <text class="ss-label">分享次数</text>
      </view>
    </view>

    <!-- ========== 3. 推广员状态卡（条件渲染）========== -->
    <view v-if="isPromoter && promoterInfo" class="promoter-card" @tap="goPromoter">
      <view class="pc-head">
        <text class="pc-eyebrow">PROMOTER STATUS</text>
        <text class="pc-status" :class="`is-${promoterInfo.status}`">
          {{ promoterStatusText }}
        </text>
      </view>
      <view class="pc-row">
        <view class="pc-item">
          <text class="pc-num">{{ formatYuanWithSign(promoterInfo.balance ?? 0) }}</text>
          <text class="pc-label">可提现佣金</text>
        </view>
        <view class="pc-divider" />
        <view class="pc-item">
          <text class="pc-num">{{ formatYuanWithSign(promoterInfo.total_earnings ?? 0) }}</text>
          <text class="pc-label">累计收益</text>
        </view>
      </view>
      <view class="pc-cta">
        <text>进入推广员工作台</text>
        <text class="pc-arrow">›</text>
      </view>
    </view>
    <view v-else class="promoter-cta" @tap="goPromoterApply">
      <view class="pcta-text">
        <text class="pcta-title">成为推广员</text>
        <text class="pcta-sub">分享专属链接，每单最高 50% 分佣</text>
      </view>
      <view class="pcta-btn">立即入驻</view>
    </view>

    <!-- ========== 4. 功能网格（2×3）========== -->
    <view class="grid">
      <view
        v-for="(it, i) in gridItems"
        :key="it.key"
        class="grid-item"
        @tap="handleGrid(it)"
      >
        <view class="grid-icon">
          <UiIcon :name="it.icon" :size="44" :color="it.color" />
        </view>
        <text class="grid-label">{{ it.label }}</text>
        <text v-if="it.sub" class="grid-sub">{{ it.sub }}</text>
      </view>
    </view>

    <!-- ========== 5. 其他列表（左右滑动 + 右箭头）========== -->
    <view class="menu">
      <view
        v-for="(m, i) in menuItems"
        :key="m.key"
        class="menu-item"
        :class="{ 'is-last': i === menuItems.length - 1 }"
        @tap="handleMenu(m)"
      >
        <view class="menu-icon">
          <UiIcon :name="m.icon" :size="36" :color="m.color || '#5A6473'" />
        </view>
        <text class="menu-text">{{ m.text }}</text>
        <text v-if="m.badge" class="menu-badge">{{ m.badge }}</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- ========== 6. 退出登录（仅已登录显示）========== -->
    <view v-if="isLogin" class="logout-bar" @tap="handleLogout">
      <text class="logout-text">退出登录</text>
    </view>

    <!-- ========== 7. 底部版本信息 ========== -->
    <view class="version">
      <text class="version-line">{{ siteStore.brandName }}</text>
      <text class="version-sub">v3.4 · 模拟测评 · 非银行官方</text>
    </view>

    <!-- tabBar 安全区占位（避免被底部 tabBar 遮挡）-->
    <view class="tabbar-safe" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
import UiIcon from '@/components/ui-icon/ui-icon.vue'
import { useUserStore } from '@/store/user'
import { usePromoterStore } from '@/store/promoter'
import { useAssessmentStore } from '@/store/assessment'
import { useSiteStore } from '@/store/site'
import { formatYuanWithSign, maskPhone } from '@/utils/format'
import { pageView, track } from '@/utils/track'
import { getStorage } from '@/utils/storage'

const userStore     = useUserStore()
const promoterStore = usePromoterStore()
const assessStore   = useAssessmentStore()
const siteStore     = useSiteStore()

const userInfo      = computed(() => userStore.userInfo)
const isLogin       = computed(() => userStore.isLogin)
const isPromoter    = computed(() => userStore.isPromoter())
const promoterInfo  = computed(() => promoterStore.info)
const totalCount    = computed(() => assessStore.totalCount)
const paidCount     = computed(() => assessStore.paidCount)

// 分享次数（本地粗略统计：取历史记录 + 推广码触发次数）
const shareCount = ref(0)
function loadShareCount() {
  const c = getStorage<number>('share_count', 0) ?? 0
  shareCount.value = c
}

onShow(() => {
  pageView('mine/index')
  loadShareCount()
  // 同步历史（其他页面可能新增了记录）
  assessStore.restoreFromStorage()
})

// ============ 用户展示字段 ============
const avatarText = computed(() => {
  const n = userInfo.value?.nickname
  if (n) return n.slice(0, 1)
  const p = userInfo.value?.openid
  return p ? p.slice(-2) : '客'
})

const displayName = computed(() => {
  if (userInfo.value?.nickname) return userInfo.value.nickname
  if (userInfo.value?.openid)   return '信测通用户'
  return '未登录'
})

const displayPhone = computed(() => {
  const phone = (userInfo.value as any)?.phone || ''
  if (phone) return maskPhone(phone)
  if (userInfo.value?.openid) return `ID · ${userInfo.value.openid.slice(-6)}`
  return '登录后可同步历史记录'
})

const uidDisplay = computed(() => {
  if (userInfo.value?.id) return `#${String(userInfo.value.id).padStart(6, '0')}`
  return '#000000'
})

const roleLabel = computed(() => {
  if (userStore.isAdmin())    return '管理员'
  if (userStore.isPromoter()) return '推广员'
  return ''
})

const promoterStatusText = computed(() => {
  const s = promoterInfo.value?.status
  if (s === 'approved') return '已认证'
  if (s === 'pending')  return '审核中'
  if (s === 'rejected') return '已拒绝'
  if (s === 'banned')   return '已封禁'
  return '未入驻'
})

// ============ 网格入口（2×3）============
type IconName =
  | 'check' | 'bank' | 'chart' | 'lock' | 'shield' | 'handshake' | 'star'
  | 'arrow-right' | 'arrow-down' | 'arrow-up' | 'arrow-left' | 'doc' | 'wallet'
  | 'clock' | 'bell' | 'list' | 'info' | 'user' | 'history' | 'settings'
  | 'phone' | 'share' | 'exit' | 'promoter' | 'legal' | 'service' | 'about'
  | 'link' | 'eye' | 'gift' | 'close' | 'check-circle' | 'warning'

interface GridItem {
  key: string
  icon: IconName
  label: string
  sub?: string
  color: string
  action: () => void
}
const gridItems = computed<GridItem[]>(() => [
  {
    key: 'assess', icon: 'chart', label: '立即测评',
    sub: '6 大产品独立测算', color: '#0B2545',
    action: () => uni.switchTab({ url: '/pages/assess/type' }),
  },
  {
    key: 'history', icon: 'history', label: '测评历史',
    sub: totalCount.value > 0 ? `共 ${totalCount.value} 次` : '暂无记录',
    color: '#0B2545', action: goHistory,
  },
  {
    key: 'share', icon: 'share', label: '分享应用',
    sub: '邀请好友 / 获得报告', color: '#B89554',
    action: goShare,
  },
  {
    key: 'promoter', icon: 'promoter', label: '推广中心',
    sub: isPromoter.value ? '查看收益' : '0 门槛入驻', color: '#2C7A4B',
    action: goPromoter,
  },
  {
    key: 'legal', icon: 'legal', label: '法务咨询',
    sub: '专业律师在线答疑', color: '#0B2545',
    action: () => uni.navigateTo({ url: '/pages/legal/index' }),
  },
  {
    key: 'service', icon: 'service', label: '联系客服',
    sub: '工作日 9:00-18:00', color: '#5A6473',
    action: contactService,
  },
])

// ============ 列表入口 ============
interface MenuItem {
  key: string
  icon: IconName
  text: string
  badge?: string
  color?: string
  action: () => void
}
const menuItems: MenuItem[] = [
  { key: 'method', icon: 'about',   text: '我们的方法论',     color: '#0B2545', action: () => uni.navigateTo({ url: '/pages/about/methodology' }) },
  { key: 'legal',  icon: 'eye',     text: '隐私与协议',       color: '#0B2545', action: () => uni.navigateTo({ url: '/pages/legal/index' }) },
  { key: 'clear',  icon: 'close',   text: '清除本地缓存',     color: '#9B2226', action: handleClearCache },
  { key: 'about',  icon: 'info',    text: '关于信测通',       color: '#5A6473', action: handleAbout },
]

// ============ 动作 ============
function goHistory() {
  uni.navigateTo({ url: '/pages/mine/history' })
}
function goShare() {
  uni.navigateTo({ url: '/pages/share/index' })
}
function goPromoter() {
  if (isPromoter.value) {
    uni.navigateTo({ url: '/pages/promoter/dashboard' })
  } else {
    uni.navigateTo({ url: '/pages/promoter/login' })
  }
}
function goPromoterApply() {
  uni.navigateTo({ url: '/pages/promoter/login' })
}
function contactService() {
  uni.showModal({
    title: '联系客服',
    content: '客服微信：xincetong-cs\n工作时间：工作日 9:00-18:00',
    showCancel: false,
    confirmText: '我知道了',
  })
}
function handleClearCache() {
  uni.showModal({
    title: '清除本地缓存',
    content: '将删除测评历史和草稿数据，未同步到云端的记录将丢失。是否继续？',
    success: (res) => {
      if (!res.confirm) return
      assessStore.clearHistory()
      assessStore.reset()
      uni.showToast({ title: '已清除', icon: 'success' })
      track({ event: 'button_click', page: 'mine/index', data: { action: 'clear_cache' } })
    },
  })
}
function handleAbout() {
  uni.showModal({
    title: '关于信测通',
    content: `${siteStore.brandName}\n${siteStore.brandSubtitle}\n\nv3.4 · 阶段 3 验收完成\n模拟测评 · 非银行官方 · 不查征信`,
    showCancel: false,
    confirmText: '我知道了',
  })
}
function handleLogout() {
  uni.showModal({
    title: '退出登录',
    content: '退出后历史记录仍保留在本地，但不会同步到云端',
    success: (res) => {
      if (!res.confirm) return
      userStore.logout()
      uni.showToast({ title: '已退出', icon: 'none' })
      track({ event: 'button_click', page: 'mine/index', data: { action: 'logout' } })
    },
  })
}
function handleGrid(it: GridItem) {
  track({ event: 'button_click', page: 'mine/index', data: { grid: it.key } })
  it.action()
}
function handleMenu(m: MenuItem) {
  track({ event: 'button_click', page: 'mine/index', data: { menu: m.key } })
  m.action()
}
</script>

<style lang="scss" scoped>
/* =========================================================================
   设计 token（沿用 v3.2 编辑感）
   8rpx 网格：4/8/16/24/32/48/64
   唯一品牌色：$primary（深蓝）+ $accent（金）
   ========================================================================= */
.mine {
  min-height: 100vh;
  background: $bg;
  padding-bottom: 32rpx;
}

/* ========== 1. 用户卡 ========== */
.user-card {
  background: $primary;
  margin: 0 32rpx;
  padding: 48rpx 40rpx 40rpx;
  position: relative;
  border-left: 4rpx solid $accent;
}
.user-card-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 96rpx;
  height: 2rpx;
  background: $accent;
}
.user-row {
  display: flex;
  align-items: center;
  gap: 24rpx;
}
.user-avatar {
  width: 112rpx;
  height: 112rpx;
  border-radius: 0;
  background: rgba(255, 255, 255, 0.08);
  border: 1rpx solid rgba(184, 149, 84, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.user-avatar-text {
  font-family: $ff-serif;
  font-size: 48rpx;
  font-weight: 600;
  color: $accent;
  letter-spacing: 0;
  line-height: 1;
}
.user-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;
}
.user-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
}
.user-name {
  font-family: $ff-serif;
  font-size: 36rpx;
  font-weight: 700;
  color: $text-white;
  letter-spacing: 1rpx;
  line-height: 1.2;
}
.user-role {
  font-family: $ff-mono;
  font-size: 20rpx;
  color: $accent;
  letter-spacing: 2rpx;
  padding: 4rpx 12rpx;
  border: 1rpx solid $accent;
  font-weight: 500;
}
.user-phone {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.65);
  letter-spacing: 0.5rpx;
  font-family: $ff-mono;
}
.user-card-rule {
  width: 48rpx;
  height: 1rpx;
  background: rgba(184, 149, 84, 0.4);
  margin: 32rpx 0 16rpx;
}
.user-uid-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.user-uid-label {
  font-family: $ff-mono;
  font-size: 20rpx;
  color: rgba(184, 149, 84, 0.7);
  letter-spacing: 4rpx;
  font-weight: 500;
}
.user-uid {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 1rpx;
}

/* ========== 2. 数据条 ========== */
.stats-strip {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  background: $card;
  margin: 32rpx 32rpx 0;
  border-top: 1rpx solid $border-light;
  border-bottom: 1rpx solid $border-light;
}
.ss-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 32rpx 24rpx;
  border-right: 1rpx solid $border-light;
  &:last-child { border-right: none; }
  &.ss-item-mid { padding-left: 16rpx; }
}
.ss-num {
  font-family: $ff-serif;
  font-size: 48rpx;
  font-weight: 600;
  color: $primary;
  letter-spacing: 0.5rpx;
  line-height: 1;
  font-feature-settings: 'tnum' 1;
  font-variant-numeric: tabular-nums;
}
.ss-rule {
  width: 32rpx;
  height: 1rpx;
  background: $accent;
  margin: 16rpx 0;
}
.ss-label {
  font-size: 24rpx;
  color: $text-sub;
  letter-spacing: 1rpx;
  line-height: 1.4;
}

/* ========== 3. 推广员卡 ========== */
.promoter-card {
  background: $card;
  margin: 32rpx 32rpx 0;
  padding: 32rpx 32rpx 0;
  border-left: 4rpx solid $success;
}
.pc-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 24rpx;
  border-bottom: 1rpx solid $border-light;
}
.pc-eyebrow {
  font-family: $ff-mono;
  font-size: 22rpx;
  color: $accent;
  letter-spacing: 4rpx;
  font-weight: 500;
}
.pc-status {
  font-family: $ff-mono;
  font-size: 22rpx;
  letter-spacing: 2rpx;
  padding: 4rpx 12rpx;
  border: 1rpx solid currentColor;
  &.is-approved { color: $success; }
  &.is-pending  { color: $warning; }
  &.is-rejected { color: $danger; }
  &.is-banned   { color: $danger; }
}
.pc-row {
  display: flex;
  align-items: center;
  padding: 32rpx 0;
}
.pc-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.pc-num {
  font-family: $ff-serif;
  font-size: 36rpx;
  font-weight: 600;
  color: $primary;
  letter-spacing: 0.5rpx;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.pc-label {
  font-size: 22rpx;
  color: $text-sub;
  letter-spacing: 1rpx;
}
.pc-divider {
  width: 1rpx;
  height: 48rpx;
  background: $border-light;
  margin: 0 24rpx;
}
.pc-cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 0;
  border-top: 1rpx solid $border-light;
  margin: 0 -32rpx;
  padding-left: 32rpx;
  padding-right: 32rpx;
  font-size: 26rpx;
  color: $primary;
  letter-spacing: 1rpx;
}
.pc-arrow {
  color: $primary;
  font-size: 28rpx;
  line-height: 1;
}

.promoter-cta {
  background: $card;
  margin: 32rpx 32rpx 0;
  padding: 32rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-left: 4rpx solid $accent;
}
.pcta-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  min-width: 0;
}
.pcta-title {
  font-family: $ff-serif;
  font-size: 30rpx;
  font-weight: 600;
  color: $primary;
  letter-spacing: 1rpx;
}
.pcta-sub {
  font-size: 22rpx;
  color: $text-sub;
  letter-spacing: 0.5rpx;
}
.pcta-btn {
  font-size: 24rpx;
  color: $accent;
  letter-spacing: 2rpx;
  padding: 12rpx 24rpx;
  border: 1rpx solid $accent;
  font-family: $ff-mono;
  font-weight: 500;
  flex-shrink: 0;
}

/* ========== 4. 功能网格 ========== */
.grid {
  background: $card;
  margin: 32rpx 32rpx 0;
  padding: 16rpx 0;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
}
.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  padding: 24rpx 16rpx;
  border-right: 1rpx solid $border-light;
  border-bottom: 1rpx solid $border-light;
  &:nth-child(3n) { border-right: none; }
  &:nth-last-child(-n+3) { border-bottom: none; }
}
.grid-icon {
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 4rpx;
}
.grid-label {
  font-size: 26rpx;
  color: $primary;
  letter-spacing: 1rpx;
  font-weight: 500;
}
.grid-sub {
  font-size: 20rpx;
  color: $text-weak;
  letter-spacing: 0.5rpx;
  text-align: center;
  line-height: 1.3;
}

/* ========== 5. 列表入口 ========== */
.menu {
  background: $card;
  margin: 32rpx 32rpx 0;
  padding: 0 32rpx;
}
.menu-item {
  display: flex;
  align-items: center;
  padding: 32rpx 0;
  border-bottom: 1rpx solid $border-light;
  &.is-last { border-bottom: none; }
}
.menu-icon {
  width: 48rpx;
  height: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-right: 16rpx;
}
.menu-text {
  flex: 1;
  font-size: 28rpx;
  color: $text-main;
  letter-spacing: 0.5rpx;
}
.menu-badge {
  font-size: 20rpx;
  color: $text-weak;
  letter-spacing: 1rpx;
  margin-right: 8rpx;
  font-family: $ff-mono;
}
.menu-arrow {
  color: $text-weak;
  font-size: 32rpx;
  line-height: 1;
}

/* ========== 6. 退出登录 ========== */
.logout-bar {
  background: $card;
  margin: 32rpx 32rpx 0;
  padding: 32rpx;
  text-align: center;
}
.logout-text {
  font-size: 28rpx;
  color: $danger;
  letter-spacing: 4rpx;
  font-weight: 500;
}

/* ========== 7. 版本信息 ========== */
.version {
  margin: 48rpx 0 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}
.version-line {
  font-family: $ff-serif;
  font-size: 22rpx;
  color: $text-weak;
  letter-spacing: 4rpx;
  font-weight: 500;
}
.version-sub {
  font-size: 20rpx;
  color: $text-weak;
  letter-spacing: 1rpx;
  font-family: $ff-mono;
}

/* tabBar 安全区 */
.tabbar-safe {
  height: 64rpx;
}
</style>
