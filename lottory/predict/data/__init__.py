#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据获取层 —— 统一的数据获取抽象与各玩法实现。"""

from .base import BaseFetcher
from .ssq import SSQFetcher
from .dlt import DLTFetcher
from .synthetic import SyntheticFetcher

__all__ = ["BaseFetcher", "SSQFetcher", "DLTFetcher", "SyntheticFetcher"]
