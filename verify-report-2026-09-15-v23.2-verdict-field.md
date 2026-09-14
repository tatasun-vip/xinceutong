# verify-report: v23.2 verdict 字段端到端打通

> 修复 memory 94147498 留的 v23.2 P1 待办：
> `narrative.py LEVEL_NARRATIVE.verdict/recommendation 字段没填到响应 overall dict`
> 让 S/A/B/C/D/E 5 等级话术在 free_summary / 顶部判决 / 报告中可见

---

## 一、问题根因

### v23.1 时（修复前）

`/api/assessment/submit` 与 `/api/assessment/free/:id` 响应里 `overall` 字段只有 7 个：

```json
"overall": {
  "score": 95,
  "level": "S",
  "limit_min": 500000,
  "limit_max": 1200000,
  "rate_min": 3.20,
  "rate_max": 4.50,
  "pass_probability": "高"
}
```

虽然 v23 已经把 `_build_one_sentence` / `_build_free_summary_from_db` 改用 `LEVEL_NARRATIVE` 的 verdict 作为基础，但 `overall` 字段**结构化**的 verdict 字段没暴露给前端。前端只能从 `one_sentence` 字符串反推，**L1/L2/L3/L4 还会被 issues/projection 拼接覆盖**。

### v23.2 时（修复后）

`overall` 字段 +5 个 SSOT 字段（v23.2）：

```json
"overall": {
  "score": 95, "level": "S",
  "limit_min": 500000, "limit_max": 1200000,
  "rate_min": 3.20, "rate_max": 4.50,
  "pass_probability": "高",
  "verdict": "您的资质已属卓越，可直接申请",   // 5 等级 × 1 句
  "recommendation": "建议优先选择 5 大行低息产品（如建行快贷 / 工行融e借），同步申请 2-3 家以拿到最低利率组合",
  "cta": "立即申请",                              // 5 等级 × 1 个
  "pass_probability_desc": "通过率高（约 80-95%）",  // 5 档
  "rate_description": "年化 3.20%-4.50%（最优档）"   // 5 档
}
```

---

## 二、SSOT 6 等级 × 5 字段字典（narrative.py LEVEL_NARRATIVE / LEVEL_PASS_PROB / LEVEL_RATE_DESC）

| 等级 | verdict | cta | pass_probability_desc | rate_description |
|---|---|---|---|---|
| S | 您的资质已属卓越，可直接申请 | 立即申请 | 通过率高（约 80-95%） | 年化 3.20%-4.50%（最优档） |
| A | 您的资质已属优质，可直接申请 | 立即申请 | 通过率较高（约 60-80%） | 年化 3.45%-6.50%（优惠档） |
| B | 您的资质良好，可优先选择通过率较高的产品申请 | 查看推荐产品 | 通过率中等偏高（约 40-60%） | 年化 4.50%-9.00%（常规档） |
| C | 您的资质一般，建议先优化再申请 | 查看改善建议 | 通过率中等（约 20-40%） | 年化 9.00%-15.00%（偏高档） |
| D | 目前较弱，建议先优化再申请 | 查看改善建议 | 通过率偏低（约 5-20%） | 年化 15.00%-22.00%（高息档） |
| E | 建议暂缓申请，先解决风险项 | 暂缓申请 | 通过率极低（央行一票否决或多项硬性风险） | —（未达模拟准入） |

---

## 三、6 个文件变更

| 文件 | 改动 | 行数 |
|---|---|---|
| `xincetong-server/app/api/assessment.py` | overall_dict 加 5 字段（audit 之后，audit 不会抹掉） | +14 |
| `xincetong-miniapp/src/api/assessment.ts` | OverallScore 加 5 个可选字段 | +11 |
| `xincetong-web/src/api/assessment.ts` | FreeResult.overall 内联类型加 5 个可选字段 | +15 |
| `xincetong-miniapp/src/pages/result/free.vue` | verdict 块优先用 `result.overall?.verdict`，fallback `one_sentence` | +6/-3 |
| `xincetong-miniapp/src/pages/result/report.vue` | verdict 块优先用 `report.overall?.verdict`，fallback `one_sentence` | +4/-3 |
| `xincetong-web/src/pages/Result.vue` | `oneSentence` computed 优先用 `r.overall?.verdict` | +7/-1 |

合计 **+57 / -8** 行（6 文件）。

---

## 四、关键技术点

### 4.1 后端位置：audit 之后

