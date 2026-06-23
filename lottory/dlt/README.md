# 大乐透彩票分析预测系统 🎰

基于国家体育总局彩票中心官方 API 的完整彩票分析和预测系统。

## 🌟 系统特性

- **官方 API 数据源**: 使用国家体育总局彩票中心官方接口，数据权威可靠
- **日期隔离存储**: 日志、数据、报告均按日期分目录存放，便于管理
- **一键流水线**: `main.py --pipeline` 自动完成爬取→分析→预测→报告全流程
- **智能预测**: 机器学习 + 统计分析的多策略综合预测
- **交互式报告**: Plotly 交互式 HTML 仪表板，浏览器即可查看

## 📁 项目结构

```
lottory/dlt/
├── main.py                    # ★ 统一主入口（日志配置、目录管理、流水线编排）
├── official_api_crawler.py    # 官方 API 数据爬虫
├── lottery_analyzer.py        # 数据分析模块
├── predictor.py               # 预测算法模块
├── dashboard.py               # HTML 可视化报告生成器
├── final_demo.py              # 完整流程演示脚本
├── example_usage.py           # 爬虫使用示例
├── test_official_api.py       # API 功能测试
├── requirements.txt           # Python 依赖
├── logs/                      # 日志目录
│   └── lottery_YYYYMMDD.log   # 按日期命名的日志文件
├── data/                      # 数据目录
│   └── YYYYMMDD/              # 按日期分目录
│       └── dlt_history.xlsx   # 开奖数据
└── analysis_results/          # 分析结果目录
    └── YYYYMMDD/              # 按日期分目录
        ├── frequency_analysis.png
        ├── hot_cold_analysis.png
        ├── sum_distribution.png
        └── dlt_unified_report.html
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 一键执行完整流程

```bash
# 爬取数据 → 分析 → 预测 → 生成报告
python main.py --pipeline --pages 5
```

### 3. 分步执行

```bash
# 仅爬取数据
python main.py --crawl --pages 10

# 仅分析数据
python main.py --analyze

# 仅生成预测
python main.py --predict --eval

# 仅生成 HTML 报告
python main.py --dashboard

# 导出文本报告
python main.py --report
```

### 4. 交互式菜单

```bash
python main.py
```

### 5. 指定已有数据文件

```bash
python main.py --analyze --data-file data/20260623/dlt_history.xlsx
```

## 📊 功能详解

### 数据爬虫 (`official_api_crawler.py`)
- 国家体育总局彩票中心官方 API
- 接口: `https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry`
- 自动分页获取全部历史数据
- 输出: `data/{日期}/dlt_history.xlsx`（含多工作表）

### 统计分析 (`lottery_analyzer.py`)
- 号码频率统计（全量 + 近期）
- 热门/冷门号码识别
- 和值分布分析
- 奇偶比统计
- 连号模式分析
- 生成 PNG 图表到 `analysis_results/{日期}/`

### 预测算法 (`predictor.py`)
- 机器学习预测（随机森林）
- 频率统计预测
- 热门/冷门号码预测
- 混合投票预测
- 回测评估

### 可视化报告 (`dashboard.py`)
- 交互式 HTML 报告（Plotly）
- 仪表板概览、频率分析、冷热号、和值分布、预测结果
- 输出: `analysis_results/{日期}/dlt_unified_report.html`

## 🎯 Python API 使用

```python
from main import LotteryPipeline, setup_logging

# 初始化
setup_logging()
pipeline = LotteryPipeline()

# 一键流水线
result = pipeline.run_full_pipeline(max_pages=5)

# 或分步调用
pipeline.load_existing_data()
pipeline.crawl_data(max_pages=5)
pipeline.analyze_data()
predictions = pipeline.generate_predictions()
pipeline.generate_report(predictions)
```

```python
# 单独使用各模块
from official_api_crawler import OfficialApiCrawler
crawler = OfficialApiCrawler()
raw_data = crawler.fetch_all_history(max_pages=3)
df = crawler.process_official_data(raw_data)
crawler.save_to_excel(df, "data/20260623/dlt_history.xlsx")
```

## 📈 输出示例

### 终端输出
```
📊 大乐透数据分析报告
==================================================
📈 号码频率统计:
   红球最高频: {1: 15, 16: 14, 23: 13, 8: 12, 31: 11}
   蓝球最高频: {1: 8, 7: 7, 12: 6}

🔥 近期热门号码: {1: 5, 16: 4, 23: 4, 8: 3, 31: 3}
🧊 近期冷门号码: {2: 0, 15: 0, 24: 0, 9: 1, 32: 1}

🧮 和值统计:
   红球和值平均: 85.3
   总和值平均:   95.7
```

### 预测结果
```
🔮 大乐透预测结果
==================================================
  方案 1: machine_learning
  红球: [3, 12, 18, 25, 31]
  蓝球: [2, 9]

  方案 2: frequency_based
  红球: [1, 16, 23, 8, 31]
  蓝球: [1, 7]
```

## ⚠️ 重要提醒

1. **仅供娱乐**: 彩票预测仅供参考，不保证准确性
2. **理性投注**: 请理性对待彩票，切勿沉迷
3. **合法合规**: 遵守当地法律法规

## 🔧 环境要求

- Python 3.7+
- 依赖包详见 `requirements.txt`

---
**免责声明**: 本系统仅为数据分析工具，不对任何购彩行为负责。
