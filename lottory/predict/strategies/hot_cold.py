#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 冷热号策略
 Hot/cold strategy —— 近期热度减去远期热度
=============================================================================

 置信度 = 近期窗口内的出现次数 - 远期窗口内的出现次数（对近期更敏感）。
 用于捕捉「近期转热」的号码。
"""

from __future__ import annotations

import pandas as pd

from .base import BaseStrategy, Prediction
from ..config import GameConfig, red_columns, blue_columns


class HotColdStrategy(BaseStrategy):
    """冷热号预测策略。"""

    name = "hot_cold"

    def __init__(self, game: GameConfig, window: int = 30):
        super().__init__(game)
        self.window = window

    def predict(self, history: pd.DataFrame) -> Prediction:
        red_conf = self._trend_score(history, "red")
        blue_conf = self._trend_score(history, "blue")
        return self._finalize(red_conf, blue_conf)

    def _trend_score(self, history: pd.DataFrame, zone: str) -> dict:
        cols = red_columns(self.game) if zone == "red" else blue_columns(self.game)
        mx = self.game.red_max if zone == "red" else self.game.blue_max
        scores = {n: 0.0 for n in range(1, mx + 1)}

        n = len(history)
        if n == 0:
            return scores

        recent = history.tail(self.window)
        earlier = history.iloc[: max(0, n - self.window)]

        def _count(frame, v):
            return sum(1 for _, row in frame.iterrows()
                       for c in cols if _match(row, c, v))

        for v in range(1, mx + 1):
            hot = _count(recent, v)
            cold = _count(earlier, v)
            # 近期热度权重高于远期
            scores[v] = hot * 1.0 - cold * 0.3
        return scores


def _match(row, col, v) -> bool:
    try:
        return int(row[col]) == v
    except (ValueError, TypeError):
        return False
