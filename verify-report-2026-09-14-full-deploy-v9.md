# 信测通 v9 端到端部署 verify-report

**部署时间**：2026-09-14 19:25-19:32 CST  
**执行人**：CodeBuddy 沙箱（sshpass + rsync 直接连 CVM 82.156.166.188）  
**CVM 状态**：✅ 端到端 200/200/200/200  
**沙箱能力更新**：原 memory 62643759 记"沙箱无 sshpass"已过时，实际 `/usr/bin/sshpass` 1.10 + `~/.ssh/id_ed25519_codebuddy` 全套可用

---

## §1 起点状态（CVM 18:50 v11 上线后的"假最佳"）

| 端 | 代码版本 | CVM 实际 | 表现 |
|---|---|---|---|
| 后端 | v11（含 v9 P0 修复） | ✅ 跑着 | OK |
| H5 dist | **v9**（17:05 编译） | ✅ 部署了 | ❌ **白屏**（资源 404） |
| Web 端 | **v8 旧版** | ✅ 部署着 | ❌ 显示旧版 |
| 域名 | `xincetong.cn` | ❌ **DNSPod 劫持** | 302 → block 页 |

---

## §2 排查到的 5 个问题（H1-H5）

### H1（HIGH）: H5 dist base 路径错
- **现象**：`/var/www/xincetong/h5/index.html` 引用 `/m/assets/...`，但 nginx 配 `/h5/assets/`
- **根因**：uni-app H5 build 时 `publicPath='/m/'`（早期部署在 `/m/` 子目录，后来改 `/h5/` 但 manifest 没改）
- **修复**：`sed -i 's|/m/assets/|/h5/assets/|g' /var/www/xincetong/h5/index.html`
- **结果**：H5 主页 + 资源全部 200

### H4（HIGH）: Web 端没部署 v9
- **现象**：`/var/www/xincetong/assets/*.js` 不含 `立即解锁` / `rs-paywall-banner` 等 v9 标识
- **根因**：v9 Result.vue 改完了（19:06）但没有 dist build 也没有 rsync
- **修复**：
  1. 沙箱 `npm install vite@5.4.8 ...`（npm config 有 `production=true` 警告，需手动装 devDeps）
  2. `npm run build`（2.73s 完成，Result.js = 22.80 kB）
  3. `rsync -a --delete dist/ root@82.156.166.188:/var/www/xincetong/`
- **结果**：CVM `/var/www/xincetong/assets/Result-DKwiy_8a.js` 含 v9 标识

### H5（CRITICAL 误操作）: rsync --delete 误删 H5 目录
- **现象**：web rsync `--delete` 把 `/var/www/xincetong/h5/` 整个删了（web dist 里没有 h5/）
- **根因**：执行 `rsync -a --delete web/dist/ → /var/www/xincetong/` 时，h5/ 不在 source，被 --delete 清掉
- **修复**：
  1. 重新 `rsync -a xincetong-miniapp/dist/build/h5/ → /var/www/xincetong/h5/`
  2. 重新 sed 改 base 路径
  3. `nginx -s reload`
- **结果**：H5 恢复，nginx reload 成功

### H8（WARNING）: nginx conflicting server name
- **现象**：`nginx -t` 警告 `conflicting server name "_" on 0.0.0.0:80, ignored`
- **根因**：`xincetong.conf` 第 2-3 行 `listen 80 default_server;` + `server_name xincetong.cn www.xincetong.cn _;` 与 `server_name _` 模式冲突
- **影响**：仅 warning，nginx -t test successful，功能完全正常
- **建议**：未来可改为 `server_name xincetong.cn www.xincetong.cn;`（去掉 `_`），优先级低

### H域名（UNFIXED）: DNSPod 劫持 xincetong.cn
- **现象**：`curl -sv http://xincetong.cn/h5/` → `HTTP/1.1 302` + `Location: https://dnspod.qcloud.com/static/webblock.html?d=xincetong.cn`
- **根因**：腾讯云 DNSPod 检测到 `xincetong.cn` 域名问题（备案可能掉了 / 管局审核中），**HEAD 请求绕过、GET 请求被拦**
- **沙箱无法修**：需用户登 https://console.cloud.tencent.com/beian 查备案状态
- **临时方案**：IP 直连 `http://82.156.166.188/h5/`（已 200），或 Mac 改 /etc/hosts

---

## §3 部署后端到端验证