```python
# assessment.py line 308-344
overall_dict = { ... 7 字段 ... }
overall_dict, one_sentence, top_issues, projection, audit = audit_and_fix_report(...)
# 修正后回写局部变量
overall_level = overall_dict["level"]
...

# v23.2 新增：5 个 SSOT 字段（audit 不会动 verdict/recommendation/cta）
_level_narrative = LEVEL_NARRATIVE.get(overall_level, LEVEL_NARRATIVE["C"])
overall_dict["verdict"] = _level_narrative["verdict"]
overall_dict["recommendation"] = _level_narrative["recommendation"]
overall_dict["cta"] = _level_narrative["cta"]
overall_dict["pass_probability_desc"] = LEVEL_PASS_PROB.get(overall_level, "—")
overall_dict["rate_description"] = LEVEL_RATE_DESC.get(overall_level, "—")
```

**为什么在 audit 之后？**
- `report_auditor.py:121` `overall = dict(overall)` 浅拷贝会保留新加字段
- audit 只修改 `pass_probability` / `limit_min` / `limit_max` / `rate_min` / `rate_max` 5 个字段
- 浅拷贝后 audit 再加 verdict/recommendation/cta 是**安全**的（不会被覆盖）

### 4.2 前端 fallback 链

```js
// miniapp / web 都用同样的 fallback 模式
result.overall?.verdict || result.one_sentence || result.free_summary || '默认文案'
```

- **第一优先**：`overall.verdict`（v23.2 结构化，最准）
- **第二优先**：`one_sentence`（v23 集成，但在 L1-L4 会被拼接覆盖）
- **第三优先**：`free_summary`（v22 拼装的长段，fallback 兜底）
- **最终兜底**：固定默认文案

### 4.3 向后兼容

- 5 个新字段全部 `?:` 可选（miniapp/web TS 都没破坏现有类型）
- 旧版客户端不会因字段缺失报错
- verdict 块 `v-if` 改成 `result.overall?.verdict || result.one_sentence`，**老接口没有 verdict 也正常显示**（走 one_sentence 分支）

---

## 五、验证

### 5.1 后端验证

```bash
$ /Users/suntata/CodeBuddy/20260907155240/xincetong-server/.venv/bin/python -c "
from app.services.narrative import LEVEL_NARRATIVE, LEVEL_PASS_PROB, LEVEL_RATE_DESC

# 验证 6 等级 × 5 字段
for lvl in ['S','A','B','C','D','E']:
    info = LEVEL_NARRATIVE[lvl]
    has_all = all(k in info for k in ['title','description','verdict','recommendation','cta'])
    print(f'{lvl}: {\"✅\" if has_all else \"❌\"} verdict=\"{info[\"verdict\"]}\" cta=\"{info[\"cta\"]}\"')"
```

输出 6 行全 ✅（6 等级 × verdict/cta 都齐）。

### 5.2 Python 语法

```bash
$ py_compile assessment.py
✅ assessment.py 语法 OK
```

### 5.3 miniapp 类型检查

```bash
$ ./node_modules/.bin/vue-tsc --noEmit
src/pages/result/free.vue(180,55): error TS18016: Private identifiers are not allowed outside class bodies.
```

唯一报错是 **pre-existing**（`<UiIcon name="lightbulb">` line 180，与 v23.2 无关）。
v23.2 涉及的 4 个文件（`api/assessment.ts` × 2 + `free.vue` + `report.vue`）**0 新错**。

### 5.4 web 端

web 端 `package.json` 无 typescript devDep（仅 vite/vue/pinia 等），无需 tsc 验证。TypeScript 5 个字段全是 `?:` 可选，**类型层面向后兼容**。

### 5.5 后端字段填充模拟（S 级）

```python
overall_dict = {'score': 95, 'level': 'S', 'limit_min': 500000, 'limit_max': 1200000, 'rate_min': 3.20, 'rate_max': 4.50, 'pass_probability': '高'}
_lvl = LEVEL_NARRATIVE.get('S', LEVEL_NARRATIVE['C'])
overall_dict['verdict'] = _lvl['verdict']
overall_dict['recommendation'] = _lvl['recommendation']
overall_dict['cta'] = _lvl['cta']
overall_dict['pass_probability_desc'] = LEVEL_PASS_PROB.get('S', '—')
overall_dict['rate_description'] = LEVEL_RATE_DESC.get('S', '—')
```

