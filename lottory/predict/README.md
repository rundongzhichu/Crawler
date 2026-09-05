# 彩票预测回测系统（双色球 / 大乐透）

面向**双色球（ssq）** 与**大乐透（dlt）** 的统一预测回测系统，采用分层 OOP 架构：

```
lottory/predict/
├── config.py              # 玩法配置（号码范围、候选池大小、目标置信度）
├── data/                  # 数据获取层
│   ├── base.py            #   BaseFetcher 抽象基类（统一数据结构 / 存储）
│   ├── ssq.py             #   SSQFetcher    双色球（cwl.gov.cn）
│   ├── dlt.py             #   DLTFetcher    大乐透（sporttery.cn）
│   └── synthetic.py       #   SyntheticFetcher 离线合成数据（测试用）
├── strategies/            # 预测策略层
│   ├── base.py            #   BaseStrategy 抽象基类 + Prediction 数据结构
│   ├── random.py          #   RandomStrategy   随机基线
│   ├── frequency.py       #   FrequencyStrategy 频率统计
│   ├── hot_cold.py        #   HotColdStrategy   冷热号
│   ├── ml.py              #   MLStrategy       随机森林
│   └── hybrid.py          #   HybridStrategy   混合投票
├── backtest.py            # 回测模块（滚动 walk-forward + 三项指标）
├── service.py             # PredictionService 主服务（编排 / 记录 / 报告）
├── report.py              # 报告生成（文本 / JSON / Markdown）
├── visual/                # ── 可视化层（HTML 报告）──
│   └── html.py            #   Plotly 交互式 HTML 报告生成
├── main.py                # CLI 入口
└── requirements.txt
```

## 架构

- **数据获取基类** `BaseFetcher`：定义 `fetch_raw()`（抓取）+ `parse()`（解析为统一结构）
  两个抽象接口，并复用统一的列补齐、排序、存/取。`SSQFetcher` / `DLTFetcher`
  分别把不同官方接口的原始格式解析成同一张表（`issue / date / red1..redN / blue1..blueM`）。
- **策略基类** `BaseStrategy`：策略只需产出「每个号码的置信度分数」，基类
  `_finalize()` 统一生成具体推荐、候选池、属性。`Prediction` 是统一结果结构。
- **主服务** `PredictionService`：选择数据获取器 → 构建策略 → 滚动回测 → 预测下一期
  → 记录完整过程（日志 + `runs/history.jsonl`）→ 生成报告。
- **可视化层** `visual/`：独立于 `report.py`（文本/JSON/Markdown），负责生成 Plotly
  交互式 HTML 报告（覆盖命中率 / 置信度校准 / 属性预测三张图 + 明细表 + 推荐表）；
  Plotly 缺失时自动降级为纯 HTML 表格。

## 三项回测指标（目标 70%）

| 指标 | 含义 | 说明 |
| --- | --- | --- |
| 覆盖命中率 coverage | 候选池覆盖实际开奖号码的比例 | 随机基线 ~ 候选池大小×开奖数/号码范围 |
| 置信度校准 calibration | 高置信区间（≥0.7）预测的实际命中率 | 对照整体命中率（基线） |
| 属性预测 property | 和值档位 / 奇偶个数 / 大小个数的准确率 | 每项对比随机基线 |

> **重要**：彩票开奖是独立均匀随机过程，任何策略在样本外都无法稳定超越随机基线。
> 回测结果若高于基线，通常来自过拟合。这里的「70%」是报告的目标口径，系统如实
> 输出实测值 / 基线 / 是否达标，而非保证能命中。

## 快速开始

```bash
pip install -r requirements.txt

# 离线回测（合成数据，无需网络）
python main.py --game dlt --synthetic 300 --test-size 50

# 在线抓取并回测（需要网络）
python main.py --game ssq --crawl-limit 500 --test-size 100

# 指定本地数据文件
python main.py --game dlt --data-file data/20260905/dlt_history.xlsx

# 指定策略组合
python main.py --game dlt --strategies frequency,hot_cold,ml,hybrid
```

输出：终端文本报告 + `runs/report_*.html`（交互式图表）+ `runs/report_*.json`
+ `runs/report_*.md` + 运行记录 `runs/history.jsonl`。

## Python API

```python
from predict.service import PredictionService

service = PredictionService(game_name="dlt")
result = service.run(synthetic=300, test_size=50)
print(result["report"]["text"])
```

## 免责声明

本系统仅用于数据分析与软件架构学习，不构成任何购彩建议。请理性对待彩票，切勿沉迷。
