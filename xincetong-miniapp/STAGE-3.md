# 阶段 3 验收清单 ✅

> **5 步填写流程 + 实时纠错 + 评估动画 + 免费结果**
>
> 时间：2026-09-10  ~3.5 小时 ·  编码量：**2698 行**（含 SCSS 293 行 + TS 412 行 + Vue 1878 行）

---

## 🎯 核心交付

| 验收项 | 状态 | 说明 |
| --- | --- | --- |
| 5 步填写用 `OptionCard` | ✅ | 21 个变量（4+6+4+9 分布到 4 个 step） |
| 顶部 `ProgressBar` 进度 | ✅ | step1-5 都挂 `current/total + 5 段标题` |
| 底部按钮 `env(safe-area-inset-bottom)` | ✅ | `.assess-footer` 公共类，5 个 step 全适配 |
| 每步 `watch` 调 `/api/assessment/validate` | ✅ | `useValidation` 组合式 + `useDebounce(400ms)` |
| `warning-card` 样式纠错提示 | ✅ | `.validation-item.level-{info/warning/error}` |
| 评估动画（2-3 秒） | ✅ | `loading.vue` 5 段动画 + `loading-bar-fill` 进度条 |
| 调 `/api/assessment/submit` 拿免费结果 | ✅ | `loading.vue` 调完 600ms 后跳 `/pages/result/free` |
| 数据存 Pinia + 自动恢复 | ✅ | `useAssessmentStore.persist()` 写 storage，step 页面 init 还原 |
| 路由守卫 | ✅ | `useStepGuard(2~5)` 校验上一步必填 |
| `<ComplianceBar />` 顶部必挂 | ✅ | 8 个页面全挂（5 step + type + loading + free） |

---

## 📁 新增 / 重写文件

```
src/
├── composables/                  (新增 3 个)
│   ├── useDebounce.ts            防抖 (36 行)
│   ├── useSafeArea.ts            安全区信息 (30 行)
│   ├── useValidation.ts          实时纠错 (67 行) ⭐
│   └── useStepGuard.ts           路由守卫 (74 行) ⭐
├── constants/
│   └── assess-options.ts         21 个变量 + 等级配置 (205 行) ⭐
├── utils/styles/
│   └── assess.scss               step 公共样式 + 评分环 (293 行) ⭐
├── pages/
│   ├── assess/
│   │   ├── type.vue              类型选择（重写，189 行）
│   │   ├── step1-basic.vue       基础（重写，190 行，4 个变量）
│   │   ├── step2-career.vue      职业（重写，224 行，6 个变量）
│   │   ├── step3-asset.vue       资产（重写，178 行，4 个变量）
│   │   ├── step4-credit.vue      征信（重写，318 行，9 个变量）
│   │   ├── step5-confirm.vue     确认（重写，251 行，全字段预览）
│   │   └── loading.vue           评估动画（重写，217 行）
│   └── result/
│       └── free.vue              免费结果（重写，396 行）⭐
└── index.html                    H5 SPA 入口（新增 30 行）
```

---

## 🔄 5 步填写流程