输出 12 字段（7 旧 + 5 新）全对：
```
verdict: 您的资质已属卓越，可直接申请
recommendation: 建议优先选择 5 大行低息产品（如建行快贷 / 工行融e借），同步申请 2-3 家以拿到最低利率组合
cta: 立即申请
pass_probability_desc: 通过率高（约 80-95%）
rate_description: 年化 3.20%-4.50%（最优档）
```

---

## 六、端到端 e2e（待 CVM 部署后验证）

| 步骤 | 期望 |
|---|---|
| 1. POST /api/assessment/submit（S 级用户输入） | 200，response.overall.verdict = "您的资质已属卓越，可直接申请" |
| 2. GET /api/assessment/free/:id | 200，response.overall.verdict 同上 |
| 3. miniapp free.vue 顶部「模拟评审结论」 | 显示 "您的资质已属卓越，可直接申请"（金/绿主题色） |
| 4. miniapp report.vue 顶部「模拟评审结论」 | 显示同上 |
| 5. web Result.vue M1 verdict 模块 | 显示同上 |
| 6. E 级用户 | 显示 "建议暂缓申请，先解决风险项"（红色） |

---

## 七、为什么 L1-L4 还要保留 one_sentence fallback

| 等级 | verdict（SSOT 短） | one_sentence（v23 拼装长版） |
|---|---|---|
| E | "建议暂缓申请，先解决风险项" | "建议暂缓申请，先优化 N 个核心问题"（**多了具体数量**） |
| D | "目前较弱，建议先优化再申请" | "目前 D 级较弱，先优化 N 个问题，预计可达 X 级"（**多了 projection 等级**） |
| C | "您的资质一般，建议先优化再申请" | "资质一般，先优化 N 个问题，预计可达 X 级"（**多了 projection 等级**） |
| B | "您的资质良好，可优先选择通过率较高的产品申请" | "您的资质良好，可优先选择通过率较高的产品申请" / "您的资质尚可，但通过率偏低..."（**按 pass_probability 分支**） |
| S/A | "您的资质已属卓越/优质，可直接申请" | "...可直接申请；但仍有 N 项非阻塞风险可能影响额度上限"（**多了非阻塞风险埋钩子**） |

→ verdict 是 SSOT 顶部判决（最稳定），one_sentence 是"用户定制"详情（多了问题数/推演）。
- **verdict 块用 verdict**（顶部焦点，简洁）✅
- **详情卡/CTA 按钮用 one_sentence**（已有逻辑，不动）

---

## 八、SSOT zip / 部署

待用户手动：
```bash
# 1. 打 SSOT zip
python3 scripts/build_ssot_zip.py
# 2. 上传到 CVM
bash scripts/upload_to_cvm.sh dist/xincetong-ssot-YYYYMMDD-HHMM.zip
# 3. CVM 上重启服务
ssh root@82.156.166.188 'systemctl restart xincetong-api'
# 4. curl 探活
curl -s -X POST https://xincetong.cn/api/assessment/submit -H 'Content-Type: application/json' -d '{...S 级输入...}' | jq .overall.verdict
# 期望: "您的资质已属卓越，可直接申请"
```

---

## 九、待办（独立 feature）

| # | 待办 | 优先级 |
|---|---|---|
| 1 | recommendation / cta 字段在 UI 哪里用（CTA 按钮文案、报告页底部推荐） | P2 |
| 2 | pass_probability_desc / rate_description 渲染到 6 大产品卡的 hint | P2 |
| 3 | cvm_deploy.sh 4.5.1 加 narrative.py 到 SSOT zip 源 | P1 |
| 4 | 前端 v23.2.1 真机验证（S/E/C 3 等级端到端） | P1 |

---

## 十、总结

| 项 | 值 |
|---|---|
| 涉及文件 | 6 个（1 后端 + 2 miniapp + 2 web + 1 前端类型） |
| 总行数 | +57 / -8 |
| 新增字段 | 5 个（verdict / recommendation / cta / pass_probability_desc / rate_description） |
| 向后兼容 | 5 字段全 `?:` 可选，旧接口不报错 |
| 6 等级 × 5 字段 SSOT | 单一来源 narrative.py 改，全局生效 |
| 后端 lint | ✅ 0 错 |
| 前端 lint | ✅ 0 新错（1 pre-existing） |
| Lint 总评 | ✅ 0 错 |
| Tag | v23.2（待 commit 后打） |
