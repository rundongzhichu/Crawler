#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 机器学习策略（随机森林）
 Machine-learning strategy —— RandomForest 分类器
=============================================================================

 把「某个号码在下一期是否出现」建模为二分类问题。对每个号码构建特征：
   - lag1..lagN：过去 N 期是否出现
   - gap：距上次出现的期数
   - freq10 / freq30 / freq_all：不同窗口内的出现次数
   - is_odd / is_big：号码本身的奇偶 / 大小属性
 用随机森林输出每号码的「出现概率」作为置信度分数。

 当历史数据不足时回退到频率策略。
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .base import BaseStrategy, Prediction
from .frequency import FrequencyStrategy
from ..config import GameConfig, red_columns, blue_columns


class MLStrategy(BaseStrategy):
    """随机森林机器学习预测策略。"""

    name = "ml"

    def __init__(self, game: GameConfig, lag: int = 5, min_train: int = 40,
                 n_estimators: int = 100, random_state: int = 0):
        super().__init__(game)
        self.lag = lag
        self.min_train = min_train
        self.n_estimators = n_estimators
        self.random_state = random_state
        self._fallback = FrequencyStrategy(game)

    def predict(self, history: pd.DataFrame) -> Prediction:
        if len(history) < self.min_train:
            self.logger.info("历史数据不足 %d 期，回退到频率策略", self.min_train)
            return self._fallback.predict(history)

        red_conf = self._predict_zone(history, "red")
        blue_conf = self._predict_zone(history, "blue")
        return self._finalize(red_conf, blue_conf)

    # ------------------------------------------------------------------
    #  建模
    # ------------------------------------------------------------------

    def _predict_zone(self, history: pd.DataFrame, zone: str) -> dict:
        cols = red_columns(self.game) if zone == "red" else blue_columns(self.game)
        mx = self.game.red_max if zone == "red" else self.game.blue_max

        presence = self._presence_matrix(history, cols, mx)
        n = presence.shape[0]

        X_train, y_train = self._build_samples(presence, n, mx, end=n - 1)
        if X_train.empty:
            return {v: 0.5 for v in range(1, mx + 1)}

        from sklearn.ensemble import RandomForestClassifier  # 延迟导入

        clf = RandomForestClassifier(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            n_jobs=-1,
        )
        clf.fit(X_train, y_train)

        # 用当前（最后一期）的特征预测下一期
        X_next = self._build_samples(presence, n, mx, end=n, next_only=True)
        proba = clf.predict_proba(X_next)[:, 1]
        return {v: float(proba[v - 1]) for v in range(1, mx + 1)}

    def _presence_matrix(self, history: pd.DataFrame, cols, mx) -> np.ndarray:
        n = len(history)
        presence = np.zeros((n, mx + 1), dtype=np.int8)
        for i, (_, row) in enumerate(history.iterrows()):
            for c in cols:
                try:
                    v = int(row[c])
                    if 1 <= v <= mx:
                        presence[i, v] = 1
                except (ValueError, TypeError):
                    continue
        return presence

    def _build_samples(self, presence, n, mx, end, next_only: bool = False):
        """构建特征矩阵。

        - 训练模式: 对第 i 期（lag <= i <= end），用 i 之前的信息预测 i 期；
        - 预测模式: 只产出「第 n 期之后」一期的样本（end = n）。
        """
        rows = []
        if next_only:
            indices = [n]  # 预测下一期，特征取自 0..n-1
        else:
            indices = list(range(self.lag, end + 1))

        for i in indices:
            for num in range(1, mx + 1):
                feat = {
                    "number": num,
                    "is_odd": num % 2,
                    "is_big": 1 if num > mx / 2 else 0,
                    "gap": self._gap(presence, i, num),
                }
                for j in range(1, self.lag + 1):
                    feat[f"lag{j}"] = int(presence[i - j, num]) if i - j >= 0 else 0
                lo10 = max(0, i - 10)
                lo30 = max(0, i - 30)
                feat["freq10"] = int(presence[lo10:i, num].sum())
                feat["freq30"] = int(presence[lo30:i, num].sum())
                feat["freq_all"] = int(presence[:i, num].sum())
                rows.append(feat)

        X = pd.DataFrame(rows)
        if next_only:
            return X
        y = np.array([
            int(presence[i, num]) for i in indices for num in range(1, mx + 1)
        ])
        return X, y

    @staticmethod
    def _gap(presence, i, num, cap: int = 50) -> int:
        col = presence[:i, num]
        idx = np.where(col == 1)[0]
        if len(idx) == 0:
            return cap
        return min(cap, i - int(idx[-1]))
