#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""预测策略层 —— 策略基类与多种预测策略。"""

from .base import BaseStrategy, Prediction, compute_properties
from .random import RandomStrategy
from .frequency import FrequencyStrategy
from .hot_cold import HotColdStrategy
from .ml import MLStrategy
from .hybrid import HybridStrategy

__all__ = [
    "BaseStrategy",
    "Prediction",
    "compute_properties",
    "RandomStrategy",
    "FrequencyStrategy",
    "HotColdStrategy",
    "MLStrategy",
    "HybridStrategy",
]
