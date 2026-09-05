#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 主预测服务
 Prediction service —— 编排数据获取 / 策略应用 / 回测 / 报告
=============================================================================

 职责：
   1. 根据玩法类型选择对应的数据获取器（SSQ / DLT / 合成）
   2. 组织一组预测策略（含随机基线）
   3. 执行滚动回测，产出三项指标
   4. 生成下一期推荐
   5. 记录完整预测过程（日志 + 结构化运行记录 JSON）
   6. 生成分析报告（文本 / JSON / Markdown）
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from .config import GAMES, GameConfig, TARGET_CONFIDENCE
from .data.base import BaseFetcher
from .data.ssq import SSQFetcher
from .data.dlt import DLTFetcher
from .data.synthetic import SyntheticFetcher
from .strategies import (
    BaseStrategy, Prediction, RandomStrategy,
    FrequencyStrategy, HotColdStrategy, MLStrategy, HybridStrategy,
)
from .backtest import Backtester
from .report import generate_report
from .visual import generate_html_report


# 可用策略工厂
STRATEGY_FACTORY = {
    "random": lambda g: RandomStrategy(g),
    "frequency": lambda g: FrequencyStrategy(g),
    "hot_cold": lambda g: HotColdStrategy(g),
    "ml": lambda g: MLStrategy(g),
    "hybrid": lambda g: HybridStrategy(g),
}


def build_strategies(game: GameConfig, names: Optional[List[str]] = None) -> List[BaseStrategy]:
    """按名称列表构建策略；None 表示全部策略（含随机基线）。"""
    if names is None:
        names = ["random", "frequency", "hot_cold", "ml", "hybrid"]
    strategies = []
    for n in names:
        if n in STRATEGY_FACTORY:
            strategies.append(STRATEGY_FACTORY[n](game))
        else:
            logging.getLogger("service").warning("未知策略: %s，已跳过", n)
    # 保证随机基线存在
    if not any(s.name == "random" for s in strategies):
        strategies.insert(0, RandomStrategy(game))
    return strategies


class PredictionService:
    """主预测服务：统一入口，负责全流程编排与过程记录。"""

    def __init__(self, game_name: str, strategies: Optional[List[str]] = None,
                 output_dir: str = "runs"):
        if game_name not in GAMES:
            raise ValueError(f"未知玩法: {game_name}，可选 {list(GAMES)}")

        self.game: GameConfig = GAMES[game_name]
        self.strategy_names = strategies
        self.output_dir = output_dir
        self.logger = logging.getLogger(self.__class__.__name__)

        self.fetcher: BaseFetcher = self._default_fetcher(game_name)
        self.strategies = build_strategies(self.game, strategies)
        self.backtester = Backtester(self.game, self.strategies)

        # 结构化运行记录（记录预测过程）
        self.run_record: Dict = {"steps": []}

    # ------------------------------------------------------------------
    #  数据获取
    # ------------------------------------------------------------------

    def _default_fetcher(self, game_name: str) -> BaseFetcher:
        return SSQFetcher(self.game) if game_name == "ssq" else DLTFetcher(self.game)

    def get_data(self, limit: Optional[int] = None,
                 data_file: Optional[str] = None,
                 synthetic: Optional[int] = None) -> pd.DataFrame:
        """获取历史数据：优先级 指定文件 > 合成数据 > 在线抓取。"""
        if data_file:
            self._record("load", f"加载本地数据 {data_file}")
            df = self.fetcher.load(data_file)
        elif synthetic:
            self._record("synthetic", f"生成 {synthetic} 期合成数据")
            df = SyntheticFetcher(self.game).fetch(limit=synthetic)
        else:
            self._record("crawl", "在线抓取数据")
            df = self.fetcher.fetch(limit=limit)

        self._record("data", f"得到 {len(df)} 期数据")
        return df

    # ------------------------------------------------------------------
    #  回测 + 预测
    # ------------------------------------------------------------------

    def backtest(self, df: pd.DataFrame, test_size: int = 50) -> Dict:
        self._record("backtest", f"滚动回测 {test_size} 期")
        return self.backtester.run(df, test_size=test_size)

    def predict_next(self, df: pd.DataFrame) -> List[Prediction]:
        predictions = []
        for strategy in self.strategies:
            pred = strategy.predict(df)
            predictions.append(pred)
            self._record("predict", f"策略 {strategy.name} 推荐 "
                         f"红球 {pred.red_balls} 蓝球 {pred.blue_balls}")
        return predictions

    # ------------------------------------------------------------------
    #  总流程
    # ------------------------------------------------------------------

    def run(self, limit: Optional[int] = None, data_file: Optional[str] = None,
            synthetic: Optional[int] = None, test_size: int = 50) -> Dict:
        """执行完整流程：获取数据 → 回测 → 预测 → 报告，并返回结果。"""
        self.logger.info("=" * 50)
        self.logger.info("启动预测服务: %s", self.game.display_name)
        self.logger.info("=" * 50)

        df = self.get_data(limit=limit, data_file=data_file, synthetic=synthetic)
        if df.empty:
            self.logger.error("无可用数据，流程终止")
            return {}

        backtest = self.backtest(df, test_size=test_size)
        next_predictions = self.predict_next(df)

        payload = self._build_payload(df, backtest, next_predictions)

        # 记录过程到本地 JSON（runs/ 目录，追加式历史）
        self._save_run_record(payload)

        report = generate_report(payload, self.output_dir)
        report["html"] = generate_html_report(payload, self.output_dir)
        self.logger.info("报告已生成: %s", report["json"])

        self.run_record["report_paths"] = report
        return {**payload, "report": report}

    # ------------------------------------------------------------------
    #  过程记录
    # ------------------------------------------------------------------

    def _record(self, step: str, detail: str):
        self.run_record["steps"].append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "step": step,
            "detail": detail,
        })
        self.logger.info("[%s] %s", step, detail)

    def _build_payload(self, df, backtest, next_predictions) -> Dict:
        date_range = (
            f"{df['date'].min()} ~ {df['date'].max()}" if not df.empty else "N/A"
        )
        return {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target": TARGET_CONFIDENCE,
            "game": {
                "name": self.game.name,
                "display_name": self.game.display_name,
                "red_count": self.game.red_count,
                "red_max": self.game.red_max,
                "blue_count": self.game.blue_count,
                "blue_max": self.game.blue_max,
                "source": self.game.source,
            },
            "data": {
                "n_records": int(len(df)),
                "date_range": date_range,
            },
            "strategies": [s.name for s in self.strategies],
            "baseline_strategy": "random",
            "backtest": backtest,
            "next_predictions": [p.to_dict() for p in next_predictions],
            "process": self.run_record["steps"],
        }

    def _save_run_record(self, payload: Dict):
        """把本次运行记录追加到 runs/history.jsonl。"""
        os.makedirs(self.output_dir, exist_ok=True)
        history_path = os.path.join(self.output_dir, "history.jsonl")
        with open(history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        self.logger.info("运行记录已追加 → %s", history_path)
