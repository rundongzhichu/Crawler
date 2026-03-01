import random
import time
import requests
import json
import pandas as pd
import urllib3
from fake_useragent import UserAgent
from pathlib import Path
from typing import List, Dict, Optional
import logging

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SuperLottoCrawler:
    """大乐透彩票数据爬虫类"""
    
    def __init__(self):
        self.base_url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
        self.lottery_type = "dlt"  # 大乐透代码
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': UserAgent().random})
        
        # Proxy lists for rotation
        self.http_proxies = [
            'http://139.59.1.14:80',
            'http://14.195.16.140:80',
            'http://45.146.163.31:80',
            'http://78.47.127.91:80',
            'http://193.31.27.11:80',
        ]
        
        self.https_proxies = [
            'https://161.35.98.111:8080',
            'https://67.43.236.21:31517',
            'https://51.44.163.128:3128',
            'https://13.126.217.46:3128',
            'https://18.170.63.85:999',
            'https://195.158.8.123:3128'
        ]
        
        self.sleep_time = 2  # 请求间隔时间
        
    def _get_random_proxy(self) -> Dict[str, str]:
        """获取随机代理"""
        http_proxy = random.choice(self.http_proxies)
        https_proxy = random.choice(self.https_proxies)
        return {'http': http_proxy, 'https': https_proxy}
    
    def _build_request_params(self, page_no: int = 1, page_size: int = 30, 
                            issue_count: Optional[int] = None,
                            issue_start: Optional[str] = None,
                            issue_end: Optional[str] = None,
                            day_start: Optional[str] = None,
                            day_end: Optional[str] = None) -> Dict:
        """构建请求参数"""
        params = {
            'name': self.lottery_type,
            'issueCount': issue_count or '',
            'issueStart': issue_start or '',
            'issueEnd': issue_end or '',
            'dayStart': day_start or '',
            'dayEnd': day_end or '',
            'pageNo': page_no,
            'pageSize': page_size,
            'week': '',
            'systemType': 'PC'
        }
        return params
    
    def fetch_lottery_data(self, page_no: int = 1, page_size: int = 30) -> Optional[List[Dict]]:
        """获取彩票数据"""
        try:
            params = self._build_request_params(page_no, page_size)
            proxy = self._get_random_proxy()
            
            response = self.session.get(
                self.base_url,
                params=params,
                proxies=proxy,
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result', [])
            else:
                logger.error(f"HTTP Error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return None
    
    def fetch_all_history(self, max_pages: Optional[int] = None) -> List[Dict]:
        """获取所有历史数据"""
        all_data = []
        page_no = 1
        
        # 先获取第一页以确定总页数
        first_page_data = self.fetch_lottery_data(1, 30)
        if not first_page_data:
            logger.error("Failed to fetch initial data")
            return all_data
            
        # 获取总数并计算总页数
        # 注意：实际API可能需要额外请求来获取总数
        
        while True:
            if max_pages and page_no > max_pages:
                break
                
            logger.info(f"Fetching page {page_no}")
            data = self.fetch_lottery_data(page_no, 30)
            
            if not data:
                logger.warning(f"No data found for page {page_no}")
                break
                
            all_data.extend(data)
            logger.info(f"Retrieved {len(data)} records from page {page_no}")
            
            # 如果返回的数据少于请求的数量，说明已经是最后一页
            if len(data) < 30:
                break
                
            page_no += 1
            time.sleep(self.sleep_time)
            
        logger.info(f"Total records fetched: {len(all_data)}")
        return all_data
    
    def process_super_lotto_data(self, raw_data: List[Dict]) -> pd.DataFrame:
        """处理大乐透数据"""
        processed_data = []
        
        for item in raw_data:
            try:
                # 解析开奖号码
                red_balls = item['red'].split(',') if isinstance(item['red'], str) else item['red']
                blue_balls = item['blue'].split(',') if isinstance(item['blue'], str) else item['blue']
                
                # 确保是列表格式
                if isinstance(red_balls, str):
                    red_balls = red_balls.split(',')
                if isinstance(blue_balls, str):
                    blue_balls = blue_balls.split(',')
                
                record = {
                    'issue': item['code'],           # 期号
                    'date': item['date'],            # 开奖日期
                    'red1': int(red_balls[0]) if len(red_balls) > 0 else None,
                    'red2': int(red_balls[1]) if len(red_balls) > 1 else None,
                    'red3': int(red_balls[2]) if len(red_balls) > 2 else None,
                    'red4': int(red_balls[3]) if len(red_balls) > 3 else None,
                    'red5': int(red_balls[4]) if len(red_balls) > 4 else None,
                    'blue1': int(blue_balls[0]) if len(blue_balls) > 0 else None,
                    'blue2': int(blue_balls[1]) if len(blue_balls) > 1 else None,
                    'red_balls': ','.join(map(str, red_balls)),  # 原始红球字符串
                    'blue_balls': ','.join(map(str, blue_balls))  # 原始蓝球字符串
                }
                processed_data.append(record)
                
            except (ValueError, IndexError, KeyError) as e:
                logger.warning(f"Error processing record {item.get('code', 'unknown')}: {str(e)}")
                continue
        
        return pd.DataFrame(processed_data)
    
    def save_to_excel(self, df: pd.DataFrame, filename: str = "super_lotto_history.xlsx"):
        """保存数据到Excel文件"""
        try:
            file_path = Path(filename)
            
            if not file_path.exists():
                # 创建新文件
                df.to_excel(filename, sheet_name='lottery_data', index=False)
                logger.info(f"Created new file: {filename}")
            else:
                # 追加到现有文件
                with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                    book = writer.book
                    
                    if 'lottery_data' in book.sheetnames:
                        start_row = book['lottery_data'].max_row
                    else:
                        book.create_sheet('lottery_data')
                        start_row = 0
                    
                    df.to_excel(
                        writer,
                        sheet_name='lottery_data',
                        startrow=start_row,
                        header=False if start_row > 0 else True,
                        index=False
                    )
                logger.info(f"Appended data to existing file: {filename}")
                
        except Exception as e:
            logger.error(f"Error saving to Excel: {str(e)}")
    
    def load_from_excel(self, filename: str = "super_lotto_history.xlsx") -> pd.DataFrame:
        """从Excel文件加载数据"""
        try:
            df = pd.read_excel(filename, sheet_name='lottery_data')
            logger.info(f"Loaded {len(df)} records from {filename}")
            return df
        except FileNotFoundError:
            logger.warning(f"File {filename} not found")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading from Excel: {str(e)}")
            return pd.DataFrame()

def main():
    """主函数 - 演示基本用法"""
    crawler = SuperLottoCrawler()
    
    # 获取最新几期数据作为演示
    logger.info("Starting Super Lotto crawler...")
    recent_data = crawler.fetch_lottery_data(1, 10)  # 获取第1页的10条记录
    
    if recent_data:
        df = crawler.process_super_lotto_data(recent_data)
        print("Recent lottery data:")
        print(df.head())
        crawler.save_to_excel(df)
    else:
        logger.error("Failed to fetch lottery data")

if __name__ == "__main__":
    main()