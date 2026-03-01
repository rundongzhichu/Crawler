import requests
import pandas as pd
import json
import time
import logging
from typing import List, Dict, Optional
from fake_useragent import UserAgent
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OfficialApiCrawler:
    """官方API数据爬虫 - 专门针对指定的体育总局彩票中心接口"""
    
    def __init__(self):
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
        
        # API参数配置
        self.default_params = {
            'gameNo': '85',      # 大乐透游戏编号
            'provinceId': '0',   # 全国数据
            'pageSize': '30',    # 每页30条
            'isVerify': '1'      # 验证参数
        }
        
        self.sleep_time = 1  # 请求间隔时间
    
    def fetch_single_page(self, page_no: int = 1, page_size: int = 30) -> Optional[Dict]:
        """获取单页数据"""
        try:
            params = self.default_params.copy()
            params['pageNo'] = str(page_no)
            params['pageSize'] = str(page_size)
            
            logger.info(f"正在获取第 {page_no} 页数据...")
            
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=15,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API响应状态: {data.get('status', 'unknown')}")
                
                # 检查API响应结构
                if 'value' in data and data['value'] is not None:
                    # 检查是否有list数据
                    if 'list' in data['value'] and data['value']['list']:
                        return data['value']
                    else:
                        logger.warning("API返回的value中没有list数据")
                        return data['value']  # 仍然返回value以便调试
                else:
                    logger.error(f"API返回格式不符合预期: {list(data.keys()) if isinstance(data, dict) else 'Not dict'}")
                    logger.error(f"完整响应: {data}")
                    return None
                    return None
            else:
                logger.error(f"HTTP错误: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取第 {page_no} 页数据失败: {str(e)}")
            return None
    
    def fetch_all_history(self, max_pages: Optional[int] = None) -> List[Dict]:
        """获取所有历史数据"""
        all_data = []
        page_no = 1
        
        while True:
            if max_pages and page_no > max_pages:
                break
            
            # 获取当页数据
            page_data = self.fetch_single_page(page_no, 30)
            
            if not page_data:
                logger.warning(f"第 {page_no} 页获取失败")
                break
            
            # 检查是否有数据
            list_data = page_data.get('list', [])
            logger.info(f"第 {page_no} 页获取到 {len(list_data)} 条记录")
            if not list_data:
                logger.info(f"第 {page_no} 页无数据，结束爬取")
                break
            
            all_data.extend(list_data)
            logger.info(f"第 {page_no} 页获取 {len(list_data)} 条记录")
            
            # 检查是否还有更多数据
            if len(list_data) < 30:
                logger.info("已到达最后一页")
                break
            
            page_no += 1
            time.sleep(self.sleep_time)
        
        logger.info(f"总共获取 {len(all_data)} 条记录")
        return all_data
    
    def process_official_data(self, raw_data: List[Dict]) -> pd.DataFrame:
        """处理官方API返回的数据"""
        processed_data = []
        
        for item in raw_data:
            try:
                # 提取基本信息
                record = {
                    'issue': str(item.get('lotteryDrawNum', '')),      # 期号
                    'date': str(item.get('lotteryDrawTime', '')),      # 开奖日期
                    'pool_amount': str(item.get('poolBalanceAfterdraw', '')),  # 奖池金额
                    'sales_amount': str(item.get('lotterySaleEndtime', ''))    # 销售金额
                }
                
                # 处理开奖号码
                draw_result = item.get('lotteryDrawResult', '')
                if draw_result:
                    # 大乐透格式: 前区5个号码 + 后区2个号码，用空格分隔
                    numbers = draw_result.split()
                    if len(numbers) >= 7:
                        # 前区红球（前5个）
                        record.update({
                            'red1': int(numbers[0]) if numbers[0].isdigit() else None,
                            'red2': int(numbers[1]) if numbers[1].isdigit() else None,
                            'red3': int(numbers[2]) if numbers[2].isdigit() else None,
                            'red4': int(numbers[3]) if numbers[3].isdigit() else None,
                            'red5': int(numbers[4]) if numbers[4].isdigit() else None,
                            # 后区蓝球（后2个）
                            'blue1': int(numbers[5]) if numbers[5].isdigit() else None,
                            'blue2': int(numbers[6]) if numbers[6].isdigit() else None,
                            # 原始号码字符串
                            'red_balls': ','.join(numbers[:5]),
                            'blue_balls': ','.join(numbers[5:7])
                        })
                
                # 处理奖项信息
                prize_levels = item.get('prizeLevelList', [])
                for i, prize_info in enumerate(prize_levels[:10]):  # 前10个奖项
                    level = prize_info.get('prizeLevel', '')
                    bonus = prize_info.get('stakeAmount', '')
                    count = prize_info.get('stakeCount', '')
                    record[f'prize_level_{level}_bonus'] = bonus
                    record[f'prize_level_{level}_count'] = count
                
                processed_data.append(record)
                
            except Exception as e:
                logger.warning(f"处理记录失败: {str(e)}, 数据: {item}")
                continue
        
        df = pd.DataFrame(processed_data)
        
        # 确保必要的列存在
        required_columns = ['issue', 'date', 'red1', 'red2', 'red3', 'red4', 'red5', 
                           'blue1', 'blue2', 'red_balls', 'blue_balls']
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = None
        
        # 按期号排序
        df = df.sort_values('issue', ascending=False).reset_index(drop=True)
        
        return df
    
    def save_to_excel(self, df: pd.DataFrame, filename: str = "official_lottery_data.xlsx"):
        """保存数据到Excel"""
        try:
            # 创建多个工作表
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 主要数据表
                df.to_excel(writer, sheet_name='lottery_data', index=False)
                
                # 统计信息表
                if not df.empty:
                    stats_df = self.generate_statistics(df)
                    stats_df.to_excel(writer, sheet_name='statistics', index=False)
                
                # 号码频率表
                if not df.empty:
                    freq_data = self.generate_frequency_stats(df)
                    if isinstance(freq_data, dict):
                        # 分别保存红球和蓝球频率
                        freq_data['red_frequency'].to_excel(writer, sheet_name='red_frequency', index=False)
                        freq_data['blue_frequency'].to_excel(writer, sheet_name='blue_frequency', index=False)
                    else:
                        freq_data.to_excel(writer, sheet_name='frequency', index=False)
            
            logger.info(f"数据已保存到: {filename}")
            
        except Exception as e:
            logger.error(f"保存Excel失败: {str(e)}")
    
    def generate_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成统计信息"""
        if df.empty:
            return pd.DataFrame()
        
        stats_data = []
        
        # 基本统计
        total_records = len(df)
        date_range = f"{df['date'].min()} 到 {df['date'].max()}"
        
        # 号码范围统计
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
        
        stats_data.append({
            '统计项': '总记录数',
            '数值': total_records
        })
        stats_data.append({
            '统计项': '数据时间范围',
            '数值': date_range
        })
        stats_data.append({
            '统计项': '红球号码范围',
            '数值': f"{min(all_red_numbers)} - {max(all_red_numbers)}" if all_red_numbers else "N/A"
        })
        stats_data.append({
            '统计项': '蓝球号码范围',
            '数值': f"{min(all_blue_numbers)} - {max(all_blue_numbers)}" if all_blue_numbers else "N/A"
        })
        
        return pd.DataFrame(stats_data)
    
    def generate_frequency_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成号码频率统计"""
        if df.empty:
            return pd.DataFrame()
        
        # 统计红球频率
        red_cols = ['red1', 'red2', 'red3', 'red4', 'red5']
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
        
        # 统计蓝球频率
        blue_cols = ['blue1', 'blue2']
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
        
        # 合并两个DataFrame
        # 由于长度可能不同，需要分别处理
        return {
            'red_frequency': red_freq_df,
            'blue_frequency': blue_freq_df
        }
    
    def print_summary(self, df: pd.DataFrame):
        """打印数据摘要"""
        if df.empty:
            print("❌ 未获取到有效数据")
            return
        
        print("\n" + "="*60)
        print("🎯 官方API大乐透数据获取成功")
        print("="*60)
        print(f"📊 总记录数: {len(df)}")
        print(f"📅 最新期号: {df.iloc[0]['issue'] if not df.empty else 'N/A'}")
        print(f"🗓️  最新开奖日期: {df.iloc[0]['date'] if not df.empty else 'N/A'}")
        
        if not df.empty:
            latest = df.iloc[0]
            red_balls = [latest[f'red{i}'] for i in range(1, 6) if pd.notna(latest[f'red{i}'])]
            blue_balls = [latest[f'blue{i}'] for i in range(1, 3) if pd.notna(latest[f'blue{i}'])]
            print(f"🔴 最新红球号码: {sorted(red_balls)}")
            print(f"🔵 最新蓝球号码: {sorted(blue_balls)}")
        
        print("="*60)
        
        # 显示最近几期数据
        print("\n📋 最近5期开奖数据:")
        display_cols = ['issue', 'date', 'red_balls', 'blue_balls']
        print(df[display_cols].head().to_string(index=False))

def main():
    """主函数 - 演示官方API爬虫"""
    print("🚀 启动官方API大乐透数据爬虫...")
    
    # 创建爬虫实例
    crawler = OfficialApiCrawler()
    
    # 获取数据
    print("🌐 正在从官方API获取数据...")
    raw_data = crawler.fetch_all_history(max_pages=5)  # 先获取5页作为测试
    
    if not raw_data:
        print("❌ 未能从官方API获取数据")
        return
    
    # 处理数据
    print("⚙️  正在处理数据...")
    df = crawler.process_official_data(raw_data)
    
    if df.empty:
        print("❌ 数据处理后为空")
        return
    
    # 显示摘要
    crawler.print_summary(df)
    
    # 保存数据
    print("💾 正在保存数据...")
    crawler.save_to_excel(df, "official_dlt_data.xlsx")
    
    # 显示前几行详细数据
    print("\n🔍 详细数据预览:")
    print(df.head(3))

if __name__ == "__main__":
    main()