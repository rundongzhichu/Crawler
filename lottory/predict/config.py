#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 彩票预测系统 - 游戏配置
 Game configuration for the lottery prediction system
=============================================================================

 统一描述双色球 / 大乐透两种玩法的号码范围，供数据层、策略层、回测层共用。
 两种玩法被抽象为同一套字段（前区 red / 后区 blue），仅数量与范围不同。
"""

from __future__ import annotations

from dataclasses import dataclass


# 回测目标置信度（用户口径：>= 70%）
TARGET_CONFIDENCE = 0.70


@dataclass(frozen=True)
class GameConfig:
    """单种彩票玩法的静态配置。

    Attributes:
        name:           玩法英文标识，如 "ssq" / "dlt"
        display_name:   中文名
        red_count:      前区（红球）每期开奖个数
        red_max:        前区号码取值范围上限（1 ~ red_max）
        blue_count:     后区（蓝球）每期开奖个数
        blue_max:       后区号码取值范围上限
        red_pool_size:  候选池推荐的前区号码数量（用于覆盖命中率指标）
        blue_pool_size: 候选池推荐的后区号码数量
        source:         官方数据来源
    """

    name: str
    display_name: str
    red_count: int
    red_max: int
    blue_count: int
    blue_max: int
    red_pool_size: int
    blue_pool_size: int
    source: str


SSQ = GameConfig(
    name="ssq",
    display_name="双色球",
    red_count=6,
    red_max=33,
    blue_count=1,
    blue_max=16,
    red_pool_size=12,
    blue_pool_size=4,
    source="cwl.gov.cn",
)

DLT = GameConfig(
    name="dlt",
    display_name="大乐透",
    red_count=5,
    red_max=35,
    blue_count=2,
    blue_max=12,
    red_pool_size=12,
    blue_pool_size=4,
    source="sporttery.cn",
)

GAMES = {"ssq": SSQ, "dlt": DLT}


def red_columns(game: GameConfig) -> list:
    """返回前区（红球）列的列名列表，如 ['red1', ..., 'red6']。"""
    return [f"red{i}" for i in range(1, game.red_count + 1)]


def blue_columns(game: GameConfig) -> list:
    """返回后区（蓝球）列的列名列表，如 ['blue1', 'blue2']。"""
    return [f"blue{i}" for i in range(1, game.blue_count + 1)]
