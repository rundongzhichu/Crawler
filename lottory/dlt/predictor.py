import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from collections import Counter
import random
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class LotteryPredictor:
    """彩票预测模型"""
    
    def __init__(self, data_df: pd.DataFrame):
        self.df = data_df.copy()
        self.red_ball_columns = ['red1', 'red2', 'red3', 'red4', 'red5']
        self.blue_ball_columns = ['blue1', 'blue2']
        self.models = {}  # 存储训练好的模型
        
        # 确保数据按期号排序
        if 'issue' in self.df.columns:
            self.df = self.df.sort_values('issue').reset_index(drop=True)
    
    def prepare_features(self) -> pd.DataFrame:
        """准备特征数据"""
        features = pd.DataFrame()
        
        # 基础统计特征
        for i, col in enumerate(self.red_ball_columns):
            # 历史出现次数特征
            rolling_counts = []
            for idx in range(len(self.df)):
                if idx < 10:  # 前10期用全局统计
                    count = (self.df[col][:idx+1] == self.df[col].iloc[idx]).sum()
                else:
                    count = (self.df[col][idx-10:idx] == self.df[col].iloc[idx]).sum()
                rolling_counts.append(count)
            features[f'{col}_recent_count'] = rolling_counts
            
            # 号码本身作为特征
            features[col] = self.df[col]
            
            # 号码的数学特征
            features[f'{col}_is_odd'] = (self.df[col] % 2 == 1).astype(int)
            features[f'{col}_div_3'] = (self.df[col] % 3 == 0).astype(int)
            features[f'{col}_div_5'] = (self.df[col] % 5 == 0).astype(int)
        
        # 蓝球特征
        for i, col in enumerate(self.blue_ball_columns):
            rolling_counts = []
            for idx in range(len(self.df)):
                if idx < 5:
                    count = (self.df[col][:idx+1] == self.df[col].iloc[idx]).sum()
                else:
                    count = (self.df[col][idx-5:idx] == self.df[col].iloc[idx]).sum()
                rolling_counts.append(count)
            features[f'{col}_recent_count'] = rolling_counts
            features[col] = self.df[col]
            features[f'{col}_is_odd'] = (self.df[col] % 2 == 1).astype(int)
        
        # 整体特征
        # 前一期的红球和值
        red_sums = []
        for idx in range(len(self.df)):
            if idx == 0:
                red_sums.append(0)
            else:
                prev_red = [self.df[col].iloc[idx-1] for col in self.red_ball_columns]
                red_sums.append(sum(prev_red))
        features['prev_red_sum'] = red_sums
        
        # 前一期的蓝球和值
        blue_sums = []
        for idx in range(len(self.df)):
            if idx == 0:
                blue_sums.append(0)
            else:
                prev_blue = [self.df[col].iloc[idx-1] for col in self.blue_ball_columns]
                blue_sums.append(sum(prev_blue))
        features['prev_blue_sum'] = blue_sums
        
        # 期号特征（趋势）
        if 'issue' in self.df.columns:
            features['issue_num'] = pd.to_numeric(self.df['issue'], errors='coerce').fillna(0)
        
        return features
    
    def train_prediction_models(self):
        """训练预测模型"""
        features = self.prepare_features()
        
        # 训练红球预测模型（每个位置一个模型）
        for i, col in enumerate(self.red_ball_columns):
            X = features.drop(columns=self.red_ball_columns + self.blue_ball_columns)
            y = self.df[col]
            
            # 分割训练测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # 训练随机森林模型
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            # 评估模型
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            self.models[f'red_position_{i+1}'] = model
            logger.info(f"红球位置 {i+1} 模型准确率: {accuracy:.3f}")
        
        # 训练蓝球预测模型
        for i, col in enumerate(self.blue_ball_columns):
            X = features.drop(columns=self.red_ball_columns + self.blue_ball_columns)
            y = self.df[col]
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            self.models[f'blue_position_{i+1}'] = model
            logger.info(f"蓝球位置 {i+1} 模型准确率: {accuracy:.3f}")
    
    def predict_next_draw_ml(self) -> Dict[str, List[int]]:
        """使用机器学习模型预测下一期号码"""
        if not self.models:
            self.train_prediction_models()
        
        # 准备最后一期的特征用于预测
        features = self.prepare_features()
        last_features = features.iloc[-1:].drop(
            columns=self.red_ball_columns + self.blue_ball_columns
        )
        
        predicted_numbers = {
            'red_balls': [],
            'blue_balls': []
        }
        
        # 预测红球
        for i in range(5):
            model_key = f'red_position_{i+1}'
            if model_key in self.models:
                pred = self.models[model_key].predict(last_features)[0]
                predicted_numbers['red_balls'].append(int(pred))
        
        # 预测蓝球
        for i in range(2):
            model_key = f'blue_position_{i+1}'
            if model_key in self.models:
                pred = self.models[model_key].predict(last_features)[0]
                predicted_numbers['blue_balls'].append(int(pred))
        
        return predicted_numbers
    
    def predict_next_draw_statistical(self, method: str = 'frequency') -> Dict[str, List[int]]:
        """基于统计方法预测下一期号码"""
        predictions = {
            'red_balls': [],
            'blue_balls': []
        }
        
        if method == 'frequency':
            # 基于频率的预测
            freq_data = self._calculate_frequencies()
            
            # 选择高频号码
            red_freq_sorted = freq_data['red_frequency'].sort_values(ascending=False)
            blue_freq_sorted = freq_data['blue_frequency'].sort_values(ascending=False)
            
            predictions['red_balls'] = red_freq_sorted.head(5).index.tolist()
            predictions['blue_balls'] = blue_freq_sorted.head(2).index.tolist()
            
        elif method == 'recent_hot':
            # 基于近期热门号码
            recent_data = self.df.tail(20)  # 最近20期
            
            # 统计近期出现频率
            red_numbers = []
            for col in self.red_ball_columns:
                red_numbers.extend(recent_data[col].dropna().astype(int).tolist())
            red_counter = Counter(red_numbers)
            
            blue_numbers = []
            for col in self.blue_ball_columns:
                blue_numbers.extend(recent_data[col].dropna().astype(int).tolist())
            blue_counter = Counter(blue_numbers)
            
            predictions['red_balls'] = [num for num, _ in red_counter.most_common(5)]
            predictions['blue_balls'] = [num for num, _ in blue_counter.most_common(2)]
            
        elif method == 'cold_numbers':
            # 基于冷门号码（长期未出现）
            freq_data = self._calculate_frequencies()
            
            # 选择低频号码
            red_freq_sorted = freq_data['red_frequency'].sort_values()
            blue_freq_sorted = freq_data['blue_frequency'].sort_values()
            
            predictions['red_balls'] = red_freq_sorted.head(5).index.tolist()
            predictions['blue_balls'] = blue_freq_sorted.head(2).index.tolist()
        
        return predictions
    
    def _calculate_frequencies(self) -> Dict:
        """计算号码频率"""
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
    
    def predict_next_draw_hybrid(self) -> Dict[str, List[int]]:
        """混合预测方法"""
        # 获取多种预测结果
        ml_pred = self.predict_next_draw_ml()
        freq_pred = self.predict_next_draw_statistical('frequency')
        hot_pred = self.predict_next_draw_statistical('recent_hot')
        
        # 综合预测 - 投票机制
        final_prediction = {
            'red_balls': [],
            'blue_balls': []
        }
        
        # 红球综合
        all_red_predictions = (
            ml_pred['red_balls'] + 
            freq_pred['red_balls'] + 
            hot_pred['red_balls']
        )
        red_counter = Counter(all_red_predictions)
        final_prediction['red_balls'] = [num for num, _ in red_counter.most_common(5)]
        
        # 蓝球综合
        all_blue_predictions = (
            ml_pred['blue_balls'] + 
            freq_pred['blue_balls'] + 
            hot_pred['blue_balls']
        )
        blue_counter = Counter(all_blue_predictions)
        final_prediction['blue_balls'] = [num for num, _ in blue_counter.most_common(2)]
        
        return final_prediction
    
    def generate_multiple_predictions(self, count: int = 5) -> List[Dict[str, List[int]]]:
        """生成多组预测方案"""
        predictions = []
        
        # 方法1: 机器学习预测
        predictions.append({
            'method': 'machine_learning',
            'numbers': self.predict_next_draw_ml()
        })
        
        # 方法2: 频率统计预测
        predictions.append({
            'method': 'frequency_based',
            'numbers': self.predict_next_draw_statistical('frequency')
        })
        
        # 方法3: 热门号码预测
        predictions.append({
            'method': 'hot_numbers',
            'numbers': self.predict_next_draw_statistical('recent_hot')
        })
        
        # 方法4: 冷门号码预测
        predictions.append({
            'method': 'cold_numbers',
            'numbers': self.predict_next_draw_statistical('cold_numbers')
        })
        
        # 方法5: 混合预测
        predictions.append({
            'method': 'hybrid_approach',
            'numbers': self.predict_next_draw_hybrid()
        })
        
        return predictions[:count]

