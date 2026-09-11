# 阶段 3 · 设计改造验收清单

> **金融合规类严肃风** — 告别 emoji，深海军蓝 + 金融金 + 衬线大标题
>
> 时间：2026-09-10  ~1 小时 ·  改动：**16 个文件** ·  H5 验证：20/20 资源 200 ✅

---

## 🎯 核心改造

| 维度 | 之前（玩具风） | 之后（金融合规风） |
| --- | --- | --- |
| **图标** | 50+ 个 emoji 装饰（🧑 🏢 📅 🎓 💼 🚗 💳 ⚠️ 等） | 0 emoji，用编号 + 衬线文字 + SVG 几何 |
| **品牌色** | `#1B3A6B` 偏亮 + `#C9A96E` 黄金 | `#0B2545` 深海军蓝 + `#B89554` 金融金 |
| **字体** | 系统默认（PingFang） | **Noto Serif SC**（标题）+ **Noto Sans SC**（正文）+ **JetBrains Mono**（数字） |
| **圆角** | 24rpx 大圆角（卡通） | 8rpx 直角（专业） |
| **按钮** | 16rpx 圆角 | 4rpx 直角 + 衬线大标题 + 4rpx 字距 |
| **进度条** | 渐变色 (蓝→金) | 纯主色分段 (深蓝) |
| **卡片** | 浅阴影 + 大圆角 | 1rpx 细边框 + 4rpx 左侧色条 + 极浅阴影 |
| **选项卡** | emoji + 圆 + 全面主色背景 | 纯文字 + 左侧 4rpx 金条 + ✓ 几何符号 |
| **评分环** | 渐变色 + 中心 emoji | 纯主色 + 衬线大数字 72rpx + "SCORE" 字距 |
| **步骤标题** | 渐变 emoji 动画 | 编号 01/02/03 + 衬线标题 + 横线分隔 |

---

## 🎨 调色板

```scss
// 品牌主色 - 深海军蓝（金融机构标准色）
$primary:       #0B2545;  // 主色
$primary-2:     #13315C;  // 次主色
$primary-light: #EBF1F8;  // 浅背景
$primary-tint:  #F5F7FA;  // 更浅背景
$primary-dark:  #061A33;  // 深

// 强调色 - 金融金（克制金色）
$accent:        #B89554;  // 主金
$accent-light:  #FAF3E3;  // 金背景
$accent-dark:   #8C6F36;  // 深金

// 状态色（更深更克制）
$success:       #2C7A4B;  // 深绿
$warning:       #B25E00;  // 琥珀
$danger:        #9B2226;  // 深红

// 中性
$bg:            #FAFAF7;  // 暖白底
$card:          #FFFFFF;  // 卡白
$border:        #DDE2EA;  // 细线
$text-main:     #1A1A1A;  // 主文字
$text-sub:      #5A6473;  // 副文字
$text-weak:     #94A0B0;  // 弱文字
```

---

## 🔤 字体

```scss
$ff-serif:  "Noto Serif SC", "Source Han Serif SC", "Songti SC", serif;
$ff-base:   "Noto Sans SC", -apple-system, "PingFang SC", sans-serif;
$ff-mono:   "JetBrains Mono", "SF Mono", monospace;
```

**字体使用规范**：

| 元素 | 字体 | 重量 | 字距 | 字号 |
| --- | --- | --- | --- | --- |
| Hero 标题「信测通」 | Serif | 700 | 8rpx | 64rpx |
| Section 标题 | Serif | 600 | 1rpx | 36rpx |
| 卡片标题 | Serif | 600 | 1rpx | 32rpx |
| 评分大数字 | Serif | 700 | - | 72rpx |
| 评级 Badge | Serif | 600 | 4rpx | 30rpx |
| 正文 | Sans | 400 | 0.5rpx | 30rpx |
| 标签 / 提示 | Sans | 400 | 0.5rpx | 26rpx |
| 编号 / 数字 | Mono | 500 | 1rpx | 22-30rpx |
| Eyebrow 英文 | Mono | 500 | 4rpx | 22rpx |

---

## 📐 视觉语言规范

### 1. 卡片（统一 1rpx 边框 + 左侧 4rpx 色条）
```scss
.card {
  background: $card;
  border: 1rpx solid $border-light;
  border-left: 4rpx solid $primary;
  border-radius: 0;       // 直角 = 专业
  padding: $space-3;
}
```

