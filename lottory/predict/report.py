#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 报告生成模块
 Report generator —— 生成文本 / JSON / Markdown 分析报告
=============================================================================

 输入为 PredictionService.run() 产出的结果字典，输出三种格式：
   - 终端文本报告（直接打印）
   - JSON（机器可读，含完整指标）
   - Markdown（人可读，落盘）
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Dict, List


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def _met(flag: bool) -> str:
    return "✅ 达标" if flag else "❌ 未达标"


def render_text(payload: Dict) -> str:
    """生成终端文本报告。"""
    game = payload["game"]
    lines: List[str] = []
    lines.append("=" * 62)
    lines.append(f"  {game['display_name']} 预测回测分析报告")
    lines.append("=" * 62)
    lines.append(f"  生成时间: {payload['generated_at']}")
    lines.append(f"  数据规模: {payload['data']['n_records']} 期"
                 f"（{payload['data']['date_range']}）")
    lines.append(f"  目标置信度: {_pct(payload['target'])}")

    bt = payload["backtest"]
    baseline_name = payload.get("baseline_strategy", "random")
    lines.append("")
    lines.append("-" * 62)
    lines.append(" 回测结果（滚动 walk-forward）")
    lines.append("-" * 62)

    for name, m in bt.items():
        tag = "（基线）" if name == baseline_name else ""
        lines.append(f"\n▶ 策略: {name}{tag}")
        cov = m["coverage"]
        lines.append(f"   覆盖命中率: 红球 {_pct(cov['red'])}"
                     f" / 蓝球 {_pct(cov['blue'])}"
                     f" / 综合 {_pct(cov['overall'])}  {_met(cov['met'])}")
        cal = m["calibration"]
        lines.append(f"   置信度校准: 高置信区间命中率 "
                     f"红 {_pct(cal['red']['high_conf_hit_rate'])}"
                     f" / 蓝 {_pct(cal['blue']['high_conf_hit_rate'])}"
                     f"（基线 {_pct(cal['red']['baseline'])}）  {_met(cal['met'])}")
        prop = m["properties"]
        lines.append(f"   属性预测: 和值档位 {_pct(prop['sum_level'])}"
                     f" / 奇偶个数 {_pct(prop['odd_count'])}"
                     f" / 大小个数 {_pct(prop['big_count'])}"
                     f" / 综合 {_pct(prop['overall'])}  {_met(prop['met'])}")

    preds = payload.get("next_predictions", [])
    if preds:
        lines.append("")
        lines.append("-" * 62)
        lines.append(" 下一期推荐")
        lines.append("-" * 62)
        for p in preds:
            lines.append(f"   [{p['strategy']}]")
            lines.append(f"     红球: {p['red_balls']}")
            lines.append(f"     蓝球: {p['blue_balls']}")

    lines.append("")
    lines.append("-" * 62)
    lines.append(" ⚠️ 免责声明")
    lines.append("-" * 62)
    lines.append(" 彩票开奖为独立均匀随机过程，任何策略在样本外都无法")
    lines.append(" 稳定超越随机基线。本报告仅供数据分析学习，不构成投注建议，")
    lines.append(" 请理性对待彩票，切勿沉迷。")
    lines.append("=" * 62)
    return "\n".join(lines)


def write_json(payload: Dict, path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    return path


def write_markdown(payload: Dict, path: str) -> str:
    game = payload["game"]
    lines = [
        f"# {game['display_name']} 预测回测分析报告",
        "",
        f"- 生成时间: {payload['generated_at']}",
        f"- 数据规模: {payload['data']['n_records']} 期"
        f"（{payload['data']['date_range']}）",
        f"- 目标置信度: {_pct(payload['target'])}",
        "",
        "## 回测结果（滚动 walk-forward）",
        "",
        "| 策略 | 覆盖命中率(红/蓝) | 高置信命中率(红/蓝) | 属性预测(综合) |",
        "| --- | --- | --- | --- |",
    ]
    baseline_name = payload.get("baseline_strategy", "random")
    for name, m in payload["backtest"].items():
        cov = m["coverage"]
        cal = m["calibration"]
        prop = m["properties"]
        tag = "（基线）" if name == baseline_name else ""
        lines.append(
            f"| {name}{tag} | {_pct(cov['red'])} / {_pct(cov['blue'])} | "
            f"{_pct(cal['red']['high_conf_hit_rate'])} / {_pct(cal['blue']['high_conf_hit_rate'])} | "
            f"{_pct(prop['overall'])} |"
        )

    preds = payload.get("next_predictions", [])
    if preds:
        lines += ["", "## 下一期推荐", ""]
        for p in preds:
            lines.append(f"- **{p['strategy']}**: "
                         f"红球 `{p['red_balls']}` / 蓝球 `{p['blue_balls']}`")

    lines += [
        "",
        "## 免责声明",
        "",
        "> 彩票开奖为独立均匀随机过程，任何策略在样本外都无法稳定超越随机基线。"
        "本报告仅供数据分析学习，不构成投注建议，请理性对待彩票。",
    ]
    content = "\n".join(lines)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def generate_report(payload: Dict, out_dir: str) -> Dict[str, str]:
    """生成文本（打印）+ JSON + Markdown，返回文件路径。"""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(out_dir, f"report_{stamp}.json")
    md_path = os.path.join(out_dir, f"report_{stamp}.md")

    text = render_text(payload)
    write_json(payload, json_path)
    write_markdown(payload, md_path)
    return {"text": text, "json": json_path, "markdown": md_path}