def evaluate_prediction_accuracy(predictor: LotteryPredictor, test_periods: int = 10):
    """评估预测准确性（回测）"""
    if len(predictor.df) <= test_periods:
        logger.warning("数据量不足进行回测")
        return
    
    # 使用历史数据进行回测
    historical_df = predictor.df[:-test_periods]  # 训练数据
    test_df = predictor.df[-test_periods:]       # 测试数据
    
    # 在历史数据上重新训练模型
    temp_predictor = LotteryPredictor(historical_df)
    temp_predictor.train_prediction_models()
    
    correct_predictions = 0
    total_predictions = test_periods
    
    for i in range(test_periods):
        # 预测当前期
        predicted = temp_predictor.predict_next_draw_hybrid()
        
        # 获取实际结果
        actual_red = test_df.iloc[i][predictor.red_ball_columns].dropna().astype(int).tolist()
        actual_blue = test_df.iloc[i][predictor.blue_ball_columns].dropna().astype(int).tolist()
        
        # 检查预测准确性（只要有一个号码匹配就算正确）
        red_matches = len(set(predicted['red_balls']) & set(actual_red))
        blue_matches = len(set(predicted['blue_balls']) & set(actual_blue))
        
        if red_matches > 0 or blue_matches > 0:
            correct_predictions += 1
        
        # 更新训练数据
        updated_df = pd.concat([historical_df, test_df.iloc[:i+1]])
        temp_predictor = LotteryPredictor(updated_df)
        temp_predictor.train_prediction_models()
    
    accuracy = correct_predictions / total_predictions
    logger.info(f"回测准确率: {accuracy:.2%} ({correct_predictions}/{total_predictions})")

def main():
    """测试预测功能"""
    try:
        # 读取数据
        df = pd.read_excel("super_lotto_history.xlsx", sheet_name='lottery_data')
        predictor = LotteryPredictor(df)
        
        # 训练模型
        logger.info("正在训练预测模型...")
        predictor.train_prediction_models()
        
        # 生成预测
        logger.info("生成预测结果...")
        predictions = predictor.generate_multiple_predictions(5)
        
        print("\n=== 预测结果 ===")
        for pred in predictions:
            print(f"\n方法: {pred['method']}")
            print(f"红球: {sorted(pred['numbers']['red_balls'])}")
            print(f"蓝球: {sorted(pred['numbers']['blue_balls'])}")
        
        # 回测评估
        logger.info("正在进行回测评估...")
        evaluate_prediction_accuracy(predictor, test_periods=5)
        
    except FileNotFoundError:
        print("数据文件未找到，请先运行爬虫获取数据")
    except Exception as e:
        print(f"预测过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main()