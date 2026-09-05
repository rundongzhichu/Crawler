#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 双色球数据获取
 SSQ data fetcher —— 中国福彩网 cwl.gov.cn
=============================================================================

 数据源: https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice
 玩法:   name=ssq（红球 6 个 1-33 + 蓝球 1 个 1-16）

 原始返回字段（result 列表内每条）:
   code  期号
   date  开奖日期
   red   红球号码串（逗号分隔，如 "01,02,03,04,05,06"）
   blue  蓝球号码（单值，如 "16"）
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


class SSQFetcher(BaseFetcher):
    """双色球数据获取器。"""

    BASE_URL = (
        "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
    )

    def __init__(self, game: GameConfig):
        super().__init__(game)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": UserAgent().random,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.cwl.gov.cn/",
        })

    # ------------------------------------------------------------------
    #  抓取
    # ------------------------------------------------------------------

    def fetch_raw(self, limit: Optional[int] = None, page_size: int = 100,
                  sleep_time: float = 0.5, **kwargs) -> List[dict]:
        """分页抓取双色球开奖记录。

        Args:
            limit:     最多抓取记录条数，None 表示全部
            page_size: 每页条数（该接口支持较大 pageSize）
        """
        all_data: List[dict] = []
        page_no = 1
        total = None

        while True:
            params = {
                "name": self.game.name,
                "issueCount": "", "issueStart": "", "issueEnd": "",
                "dayStart": "", "dayEnd": "",
                "pageNo": page_no,
                "pageSize": page_size,
                "week": "",
                "systemType": "PC",
            }
            try:
                resp = self.session.get(
                    self.BASE_URL, params=params, timeout=15, verify=False
                )
                resp.encoding = "utf-8"
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                self.logger.error("抓取第 %d 页失败: %s", page_no, exc)
                break

            if total is None:
                total = int(data.get("total", 0) or 0)
            result = data.get("result") or []
            all_data.extend(result)
            self.logger.info("第 %d 页获取 %d 条（累计 %d / %d）",
                             page_no, len(result), len(all_data), total)

            if limit and len(all_data) >= limit:
                break
            if not result or page_no * page_size >= total:
                break

            page_no += 1
            time.sleep(sleep_time)

        if limit:
            all_data = all_data[:limit]
        self.logger.info("双色球共获取 %d 条记录", len(all_data))
        return all_data

    # ------------------------------------------------------------------
    #  解析
    # ------------------------------------------------------------------

    def parse(self, raw: List[dict]) -> pd.DataFrame:
        """将 cwl.gov.cn 原始记录解析为统一结构。"""
        records = []
        for item in raw:
            red_nums = [
                int(x) for x in str(item.get("red", "")).split(",")
                if x.strip().isdigit()
            ]
            blue_nums = [
                int(x) for x in str(item.get("blue", "")).split(",")
                if x.strip().isdigit()
            ]

            rec = {
                "issue": str(item.get("code", "")),
                "date": str(item.get("date", "")),
                "red_balls": ",".join(f"{n:02d}" for n in red_nums),
                "blue_balls": ",".join(f"{n:02d}" for n in blue_nums),
            }
            for i in range(self.game.red_count):
                rec[f"red{i + 1}"] = red_nums[i] if i < len(red_nums) else None
            for i in range(self.game.blue_count):
                rec[f"blue{i + 1}"] = blue_nums[i] if i < len(blue_nums) else None
            records.append(rec)

        return pd.DataFrame(records)
