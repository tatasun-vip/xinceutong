# 信测通 v11 升级报告

**日期**：2026-09-14
**Commit**：`bd76ce1`
**部署包**：`dist/xincetong-cvm-deploy-20260914-1826.zip`（0.93 MB）

---

## 1. 三项升级

### 1.1 苹果字体（仅 web 端，miniapp 已是苹果字体栈）

| 文件 | 改动 |
|---|---|
| `xincetong-web/index.html` | 删 Google Fonts `<link>`（Noto Serif/Sans SC + JetBrains Mono） |
| `xincetong-web/src/styles/variables.scss` | 字体顺序倒置：苹果系统栈放最前（`-apple-system, BlinkMacSystemFont, "PingFang SC", "Songti SC", "Hiragino Sans GB"`），Noto 降为兜底 |

**新字体栈**：
```scss
$ff-base:    -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", "Helvetica Neue", "Noto Sans SC", sans-serif;
$ff-serif:   -apple-system, "PingFang SC", "Songti SC", "STSong", "Hiragino Sans GB", "Noto Serif SC", "Source Han Serif SC", serif;
$ff-mono:    ui-monospace, "SF Mono", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
```

**miniapp 端验证**：已是苹果字体栈（`uni.scss` / `App.vue` / `uni-globals.scss` 三处一致），无需改动。

### 1.2 额度整数化（web + h5）

| 文件 | 改动 |
|---|---|
| `xincetong-miniapp/src/utils/format.ts` | 新增 `formatLimit(min,max)→"50,000~100,000 元"`、`formatYuan(n)→"50,000 元"`、`formatYuanWithSign(n)→"¥ 50,000"`，旧 `formatMoneyWan` 退化为 `formatYuan` |
| `xincetong-miniapp/src/pages/result/free.vue` | formatLimit 函数改实现 + 712 / 804 两处 `(limMin/10000).toFixed(1)` 改 `formatLimit(limMin, limMax)` |
| `xincetong-miniapp/src/pages/result/report.vue` | formatLimit 函数改实现 + 309（v9 M5 行）+ 593（v9 limitGain）两处 |
| `xincetong-miniapp/src/components/product-card/ProductCard.vue` | limitText / channelOnlineText / channelOfflineText 全部改千分位 + 元 |
| `xincetong-miniapp/src/pages/mine/index.vue` | 65/70 行 `formatMoneyWan` → `formatYuanWithSign`（`¥` + 千分位） |
| `xincetong-web/src/pages/Result.vue` | 381/460/671 三处 + 加 `formatLimit` 函数（与 miniapp 一致） |

**展示对比**：

| 旧 | 新 |
|---|---|
| ¥ 5.0 ~ 10.0 万 | 50,000~100,000 元 |
| 5.0 万 | 50,000 元 |
| ¥5,000.00 | ¥ 5,000 |

**注**：`xincetong-web/src/pages/Home.vue` 的 160/354/374/394 行仍是 "87.0 ~ 162.0 万" 形式（**静态营销文案**，不是变量），保留"万"更直观。如需改手动替换即可。

### 1.3 评估按银行产品（v7 bank_scorecard.py 命中）

**前端补传 `bank_code`**（后端 `bank_scorecard.py:138` 的 `apply_bank_bias(raw_score, bank_code, product_code)` 一直存在）：

| 文件 | 改动 |
|---|---|
| `xincetong-miniapp/src/api/assessment.ts` | `SubmitReq` interface 加 `bank_code?: string` 字段 |
| `xincetong-miniapp/src/pages/assess/loading.vue` | 提交时加 `bank_code: store.bankCode || undefined` |

**触发逻辑**：
- 用户在 `select-bank.vue` 选了某银行 → `assessment store` 存 `bankCode`
- 评估提交 → `loading.vue` 把 `bankCode` 传给后端
- 后端 `assessment.py` 接收 `bank_code` → 调用 `bank_scorecard.apply_bank_bias` → 按 10 家银行差异化评分（v7 minimax 已设计完的银行模型）

