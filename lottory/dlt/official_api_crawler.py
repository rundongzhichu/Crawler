#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 大乐透官方 API 数据爬虫模块
 Official API Crawler — 从国家体育总局彩票中心接口获取开奖数据
=============================================================================

 数据源: https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry
 游戏编号: gameNo=85 (大乐透)

 主要功能:
   - 分页获取历史开奖数据
   - 解析开奖号码（前区5红球 + 后区2蓝球）
   - 提取奖池金额、销售金额、各奖项详情
   - 保存为 Excel 文件（含多工作表）

 使用示例:
   crawler = OfficialApiCrawler()
   raw_data = crawler.fetch_all_history(max_pages=5)
   df = crawler.process_official_data(raw_data)
   crawler.save_to_excel(df, "data/20260623/dlt_history.xlsx")
=============================================================================
"""

import requests
import pandas as pd
import json
import time
import logging
from typing import List, Dict, Optional
from fake_useragent import UserAgent
import urllib3

# 禁用 SSL 警告（部分环境证书问题）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 使用统一日志配置（由 main.py 的 setup_logging() 初始化）
logger = logging.getLogger(__name__)


class OfficialApiCrawler:
    """
    官方 API 数据爬虫。

    通过国家体育总局彩票中心官方接口获取大乐透开奖数据，
    支持分页爬取、数据解析、Excel 导出等功能。

    Attributes:
        base_url: 官方 API 地址
        session: requests.Session 实例（带伪装请求头）
        default_params: 默认查询参数
        sleep_time: 请求间隔时间（秒）
    """

    def __init__(self):
        """初始化爬虫 —— 配置请求头和默认参数。"""
        self.base_url = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': UserAgent().random,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.sporttery.cn/',
            'Origin': 'https://www.sporttery.cn',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        })

        # API 查询参数
        self.default_params = {
            'gameNo': '85',      # 大乐透游戏编号
            'provinceId': '0',   # 全国数据
            'pageSize': '30',    # 每页 30 条
            'isVerify': '1'      # 验证参数
        }

        self.sleep_time = 1  # 请求间隔（秒），避免频率过高

    # ------------------------------------------------------------------
    #  数据获取
    # ------------------------------------------------------------------

    def fetch_single_page(self, page_no: int = 1, page_size: int = 30) -> Optional[Dict]:
        """
        获取单页开奖数据。

        Args:
            page_no: 页码（从 1 开始）
            page_size: 每页记录数

        Returns:
            dict: API 返回的 value 对象，失败返回 None
        """
        try:
            params = self.default_params.copy()
            params['pageNo'] = str(page_no)
            params['pageSize'] = str(page_size)

            logger.info("正在获取第 %d 页数据...", page_no)

            response = self.session.get(
                self.base_url,
                params=params,
                timeout=15,
                verify=False
            )

            if response.status_code == 200:
                data = response.json()
                logger.info("API 响应状态: %s", data.get('status', 'unknown'))

                if 'value' in data and data['value'] is not None:
                    if 'list' in data['value'] and data['value']['list']:
                        return data['value']
                    else:
                        logger.warning("API 返回的 value 中没有 list 数据")
                        return data['value']
                else:
                    logger.error(
                        "API 返回格式不符合预期: %s",
                        list(data.keys()) if isinstance(data, dict) else 'Not dict'
                    )
                    return None
            else:
                logger.error("HTTP 错误: %d", response.status_code)
                return None

        except Exception as e:
            logger.error("获取第 %d 页数据失败: %s", page_no, str(e))
            return None

    def fetch_all_history(self, max_pages: Optional[int] = None) -> List[Dict]:
        """
        获取全部历史开奖数据（自动翻页）。

        Args:
            max_pages: 最大爬取页数，None 表示获取全部

        Returns:
            list[dict]: 原始数据记录列表
        """
        all_data = []
        page_no = 1

        while True:
            if max_pages and page_no > max_pages:
                break

            page_data = self.fetch_single_page(page_no, 30)

            if not page_data:
                logger.warning("第 %d 页获取失败，停止翻页", page_no)
                break

            list_data = page_data.get('list', [])
            logger.info("第 %d 页获取到 %d 条记录", page_no, len(list_data))

            if not list_data:
                logger.info("第 %d 页无数据，已到最后一页", page_no)
                break

            all_data.extend(list_data)

            # 不足一页说明已是最后一页
            if len(list_data) < 30:
                logger.info("已到达最后一页")
                break

            page_no += 1
            time.sleep(self.sleep_time)  # 礼貌间隔

        logger.info("总共获取 %d 条记录", len(all_data))
        return all_data

    # ------------------------------------------------------------------
    #  数据解析
    # ------------------------------------------------------------------

    def process_official_data(self, raw_data: List[Dict]) -> pd.DataFrame:
        """
        将原始 API 数据解析为标准 DataFrame。

        大乐透格式: 前区 5 个红球 (01-35) + 后区 2 个蓝球 (01-12)

        Args:
            raw_data: API 返回的原始数据列表

        Returns:
            pd.DataFrame: 结构化数据，包含以下列:
                - issue: 期号
                - date: 开奖日期
                - red1~red5: 前区红球号码
                - blue1~blue2: 后区蓝球号码
                - red_balls, blue_balls: 号码字符串
                - pool_amount: 奖池金额
                - prize_level_*: 各奖项信息
        """
        processed_data = []

        for item in raw_data:
            try:
                record = {
                    'issue': str(item.get('lotteryDrawNum', '')),
                    'date': str(item.get('lotteryDrawTime', '')),
                    'pool_amount': str(item.get('poolBalanceAfterdraw', '')),
                    'sales_amount': str(item.get('lotterySaleEndtime', ''))
                }

                # 解析开奖号码（空格分隔，前5红球 + 后2蓝球）
                draw_result = item.get('lotteryDrawResult', '')
                if draw_result:
                    numbers = draw_result.split()
                    if len(numbers) >= 7:
                        record.update({
                            'red1': int(numbers[0]) if numbers[0].isdigit() else None,
                            'red2': int(numbers[1]) if numbers[1].isdigit() else None,
                            'red3': int(numbers[2]) if numbers[2].isdigit() else None,
                            'red4': int(numbers[3]) if numbers[3].isdigit() else None,
                            'red5': int(numbers[4]) if numbers[4].isdigit() else None,
                            'blue1': int(numbers[5]) if numbers[5].isdigit() else None,
                            'blue2': int(numbers[6]) if numbers[6].isdigit() else None,
                            'red_balls': ','.join(numbers[:5]),
                            'blue_balls': ','.join(numbers[5:7])
                        })

                # 解析各等奖项信息
                prize_levels = item.get('prizeLevelList', [])
                for prize_info in prize_levels[:10]:
                    level = prize_info.get('prizeLevel', '')
                    bonus = prize_info.get('stakeAmount', '')
                    count = prize_info.get('stakeCount', '')
                    record[f'prize_level_{level}_bonus'] = bonus
                    record[f'prize_level_{level}_count'] = count

                processed_data.append(record)

            except Exception as e:
                logger.warning("处理记录失败: %s, 数据: %s", str(e), item)
                continue

        df = pd.DataFrame(processed_data)

        # 确保必要列存在
        required_columns = [
            'issue', 'date', 'red1', 'red2', 'red3', 'red4', 'red5',
            'blue1', 'blue2', 'red_balls', 'blue_balls'
        ]
        for col in required_columns:
            if col not in df.columns:
                df[col] = None

        # 按期号降序排列（最新在前）
        df = df.sort_values('issue', ascending=False).reset_index(drop=True)

        return df

    # ------------------------------------------------------------------
    #  数据存储
    # ------------------------------------------------------------------

    def save_to_excel(self, df: pd.DataFrame, filename: str = None):
        """
        保存数据到 Excel 文件（含多个工作表）。

        生成的工作表:
            - lottery_data:   完整开奖数据
            - statistics:     基本统计信息
            - red_frequency:  红球频率统计
            - blue_frequency: 蓝球频率统计

        Args:
            df: 待保存的 DataFrame
            filename: 输出路径，默认保存到 data/{当天日期}/dlt_history.xlsx
        """
        if filename is None:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y%m%d")
            import os
            data_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "data", date_str
            )
            os.makedirs(data_dir, exist_ok=True)
            filename = os.path.join(data_dir, "dlt_history.xlsx")

        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 主数据表
                df.to_excel(writer, sheet_name='lottery_data', index=False)

                # 统计信息表
                if not df.empty:
                    stats_df = self.generate_statistics(df)
                    stats_df.to_excel(writer, sheet_name='statistics', index=False)

                # 号码频率表（红球和蓝球分开）
                if not df.empty:
                    freq_data = self.generate_frequency_stats(df)
                    if isinstance(freq_data, dict):
                        freq_data['red_frequency'].to_excel(
                            writer, sheet_name='red_frequency', index=False
                        )
                        freq_data['blue_frequency'].to_excel(
                            writer, sheet_name='blue_frequency', index=False
                        )
                    else:
                        freq_data.to_excel(
                            writer, sheet_name='frequency', index=False
                        )

            logger.info("数据已保存 → %s", filename)

        except Exception as e:
            logger.error("保存 Excel 失败: %s", str(e))

    # ------------------------------------------------------------------
    #  统计辅助方法
    # ------------------------------------------------------------------

    def generate_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        生成基本统计信息 DataFrame。

        Args:
            df: 开奖数据

        Returns:
            pd.DataFrame: 统计项汇总表
        """
        if df.empty:
            return pd.DataFrame()

        stats_data = []
        total_records = len(df)
        date_range = f"{df['date'].min()} 到 {df['date'].max()}"

        # 收集所有红球和蓝球号码
        red_cols = ['red1', 'red2', 'red3', 'red4', 'red5']
        blue_cols = ['blue1', 'blue2']

        all_red_numbers = []
        all_blue_numbers = []

        for _, row in df.iterrows():
            for col in red_cols:
                if pd.notna(row[col]):
                    all_red_numbers.append(int(row[col]))
            for col in blue_cols:
                if pd.notna(row[col]):
                    all_blue_numbers.append(int(row[col]))

        stats_data.extend([
            {'统计项': '总记录数', '数值': total_records},
            {'统计项': '数据时间范围', '数值': date_range},
        ])

        if all_red_numbers:
            stats_data.append({
                '统计项': '红球号码范围',
                '数值': f"{min(all_red_numbers)} - {max(all_red_numbers)}"
            })
        if all_blue_numbers:
            stats_data.append({
                '统计项': '蓝球号码范围',
                '数值': f"{min(all_blue_numbers)} - {max(all_blue_numbers)}"
            })

        return pd.DataFrame(stats_data)

    def generate_frequency_stats(self, df: pd.DataFrame) -> dict:
        """
        统计红球和蓝球各号码的出现频率。

        Args:
            df: 开奖数据

        Returns:
            dict: {
                'red_frequency':  红球频率 DataFrame,
                'blue_frequency': 蓝球频率 DataFrame
            }
        """
        if df.empty:
            return pd.DataFrame()

        red_cols = ['red1', 'red2', 'red3', 'red4', 'red5']
        blue_cols = ['blue1', 'blue2']

        # 红球频率
        red_numbers = []
        for _, row in df.iterrows():
            for col in red_cols:
                if pd.notna(row[col]):
                    red_numbers.append(int(row[col]))
        red_freq = pd.Series(red_numbers).value_counts().sort_index()
        red_freq_df = pd.DataFrame({
            '红球号码': red_freq.index,
            '出现次数': red_freq.values,
            '频率占比': (red_freq.values / len(red_numbers) * 100).round(2)
        })

        # 蓝球频率
        blue_numbers = []
        for _, row in df.iterrows():
            for col in blue_cols:
                if pd.notna(row[col]):
                    blue_numbers.append(int(row[col]))
        blue_freq = pd.Series(blue_numbers).value_counts().sort_index()
        blue_freq_df = pd.DataFrame({
            '蓝球号码': blue_freq.index,
            '出现次数': blue_freq.values,
            '频率占比': (blue_freq.values / len(blue_numbers) * 100).round(2)
        })

        return {
            'red_frequency': red_freq_df,
            'blue_frequency': blue_freq_df
        }

    # ------------------------------------------------------------------
    #  打印摘要
    # ------------------------------------------------------------------

    def print_summary(self, df: pd.DataFrame):
        """
        在控制台打印数据摘要。

        Args:
            df: 开奖数据
        """
        if df.empty:
            print("❌ 未获取到有效数据")
            return

        print("\n" + "=" * 60)
        print("🎯 官方 API 大乐透数据获取成功")
        print("=" * 60)
        print(f"📊 总记录数: {len(df)}")
        print(f"📅 最新期号: {df.iloc[0]['issue'] if not df.empty else 'N/A'}")
        print(f"🗓️  最新开奖日期: {df.iloc[0]['date'] if not df.empty else 'N/A'}")

        if not df.empty:
            latest = df.iloc[0]
            red_balls = [
                latest[f'red{i}'] for i in range(1, 6)
                if pd.notna(latest[f'red{i}'])
            ]
            blue_balls = [
                latest[f'blue{i}'] for i in range(1, 3)
                if pd.notna(latest[f'blue{i}'])
            ]
            print(f"🔴 最新红球号码: {sorted(red_balls)}")
            print(f"🔵 最新蓝球号码: {sorted(blue_balls)}")

        print("=" * 60)

        # 最近 5 期数据一览
        print("\n📋 最近 5 期开奖数据:")
        display_cols = ['issue', 'date', 'red_balls', 'blue_balls']
        print(df[display_cols].head().to_string(index=False))


# ============================================================================
#  独立运行入口（仅用于测试爬虫）
# ============================================================================

def main():
    """独立测试官方 API 爬虫功能。"""
    print("🚀 启动官方 API 大乐透数据爬虫...")

    crawler = OfficialApiCrawler()

    print("🌐 正在从官方 API 获取数据...")
    raw_data = crawler.fetch_all_history(max_pages=2)

    if not raw_data:
        print("❌ 未能从官方 API 获取数据")
        return

    print("⚙️  正在处理数据...")
    df = crawler.process_official_data(raw_data)

    if df.empty:
        print("❌ 数据处理后为空")
        return

    crawler.print_summary(df)
    crawler.save_to_excel(df)

    print("\n🔍 详细数据预览:")
    print(df.head(3))


if __name__ == "__main__":
    main()
