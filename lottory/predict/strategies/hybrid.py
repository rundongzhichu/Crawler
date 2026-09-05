#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 混合投票策略
 Hybrid strategy —— 对多个子策略的置信度做加权平均
=============================================================================

 将若干子策略（频率 / 冷热 / 机器学习）对每个号码的置信度分数加权求和，
 得到综合置信度。默认等权，可传入自定义权重。
"""

from __future__ import annotations

import pandas as pd

from .base import BaseStrategy, Prediction
from ..config import GameConfig


class HybridStrategy(BaseStrategy):
    """混合投票预测策略。"""

    name = "hybrid"

    def __init__(self, game: GameConfig, strategies: list = None,
                 weights: list = None):
        super().__init__(game)
        self.strategies = strategies or self._default_strategies(game)
        if weights is None:
            weights = [1.0] * len(self.strategies)
        self.weights = weights

    @staticmethod
    def _default_strategies(game: GameConfig):
        from .frequency import FrequencyStrategy
        from .hot_cold import HotColdStrategy
        from .ml import MLStrategy
        return [
            FrequencyStrategy(game),
            HotColdStrategy(game),
            MLStrategy(game),
        ]

    def predict(self, history: pd.DataFrame) -> Prediction:
        preds = [s.predict(history) for s in self.strategies]

        red_conf = self._blend([p.red_confidence for p in preds])
        blue_conf = self._blend([p.blue_confidence for p in preds])
        return self._finalize(red_conf, blue_conf)

    def _blend(self, conf_list: list) -> dict:
        keys = set().union(*[set(c) for c in conf_list if c]) if conf_list else set()
        blended = {}
        for k in keys:
            total = 0.0
            wsum = 0.0
            for c, w in zip(conf_list, self.weights):
                if k in c:
                    total += w * c[k]
                    wsum += w
            blended[k] = total / wsum if wsum else 0.0
        return blended
