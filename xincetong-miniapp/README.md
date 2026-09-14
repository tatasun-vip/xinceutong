# 信测通 · 小程序端（UniApp Vue3 + TypeScript）

> **信用贷模拟评审工具**（不查征信、不碰真实放贷）
>
> 跨端框架：UniApp 3.x + Vue 3 + TypeScript + Vite
> 主战场：微信小程序（同时支持 H5 / App / 支付宝 / 抖音）

## 技术栈

| 维度 | 选型 |
| --- | --- |
| 框架 | UniApp 3.x |
| 视图 | Vue 3 + `<script setup lang="ts">` |
| 语言 | TypeScript 5 |
| 状态 | Pinia 2 |
| UI | uni-ui（官方组件库） |
| 样式 | SCSS（uni.scss 自动注入） |
| 构建 | Vite 5 |
| 请求 | `uni.request` 二次封装（自动 JWT + 401 跳登录） |

## 目录结构

```
xincetong-miniapp/
├── src/
│   ├── pages/                          # 22 个页面
│   │   ├── index/index.vue
│   │   ├── assess/
│   │   │   ├── type.vue
│   │   │   ├── step1-basic.vue
│   │   │   ├── step2-career.vue
│   │   │   ├── step3-asset.vue
│   │   │   ├── step4-credit.vue
│   │   │   ├── step5-confirm.vue
│   │   │   └── loading.vue
│   │   ├── result/
│   │   │   ├── free.vue
│   │   │   ├── pay.vue
│   │   │   └── report.vue
│   │   ├── share/index.vue
│   │   ├── mine/
│   │   │   ├── index.vue
│   │   │   └── history.vue
│   │   └── promoter/
│   │       ├── login.vue
│   │       ├── dashboard.vue
│   │       ├── tools.vue
│   │       ├── price.vue
│   │       ├── customers.vue
│   │       ├── customer-detail.vue
│   │       ├── commission.vue
│   │       └── withdraw.vue
│   ├── components/                     # 5 个自定义组件
│   │   ├── compliance-bar/ComplianceBar.vue   # 顶部合规条（每个页面必挂）
│   │   ├── progress-bar/ProgressBar.vue
│   │   ├── option-card/OptionCard.vue
│   │   ├── risk-tag/RiskTag.vue
│   │   └── report-card/ReportCard.vue
│   ├── composables/                    # Vue3 组合式函数
│   │   ├── useShare.ts
│   │   └── useShareCode.ts
│   ├── api/                            # 业务接口（TypeScript）
│   │   ├── request.ts                  # 统一封装
│   │   ├── auth.ts
│   │   ├── assessment.ts
│   │   ├── order.ts
│   │   ├── promoter.ts
│   │   ├── share.ts
│   │   └── index.ts
│   ├── store/                          # Pinia
│   │   ├── user.ts
│   │   ├── assessment.ts
│   │   ├── promoter.ts
│   │   └── index.ts
│   ├── utils/
│   │   ├── format.ts                   # 金额/脱敏
│   │   ├── storage.ts                  # 跨端存储
│   │   ├── track.ts                    # 埋点
│   │   └── styles/common.scss          # 全局样式
│   ├── types/
│   │   └── index.ts                    # TS 类型定义
│   ├── static/                         # 静态资源
│   ├── App.vue
│   ├── main.ts
│   ├── pages.json                      # 路由 + 全局配置
│   ├── manifest.json                   # 应用配置（vueVersion: "3"）
│   └── uni.scss                        # 全局 SCSS 变量
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .env.development
├── .env.production
├── .env.example
└── README.md
```

## 品牌色 / 设计变量（uni.scss）

```scss
$primary: #1B3A6B;       // 主色 - 深蓝
$accent:  #C9A96E;       // 强调色 - 金色
$bg:      #F5F6FA;       // 页面背景
$card:    #FFFFFF;       // 卡片背景
$text-main: #1A1A1A;     // 主文字
$radius-card: 24rpx;
$btn-height:  104rpx;
```

页面/组件中可直接使用。

## 顶部合规条

**所有页面必须挂载** `<ComplianceBar />`（PascalCase + 显式 import）：

```vue
<template>
  <view class="page">
    <ComplianceBar />
    <!-- 页面内容 -->
  </view>
</template>

<script setup lang="ts">
import ComplianceBar from '@/components/compliance-bar/ComplianceBar.vue'
</script>
```