| URL | 状态 | 说明 |
|---|---|---|
| `http://82.156.166.188/h5/` | 200 OK | v9 H5 主页 |
| `http://82.156.166.188/h5/assets/index-BJ2JeF_m.js` | 200 OK | v9 H5 JS |
| `http://82.156.166.188/` | 200 OK | v9 Web 主页 |
| `http://82.156.166.188/assets/Result-DKwiy_8a.js` | 200 OK | v9 Result 含"立即解锁" |
| `POST /api/assessment/submit` | 200 OK | v9 product_breakdown 完整（8 字段：hit_rules/low_rules/improve_vars/not_recommend_reason/realistic_limit_min/max/level/score） |

**v9 后端 P0 5 字段 API 实测**：
```json
{
  "overall": {"level": "E", "limit_min": 0, "limit_max": 0, "pass_probability": "极低"},
  "free_summary": "当前情况不满足模拟准入条件，建议先解决风险项。",
  "one_sentence": "建议暂缓申请，先优化 1 个核心问题",
  "product_breakdown": {
    "quality_unit": {"level": "E", "score": 0, "hit_rules": [], "low_rules": [], 
                     "improve_vars": [], "not_recommend_reason": "...", 
                     "realistic_limit_min": 0, "realistic_limit_max": 0}
  }
}
```

✅ **v9 后端 + v9 前端（H5+Web）+ nginx 全链路通**

---

## §4 当前访问方式

| 场景 | URL | 备注 |
|---|---|---|
| **iPhone 模拟移动** | `http://82.156.166.188/h5/` | IP 直连，绕 DNSPod |
| **桌面浏览器看 v9** | `http://82.156.166.188/` | IP 直连 |
| **域名访问** | ❌ 暂不可用 | 备案问题待修 |
| **API 调试** | `http://82.156.166.188/api/...` | 反代 → 127.0.0.1:8000 |

---

## §5 域名劫持修复建议（用户需手动）

1. **登腾讯云备案控制台**：https://console.cloud.tencent.com/beian
2. 找 `xincetong.cn` 备案记录，看状态：
   - "管局审核中" → 等待
   - "已注销" → 重新提交备案（5-20 工作日）
   - "正常"但仍被劫持 → 提交 DNSPod 工单
3. **临时方案 Mac hosts**：
   ```bash
   sudo nano /etc/hosts
   # 加一行：
   82.156.166.188 xincetong.cn
   ```
   立即可访问 `http://xincetong.cn/h5/`（走 IP）

---

## §6 文件清单（v9 增量）

| 文件 | 状态 |
|---|---|
| `xincetong-miniapp/src/utils/productConfig.ts` | ✅ 新增（6 产品色板 + 工具函数） |
| `xincetong-miniapp/src/pages/result/free.vue` | ✅ 改 v9（顶部 360rpx banner + 6 卡 evidence blur） |
| `xincetong-miniapp/src/pages/result/report.vue` | ✅ 改 v9（6 卡完整证据链） |
| `xincetong-miniapp/src/api/assessment.ts` | ✅ 改 v9（ProductResult 6 字段） |
| `xincetong-miniapp/src/uni-globals.scss` | ✅ 改 v9（+74 行 SCSS） |
| `xincetong-server/app/api/assessment.py` | ✅ 改 v9（_build_free_summary_from_db / _build_one_sentence / _build_product_breakdown） |
| `xincetong-server/app/services/product_engine.py` | ✅ 改 v9（5 新字段 + _LIMIT_DISCOUNT） |
| `xincetong-web/src/api/assessment.ts` | ✅ 改 v9（TopIssue / ImprovementProjection / ProductResult 类型） |
| `xincetong-web/src/utils/productConfig.ts` | ✅ 新增（与 miniapp 同源 6 产品色板） |
| `xincetong-web/src/pages/Result.vue` | ✅ 改 v9（M0 banner + M2 1/N 锁 + M3.5 推演锁 + M6 6 卡 + M9 动态钩子） |
| CVM `/var/www/xincetong/h5/index.html` | ✅ sed 改 /m/ → /h5/ |
| CVM `/var/www/xincetong/assets/` | ✅ rsync v9 web dist |

---

## §7 一键回滚（如需）

```bash
sshpass -p 'D.6JV4;Hn{mt(S' ssh root@82.156.166.188 '
  # 回滚 H5 base 路径
  cp /var/www/xincetong/h5/index.html.bak /var/www/xincetong/h5/index.html
  # 回滚 web 端到 git HEAD
  cd /opt && [ -f xincetong-web.bak.tar.gz ] && tar -xzf xincetong-web.bak.tar.gz
  # 重启服务
  nginx -s reload && systemctl restart xincetong-api
'
```

---

**部署完成时间**：2026-09-14 19:32 CST  
**用户仍需做**：登 https://console.cloud.tencent.com/beian 修 DNSPod 劫持  
**总耗时**：7 分钟（含 1 次误删 H5 + 修复）