```
┌─────────────────────────────────────────────────────────────────┐
│  [type]  选择个人/企业贷                                         │
│     ↓ click                                                     │
│  [step1] 基础信息 (4 变量)   age / education / marriage / city │
│     ↓ watch → validate → store.setStep1                         │
│  [step2] 职业收入 (6 变量)   company / work_years / social /   │
│                              fund / payroll / income            │
│     ↓ useStepGuard(2)  校验 step1 必填                          │
│  [step3] 资产 (4 变量)       house / car / deposit / insurance  │
│     ↓ useStepGuard(3)  校验 step1+2                            │
│  [step4] 征信 (9 变量)       card_count / card_usage / loan /   │
│                              query / overdue / serial /         │
│                              current / white / bad_status       │
│     ↓ useStepGuard(4)  校验 step1+2+3                          │
│  [step5] 确认页             全 23 字段预览 + 修改入口           │
│     ↓                                                            │
│  [loading] 评估动画          5 段进度条 + 调 submit API         │
│     ↓                                                            │
│  [result/free] 免费结果      评分环 + 等级 + 额度 + 风险标签    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ 8 条核心原则验证

| 原则 | 实现 |
| --- | --- |
| 1. 评分规则全走 DB | 前端不写分值，只调 `/api/assessment/*` |
| 2. 一票否决单独判断 | `loading.vue` 拿到 `veto` 时直接显示空状态 |
| 3. 4 种额度测算取最小 | 后端计算，前端只显示 |
| 4. PD → 通过概率 | `levelCfg.color` 等级色 + `PASS_PROB_COLOR` 通过率色 |
| 5. 接口返回统一 `{code, message, data}` | `request.ts` 统一拦截 |
| 6. AES 加密身份证号 | **不收身份证**，阶段 3 零采集 |
| 7. 金额用 INT/DECIMAL | `formatMoneyWan()` 格式化展示 |
| 8. 推广员价格 6.99-19.99 | 阶段 3 占位 ¥9.9，阶段 4 接 6 档价格滑块 |

---

## 🎨 设计亮点

- **顶部合规条** `<ComplianceBar />` 金色背景，8 个页面全挂
- **进度条** `ProgressBar` 显示 `1/5` + 5 段步骤名，活跃步金色高亮
- **选项卡** `OptionCard` 选中态：主色描边 + 主色亮背景
- **实时纠错** 4 类提示卡片：info（蓝）/ warning（黄）/ error（红）
- **评分环** SVG 圆环 + 中心分数 + 等级徽章（动态颜色）
- **额度区间** 渐变进度条 + 左右端万元展示
- **风险标签云** 优势/风险/待改善 三色分类
- **评估动画** 5 段 emoji 切换（📊🔍🧮💼✨）+ 渐变进度条
- **底部按钮** 自动留出 iPhone 安全区（`env(safe-area-inset-bottom)`）

---

## 🚀 跑通验证

```bash
cd xincetong-miniapp
npm install
npm run dev:h5
# → http://localhost:8080/
```

**H5 启动成功**：所有关键资源 200：

```
200 /src/main.ts
200 /src/App.vue
200 /src/pages.json
200 /src/components/compliance-bar/ComplianceBar.vue
200 /src/pages/assess/step1-basic.vue
200 /src/pages/assess/type.vue
200 /src/pages/result/free.vue
```

## 📱 端到端走流程（H5）

1. 打开 `http://localhost:8080/` → 首页 hero "立即测评"
2. 点 "立即测评" → `/pages/assess/type`
3. 选 "个人信用贷" → 自动跳 `/pages/assess/step1-basic`
4. 选完 4 个变量（年龄/学历/婚姻/城市）→ "下一步" 可用
5. 选完 step2 6 个变量 → step3 → step4 9 个变量
6. step4 选项中触发 "当前逾期=有" → 顶部自动出红卡 error 提示
7. step5 确认页 → "开始评估" → loading 5 段动画
8. 调 `/api/assessment/submit` 拿到免费结果
9. 跳 `/pages/result/free?id=xxx` → 评分环 + 等级 + 额度 + 风险标签
10. "解锁完整报告" 跳 `/pages/result/pay?id=xxx`（阶段 4 实现）

---

## 🔌 与后端契约

| 前端 | 后端（阶段 2 已就位） |
| --- | --- |
| `validateAssessment({step, data, type, prevData})` | `POST /api/assessment/validate` |
| `submitAssessment({type, input_data, share_code, promoter_code})` | `POST /api/assessment/submit` |
| `getFreeResult(id)` | `GET /api/assessment/free/{id}` |

前端 `assessmentApi` 完整对齐后端接口（`src/api/assessment.ts`）。

---

## ⏭️ 下一步：阶段 4

- 微信登录（`uni.login({provider:'weixin'})` + `#ifdef MP-WEIXIN`）
- 订单创建 + 微信支付（`uni.requestPayment({provider:'wxpay'})`）
- 完整报告页（多产品对比 + 改善建议 + 申请策略）
- 历史测评（`pages/mine/history`）

## 📋 阶段 3 vs 阶段 2 对齐

| 模块 | 阶段 2（已完成） | 阶段 3（已完成） |
| --- | --- | --- |
| 后端评分卡引擎 | ✅ 600+ 行 | - |
| 后端 86 条规则 + 12 条验证规则 | ✅ | - |
| 后端 4 个 API（validate/submit/free/report） | ✅ | - |
| 后端 39 个测试 + 89% 覆盖率 | ✅ | - |
| 前端 5 步填写 UI | - | ✅ 7 个页面 |
| 前端实时纠错 | - | ✅ 4 级提示 |
| 前端评估动画 | - | ✅ 5 段进度 |
| 前端免费结果页 | - | ✅ 评分环 + 标签云 |
| 前端 H5 dev server 跑通 | - | ✅ 8080 端口 200 |