## 快速开始

```bash
cd xincetong-miniapp
npm install

# 微信小程序（主战场）
npm run dev:mp-weixin
# 打开微信开发者工具，导入 unpackage/dist/dev/mp-weixin

# H5
npm run dev:h5
# 访问 http://localhost:8080

# 类型检查
npm run type-check
```

修改 `src/manifest.json` 的 `mp-weixin.appid` 为你自己的小程序 AppID。
修改 `.env.development` / `.env.production` 的 `VITE_API_BASE_URL` 指向后端。

## 接口约定

所有接口统一返回：

```json
{ "code": 0, "message": "success", "data": {...} }
```

`code = 0` 成功；`code != 0` 失败，`message` 为错误提示（前端自动弹 toast）。
`statusCode = 401` 自动登出 + 跳首页。

```ts
import { assessmentApi } from '@/api'
const res = await assessmentApi.submitAssessment({ type: 'personal', input_data: {...} })
```

## 跨端说明

| 目标 | 命令 | 输出 |
| --- | --- | --- |
| 微信小程序 | `npm run dev:mp-weixin` | `unpackage/dist/dev/mp-weixin` |
| H5 | `npm run dev:h5` | 浏览器 |
| App | `npm run dev:app` | HBuilderX 真机 |
| 支付宝小程序 | `npm run dev:mp-alipay` | 待 HBuilderX 支持 |
| 抖音小程序 | `npm run dev:mp-toutiao` | 待 HBuilderX 支持 |

跨端差异用条件编译包裹：

```ts
// #ifdef MP-WEIXIN
uni.requestPayment({ provider: 'wxpay', ... })
// #endif

// #ifdef H5
window.location.href = '...'
// #endif
```

## 阶段 2-8 UniApp 对齐说明

| 阶段 | 前端部分改动 | 状态 |
| --- | --- | --- |
| 2 | 仅后端评分卡，不涉及前端。**接口返回统一格式** `{code, message, data}` | ✅ |
| 3 | 5 步填写用 `OptionCard` + 顶部 `ProgressBar` + 底部 `btn-primary` + `env(safe-area-inset-bottom)`。每步 `watch` + 调用 `assessmentApi.validateAssessment()` 做实时纠错，提示用 `warning-card` 样式。评估动画用 CSS 动画。**数据存 Pinia + 自动恢复**。 | ✅ 已交付（2698 行，详见 `STAGE-3.md`） |
| 4 | 微信登录用 `uni.login({ provider: 'weixin' })` 走 `#ifdef MP-WEIXIN`。支付用 `uni.requestPayment({ provider: 'wxpay', ... })`。支付成功用 `uni.redirectTo` 跳报告页。报告页 `report-card` 列表 + 底部固定免责。 | ⏳ |
| 5 | 海报后端生成（PIL），前端只展示和 `uni.saveImageToPhotosAlbum`。分享路径带 `share_code`，新用户自动识别。`onShareAppMessage` + `onShareTimeline` 配 `useShare()` composable。 | ⏳ |
| 6 | 推广员用 `uqrcodejs` 生成二维码。客户列表用 `scroll-view` + 下拉刷新 + 上拉加载。客户详情用 `RiskTag`。提现滑块范围 6.99-19.99。推广员入口用角色区分。 | ⏳ |
| 7 | 管理后台 **建议 Web 端**（Vue3 + Element Plus），独立 `xincetong-admin/` 项目 | ⏳ |
| 8 | 协议/政策用 `rich-text` 展示。首次进入弹窗同意。删除数据用 `authApi.deleteUserData()`。微信公众平台后台配 `requiredPrivateInfos`。 | ⏳ |

## 注意事项

- ⚠️ 评分/额度/利率文案必须带"模拟"字样
- ⚠️ 报告页底部固定免责声明
- ⚠️ 顶部合规条禁止删除
- ⚠️ 不收身份证号、银行卡号、人脸、征信账号密码
- ⚠️ 金额字段后端用 `INT(分)` 或 `DECIMAL(元)`，前端展示用 `formatMoney()`
- ⚠️ 跨端用 `uni.*` API，不用平台原生
- ⚠️ 所有 Pinia store 用 `uni.setStorageSync` 持久化
- ⚠️ 所有页面用 `<script setup lang="ts">`
