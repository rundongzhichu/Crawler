#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 预测策略基类
 Base prediction strategy
=============================================================================

 所有策略统一产出 Prediction 对象，包含：
   - 具体推荐号码（red_balls / blue_balls）
   - 候选池（red_pool / blue_pool，用于覆盖命中率指标）
   - 每个号码的置信度分数 red_confidence / blue_confidence（用于校准指标）
   - 由推荐号码推导出的属性（和值 / 奇偶 / 大小 / 连号，用于属性预测指标）

 策略子类只需产出「每个号码的置信度分数」，其余（推荐、候选池、属性）
 由基类 _finalize() 统一完成。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List

import pandas as pd

from ..config import GameConfig, red_columns, blue_columns


def normalize(scores: Dict[int, float]) -> Dict[int, float]:
    """将分数 min-max 归一化到 [0, 1]（常量序列归一到 0.5）。"""
    if not scores:
        return {}
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-12:
        return {k: 0.5 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def extract_numbers(row: pd.Series, game: GameConfig, zone: str) -> List[int]:
    """从一行开奖记录中取出前区/后区号码列表。"""
    cols = red_columns(game) if zone == "red" else blue_columns(game)
    out = []
    for c in cols:
        try:
            v = int(row[c])
            if v > 0:
                out.append(v)
        except (ValueError, TypeError, KeyError):
            continue
    return out


def compute_properties(red_balls: List[int], game: GameConfig) -> Dict:
    """由推荐红球集合推导统计属性。"""
    if not red_balls:
        return {"sum": 0, "odd_count": 0, "big_count": 0, "has_consecutive": False}
    s = sorted(red_balls)
    total = sum(s)
    odd = sum(1 for n in s if n % 2 == 1)
    big = sum(1 for n in s if n > game.red_max / 2)
    consec = any(b - a == 1 for a, b in zip(s, s[1:]))
    return {
        "sum": total,
        "odd_count": odd,
        "big_count": big,
        "has_consecutive": bool(consec),
    }


@dataclass
class Prediction:
    """一次预测的完整结果。"""

    strategy: str
    red_balls: List[int]                       # 具体推荐红球（已排序）
    blue_balls: List[int]                      # 具体推荐蓝球（已排序）
    red_pool: List[int] = field(default_factory=list)   # 红球候选池
    blue_pool: List[int] = field(default_factory=list)  # 蓝球候选池
    red_confidence: Dict[int, float] = field(default_factory=dict)   # 全部红球置信度
    blue_confidence: Dict[int, float] = field(default_factory=dict)  # 全部蓝球置信度
    properties: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "red_balls": self.red_balls,
            "blue_balls": self.blue_balls,
            "red_pool": self.red_pool,
            "blue_pool": self.blue_pool,
            "properties": self.properties,
        }


class BaseStrategy(ABC):
    """预测策略抽象基类。

    子类需实现 predict(history) -> Prediction，并在其中调用
    self._finalize(red_conf, blue_conf) 完成统一封装。
    """

    name = "base"

    def __init__(self, game: GameConfig):
        self.game = game
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def predict(self, history: pd.DataFrame) -> Prediction:
        """根据历史开奖（日期升序）预测下一期。"""

    # ------------------------------------------------------------------
    #  统一封装
    # ------------------------------------------------------------------

    def _finalize(self, red_conf: Dict[int, float],
                  blue_conf: Dict[int, float]) -> Prediction:
        """由置信度分数生成推荐号码、候选池与属性。"""
        red_conf = normalize(red_conf)
        blue_conf = normalize(blue_conf)

        red_sorted = sorted(red_conf, key=red_conf.get, reverse=True)
        blue_sorted = sorted(blue_conf, key=blue_conf.get, reverse=True)

        red_balls = sorted(red_sorted[: self.game.red_count])
        blue_balls = sorted(blue_sorted[: self.game.blue_count])

        pred = Prediction(
            strategy=self.name,
            red_balls=red_balls,
            blue_balls=blue_balls,
            red_pool=red_sorted[: self.game.red_pool_size],
            blue_pool=blue_sorted[: self.game.blue_pool_size],
            red_confidence=red_conf,
            blue_confidence=blue_conf,
            properties=compute_properties(red_balls, self.game),
        )
        return pred