---

## 2. 部署方式变更（删除 GHA/Vercel/Render）

| 项 | 旧（v5） | 新（v11） |
|---|---|---|
| 触发 | git push → GHA workflow | **手动：Mac 跑 `bash scripts/upload_to_cvm.sh`** |
| 传输 | catbox.moe 中转 | **scp 直传**（zip < 100MB，秒级） |
| 后端部署 | Vercel serverless | **systemd unit**（`xincetong-api.service`） |
| 静态托管 | Vercel CDN | **nginx 反代** `/var/www/xincetong/` |
| DB | Render PostgreSQL | **CVM 自建 PostgreSQL**（yum 安装） |

### 2.1 新增脚本

- `scripts/build_deploy_zip.py`：本地打包（自动跑 `npm run build` + `npm run build:h5` + 收集后端源码 + 写 zip）→ 输出 `dist/xincetong-cvm-deploy-YYYYMMDD-HHMM.zip`
- `scripts/cvm_deploy.sh`：CVM 端跑的部署脚本（解压 + venv 首次建/增量 + pip install + rsync 同步 + systemd 重启 + nginx reload + 健康检查）
- `scripts/upload_to_cvm.sh`：Mac 端上传脚本（自动检测 ssh key / 密码 fallback + scp + ssh 触发 + 域名验证）
- `scripts/upload_to_catbox.py`：保留为备用（包 > 50MB 时中转），自动找最新 zip
- `DEPLOY_CVM.md`：CVM 部署文档（环境/日常/故障/滚回/SSH key 推荐）

### 2.2 删除脚本

- `scripts/deploy.sh`：旧 GitHub + Render 部署（不再使用）

---

## 3. 部署流程（v11 起）

### 3.1 首次部署（环境搭建）
```bash
# Mac 端
cd /Users/suntata/CodeBuddy/20260907155240
python3 scripts/build_deploy_zip.py
bash scripts/upload_to_cvm.sh dist/xincetong-cvm-deploy-*.zip
# 然后 ssh 上 CVM 手动 vim /opt/xincetong/.env 填真实配置
# 手动 alembic upgrade head
```

### 3.2 日常更新
```bash
# Mac 端（3-5 分钟完成）
python3 scripts/build_deploy_zip.py
bash scripts/upload_to_cvm.sh dist/xincetong-cvm-deploy-*.zip
```

---

## 4. 验证

- **Lint**：0 错（web + miniapp 全部文件）
- **Build**：web vite ✅ + miniapp uni h5 ✅
- **打包**：3.29 MB → 0.93 MB（压缩率 71.7%）
- **Git**：commit `bd76ce1`，16 files changed（+837 / -337）

### 待用户验证（沙箱无法做）
- [ ] HBuilderX 真机/模拟器实测 miniapp 苹果字体 + 整数额度
- [ ] 浏览器实测 web 端苹果字体 + 整数额度
- [ ] CVM 端 `bash scripts/upload_to_cvm.sh dist/...zip` 一键部署
- [ ] 评估带 `bank_code` 跑 3 个 URL 回归（不传 → 通用模型；传 → 触发 apply_bank_bias）
- [ ] nginx 配置 + systemd unit 首次部署后手写

---

## 5. 已知限制

- miniapp h5 模式构建产物未在 `vite.config.ts` 调 `VITE_API_BASE_URL`（沿用旧版，会跑后端到 Vercel URL，**首次部署后需手动改 baseURL 指向 xincetong.cn**）
- `xincetong-server/sql/migrations/0002_business_dimensions.sql` 仍需在 CVM 端 `psql` 手动跑（生产 DB 未加 `dimensions` 列）
- `bank_scorecard.py` 的 10 家银行 bias 数据需 `python -m scripts.init_bank_v7_bias` 单独 seed（独立 feature，未做）
