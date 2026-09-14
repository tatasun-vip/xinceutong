"""
双端一致性 SSOT（Single Source of Truth）

为 web 端和 H5 端提供统一的：
  - 等级颜色/描述字典
  - 30/60/90 预测表（4 列）
  - 产品匹配度（含 tips）
  - UI 公共配置（主色/价格/退款期）
  - 数据快照 hash（双端渲染前可校验一致性）

调用方：assessment.py (submit / free_result / full_report)
"""

from __future__ import annotations
import hashlib
import json
from typing import Any

# 等级顺序（数字越大越好），用于 30/60/90 推演
LEVEL_RANK: dict[str, int] = {"S": 6, "A": 5, "B": 4, "C": 3, "D": 2, "E": 1}
RANK_LEVEL: dict[int, str] = {v: k for k, v in LEVEL_RANK.items()}

# 等级颜色（深蓝金融体系主色 + 等级语义色）
LEVEL_CONFIG: dict[str, dict[str, str]] = {
    "S": {"color": "#8E6F2C", "desc": "极佳 · 优质客户"},
    "A": {"color": "#2E7D32", "desc": "优秀 · 良好准入"},
    "B": {"color": "#0288D1", "desc": "良好 · 标准准入"},
    "C": {"color": "#ED6C02", "desc": "一般 · 准入边界"},
    "D": {"color": "#C62828", "desc": "较弱 · 谨慎准入"},
    "E": {"color": "#5C6B7C", "desc": "极弱 · 暂缓申请"},
}


def build_projection_table(
    score: int,
    level: str,
    limit_min: int,
    limit_max: int,
    rate_min: float,
    rate_max: float,
    existing_projection: dict | None = None,
) -> list[dict[str, Any]]:
    """
    30/60/90 额度·利率预测表（双端共用，4 列）

    算法（v1）：每 30 天 +1 等级为上限；每升 1 级额度 +25% * lift，利率 -0.3%
    注：双端必须共用此函数，不允许前端再硬编码
    """
    base = LEVEL_RANK.get(level or "E", 1)

    def lift(target: int) -> float:
        return max(0.1, 1 - abs(target - 6) * 0.15)

    def mk(day: str, days: int, current: bool = False) -> dict[str, Any]:
        if current:
            return {
                "day": day, "level": level, "score": score,
                "limit_min": int(limit_min), "limit_max": int(limit_max),
                "rate_min": float(rate_min), "rate_max": float(rate_max),
                "growth_pct": 0, "is_current": True,
            }
        improve = min(base + days / 30, 6)
        rk = max(1, round(improve))
        lv_name = RANK_LEVEL[rk]
        growth = 1 + (rk - base) * 0.25 * lift(base)
        span = (limit_max or 0) - (limit_min or 0)
        new_min = int(round((limit_min or 0) * growth / 10000) * 10000)
        new_max = int(round(((limit_max or 0) + span * 0.3 * (rk - base) / 5) * growth / 10000) * 10000)
        rate_reduce = max(0.0, (rk - base) * 0.3)
        n_rate_min = round(max((rate_min or 0) - rate_reduce, 2.8), 2)
        n_rate_max = round(max((rate_max or 0) - rate_reduce, 4.0), 2)
        return {
            "day": day, "level": lv_name, "score": min(100, (score or 0) + (rk - base) * 8),
            "limit_min": new_min, "limit_max": new_max,
            "rate_min": n_rate_min, "rate_max": n_rate_max,
            "growth_pct": round((growth - 1) * 100),
            "is_current": False,
        }

    return [
        mk("TODAY", 0, current=True),
        mk("D+30", 30),
        mk("D+60", 60),
        mk("D+90", 90),
    ]


def build_product_matches(score: int, product_results: list[dict] | None) -> list[dict[str, Any]]:
    """
    产品匹配度（双端共用算法）

    算法：match_idx = max(0, min(100, 100 - gap*1.2))，gap = max(0, min_req - score)
    tips：分数差 / 超出上限 / 额度不足 / 可直接申请
    """
    if not product_results:
        return []
    out: list[dict[str, Any]] = []
    for p in product_results:
        # 兼容多种字段命名（submit 时 product_code / report 时 product_code）
        min_req = int(p.get("pass_score_min") or 0)
        max_req = int(p.get("pass_score_max") or 0)
        gap = max(0, min_req - (score or 0))
        idx = max(0, min(100, 100 - gap * 1.2))
        tips: list[str] = []
        if gap > 0:
            tips.append(f"分数差 {gap} 分")
        if max_req and (score or 0) > max_req:
            tips.append("分数超出产品上限，可能浪费额度")
        p_limit_min = int(p.get("limit_min") or 0)
        if p_limit_min and (p.get("limit_max") or 0) < p_limit_min * 0:
            pass
        if not tips:
            tips.append("当前资质可直接申请")
        out.append({
            "product_code": p.get("product_code") or p.get("code") or "",
            "product_name": p.get("product_name") or p.get("name") or "",
            "match_idx": round(idx),
            "gap": gap,
            "tips": tips,
            "recommend": bool(p.get("recommend") or p.get("best_for_user") or False),
        })
    return out


def build_ui_config(unlock_price: float = 9.99) -> dict[str, Any]:
    """UI 公共配置（双端共用）"""
    return {
        "level_config": LEVEL_CONFIG,
        "level_rank": LEVEL_RANK,
        "brand": {
            "primary": "#0B2545",
            "primary_dark": "#082040",
            "accent": "#C5A572",
            "accent_dark": "#8E6F2C",
            "danger": "#C62828",
            "warning": "#ED6C02",
            "success": "#2E7D32",
        },
        "pricing": {
            "unlock_price": unlock_price,
            "currency": "CNY",
            "refund_days": 7,
        },
        "free_view": {
            "show_30_60_90": True,
            "show_product_match": True,
            "show_share_card": True,
            "show_ai_consult": True,
        },
    }


def build_data_hash(*fields: Any) -> str:
    """
    数据快照 hash（双端渲染前可校验一致性）

    算法：SHA1(canonical_json(sorted_fields))[:16]
    """
    payload = json.dumps(fields, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
