#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 数据获取基类
 Base data fetcher
=============================================================================

 定义所有玩法数据获取的统一接口与统一数据结构。子类只需实现
 fetch_raw()（抓取原始数据）与 parse()（解析为统一 DataFrame），
 即可复用统一的收尾（列补齐 / 排序）、存储、加载能力。

 统一 DataFrame 结构（两种玩法一致）：
   issue       期号
   date        开奖日期
   red1..redN  前区号码（N = red_count）
   blue1..blueM 后区号码（M = blue_count）
   red_balls   前区号码串（逗号分隔）
   blue_balls  后区号码串（逗号分隔）
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional

import pandas as pd

from ..config import GameConfig, red_columns, blue_columns


class BaseFetcher(ABC):
    """数据获取抽象基类。

    子类需实现:
        fetch_raw(limit, **kwargs) -> list[dict]  从数据源抓取原始记录
        parse(raw)                 -> DataFrame   解析为统一结构
    """

    def __init__(self, game: GameConfig):
        self.game = game
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    #  子类必须实现
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch_raw(self, limit: Optional[int] = None, **kwargs) -> List[dict]:
        """从数据源抓取原始开奖记录列表。

        Args:
            limit: 最多抓取的记录条数，None 表示全部
        """

    @abstractmethod
    def parse(self, raw: List[dict]) -> pd.DataFrame:
        """将原始记录解析为统一结构的 DataFrame。"""

    # ------------------------------------------------------------------
    #  统一入口
    # ------------------------------------------------------------------

    def fetch(self, limit: Optional[int] = None, **kwargs) -> pd.DataFrame:
        """抓取并解析，返回统一结构的 DataFrame（按日期升序）。"""
        raw = self.fetch_raw(limit=limit, **kwargs)
        if not raw:
            self.logger.warning("未获取到任何原始数据")
            return self._finalize(pd.DataFrame())
        df = self.parse(raw)
        return self._finalize(df)

    # ------------------------------------------------------------------
    #  统一收尾 / 存储
    # ------------------------------------------------------------------

    def _finalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """补齐必需列、剔除无号码行、按日期升序排序。"""
        if df is None or df.empty:
            df = pd.DataFrame()

        required = (
            ["issue", "date", "red_balls", "blue_balls"]
            + red_columns(self.game)
            + blue_columns(self.game)
        )
        for col in required:
            if col not in df.columns:
                df[col] = None

        # 剔除缺少前区第一位的无效行
        first_red = red_columns(self.game)[0]
        df = df[df[first_red].notna()].copy()

        df = df.sort_values("date", ascending=True).reset_index(drop=True)
        return df

    def save(self, df: pd.DataFrame, path: str) -> str:
        """保存为 Excel，返回路径。"""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        df.to_excel(path, index=False)
        self.logger.info("数据已保存 → %s", path)
        return path

    def load(self, path: str) -> pd.DataFrame:
        """从 Excel 加载历史数据。"""
        df = pd.read_excel(path)
        return self._finalize(df)
