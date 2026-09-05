#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 合成数据获取器（离线测试用）
 Synthetic data fetcher —— 无网络环境下生成随机历史数据
=============================================================================

 用于在无法访问官方接口时验证整条流水线（数据 → 回测 → 报告）可运行。
 生成的数据为均匀随机开奖，因此回测指标会落在随机基线附近——这正好
 用来验证系统行为正确，而非追求高命中率。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd

from .base import BaseFetcher
from ..config import GameConfig


class SyntheticFetcher(BaseFetcher):
    """生成均匀随机的历史开奖数据，供离线回测/演示。"""

    def __init__(self, game: GameConfig, seed: int = 42):
        super().__init__(game)
        self.rng = np.random.default_rng(seed)

    def fetch_raw(self, limit: Optional[int] = None, **kwargs) -> List[dict]:
        n = limit or 300
        base = datetime(2018, 1, 1)
        raw = []
        # 期号从大到小递减（最新在前），日期随 i 单调递增（旧 → 新）
        for i in range(n, 0, -1):
            red = sorted(self.rng.choice(
                np.arange(1, self.game.red_max + 1),
                size=self.game.red_count, replace=False,
            ).tolist())
            blue = sorted(self.rng.choice(
                np.arange(1, self.game.blue_max + 1),
                size=self.game.blue_count, replace=False,
            ).tolist())
            draw_date = (base + timedelta(days=(n - i) * 3)).strftime("%Y-%m-%d")
            raw.append({
                "code": f"{self.game.name}{2020000 + i}",
                "date": draw_date,
                "red": ",".join(f"{x:02d}" for x in red),
                "blue": ",".join(f"{x:02d}" for x in blue),
            })
        self.logger.info("生成 %d 条合成数据（%s）", n, self.game.display_name)
        return raw

    def parse(self, raw: List[dict]) -> pd.DataFrame:
        records = []
        for item in raw:
            red_nums = [int(x) for x in item["red"].split(",")]
            blue_nums = [int(x) for x in item["blue"].split(",")]
            rec = {
                "issue": item["code"],
                "date": item["date"],
                "red_balls": item["red"],
                "blue_balls": item["blue"],
            }
            for i in range(self.game.red_count):
                rec[f"red{i + 1}"] = red_nums[i]
            for i in range(self.game.blue_count):
                rec[f"blue{i + 1}"] = blue_nums[i]
            records.append(rec)
        return pd.DataFrame(records)
