# 大乐透彩票分析预测系统 🎰

这是一个完整的彩票分析和预测系统，专门针对中国体育彩票大乐透玩法设计。

## 🎉 最新更新 - 官方API支持

**重大升级！** 系统现已支持国家体育总局彩票中心官方API数据源，提供更权威、更实时的数据服务。

- ✅ 新增 `official_api_crawler.py` - 官方API专用爬虫
- ✅ 完整的命令行和交互式支持
- ✅ 丰富的测试脚本确保稳定性
- ✅ 与原有系统的无缝集成

## 🌟 系统特性

### 🚀 官方API数据源（推荐）
- **权威可靠**: 使用国家体育总局彩票中心官方接口
- **实时更新**: 获取最新的开奖数据和奖池信息
- **数据丰富**: 包含奖金详情、销售金额等完整信息
- **稳定高效**: 专业的API接口，高可用性保障

### 📊 核心功能
- **数据爬取**: 自动获取历史开奖数据（支持官方API和传统API）
- **统计分析**: 深度分析号码频率、分布规律和趋势
- **智能预测**: 基于机器学习和统计学的多重预测算法
- **可视化展示**: 丰富的图表和交互式仪表板
- **用户友好**: 命令行界面和交互式菜单

## 📁 项目结构

```
lottory/
├── official_api_crawler.py   # 官方API数据爬虫模块 (唯一)
├── lottery_analyzer.py       # 数据分析模块
├── predictor.py             # 预测算法模块
├── dashboard.py             # 统一可视化报告生成器
├── main_system.py           # 主应用程序
├── test_official_api.py     # 官方API测试脚本
├── example_usage.py         # 使用示例
├── requirements.txt         # 依赖包列表
└── README.md               # 说明文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 测试官方API爬虫（推荐第一步）

```bash
# 测试官方API连接和数据获取
python test_official_api.py
```

### 3. 运行系统

#### 交互模式（推荐新手）
```bash
python main_system.py
```

#### 命令行模式
```bash
# 爬取数据（使用官方API）
python main_system.py --crawl --pages 10

# 数据分析
python main_system.py --analyze

# 生成预测
python main_system.py --predict

# 创建统一HTML报告
python main_system.py --dashboard

# 导出分析报告
python main_system.py --report
```

## 📊 功能详解

### 数据爬虫 (official_api_crawler.py) 🔥
- 使用国家体育总局彩票中心官方API
- 接口地址: `https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry`
- 更稳定可靠的数据源
- 包含完整的开奖信息和奖金数据
- 支持获取奖池金额、销售金额等附加信息
- 英文界面显示

### 统计分析 (lottery_analyzer.py)
- 号码频率统计分析
- 热门/冷门号码识别
- 和值分布分析
- 奇偶比统计
- 连号模式分析
- 位置分布特征

### 预测算法 (predictor.py)
- 机器学习预测（随机森林）
- 频率统计预测
- 热门号码预测
- 冷门号码预测
- 混合投票预测
- 预测准确性回测

### 统一可视化报告 (dashboard.py)
- 所有分析结果整合到单一HTML文件
- 交互式图表展示
- 英文界面显示
- 包含数据摘要、频率分析、热门冷门号码、和值分布等
- 预测结果可视化展示

## 🎯 使用示例

### 基本使用流程

```python
from main_system import LotterySystem

# 创建系统实例
system = LotterySystem()

# 爬取数据
system.crawl_new_data(max_pages=5)

# 分析数据
analysis_results = system.perform_analysis()

# 生成预测
predictions = system.generate_predictions(prediction_count=5)

# 创建仪表板
system.create_dashboard(predictions)

# 导出报告
system.export_report()
```

### 单独使用各模块

```python
# 仅使用爬虫
from super_lotto_crawler import SuperLottoCrawler
crawler = SuperLottoCrawler()
data = crawler.fetch_all_history(max_pages=3)
df = crawler.process_super_lotto_data(data)

# 仅使用分析器
from lottery_analyzer import LotteryAnalyzer
analyzer = LotteryAnalyzer(df)
frequency = analyzer.get_number_frequency()
hot_cold = analyzer.find_hot_and_cold_numbers()

# 仅使用预测器
from predictor import LotteryPredictor
predictor = LotteryPredictor(df)
predictor.train_prediction_models()
predictions = predictor.generate_multiple_predictions(3)
```

## 🎯 官方API特色功能

### 新增数据字段
- **奖池金额**: pool_amount
- **销售金额**: sales_amount  
- **奖项详情**: 各等奖的奖金和中奖人数
- **完整开奖时间**: 精确到秒的时间戳

### 数据质量优势
- ✅ 官方权威数据源
- ✅ 实时更新
- ✅ 数据完整性高
- ✅ 格式标准化

## 📈 输出结果

### 分析报告示例
```
📊 大乐透数据分析报告
==================================================
红球最频繁号码: {1: 15, 16: 14, 23: 13, 8: 12, 31: 11}
蓝球最频繁号码: {1: 8, 7: 7, 12: 6}

🔥 近期热门号码: {1: 5, 16: 4, 23: 4, 8: 3, 31: 3}
🧊 近期冷门号码: {2: 0, 15: 0, 24: 0, 9: 1, 32: 1}

🧮 和值统计:
红球和值平均: 85.3
总和值平均: 95.7

⚖️  奇偶比分析:
红球平均奇数比例: 58.2%
```

### 预测结果示例
```
🔮 大乐透预测结果
==================================================

方案 1: machine_learning
红球: [3, 12, 18, 25, 31]
蓝球: [2, 9]

方案 2: frequency_based
红球: [1, 16, 23, 8, 31]
蓝球: [1, 7]

方案 3: hybrid_approach
红球: [1, 16, 23, 8, 31]
蓝球: [1, 7]
```

## 📊 可视化图表

系统会自动生成以下图表：

1. **仪表板概览** - HTML交互式仪表板
2. **频率热力图** - 各位置号码出现频率
3. **趋势分析图** - 和值、奇偶比等趋势变化
4. **分布对比图** - 号码区间分布情况
5. **相关性分析图** - 号码位置间相关关系
6. **预测仪表板** - 预测结果可视化对比

## ⚠️ 重要提醒

1. **仅供娱乐**: 彩票预测仅供参考，不保证准确性
2. **理性投注**: 请理性对待彩票，切勿沉迷
3. **合法合规**: 遵守当地法律法规
4. **风险提示**: 投资有风险，购彩需谨慎

## 🔧 系统要求

- Python 3.7+
- 依赖包详见 requirements.txt
- 建议使用虚拟环境

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进系统！

## 📄 许可证

本项目仅供学习研究使用。

---

**免责声明**: 本系统仅为数据分析工具，不对任何购彩行为负责。彩票开奖结果具有完全的随机性，请理性参与。