#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""彩票预测系统 —— 双色球 / 大乐透 数据获取、策略预测、回测与报告。"""

from .config import GAMES, SSQ, DLT, GameConfig, TARGET_CONFIDENCE
from .service import PredictionService, build_strategies
from .backtest import Backtester

__all__ = [
    "GAMES", "SSQ", "DLT", "GameConfig", "TARGET_CONFIDENCE",
    "PredictionService", "build_strategies", "Backtester",
]
