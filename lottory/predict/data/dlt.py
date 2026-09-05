#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 大乐透数据获取
 DLT data fetcher —— 国家体育总局彩票中心 sporttery.cn
=============================================================================

 数据源: https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry
 玩法:   gameNo=85（前区 5 个 1-35 + 后区 2 个 1-12）

 原始返回字段（value.list 内每条）:
   lotteryDrawNum     期号
   lotteryDrawTime    开奖时间
   lotteryDrawResult  开奖号码（空格分隔，前 5 红球 + 后 2 蓝球）
"""

from __future__ import annotations

import time
from typing import List, Optional

import pandas as pd
import requests
import urllib3
from fake_useragent import UserAgent

from .base import BaseFetcher
from ..config import GameConfig

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class DLTFetcher(BaseFetcher):
    """大乐透数据获取器。"""

    BASE_URL = (
        "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
    )

    def __init__(self, game: GameConfig):
        super().__init__(game)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": UserAgent().random,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.sporttery.cn/",
            "Origin": "https://www.sporttery.cn",
        })

    # ------------------------------------------------------------------
    #  抓取
    # ------------------------------------------------------------------

    def fetch_raw(self, limit: Optional[int] = None, page_size: int = 30,
                  sleep_time: float = 1.0, **kwargs) -> List[dict]:
        """分页抓取大乐透开奖记录。

        Args:
            limit:     最多抓取记录条数，None 表示全部
            page_size: 每页条数（官方接口固定 30 左右）
        """
        all_data: List[dict] = []
        page_no = 1

        while True:
            params = {
                "gameNo": "85",
                "provinceId": "0",
                "pageSize": str(page_size),
                "pageNo": str(page_no),
                "isVerify": "1",
            }
            try:
                resp = self.session.get(
                    self.BASE_URL, params=params, timeout=15, verify=False
                )
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                self.logger.error("抓取第 %d 页失败: %s", page_no, exc)
                break

            value = data.get("value") or {}
            result = value.get("list") or []
            all_data.extend(result)
            self.logger.info("第 %d 页获取 %d 条（累计 %d）",
                             page_no, len(result), len(all_data))

            if limit and len(all_data) >= limit:
                break
            if len(result) < page_size:
                break

            page_no += 1
            time.sleep(sleep_time)

        if limit:
            all_data = all_data[:limit]
        self.logger.info("大乐透共获取 %d 条记录", len(all_data))
        return all_data

    # ------------------------------------------------------------------
    #  解析
    # ------------------------------------------------------------------

    def parse(self, raw: List[dict]) -> pd.DataFrame:
        """将 sporttery.cn 原始记录解析为统一结构。"""
        records = []
        for item in raw:
            # 号码串为空格分隔，前 red_count 个为红球，后 blue_count 个为蓝球
            draw = str(item.get("lotteryDrawResult", "")).split()
            nums = [int(x) for x in draw if x.isdigit()]
            red_nums = nums[: self.game.red_count]
            blue_nums = nums[self.game.red_count: self.game.red_count + self.game.blue_count]

            rec = {
                "issue": str(item.get("lotteryDrawNum", "")),
                "date": str(item.get("lotteryDrawTime", ""))[:10],
                "red_balls": ",".join(f"{n:02d}" for n in red_nums),
                "blue_balls": ",".join(f"{n:02d}" for n in blue_nums),
            }
            for i in range(self.game.red_count):
                rec[f"red{i + 1}"] = red_nums[i] if i < len(red_nums) else None
            for i in range(self.game.blue_count):
                rec[f"blue{i + 1}"] = blue_nums[i] if i < len(blue_nums) else None
            records.append(rec)

        return pd.DataFrame(records)
