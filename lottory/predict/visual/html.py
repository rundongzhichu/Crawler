#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 HTML 报告生成器
 HTML report generator —— 交互式 Plotly 仪表板
=============================================================================

 输入为 PredictionService.run() 产出的 payload 字典，输出一个自包含的
 HTML 页面，包含：
   - 覆盖命中率对比图
   - 置信度校准对比图
   - 属性预测准确率对比图
   - 完整指标明细表 + 下一期推荐表

 Plotly 缺失时自动降级为纯 HTML 表格（不影响其它报告格式）。
"""

from __future__ import annotations

import os
from datetime import datetime
from html import escape
from typing import Dict

# 颜色常量
COLOR_RED = "#ef4444"
COLOR_BLUE = "#3b82f6"
COLOR_GREEN = "#10b981"
COLOR_ORANGE = "#f59e0b"
COLOR_GRAY = "#9ca3af"
STRATEGY_PALETTE = ["#6366f1", "#8b5cf6", "#ec4899", "#f59e0b", "#14b8a6", "#84cc16"]

# Plotly 可选依赖
try:
    import plotly.graph_objects as go  # type: ignore
    HAS_PLOTLY = True
except Exception:  # noqa: BLE001
    go = None
    HAS_PLOTLY = False


# ============================================================================
#  数据抽取
# ============================================================================

def _pct(v: float) -> float:
    """0-1 小数转百分比数值。"""
    return round(v * 100, 1)


def _strategy_names(payload: Dict) -> list:
    return list(payload["backtest"].keys())


# ============================================================================
#  图表
# ============================================================================

def _coverage_figure(payload: Dict):
    bt = payload["backtest"]
    names = _strategy_names(payload)
    target = payload["target"] * 100

    fig = go.Figure()
    fig.add_bar(name="红球", x=names, y=[_pct(m["coverage"]["red"]) for m in bt.values()],
                marker_color=COLOR_RED)
    fig.add_bar(name="蓝球", x=names, y=[_pct(m["coverage"]["blue"]) for m in bt.values()],
                marker_color=COLOR_BLUE)
    fig.add_bar(name="综合", x=names, y=[_pct(m["coverage"]["overall"]) for m in bt.values()],
                marker_color=COLOR_GREEN)
    fig.add_hline(y=target, line_dash="dash", line_color=COLOR_ORANGE,
                  annotation_text=f"目标 {target:.0f}%",
                  annotation_position="top right")
    fig.update_layout(
        title="候选池覆盖命中率",
        barmode="group",
        yaxis_title="覆盖率 (%)",
        yaxis_range=[0, 100],
        template="plotly_white",
    )
    return fig


def _calibration_figure(payload: Dict):
    bt = payload["backtest"]
    names = _strategy_names(payload)
    target = payload["target"] * 100

    red_hr = [_pct(m["calibration"]["red"]["high_conf_hit_rate"]) for m in bt.values()]
    blue_hr = [_pct(m["calibration"]["blue"]["high_conf_hit_rate"]) for m in bt.values()]
    red_base = [_pct(m["calibration"]["red"]["baseline"]) for m in bt.values()]

    fig = go.Figure()
    fig.add_bar(name="红球高置信命中", x=names, y=red_hr, marker_color=COLOR_RED)
    fig.add_bar(name="蓝球高置信命中", x=names, y=blue_hr, marker_color=COLOR_BLUE)
    fig.add_trace(go.Scatter(name="红球基线（随机）", x=names, y=red_base,
                             mode="lines+markers", line=dict(color=COLOR_GRAY, dash="dot")))
    fig.add_hline(y=target, line_dash="dash", line_color=COLOR_ORANGE,
                  annotation_text=f"目标 {target:.0f}%",
                  annotation_position="top right")
    fig.update_layout(
        title="置信度校准（高置信区间命中率 vs 随机基线）",
        barmode="group",
        yaxis_title="命中率 (%)",
        yaxis_range=[0, 100],
        template="plotly_white",
    )
    return fig


def _properties_figure(payload: Dict):
    bt = payload["backtest"]
    names = _strategy_names(payload)
    target = payload["target"] * 100

    fig = go.Figure()
    fig.add_bar(name="和值档位", x=names,
                y=[_pct(m["properties"]["sum_level"]) for m in bt.values()],
                marker_color=COLOR_GREEN)
    fig.add_bar(name="奇偶个数", x=names,
                y=[_pct(m["properties"]["odd_count"]) for m in bt.values()],
                marker_color=COLOR_ORANGE)
    fig.add_bar(name="大小个数", x=names,
                y=[_pct(m["properties"]["big_count"]) for m in bt.values()],
                marker_color=COLOR_RED)
    fig.add_hline(y=target, line_dash="dash", line_color=COLOR_ORANGE,
                  annotation_text=f"目标 {target:.0f}%",
                  annotation_position="top right")
    fig.update_layout(
        title="属性预测准确率",
        barmode="group",
        yaxis_title="准确率 (%)",
        yaxis_range=[0, 100],
        template="plotly_white",
    )
    return fig


def _fig_to_html(fig) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False)


# ============================================================================
#  静态表格
# ============================================================================

def _badge(met: bool) -> str:
    return ("<span class='badge ok'>达标</span>" if met
            else "<span class='badge no'>未达标</span>")


def _metrics_table(payload: Dict) -> str:
    bt = payload["backtest"]
    rows = []
    for name, m in bt.items():
        cov = m["coverage"]
        cal = m["calibration"]
        prop = m["properties"]
        rows.append(
            f"<tr>"
            f"<td>{escape(name)}</td>"
            f"<td>{_pct(cov['red'])}%</td>"
            f"<td>{_pct(cov['blue'])}%</td>"
            f"<td>{_pct(cov['overall'])}%</td>"
            f"<td>{_badge(cov['met'])}</td>"
            f"<td>{_pct(cal['red']['high_conf_hit_rate'])}%</td>"
            f"<td>{_pct(cal['blue']['high_conf_hit_rate'])}%</td>"
            f"<td>{_pct(cal['red']['baseline'])}%</td>"
            f"<td>{_pct(prop['sum_level'])}%</td>"
            f"<td>{_pct(prop['odd_count'])}%</td>"
            f"<td>{_pct(prop['big_count'])}%</td>"
            f"<td>{_badge(prop['met'])}</td>"
            f"</tr>"
        )
    return (
        "<table><thead><tr>"
        "<th>策略</th>"
        "<th>覆盖-红</th><th>覆盖-蓝</th><th>覆盖-综合</th><th>覆盖达标</th>"
        "<th>校准-红</th><th>校准-蓝</th><th>基线-红</th>"
        "<th>属性-和值</th><th>属性-奇偶</th><th>属性-大小</th><th>属性达标</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    )


def _predictions_table(payload: Dict) -> str:
    preds = payload.get("next_predictions", [])
    if not preds:
        return "<p>无预测结果</p>"
    rows = []
    for p in preds:
        red = " ".join(f"{n:02d}" for n in p["red_balls"])
        blue = " ".join(f"{n:02d}" for n in p["blue_balls"])
        rows.append(
            f"<tr><td>{escape(p['strategy'])}</td>"
            f"<td class='mono red'>{red}</td>"
            f"<td class='mono blue'>{blue}</td></tr>"
        )
    return (
        "<table><thead><tr><th>策略</th><th>红球</th><th>蓝球</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


# ============================================================================
#  页面组装
# ============================================================================

def _charts_block(payload: Dict) -> str:
    if not HAS_PLOTLY:
        return "<div class='card'><p class='muted'>未安装 plotly，图表已降级为表格。</p></div>"
    figures = [
        _coverage_figure(payload),
        _calibration_figure(payload),
        _properties_figure(payload),
    ]
    cards = "".join(f"<div class='card'>{_fig_to_html(f)}</div>" for f in figures)
    return cards


def build_html(payload: Dict) -> str:
    """根据 payload 构建完整 HTML 页面字符串。"""
    game = payload["game"]
    data = payload["data"]
    target = payload["target"] * 100
    generated = payload.get("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    plotly_script = (
        '<script src="https://cdn.plot.ly/plotly-2.26.0.min.js" charset="utf-8"></script>'
        if HAS_PLOTLY else ""
    )

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(game['display_name'])} 预测回测分析报告</title>
{plotly_script}
<style>
  :root {{
    --bg: #f5f6f8; --card: #ffffff; --text: #1f2937; --muted: #6b7280;
    --border: #e5e7eb; --red: #ef4444; --blue: #3b82f6; --green: #10b981;
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--text);
         font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; }}
  .wrap {{ max-width: 1080px; margin: 0 auto; padding: 24px 16px 60px; }}
  header {{ background: var(--card); border: 1px solid var(--border);
            border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; }}
  header h1 {{ margin: 0 0 8px; font-size: 22px; }}
  .meta {{ color: var(--muted); font-size: 14px; line-height: 1.8; }}
  .card {{ background: var(--card); border: 1px solid var(--border);
           border-radius: 12px; padding: 16px; margin-bottom: 20px; }}
  .card h2 {{ margin: 0 0 12px; font-size: 17px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ border-bottom: 1px solid var(--border); padding: 8px 10px; text-align: center; }}
  th {{ background: #fafafa; color: var(--muted); font-weight: 600; }}
  .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 600; }}
  .red {{ color: var(--red); }} .blue {{ color: var(--blue); }}
  .badge {{ padding: 2px 8px; border-radius: 999px; font-size: 12px; }}
  .badge.ok {{ background: #ecfdf5; color: var(--green); }}
  .badge.no {{ background: #fef2f2; color: var(--red); }}
  .muted {{ color: var(--muted); }}
  footer {{ color: var(--muted); font-size: 13px; line-height: 1.7;
            border-top: 1px solid var(--border); padding-top: 16px; margin-top: 8px; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>{escape(game['display_name'])} 预测回测分析报告</h1>
    <div class="meta">
      生成时间: {escape(generated)}<br>
      数据规模: {data['n_records']} 期（{escape(data['date_range'])}）<br>
      玩法: 前区 {game['red_count']} 个 / 1-{game['red_max']}，后区 {game['blue_count']} 个 / 1-{game['blue_max']}，数据源 {escape(game['source'])}<br>
      目标置信度: <strong>{target:.0f}%</strong>
    </div>
  </header>

  <div class="card">
    <h2>图表</h2>
    {_charts_block(payload)}
  </div>

  <div class="card">
    <h2>回测指标明细</h2>
    {_metrics_table(payload)}
  </div>

  <div class="card">
    <h2>下一期推荐</h2>
    {_predictions_table(payload)}
  </div>

  <footer>
    <strong>⚠️ 免责声明</strong>：彩票开奖为独立均匀随机过程，任何策略在样本外都无法稳定超越随机基线，
    回测结果若高于基线通常来自过拟合。本报告仅供数据分析学习，不构成任何购彩建议，请理性对待彩票，切勿沉迷。
  </footer>
</div>
</body>
</html>"""
    return page


def generate_html_report(payload: Dict, out_dir: str) -> str:
    """生成并落盘 HTML 报告，返回文件路径。"""
    html = build_html(payload)
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"report_{stamp}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path
