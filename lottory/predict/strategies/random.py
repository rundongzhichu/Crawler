#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 随机策略（基线）
 Random strategy —— 均匀随机，作为回测的基线参照
=============================================================================

 每个号码的置信度完全随机。它在任何指标上的表现都代表了「无信息」
 情况下能达到的水平，用于与其它策略对比，判断是否有真实的统计优势。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import BaseStrategy, Prediction
from ..config import GameConfig


class RandomStrategy(BaseStrategy):
    """均匀随机预测策略。"""

    name = "random"

    def __init__(self, game: GameConfig, seed: int = 0):
        super().__init__(game)
        self.rng = np.random.default_rng(seed)

    def predict(self, history: pd.DataFrame) -> Prediction:
        red_conf = {
            n: float(self.rng.random())
            for n in range(1, self.game.red_max + 1)
        }
        blue_conf = {
            n: float(self.rng.random())
            for n in range(1, self.game.blue_max + 1)
        }
        return self._finalize(red_conf, blue_conf)
