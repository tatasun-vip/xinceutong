"""
P3-3 历史数据修正脚本
==================

背景：P0+P1+P2 模型修复后，数据库中已存的旧 assessment 记录
（score/level/limit_min/limit_max/product_results...）
都是用旧模型跑出来的，与当前模型不一致。

修复方案：
  ① 先建 backup_assessments_YYYYMMDD_HHMMSS 表备份旧数据
  ② 遍历所有 assessments，用新模型重算
  ③ 同步写回 score/level/limit_min/limit_max/rate_min/rate_max/
                  pass_probability/product_results
  ④ 统计旧 vs 新的差距，输出报告

运行：
  cd xincetong-server && source .venv/bin/activate
  python scripts/migrate_v2_recalc.py
  # 干跑（不写库）：python scripts/migrate_v2_recalc.py --dry-run
"""
import argparse
import asyncio
import json
import sys
import os
from datetime import datetime

# 把 server 根加到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from app.models.assessment import Assessment
from sqlalchemy import select, text

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


# ============================================================================
# 备份
# ============================================================================
BACKUP_TABLE = f"backup_assessments_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


async def backup_table():
    """复制当前 assessments 到 backup_assessments_YYYYMMDD_HHMMSS 表"""
    print(f"\n  ① 备份旧数据 → {BACKUP_TABLE}")
    async with engine.begin() as conn:
        # 通用建表（SQLite / MySQL / PostgreSQL）
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS `{BACKUP_TABLE}` AS
            SELECT * FROM `assessments`
        """))
    print(f"     ✓ 已备份")


# ============================================================================
# 重算
# ============================================================================
async def recalc_one(asm: Assessment) -> tuple[dict, dict]:
    """
    对单条 assessment 用新模型重算。

    返回：(old_summary, new_summary)
    """
    from app.services.product_engine import (
        calculate_scores_by_product,
        synthesize_overall_score,
    )

    # 1. 旧值
    old = {
        "score": asm.score,
        "level": asm.level,
        "limit_min": asm.limit_min,
        "limit_max": asm.limit_max,
    }

    # 2. 拿 input_data
    input_data = asm.input_data
    if isinstance(input_data, str):
        try:
            input_data = json.loads(input_data)
        except Exception:
            return old, old
    if not isinstance(input_data, dict):
        return old, old

    # 3. 调新模型重算
    try:
        async with async_session() as session:
            product_results = await calculate_scores_by_product(
                input_data, asm.type or "personal", session
            )
            if not product_results:
                return old, old
            overall_score, overall_level, limit_min, limit_max, rate_min, rate_max, pass_prob = (
                synthesize_overall_score(product_results)
            )
            product_results_dicts = [p.to_dict() for p in product_results]
    except Exception as e:
        print(f"     [WARN] assessment#{asm.id} 重算失败: {e}")
        return old, old

    # 4. 提取关键值
    new = {
        "score": overall_score,
        "level": overall_level,
        "limit_min": limit_min,
        "limit_max": limit_max,
        "rate_min": rate_min,
        "rate_max": rate_max,
        "pass_probability": pass_prob,
        "product_results": product_results_dicts,
    }
    return old, new


async def recalc_all(dry_run: bool = False):
    """遍历所有 assessments 重算"""
    print(f"\n  ② 遍历 assessments 重算（dry_run={dry_run}）")
    async with async_session() as session:
        result = await session.execute(select(Assessment).order_by(Assessment.id))
        asms = result.scalars().all()
        print(f"     共 {len(asms)} 条记录")

        updated = 0
        skipped = 0
        for asm in asms:
            old, new = await recalc_one(asm)
            # 显示差异
            score_delta = (new["score"] or 0) - (old["score"] or 0)
            limit_min_old = (old["limit_min"] or 0) / 10000
            limit_min_new = (new["limit_min"] or 0) / 10000
            limit_max_old = (old["limit_max"] or 0) / 10000
            limit_max_new = (new["limit_max"] or 0) / 10000
            capped_count = sum(1 for p in new.get("product_results", []) if p.get("limit_capped"))

            print(
                f"     #{asm.id:>4}  score {old['score']:>3}→{new['score']:>3} ({score_delta:+3}) | "
                f"额度 {limit_min_old:>6.1f}-{limit_max_old:>6.1f}万 → {limit_min_new:>6.1f}-{limit_max_new:>6.1f}万 | "
                f"被 cap 产品 {capped_count}/6 | level {old['level']}→{new['level']}"
            )

            if not dry_run:
                asm.score = new["score"]
                asm.level = new["level"]
                asm.limit_min = new["limit_min"]
                asm.limit_max = new["limit_max"]
                asm.rate_min = new["rate_min"]
                asm.rate_max = new["rate_max"]
                asm.pass_probability = new["pass_probability"]
                if new["product_results"]:
                    asm.product_results = new["product_results"]
                updated += 1
            else:
                skipped += 1

        if not dry_run:
            await session.commit()
            print(f"\n     ✓ 提交 {updated} 条更新")
        else:
            print(f"\n     [DRY RUN] 跳过 {skipped} 条写入")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="干跑（不写库）")
    args = parser.parse_args()

    print("=" * 80)
    print(" P3-3 历史数据修正脚本")
    print("=" * 80)

    # 1. 备份
    if not args.dry_run:
        await backup_table()

    # 2. 重算
    await recalc_all(dry_run=args.dry_run)

    print(f"\n  ③ 完成")
    if not args.dry_run:
        print(f"     已备份表：{BACKUP_TABLE}")
        print(f"     如需回滚：用 backup_assessments_YYYYMMDD_HHMMSS 表的字段 UPDATE 回 assessments")
    else:
        print("     [DRY RUN] 去掉 --dry-run 重新跑以真正写入")


if __name__ == "__main__":
    asyncio.run(main())
