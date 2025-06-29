import random
import time

import requests
import charset_normalizer as chartset
import json
import pandas as pd
import urllib3
from fake_useragent import UserAgent
from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# types=['ssq','kl8','3d','qlc']

types=['kl8','3d','qlc']
sleep_time=2

def processSsq(type:str, data:list):
    data_dic =  {}
    code = []
    name = []
    date = []
    red = []
    blue = []
    data_dic["code"] = code
    data_dic["name"] = name
    data_dic["date"] = date
    data_dic["red"] = red
    data_dic["blue"] = blue
    for item in data:
        code.append(item['code'])
        name.append(item['name'])
        date.append(item['date'])
        red.append(item['red'])
        blue.append(item['blue'])
    # 转换为 DataFrame
    df = pd.DataFrame(data_dic)

    file_name = 'output.xlsx'
    file_path = Path(file_name)
    sheet_name = type + "_sheet"
    if not file_path.exists():
        df.to_excel(file_name, sheet_name=sheet_name, header=True, index=False)
    else:

        # 追加到现有 Excel 文件
        with pd.ExcelWriter(file_name, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
            # 1. 加载现有 Excel 文件
            book = writer.book
            start_row = 0
            if sheet_name in book.sheetnames:
                start_row = book[sheet_name].max_row  # 最后一行行号
            else:
                book.create_sheet(sheet_name)
                start_row = 0  # 如果 Sheet 不存在，从第 1 行开始

            sheet = book[sheet_name]
            # 3. 追加数据（跳过列名 header=False）
            df.to_excel(
                writer,
                sheet_name=sheet_name,
                # startrow=start_row if start_row == 0 else start_row + 1,  # 避免重复列名
                startrow=start_row,
                header=False if start_row > 0 else True,  # 只有第一行写列名
                index=False
            )

# https://free-proxy-list.net/ 可以在这里获取网络代理
# 代理列表（格式：'http://IP:端口' 或 'https://IP:端口'）
http_proxies_list = [
    'http://139.59.1.14:80',
    'http://14.195.16.140:80',
    'http://45.146.163.31:80',
    'http://78.47.127.91:80',
    'http://193.31.27.11:80',
]
https_proxies_list = [
    'https://161.35.98.111:8080',
    'https://67.43.236.21:31517',
    'https://51.44.163.128:3128',
    'https://13.126.217.46:3128',
    'https://18.170.63.85:999',
    'https://195.158.8.123:3128'
]

def get_rand_proxy():
    http_proxy = random.choice(http_proxies_list)
    https_proxy = random.choice(https_proxies_list)
    proxies = {'http': http_proxy, 'https': https_proxy}
    return proxies

for type in types:
    # 参数名字
    page_no=1
    page_size=30
    # 请求地址
    url = f'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name={type}&issueCount=&issueStart=&issueEnd=&dayStart=&dayEnd=&pageNo={page_no}&pageSize={page_size}&week=&systemType=PC'

    # 添加请求头
    headers = {
        'User-Agent': UserAgent().random
    }
    # 获取得到session, 同时获取到数据大小
    session = requests.Session()
    session.headers.update(headers)
    session.proxies.update(get_rand_proxy())  # 结合代理
    r = session.get(url, verify=False)
    r.encoding = chartset.detect(r.content)['encoding']
    content = r.content.decode('utf-8')
    data = json.loads(content)
    total_cnt = data['total']

    # 分页获取数据
    for i in range(1, int(total_cnt/page_size + 1)):
        # 参数名字
        page_no = i
        url = f'https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name={type}&issueCount=&issueStart=&issueEnd=&dayStart=&dayEnd=&pageNo={i}&pageSize={page_size}&week=&systemType=PC'
        time.sleep(sleep_time)
        try:
            r = session.get(url, headers=headers, timeout=10)
            r.encoding = chartset.detect(r.content)['encoding']
            content = r.content.decode('utf-8')
            if(content != '' and content != None):
                data = json.loads(content)
                res = data['result']
                processSsq(type, res)
                print(f"success process type {type} page {page_no} of {int(total_cnt / page_size + 1)}，pagesize：{page_size}， total:{total_cnt}")
        except Exception as e:
            print(f"ERROR: process type {type} page {page_no} of {int(total_cnt/page_size + 1)}，pagesize：{page_size}， total:{total_cnt}", e)