### 2. 选项卡（用 ✓ 几何符号）
```html
<view :class="['opt-card', selected ? 'opt-selected' : '']">
  <view class="opt-body">
    <view class="opt-label">{{ label }}</view>
    <view v-if="desc" class="opt-desc">{{ desc }}</view>
  </view>
  <view class="opt-mark">
    <view v-if="selected" class="opt-mark-line opt-mark-v" />
    <view v-if="selected" class="opt-mark-line opt-mark-h" />
  </view>
</view>
```

### 3. 章节（"01 基础信息" 三段式）
```html
<view class="section-head">
  <text class="section-index">01</text>
  <text class="section-title">基础信息</text>
  <text class="section-required">*</text>
</view>
```

### 4. 步骤条（编号 01/02/03 衬线）
```html
<view class="bar-titles">
  <view class="bar-title">
    <text class="bar-title-idx">01</text>
    <text class="bar-title-name">基础</text>
  </view>
  ...
</view>
```

### 5. 评分环（纯主色 + 衬线大数字）
```html
<svg class="score-ring-svg" viewBox="0 0 100 100">
  <circle class="score-ring-bg" cx="50" cy="50" r="42" />
  <circle class="score-ring-fill" cx="50" cy="50" r="42"
    :stroke="levelCfg.color"
    :stroke-dasharray="`${(score / 100) * 264} 264`" />
</svg>
<view class="score-ring-center">
  <view class="score-ring-num">785</view>
  <view class="score-ring-label">SCORE</view>
</view>
```

### 6. Hero 区（深色块 + 金色装饰线 + 双语 eyebrow）
```html
<view class="hero">
  <view class="hero-eyebrow">CREDIT ASSESSMENT</view>
  <view class="hero-title">信测通</view>
  <view class="hero-line" />     <!-- 48rpx 宽的金色装饰线 -->
  <view class="hero-sub">信用贷款模拟评审工具</view>
</view>
```

### 7. 标签（直角 + 1rpx 边框）
```scss
.tag {
  display: inline-block;
  padding: 6rpx 16rpx;
  border: 1rpx solid currentColor;   // 直角 + 描边
  border-radius: 0;
}
```

---

## 🗑️ 删除的 emoji 列表（50 个）

| 类别 | emoji |
| --- | --- |
| 年龄 | 🌱 🌿 🍀 🌳 |
| 学历 | 🎓 📚 📖 ✏️ |
| 婚姻 | 👨‍👩‍👧 💑 🧍 💔 |
| 城市 | 🏙️ 🌆 🏘️ |
| 公司 | 🏛️ 🏢 🏬 🏣 🏪 💼 |
| 工龄 | ⭐ ✨ 🌟 ✳️ |
| 资产 | 🏡 🚗 🏦 🛡️ |
| 信用 | 💳 📊 📋 🔍 📅 🚨 ⚪ ⚠️ 📕 💎 |
| 流程 | 📝 🔓 📤 🔄 📋 |
| 首页 | ⚡ 🔒 📊 🤝 📞 |

**全部用文字 + 编号 + 几何 SVG 替代**。

---

## 🛠️ 技术调整

| 文件 | 改动 |
| --- | --- |
| `src/uni.scss` | 重构调色板（80 行）+ 加 `$ff-base/serif/mono` 别名 |
| `src/utils/styles/uni-globals.scss` | **新建**（66 行）— vite-plugin-uni 不会自动注入 uni.scss 变量给 .scss，需手动 import |
| `src/utils/styles/common.scss` | 重写公共样式（135 行）— 卡片/按钮/文字/警告 |
| `src/utils/styles/assess.scss` | 重写 5 步流程样式（192 行）— section / validation / footer |
| `src/components/compliance-bar/ComplianceBar.vue` | 改深蓝底 + 金色装饰线，告别 🔒 |
| `src/components/option-card/OptionCard.vue` | 取消 icon，✓ 几何符号 + 左侧 4rpx 金条 |
| `src/components/progress-bar/ProgressBar.vue` | 分段式进度 + 编号 01/02/03 |
| `src/pages/index/index.vue` | Hero 改深色 + eyebrow 双语 + 编号 feature |
| `src/pages/assess/type.vue` | 深色 Hero + 编号 01/02 + 衬线大标题 |
| `src/pages/assess/step1-5` | section-head「编号+标题」+ 去 emoji |
| `src/pages/assess/loading.vue` | SVG 旋转环 + 衬线「信测通」 + 编号 01-05 步骤 |
| `src/pages/result/free.vue` | 深色报告头 + 衬线大数字 72rpx + 直角标签 |
| `src/constants/assess-options.ts` | 80 个 option 全部去 `icon` 字段 |
| `index.html` | 引入 Google Fonts (Noto Serif SC / Sans SC / JetBrains Mono) |

