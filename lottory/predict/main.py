#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 彩票预测系统 - 命令行入口
 CLI entry point
=============================================================================

 使用示例：
   # 合成数据离线回测（无需网络，验证流程）
   python main.py --game dlt --synthetic 300 --test-size 50

   # 在线抓取并回测
   python main.py --game ssq --crawl-limit 500 --test-size 100

   # 指定本地数据文件
   python main.py --game dlt --data-file data/20260905/dlt_history.xlsx

   # 指定策略
   python main.py --game dlt --strategies frequency,hot_cold,ml,hybrid
=============================================================================
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime

# 使本目录可作为包根导入（predict.* 相对导入依赖此路径）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lottory.predict.service import PredictionService  # noqa: E402
from lottory.predict.config import GAMES  # noqa: E402


def setup_logging():
    """统一日志配置：同时输出到控制台与 logs/ 目录。"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(
        log_dir, f"predict_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.setLevel(logging.INFO)
    root.addHandler(fh)
    root.addHandler(sh)
    return log_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="双色球 / 大乐透 预测回测系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--game", choices=list(GAMES), default="dlt",
                        help="玩法: ssq(双色球) / dlt(大乐透)，默认 dlt")
    parser.add_argument("--crawl-limit", type=int, default=None,
                        help="在线抓取的最大记录条数（默认全部）")
    parser.add_argument("--data-file", default=None,
                        help="指定本地 Excel 数据文件（跳过抓取）")
    parser.add_argument("--synthetic", type=int, default=None,
                        help="生成 N 期合成数据做离线回测")
    parser.add_argument("--test-size", type=int, default=50,
                        help="回测期数（默认 50）")
    parser.add_argument("--strategies", default=None,
                        help="逗号分隔的策略列表: random,frequency,hot_cold,ml,hybrid")
    parser.add_argument("--output-dir", default="runs",
                        help="报告输出目录（默认 runs/）")
    return parser


def main():
    log_file = setup_logging()
    args = build_parser().parse_args()

    strategy_list = None
    if args.strategies:
        strategy_list = [s.strip() for s in args.strategies.split(",") if s.strip()]

    service = PredictionService(
        game_name=args.game,
        strategies=strategy_list,
        output_dir=args.output_dir,
    )

    result = service.run(
        limit=args.crawl_limit,
        data_file=args.data_file,
        synthetic=args.synthetic,
        test_size=args.test_size,
    )

    # 打印文本报告
    if result and result.get("report"):
        print("\n" + result["report"]["text"])

    logging.getLogger("main").info("日志文件: %s", log_file)


if __name__ == "__main__":
    main()
