#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 回测模块
 Backtester —— 三项指标的回测评估
=============================================================================

 采用「走一步预测一步」的滚动方式（walk-forward），避免未来信息泄漏：
 对第 i 期，仅用 i 期之前的历史训练，再与第 i 期真实开奖对比。

 三项指标（均输出：实测值 / 随机基线 / 是否达到 70% 目标）：
   1. 覆盖命中率 coverage      —— 候选池覆盖实际开奖号码的比例
   2. 置信度校准 calibration   —— 各置信度分桶的命中率，及高置信区间命中率
   3. 属性预测 property        —— 和值档位 / 奇偶个数 / 大小个数 的预测准确率

 注意：彩票开奖是独立均匀随机过程，随机基线即为理论上限。回测高于基线
 通常来自过拟合，而非真实优势。
"""

from __future__ import annotations

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

from .config import GameConfig, TARGET_CONFIDENCE
from .strategies.base import BaseStrategy, Prediction, compute_properties, extract_numbers


class Backtester:
    """对若干策略在历史数据上做滚动回测。"""

    def __init__(self, game: GameConfig, strategies: List[BaseStrategy]):
        self.game = game
        self.strategies = strategies
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    #  入口
    # ------------------------------------------------------------------

    def run(self, df: pd.DataFrame, test_size: int = 50) -> Dict:
        """对每个策略执行回测，返回 {strategy_name: metrics}。"""
        df = df.sort_values("date", ascending=True).reset_index(drop=True)
        n = len(df)
        if n < 20:
            self.logger.error("数据量不足（%d 期），无法回测", n)
            return {}

        test_size = min(test_size, max(1, n // 5))
        n_train = n - test_size

        # 和值档位阈值（仅用训练段计算，避免泄漏）
        sum_bins = self._sum_bins(df.iloc[:n_train])

        results = {}
        for strategy in self.strategies:
            self.logger.info("回测策略: %s", strategy.name)
            results[strategy.name] = self._run_one(
                df, strategy, n_train, test_size, sum_bins
            )
        return results

    # ------------------------------------------------------------------
    #  单项策略回测
    # ------------------------------------------------------------------

    def _run_one(self, df, strategy, n_train, test_size, sum_bins) -> dict:
        cov_red: List[float] = []
        cov_blue: List[float] = []
        prop_hits = {"sum_level": 0, "odd_count": 0, "big_count": 0}
        red_conf_pairs: List[tuple] = []
        blue_conf_pairs: List[tuple] = []

        for i in range(n_train, n_train + test_size):
            train = df.iloc[:i]
            row = df.iloc[i]
            actual_red = extract_numbers(row, self.game, "red")
            actual_blue = extract_numbers(row, self.game, "blue")

            pred = strategy.predict(train)

            # 1) 覆盖命中率
            cov_red.append(
                len(set(actual_red) & set(pred.red_pool)) / self.game.red_count
            )
            cov_blue.append(
                len(set(actual_blue) & set(pred.blue_pool)) / self.game.blue_count
            )

            # 2) 属性预测
            ap = compute_properties(actual_red, self.game)
            if self._sum_level(pred.properties["sum"], sum_bins) == \
                    self._sum_level(ap["sum"], sum_bins):
                prop_hits["sum_level"] += 1
            if pred.properties["odd_count"] == ap["odd_count"]:
                prop_hits["odd_count"] += 1
            if pred.properties["big_count"] == ap["big_count"]:
                prop_hits["big_count"] += 1

            # 3) 置信度校准样本（每个号码一条 (置信度, 是否命中)）
            for num in range(1, self.game.red_max + 1):
                red_conf_pairs.append(
                    (pred.red_confidence.get(num, 0.0), 1.0 if num in actual_red else 0.0)
                )
            for num in range(1, self.game.blue_max + 1):
                blue_conf_pairs.append(
                    (pred.blue_confidence.get(num, 0.0), 1.0 if num in actual_blue else 0.0)
                )

        n_test = test_size
        coverage = self._coverage(cov_red, cov_blue)
        calibration = self._calibration(red_conf_pairs, blue_conf_pairs)
        properties = self._properties(prop_hits, n_test)

        return {
            "n_test": n_test,
            "coverage": coverage,
            "calibration": calibration,
            "properties": properties,
        }

    # ------------------------------------------------------------------
    #  指标聚合
    # ------------------------------------------------------------------

    def _coverage(self, cov_red, cov_blue) -> dict:
        red_mean = float(np.mean(cov_red)) if cov_red else 0.0
        blue_mean = float(np.mean(cov_blue)) if cov_blue else 0.0
        overall = (red_mean + blue_mean) / 2.0
        return {
            "red": red_mean,
            "blue": blue_mean,
            "overall": overall,
            "target": TARGET_CONFIDENCE,
            "red_pool_size": self.game.red_pool_size,
            "blue_pool_size": self.game.blue_pool_size,
            "met": overall >= TARGET_CONFIDENCE,
        }

    def _calibration(self, red_pairs, blue_pairs) -> dict:
        red = self._calibration_zone(red_pairs)
        blue = self._calibration_zone(blue_pairs)
        return {
            "red": red,
            "blue": blue,
            "target": TARGET_CONFIDENCE,
            # 以高置信区间（>=0.7）命中率是否达标作为整体判定
            "met": (red["high_conf_hit_rate"] >= TARGET_CONFIDENCE or
                    blue["high_conf_hit_rate"] >= TARGET_CONFIDENCE),
        }

    def _calibration_zone(self, pairs) -> dict:
        if not pairs:
            return {"baseline": 0.0, "high_conf_hit_rate": 0.0, "bins": []}

        confs = np.array([p[0] for p in pairs])
        hits = np.array([p[1] for p in pairs])

        baseline = float(hits.mean())

        # 10 个置信度分桶
        edges = np.linspace(0.0, 1.0, 11)
        bins = []
        for k in range(10):
            lo, hi = edges[k], edges[k + 1]
            mask = (confs >= lo) & (confs < hi)
            if hi >= 1.0:
                mask = (confs >= lo) & (confs <= hi)
            n = int(mask.sum())
            hr = float(hits[mask].mean()) if n else 0.0
            bins.append({"range": [round(lo, 2), round(hi, 2)], "n": n, "hit_rate": round(hr, 4)})

        high_mask = confs >= TARGET_CONFIDENCE
        high_n = int(high_mask.sum())
        high_conf_hit_rate = float(hits[high_mask].mean()) if high_n else 0.0

        return {
            "baseline": round(baseline, 4),
            "high_conf_hit_rate": round(high_conf_hit_rate, 4),
            "high_conf_n": high_n,
            "bins": bins,
        }

    def _properties(self, prop_hits, n_test) -> dict:
        acc = {k: (v / n_test if n_test else 0.0) for k, v in prop_hits.items()}
        overall = float(np.mean(list(acc.values())))
        return {
            "sum_level": acc["sum_level"],
            "odd_count": acc["odd_count"],
            "big_count": acc["big_count"],
            "overall": overall,
            "target": TARGET_CONFIDENCE,
            "met": overall >= TARGET_CONFIDENCE,
        }

    # ------------------------------------------------------------------
    #  辅助
    # ------------------------------------------------------------------

    def _sum_bins(self, train_df) -> tuple:
        """用训练段和值分布的三分位数作为档位阈值。"""
        sums = []
        for _, row in train_df.iterrows():
            red = extract_numbers(row, self.game, "red")
            if red:
                sums.append(sum(red))
        if len(sums) < 3:
            return (0, float("inf"))
        q1, q2 = np.percentile(sums, [33.3, 66.7])
        return (float(q1), float(q2))

    @staticmethod
    def _sum_level(total, bins) -> str:
        lo, hi = bins
        if total <= lo:
            return "low"
        if total <= hi:
            return "mid"
        return "high"
