#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
 大乐透号码预测模块
 Lottery Predictor — 多策略综合预测
=============================================================================

 预测策略:
   1. machine_learning  — 随机森林模型按位置预测
   2. frequency_based    — 全量历史高频号码
   3. hot_numbers        — 近期热门号码（最近 20 期）
   4. cold_numbers       — 长期冷门号码（回补策略）
   5. hybrid_approach    — 投票综合（前 4 种策略加权投票）

 回测评估:
   evaluate_prediction_accuracy() — 滚动训练回测，评估预测命中率

 使用示例:
   predictor = LotteryPredictor(df)
   predictor.train_prediction_models()
   predictions = predictor.generate_multiple_predictions(5)
=============================================================================
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from collections import Counter
import random
from typing import List, Dict, Tuple, Optional
import logging

# 使用统一日志配置（由 main.py 的 setup_logging() 初始化）
logger = logging.getLogger(__name__)


class LotteryPredictor:
    """
    大乐透彩票预测器。

    集成多种预测策略：机器学习（随机森林）、频率统计、
    热门号码、冷门号码、混合投票。

    Attributes:
        df:               开奖数据 DataFrame
        red_ball_columns: 红球列名
        blue_ball_columns:蓝球列名
        models:           已训练的模型字典
    """

    def __init__(self, data_df: pd.DataFrame):
        """
        初始化预测器。

        Args:
            data_df: 包含开奖数据的 DataFrame
        """
        self.df = data_df.copy()
        self.red_ball_columns = ['red1', 'red2', 'red3', 'red4', 'red5']
        self.blue_ball_columns = ['blue1', 'blue2']
        self.models = {}  # { 'red_position_1': model, ... }

        # 按期号排序
        if 'issue' in self.df.columns:
            self.df = self.df.sort_values('issue').reset_index(drop=True)

    # ==================================================================
    #  特征工程
    # ==================================================================

    def prepare_features(self) -> pd.DataFrame:
        """
        构建机器学习特征矩阵。

        特征包括:
            - 各位置号码的滑动窗口出现次数
            - 号码本身的奇偶、除3、除5属性
            - 上一期的红球/蓝球和值
            - 期号趋势

        Returns:
            pd.DataFrame: 特征矩阵（不包含目标列）
        """
        features = pd.DataFrame()

        # ---- 红球特征 ----
        for i, col in enumerate(self.red_ball_columns):
            # 滑动窗口出现次数（前 10 期内出现次数）
            rolling_counts = []
            for idx in range(len(self.df)):
                if idx < 10:
                    count = (
                        (self.df[col][:idx + 1] == self.df[col].iloc[idx]).sum()
                    )
                else:
                    count = (
                        (self.df[col][idx - 10:idx] == self.df[col].iloc[idx]).sum()
                    )
                rolling_counts.append(count)
            features[f'{col}_recent_count'] = rolling_counts

            # 号码本身
            features[col] = self.df[col]

            # 数学属性
            features[f'{col}_is_odd'] = (self.df[col] % 2 == 1).astype(int)
            features[f'{col}_div_3'] = (self.df[col] % 3 == 0).astype(int)
            features[f'{col}_div_5'] = (self.df[col] % 5 == 0).astype(int)

        # ---- 蓝球特征 ----
        for i, col in enumerate(self.blue_ball_columns):
            rolling_counts = []
            for idx in range(len(self.df)):
                if idx < 5:
                    count = (
                        (self.df[col][:idx + 1] == self.df[col].iloc[idx]).sum()
                    )
                else:
                    count = (
                        (self.df[col][idx - 5:idx] == self.df[col].iloc[idx]).sum()
                    )
                rolling_counts.append(count)
            features[f'{col}_recent_count'] = rolling_counts
            features[col] = self.df[col]
            features[f'{col}_is_odd'] = (self.df[col] % 2 == 1).astype(int)

        # ---- 跨期特征 ----
        # 上一期红球和值
        red_sums = [0]
        for idx in range(1, len(self.df)):
            prev_red = [
                self.df[col].iloc[idx - 1] for col in self.red_ball_columns
            ]
            red_sums.append(sum(prev_red))
        features['prev_red_sum'] = red_sums

        # 上一期蓝球和值
        blue_sums = [0]
        for idx in range(1, len(self.df)):
            prev_blue = [
                self.df[col].iloc[idx - 1] for col in self.blue_ball_columns
            ]
            blue_sums.append(sum(prev_blue))
        features['prev_blue_sum'] = blue_sums

        # 期号趋势
        if 'issue' in self.df.columns:
            features['issue_num'] = pd.to_numeric(
                self.df['issue'], errors='coerce'
            ).fillna(0)

        return features

    # ==================================================================
    #  模型训练
    # ==================================================================

    def train_prediction_models(self):
        """
        训练所有预测模型。

        为每个红球位置 (5) 和蓝球位置 (2) 各训练一个随机森林分类器。
        训练完成后模型存储在 self.models 字典中。
        """
        features = self.prepare_features()

        # 红球模型（每位置一个）
        for i, col in enumerate(self.red_ball_columns):
            X = features.drop(
                columns=self.red_ball_columns + self.blue_ball_columns,
                errors='ignore'
            )
            y = self.df[col]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            self.models[f'red_position_{i + 1}'] = model
            logger.info("红球位置 %d 模型准确率: %.3f", i + 1, accuracy)

        # 蓝球模型（每位置一个）
        for i, col in enumerate(self.blue_ball_columns):
            X = features.drop(
                columns=self.red_ball_columns + self.blue_ball_columns,
                errors='ignore'
            )
            y = self.df[col]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)

            self.models[f'blue_position_{i + 1}'] = model
            logger.info("蓝球位置 %d 模型准确率: %.3f", i + 1, accuracy)

    # ==================================================================
    #  预测策略
    # ==================================================================

    def predict_next_draw_ml(self) -> Dict[str, List[int]]:
        """
        策略 1: 机器学习预测。

        使用已训练的随机森林模型，基于最后一条数据的特征预测下一期号码。

        Returns:
            dict: {'red_balls': [5个号码], 'blue_balls': [2个号码]}
        """
        if not self.models:
            self.train_prediction_models()

        features = self.prepare_features()
        last_features = features.iloc[-1:].drop(
            columns=self.red_ball_columns + self.blue_ball_columns,
            errors='ignore'
        )

        predicted = {'red_balls': [], 'blue_balls': []}

        # 预测红球
        for i in range(5):
            model_key = f'red_position_{i + 1}'
            if model_key in self.models:
                pred = self.models[model_key].predict(last_features)[0]
                predicted['red_balls'].append(int(pred))

        # 预测蓝球
        for i in range(2):
            model_key = f'blue_position_{i + 1}'
            if model_key in self.models:
                pred = self.models[model_key].predict(last_features)[0]
                predicted['blue_balls'].append(int(pred))

        return predicted

    def predict_next_draw_statistical(
        self, method: str = 'frequency'
    ) -> Dict[str, List[int]]:
        """
        策略 2/3/4: 统计方法预测。

        Args:
            method: 策略名称
                - 'frequency':   全量高频号码
                - 'recent_hot':  近期 (20期) 热门号码
                - 'cold_numbers': 长期冷门号码

        Returns:
            dict: {'red_balls': [...], 'blue_balls': [...]}
        """
        predictions = {'red_balls': [], 'blue_balls': []}

        if method == 'frequency':
            freq_data = self._calculate_frequencies()
            predictions['red_balls'] = (
                freq_data['red_frequency'].sort_values(ascending=False)
                .head(5).index.tolist()
            )
            predictions['blue_balls'] = (
                freq_data['blue_frequency'].sort_values(ascending=False)
                .head(2).index.tolist()
            )

        elif method == 'recent_hot':
            recent_data = self.df.tail(20)

            red_numbers = []
            for col in self.red_ball_columns:
                red_numbers.extend(
                    recent_data[col].dropna().astype(int).tolist()
                )
            red_counter = Counter(red_numbers)

            blue_numbers = []
            for col in self.blue_ball_columns:
                blue_numbers.extend(
                    recent_data[col].dropna().astype(int).tolist()
                )
            blue_counter = Counter(blue_numbers)

            predictions['red_balls'] = [
                num for num, _ in red_counter.most_common(5)
            ]
            predictions['blue_balls'] = [
                num for num, _ in blue_counter.most_common(2)
            ]

        elif method == 'cold_numbers':
            freq_data = self._calculate_frequencies()
            predictions['red_balls'] = (
                freq_data['red_frequency'].sort_values()
                .head(5).index.tolist()
            )
            predictions['blue_balls'] = (
                freq_data['blue_frequency'].sort_values()
                .head(2).index.tolist()
            )

        return predictions

    def predict_next_draw_hybrid(self) -> Dict[str, List[int]]:
        """
        策略 5: 混合投票预测。

        综合 ML、频率、热门三种策略的结果，投票选出最终号码。

        Returns:
            dict: {'red_balls': [...], 'blue_balls': [...]}
        """
        ml_pred = self.predict_next_draw_ml()
        freq_pred = self.predict_next_draw_statistical('frequency')
        hot_pred = self.predict_next_draw_statistical('recent_hot')

        final_prediction = {'red_balls': [], 'blue_balls': []}

        # 红球投票
        all_red = ml_pred['red_balls'] + freq_pred['red_balls'] + hot_pred['red_balls']
        red_counter = Counter(all_red)
        final_prediction['red_balls'] = [
            num for num, _ in red_counter.most_common(5)
        ]

        # 蓝球投票
        all_blue = ml_pred['blue_balls'] + freq_pred['blue_balls'] + hot_pred['blue_balls']
        blue_counter = Counter(all_blue)
        final_prediction['blue_balls'] = [
            num for num, _ in blue_counter.most_common(2)
        ]

        return final_prediction

    # ==================================================================
    #  内部辅助
    # ==================================================================

    def _calculate_frequencies(self) -> Dict:
        """计算全量红球和蓝球频率。"""
        red_numbers = []
        for col in self.red_ball_columns:
            red_numbers.extend(self.df[col].dropna().astype(int).tolist())
        red_freq = pd.Series(Counter(red_numbers))

        blue_numbers = []
        for col in self.blue_ball_columns:
            blue_numbers.extend(self.df[col].dropna().astype(int).tolist())
        blue_freq = pd.Series(Counter(blue_numbers))

        return {
            'red_frequency': red_freq,
            'blue_frequency': blue_freq
        }

    # ==================================================================
    #  多方案生成
    # ==================================================================

    def generate_multiple_predictions(
        self, count: int = 5
    ) -> List[Dict]:
        """
        生成多组预测方案（最多 5 种策略）。

        Args:
            count: 返回方案数 (1-5)

        Returns:
            list[dict]: 每个元素为 {'method': str, 'numbers': {...}}
        """
        methods = [
            ('machine_learning', self.predict_next_draw_ml),
            ('frequency_based', lambda: self.predict_next_draw_statistical('frequency')),
            ('hot_numbers', lambda: self.predict_next_draw_statistical('recent_hot')),
            ('cold_numbers', lambda: self.predict_next_draw_statistical('cold_numbers')),
            ('hybrid_approach', self.predict_next_draw_hybrid),
        ]

        predictions = []
        for method_name, predict_fn in methods[:count]:
            try:
                predictions.append({
                    'method': method_name,
                    'numbers': predict_fn()
                })
            except Exception as e:
                logger.warning("策略 %s 预测失败: %s", method_name, str(e))

        return predictions


