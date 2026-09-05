#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 频率统计策略
 Frequency strategy —— 按历史出现频率加权打分
=============================================================================

 每个号码的置信度 = 历史出现频率的指数衰减加权和（越近的期权重越高）。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import BaseStrategy, Prediction
from ..config import GameConfig, red_columns, blue_columns


class FrequencyStrategy(BaseStrategy):
    """频率统计预测策略。"""

    name = "frequency"

    def __init__(self, game: GameConfig, decay: float = 0.92):
        super().__init__(game)
        self.decay = decay

    def predict(self, history: pd.DataFrame) -> Prediction:
        red_conf = self._weighted_freq(history, "red")
        blue_conf = self._weighted_freq(history, "blue")
        return self._finalize(red_conf, blue_conf)

    def _weighted_freq(self, history: pd.DataFrame, zone: str) -> dict:
        cols = red_columns(self.game) if zone == "red" else blue_columns(self.game)
        mx = self.game.red_max if zone == "red" else self.game.blue_max
        scores = {n: 0.0 for n in range(1, mx + 1)}

        n = len(history)
        if n == 0:
            return scores

        # 指数衰减权重，索引 0 为最旧一期
        weights = self.decay ** np.arange(n - 1, -1, -1)

        for i, (_, row) in enumerate(history.iterrows()):
            w = weights[i]
            for c in cols:
                try:
                    v = int(row[c])
                    if 1 <= v <= mx:
                        scores[v] += w
                except (ValueError, TypeError):
                    continue
        return scores