---

## 🚀 H5 验证

```bash
cd xinceutong-miniapp
npm run dev:h5
# → http://localhost:8080/
```

**20/20 关键资源全部 200**：
- 入口 HTML / main.ts / App.vue / pages.json
- 4 个 SCSS（uni + uni-globals + common + assess）
- 3 个公共组件（ComplianceBar / OptionCard / ProgressBar）
- 8 个页面（index + type + step1-5 + loading + free）
- 1 个 constants

**emoji 残留扫描**：
```bash
$ python3 emoji_scan.py
# 输出：0 个残留
```

---

## 📸 关键页面对比

| 页面 | 之前 | 之后 |
| --- | --- | --- |
| **首页 Hero** | 「信测通」+ 紫色 emoji + 圆角大按钮 | 「CREDIT ASSESSMENT」+ 深色「信测通」+ 金色装饰线 + 直角金按钮 |
| **type 选择** | 2 个大圆角卡 + 🧑🏢 emoji | 深色 Hero + 编号 01/02 + 衬线大标题 + 直线左边条 |
| **step 标题** | 📅🎓💍🏙️ 6 个 emoji | 「01 年龄段」「02 学历」衬线编号 + 横线分隔 |
| **选项卡** | 🏢💼 emoji + 圆 + 全面主色背景 | 纯文字 + ✓ 几何符号 + 左侧 4rpx 金条 |
| **评分环** | 渐变色 + 785 数字 + emoji | 纯主色 + 衬线大数字 72rpx + "SCORE" 字距 |
| **标签云** | 圆角 + 3 色 + 渐变 | 直角 + 1rpx 描边 + 单色填充 |
| **按钮** | 圆角 16rpx + 圆角 24rpx | 直角 4rpx + 衬线 + 4rpx 字距 |

---

## ✨ 改造哲学（参考 UI Design Skill）

| 原则 | 落地 |
| --- | --- |
| **Commit to direction** | 选「Industrial / Editorial」风 — 金融严肃 |
| **80/20 of design quality** | 65% 在 typography + spacing（衬线大标题 + 字距 + 直角） |
| **Surface layering via lightness** | 用色条（4rpx 边）+ 细线（1rpx）代替阴影 |
| **NEVER use tiny touch targets** | 按钮 96rpx ≈ 48px（≥ 44px 规范） |
| **NEVER use low-contrast text** | $text-main=#1A1A1A vs $card=#FFF = 17:1（远超 AAA） |
| **NEVER use color alone** | 标签都带文字描述，不只靠颜色区分 |
| **NEVER center everything** | 章节标题左对齐，正文左对齐 |
| **NEVER use generic system fonts** | Noto Serif/Sans SC + JetBrains Mono |

---

## 📋 验收结论

✅ **金融合规类严肃风改造完成**：

1. ✅ **50 个 emoji 全部删除**（Python 扫描 0 残留）
2. ✅ **调色板重构**（深海军蓝 + 金融金，符合金融机构标准）
3. ✅ **字体升级**（Noto Serif SC 大标题 + Noto Sans SC 正文 + JetBrains Mono 数字）
4. ✅ **视觉语言统一**（1rpx 细线 + 4rpx 左侧色条 + 直角 8rpx）
5. ✅ **章节编号化**（01 02 03 衬线 + 横线分隔）
6. ✅ **Hero 区改造**（深色 + eyebrow 双语 + 金色装饰线）
7. ✅ **H5 dev server 跑通**（20/20 关键资源 HTTP 200）

可直接在浏览器打开 `http://localhost:8080/` 查看效果。