# ============================================================================
#  回测评估
# ============================================================================

def evaluate_prediction_accuracy(
    predictor: LotteryPredictor, test_periods: int = 10
):
    """
    滚动回测 —— 评估预测策略在历史数据上的表现。

    使用滚动训练方式：每次用历史数据训练，预测下一期，
    然后加入实际结果继续训练。

    Args:
        predictor: LotteryPredictor 实例
        test_periods: 回测期数
    """
    if len(predictor.df) <= test_periods:
        logger.warning("数据量不足进行回测（需要 > %d 期）", test_periods)
        return

    historical_df = predictor.df[:-test_periods]
    test_df = predictor.df[-test_periods:]

    correct_predictions = 0
    temp_predictor = LotteryPredictor(historical_df)
    temp_predictor.train_prediction_models()

    for i in range(test_periods):
        predicted = temp_predictor.predict_next_draw_hybrid()

        actual_red = (
            test_df.iloc[i][predictor.red_ball_columns]
            .dropna().astype(int).tolist()
        )
        actual_blue = (
            test_df.iloc[i][predictor.blue_ball_columns]
            .dropna().astype(int).tolist()
        )

        red_matches = len(set(predicted['red_balls']) & set(actual_red))
        blue_matches = len(set(predicted['blue_balls']) & set(actual_blue))

        if red_matches > 0 or blue_matches > 0:
            correct_predictions += 1

        # 滚动更新训练数据
        updated_df = pd.concat([historical_df, test_df.iloc[:i + 1]])
        temp_predictor = LotteryPredictor(updated_df)
        temp_predictor.train_prediction_models()

    accuracy = correct_predictions / test_periods
    logger.info(
        "回测准确率: %.2f%% (%d/%d)",
        accuracy * 100, correct_predictions, test_periods
    )


# ============================================================================
#  独立运行入口
# ============================================================================

def main():
    """独立测试预测功能。"""
    try:
        df = pd.read_excel(
            "super_lotto_history.xlsx", sheet_name='lottery_data'
        )
        predictor = LotteryPredictor(df)

        logger.info("正在训练预测模型...")
        predictor.train_prediction_models()

        logger.info("生成预测结果...")
        predictions = predictor.generate_multiple_predictions(5)

        print("\n=== 预测结果 ===")
        for pred in predictions:
            print(f"\n方法: {pred['method']}")
            print(f"红球: {sorted(pred['numbers']['red_balls'])}")
            print(f"蓝球: {sorted(pred['numbers']['blue_balls'])}")

        logger.info("正在进行回测评估...")
        evaluate_prediction_accuracy(predictor, test_periods=5)

    except FileNotFoundError:
        print("数据文件未找到，请先运行爬虫获取数据")
    except Exception as e:
        print(f"预测过程中出现错误: {str(e)}")


if __name__ == "__main__":
    main()
