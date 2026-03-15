#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单回测脚本 - 不依赖backtrader
使用基本Python库进行策略验证
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class SimpleBacktest:
    """
    简单回测系统
    """
    
    def __init__(self):
        # 策略参数
        self.params = {
            'buy_amount': 10000,           # 每次买入金额
            'max_cost': 200000,            # 最大持仓成本
            'volume_ratio_threshold': 3,   # 成交量过滤阈值
            'sell_volume_ratio': 1.5,      # 卖出放量阈值
            'm_days': 5,                   # 条件1：前m天
            'n_days': 3,                   # 条件1：满足n天
            'a_days': 5,                   # 条件2：前a天
            'b_days': 3,                   # 条件2：满足b天
            'rebound_threshold': 0.0003,   # 反弹阈值
            'profit_loss_ratio_take_profit': 0.15,  # 止盈阈值15%
            'max_drawdown_stop': 0.05,     # 回撤清仓阈值5%
            'profit_loss_ratio_stop_loss': -0.05,   # 止损阈值-5%
            't_gain_threshold': 0.05,      # 做T涨幅阈值5%
            't_pullback_threshold': 0.01,  # 做T回落阈值1%
            't_1455_gain_threshold': 0.02, # 14:55做T涨幅阈值2%
        }
        
        # 回测结果
        self.results = {
            'initial_cash': 100000,
            'current_cash': 100000,
            'total_shares': 0,
            'avg_cost': 0,
            'total_cost': 0,
            'trades': [],
            'daily_pnl': [],
            'cumulative_pnl': [],
        }
        
        # 状态变量
        self.last_buy_price = None
        self.highest_buy_price = None
        self.position_high = 0
        self.today_buy_amount = 0
        self.t_done_today = False
        self.buy_count = 0
        self.last_buy_date = None
        self.day_low = None
        self.day_high = 0
        
    def load_data(self, file_path=None):
        """加载数据"""
        if file_path and os.path.exists(file_path):
            # 从文件加载
            df = pd.read_csv(file_path)
        else:
            # 生成模拟数据
            print("生成模拟数据...")
            dates = pd.date_range('2025-12-01', '2026-03-12')
            
            # 生成基础价格数据
            base_price = 1.5
            prices = []
            volumes = []
            
            for i, date in enumerate(dates):
                # 简单的价格生成（加入一些波动）
                change = np.random.normal(0, 0.02)
                if i == 0:
                    price = base_price
                else:
                    price = prices[-1] * (1 + change)
                
                # 成交量
                volume = np.random.normal(100000000, 50000000)
                
                prices.append(price)
                volumes.append(volume)
            
            df = pd.DataFrame({
                'date': dates,
                'open': [p * 0.999 for p in prices],
                'close': prices,
                'high': [p * 1.01 for p in prices],
                'low': [p * 0.99 for p in prices],
                'volume': volumes
            })
        
        # 计算MA5
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        
        return df
    
    def run(self, data):
        """运行回测"""
        print('开始回测...')
        print(f'回测时间：{data["date"].iloc[0].strftime("%Y-%m-%d")} - {data["date"].iloc[-1].strftime("%Y-%m-%d")}')
        print(f'初始资金：{self.results["initial_cash"]}元')
        print('='*60)
        
        for i, row in data.iterrows():
            current_date = row['date']
            current_price = row['close']
            current_open = row['open']
            current_high = row['high']
            current_low = row['low']
            current_volume = row['volume']
            ma5 = row['ma5']
            
            # 检查是否为新的一天
            if self.last_buy_date != current_date.date():
                self.day_low = current_low
                self.day_high = current_high
                self.today_buy_amount = 0
                self.t_done_today = False
            else:
                if self.day_low is None or current_low < self.day_low:
                    self.day_low = current_low
                if current_high > self.day_high:
                    self.day_high = current_high
                    
            # 更新持仓最高价
            if self.results['total_shares'] > 0 and current_price > self.position_high:
                self.position_high = current_price
                
            # 获取历史数据
            if i >= 4:
                hist_data = data.iloc[max(0, i-19):i+1]
                avg_5d_volume = hist_data['volume'].tail(5).mean()
                avg_20d_volume = hist_data['volume'].mean()
                yesterday_close = data.iloc[i-1]['close'] if i > 0 else current_price
            else:
                continue
            
            # 买入条件检查
            if self.results['total_shares'] == 0:
                # 条件1：前m天中有n天满足收盘价>开盘价且收盘价>5日均线
                condition1_count = 0
                m_days = self.params['m_days']
                n_days = self.params['n_days']
                
                for j in range(max(0, i-m_days), i):
                    if j >= 0:
                        close = data.iloc[j]['close']
                        open_price = data.iloc[j]['open']
                        ma5_val = data.iloc[j]['ma5']
                        if close > open_price and close > ma5_val:
                            condition1_count += 1
                            
                condition1 = condition1_count >= n_days
                
                # 条件2：前a天中有b天满足5日均线上升
                condition2_count = 0
                a_days = self.params['a_days']
                b_days = self.params['b_days']
                
                for j in range(max(0, i-a_days-1), i-1):
                    if j + 1 < i:
                        if data.iloc[j+1]['ma5'] > data.iloc[j]['ma5']:
                            condition2_count += 1
                            
                condition2 = condition2_count >= b_days
                
                # 条件3：回踩确认
                condition3 = self.day_low < yesterday_close if self.day_low else False
                
                # 反弹确认
                rebound_confirm = current_price >= self.day_low * (1 + self.params['rebound_threshold']) if self.day_low else True
                
                # 成交量过滤
                volume_filter = avg_5d_volume / avg_20d_volume < self.params['volume_ratio_threshold'] if avg_20d_volume > 0 else True
                
                # 资金管理
                cost_check = self.results['total_cost'] < self.params['max_cost']
                
                # 价格检查
                price_check = True
                if self.last_buy_price is not None and current_price < self.last_buy_price:
                    price_check = False
                    
                # 执行买入
                if condition1 and condition2 and condition3 and rebound_confirm and volume_filter and cost_check and price_check:
                    buy_shares = int(self.params['buy_amount'] / current_price) // 100 * 100
                    if buy_shares >= 100:
                        cost = buy_shares * current_price
                        if self.results['current_cash'] >= cost:
                            print(f'{current_date.strftime("%Y-%m-%d")} - 买入: {buy_shares}股, 价格: {current_price:.2f}, 成本: {cost:.2f}')
                            
                            # 更新持仓
                            self.results['total_shares'] += buy_shares
                            self.results['total_cost'] += cost
                            self.results['avg_cost'] = self.results['total_cost'] / self.results['total_shares']
                            self.results['current_cash'] -= cost
                            
                            # 更新状态
                            self.last_buy_price = current_price
                            self.today_buy_amount += buy_shares
                            self.buy_count += 1
                            if self.highest_buy_price is None or current_price > self.highest_buy_price:
                                self.highest_buy_price = current_price
                            if self.position_high == 0 or current_price > self.position_high:
                                self.position_high = current_price
                            
                            self.last_buy_date = current_date.date()
                            
                            # 记录交易
                            self.results['trades'].append({
                                'date': current_date,
                                'type': 'buy',
                                'shares': buy_shares,
                                'price': current_price,
                                'cost': cost
                            })
            else:
                # 持仓状态下的操作
                position_size = self.results['total_shares']
                avg_cost = self.results['avg_cost']
                profit_loss_ratio = (current_price - avg_cost) / avg_cost if avg_cost > 0 else 0
                
                # 计算从最高点回撤
                drawdown = (self.position_high - current_price) / self.position_high if self.position_high > 0 else 0
                
                # 分批止盈检查
                volume_condition = current_volume > avg_5d_volume * self.params['sell_volume_ratio']
                profit_condition = profit_loss_ratio > self.params['profit_loss_ratio_take_profit']
                
                if volume_condition or profit_condition:
                    sell_shares = position_size // 2
                    if sell_shares > 0:
                        sell_shares = ((sell_shares + 99) // 100) * 100  # 向上取整到100股
                        proceeds = sell_shares * current_price
                        
                        print(f'{current_date.strftime("%Y-%m-%d")} - 分批止盈: {sell_shares}股, 价格: {current_price:.2f}, 收入: {proceeds:.2f}')
                        
                        # 更新持仓
                        self.results['total_shares'] -= sell_shares
                        self.results['total_cost'] = self.results['avg_cost'] * self.results['total_shares']
                        self.results['current_cash'] += proceeds
                        
                        # 记录交易
                        self.results['trades'].append({
                            'date': current_date,
                            'type': 'sell_partial',
                            'shares': sell_shares,
                            'price': current_price,
                            'proceeds': proceeds
                        })
                
                # 做T条件检查
                elif not self.t_done_today and self.last_buy_date == current_date.date() and self.today_buy_amount > 0:
                    # 做T条件1：单日涨幅>5%且回落1%
                    gain = (current_price / yesterday_close - 1)
                    pullback = (self.day_high - current_price) / self.day_high if self.day_high > 0 else 0
                    
                    if gain > self.params['t_gain_threshold'] and pullback > self.params['t_pullback_threshold']:
                        sell_shares = min(position_size, self.today_buy_amount)
                        if sell_shares > 0:
                            proceeds = sell_shares * current_price
                            
                            print(f'{current_date.strftime("%Y-%m-%d")} - 做T: {sell_shares}股, 价格: {current_price:.2f}, 收入: {proceeds:.2f}')
                            
                            # 更新持仓
                            self.results['total_shares'] -= sell_shares
                            self.results['total_cost'] = self.results['avg_cost'] * self.results['total_shares']
                            self.results['current_cash'] += proceeds
                            
                            # 更新状态
                            self.today_buy_amount -= sell_shares
                            self.t_done_today = True
                            
                            # 记录交易
                            self.results['trades'].append({
                                'date': current_date,
                                'type': 't_sell',
                                'shares': sell_shares,
                                'price': current_price,
                                'proceeds': proceeds
                            })
                
                # 清仓条件检查
                drawdown_condition = drawdown > self.params['max_drawdown_stop']
                stop_loss_condition = profit_loss_ratio < self.params['profit_loss_ratio_stop_loss']
                
                if drawdown_condition or stop_loss_condition:
                    if drawdown_condition:
                        print(f'{current_date.strftime("%Y-%m-%d")} - 回撤清仓: 回撤={drawdown:.2%}, 最高价={self.position_high:.2f}')
                    if stop_loss_condition:
                        print(f'{current_date.strftime("%Y-%m-%d")} - 止损清仓: 盈亏率={profit_loss_ratio:.2%}')
                    
                    proceeds = position_size * current_price
                    print(f'{current_date.strftime("%Y-%m-%d")} - 清仓: {position_size}股, 价格: {current_price:.2f}, 收入: {proceeds:.2f}')
                    
                    # 更新持仓
                    self.results['current_cash'] += proceeds
                    self.results['total_shares'] = 0
                    self.results['total_cost'] = 0
                    self.results['avg_cost'] = 0
                    
                    # 重置状态
                    self.position_high = 0
                    self.buy_count = 0
                    
                    # 记录交易
                    self.results['trades'].append({
                        'date': current_date,
                        'type': 'sell_all',
                        'shares': position_size,
                        'price': current_price,
                        'proceeds': proceeds
                    })
            
            # 计算当日盈亏
            current_value = self.results['total_shares'] * current_price
            total_value = self.results['current_cash'] + current_value
            daily_pnl = total_value - (self.results['initial_cash'] + sum(self.results['daily_pnl']))
            self.results['daily_pnl'].append(daily_pnl)
            self.results['cumulative_pnl'].append(sum(self.results['daily_pnl']))
        
        # 结束时清仓
        if self.results['total_shares'] > 0:
            current_price = data.iloc[-1]['close']
            proceeds = self.results['total_shares'] * current_price
            self.results['current_cash'] += proceeds
            self.results['total_shares'] = 0
            self.results['total_cost'] = 0
            self.results['avg_cost'] = 0
            
            print(f'{data.iloc[-1]["date"].strftime("%Y-%m-%d")} - 最终清仓: {proceeds:.2f}')
        
        # 计算最终结果
        final_value = self.results['current_cash']
        total_return = (final_value - self.results['initial_cash']) / self.results['initial_cash']
        
        print('\n' + '='*60)
        print('回测结果')
        print('='*60)
        print(f'初始资金: {self.results["initial_cash"]:.2f}元')
        print(f'最终资金: {final_value:.2f}元')
        print(f'总收益率: {total_return*100:.2f}%')
        print(f'交易次数: {len(self.results["trades"])}')
        print('='*60)
        
        # 绘制结果
        self.plot_results(data)
    
    def plot_results(self, data):
        """绘制回测结果"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
            
            # 价格和MA
            ax1.plot(data['date'], data['close'], label='价格')
            ax1.plot(data['date'], data['ma5'], label='MA5')
            ax1.plot(data['date'], data['ma20'], label='MA20')
            
            # 标记交易
            buy_dates = []
            buy_prices = []
            sell_dates = []
            sell_prices = []
            
            for trade in self.results['trades']:
                if trade['type'] in ['buy']:
                    buy_dates.append(trade['date'])
                    buy_prices.append(trade['price'])
                elif trade['type'] in ['sell_partial', 'sell_all', 't_sell']:
                    sell_dates.append(trade['date'])
                    sell_prices.append(trade['price'])
            
            ax1.scatter(buy_dates, buy_prices, color='green', marker='^', label='买入')
            ax1.scatter(sell_dates, sell_prices, color='red', marker='v', label='卖出')
            
            ax1.set_ylabel('价格')
            ax1.set_title('价格走势和交易信号')
            ax1.legend()
            
            # 累计盈亏
            ax2.plot(data['date'], self.results['cumulative_pnl'])
            ax2.set_ylabel('累计盈亏')
            ax2.set_xlabel('日期')
            ax2.set_title('累计盈亏曲线')
            
            plt.tight_layout()
            plt.savefig('backtest_results.png')
            print('回测结果已保存为 backtest_results.png')
            
        except Exception as e:
            print(f'绘制图表失败: {e}')


def main():
    """主函数"""
    backtest = SimpleBacktest()
    data = backtest.load_data()
    backtest.run(data)


if __name__ == '__main__':
    main()
