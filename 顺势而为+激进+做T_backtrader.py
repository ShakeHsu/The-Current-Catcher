#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtrader版本策略 - 用于本地回测验证
原PTrade策略的Backtrader适配版本
"""

import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class TrendFollowingStrategy(bt.Strategy):
    """
    顺势而为+激进+做T策略的Backtrader实现
    """
    
    # 策略参数
    params = (
        ('security', '159206.SZ'),      # 交易标的
        ('buy_amount', 10000),           # 每次买入金额
        ('max_cost', 200000),            # 最大持仓成本
        ('volume_ratio_threshold', 3),   # 成交量过滤阈值
        ('sell_volume_ratio', 1.5),      # 卖出放量阈值
        ('m_days', 5),                   # 条件1：前m天
        ('n_days', 3),                   # 条件1：满足n天
        ('a_days', 5),                   # 条件2：前a天
        ('b_days', 3),                   # 条件2：满足b天
        ('rebound_threshold', 0.0003),   # 反弹阈值
        ('profit_loss_ratio_take_profit', 0.15),  # 止盈阈值15%
        ('max_drawdown_stop', 0.05),     # 回撤清仓阈值5%
        ('profit_loss_ratio_stop_loss', -0.05),   # 止损阈值-5%
        ('t_gain_threshold', 0.05),      # 做T涨幅阈值5%
        ('t_pullback_threshold', 0.01),  # 做T回落阈值1%
        ('t_1455_gain_threshold', 0.02), # 14:55做T涨幅阈值2%
    )
    
    def __init__(self):
        # 数据引用
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavolume = self.datas[0].volume
        
        # 技术指标
        self.ma5 = bt.indicators.SimpleMovingAverage(self.dataclose, period=5)
        self.ma20 = bt.indicators.SimpleMovingAverage(self.dataclose, period=20)
        
        # 状态变量
        self.total_cost = 0              # 累计成本
        self.avg_cost = 0                # 平均成本
        self.last_buy_price = None       # 上次买入价格
        self.highest_buy_price = None    # 最高买入价格
        self.position_high = 0           # 持仓期间最高价
        self.today_buy_amount = 0        # 当日买入量
        self.t_done_today = False        # 当日是否已做T
        self.buy_count = 0               # 买入次数
        self.last_buy_date = None        # 上次买入日期
        self.day_low = None              # 当日最低价
        self.day_high = 0                # 当日最高价
        
        # 跟踪订单
        self.order = None
        
        # 交易记录
        self.trade_history = []
        
    def log(self, txt, dt=None):
        """日志输出"""
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} - {txt}')
        
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            current_datetime = self.datas[0].datetime.datetime(0)
            if order.isbuy():
                self.log(f'买入执行: 价格={order.executed.price:.2f}, 数量={order.executed.size}')
                # 更新成本
                self.total_cost += order.executed.size * order.executed.price
                self.avg_cost = self.total_cost / self.position.size if self.position.size > 0 else 0
                self.last_buy_price = order.executed.price
                self.today_buy_amount += order.executed.size
                self.buy_count += 1
                if self.highest_buy_price is None or order.executed.price > self.highest_buy_price:
                    self.highest_buy_price = order.executed.price
                if self.position_high == 0 or order.executed.price > self.position_high:
                    self.position_high = order.executed.price
                # 计算实际成本
                actual_cost = order.executed.price * order.executed.size
                # 记录交易
                self.trade_history.append({
                    'datetime': current_datetime,
                    'type': 'buy',
                    'price': order.executed.price,
                    'size': order.executed.size,
                    'cost': actual_cost
                })
            else:
                self.log(f'卖出执行: 价格={order.executed.price:.2f}, 数量={order.executed.size}')
                # 更新成本
                self.total_cost = self.avg_cost * self.position.size if self.position.size > 0 else 0
                # 计算实际价值
                actual_value = order.executed.price * abs(order.executed.size)
                # 记录交易
                self.trade_history.append({
                    'datetime': current_datetime,
                    'type': 'sell',
                    'price': order.executed.price,
                    'size': abs(order.executed.size),
                    'value': actual_value
                })
                
        self.order = None
        
    def next(self):
        """策略主逻辑 - 每个bar调用一次"""
        current_datetime = self.datas[0].datetime.datetime(0)
        current_date = current_datetime.date()
        current_time = current_datetime.time()
        current_price = self.dataclose[0]
        current_open = self.dataopen[0]
        current_high = self.datahigh[0]
        current_low = self.datalow[0]
        current_volume = self.datavolume[0]
        
        # 在每个分钟都执行策略（使用真实分钟级数据）
        current_time_str = current_time.strftime('%H:%M:%S')
        
        # 只在关键时间点输出日志，避免输出过多
        key_times = ['09:30:00', '10:00:00', '10:30:00', '11:00:00', '11:30:00', 
                     '13:30:00', '14:00:00', '14:30:00', '14:55:00', '15:00:00']
        
        if current_time_str in key_times:
            time_label = current_time.strftime('%H:%M')
            self.log(f"[{time_label}] 监测价格: {current_price:.2f}")
        
        # 检查是否为新的一天
        if self.last_buy_date != current_date:
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
        if self.position and current_price > self.position_high:
            self.position_high = current_price
            
        # 获取历史数据用于计算
        hist_close = []
        hist_open = []
        hist_volume = []
        hist_ma5 = []
        
        # 获取最近20天的数据（使用日级数据计算）
        # 由于是分钟级数据，我们需要获取足够的历史数据
        for i in range(min(20, len(self.dataclose))):
            idx = -i
            if len(self.dataclose) + idx >= 0:
                hist_close.append(self.dataclose[idx])
                hist_open.append(self.dataopen[idx])
                hist_volume.append(self.datavolume[idx])
                hist_ma5.append(self.ma5[idx])
                
        hist_close = list(reversed(hist_close))
        hist_open = list(reversed(hist_open))
        hist_volume = list(reversed(hist_volume))
        hist_ma5 = list(reversed(hist_ma5))
        
        # 计算均线和成交量
        if len(hist_close) >= 5:
            avg_5d_volume = np.mean(hist_volume[-5:]) if len(hist_volume) >= 5 else current_volume
            avg_20d_volume = np.mean(hist_volume[-20:]) if len(hist_volume) >= 20 else current_volume
            yesterday_close = hist_close[-2] if len(hist_close) >= 2 else current_price
        else:
            return
        
        # 执行策略逻辑
        self.execute_strategy_at_minute(current_date, current_time_str, current_price, current_open, 
                                      current_high, current_low, current_volume, yesterday_close, 
                                      avg_5d_volume, avg_20d_volume, hist_close, hist_open, hist_ma5)
    
    def execute_strategy_at_minute(self, current_date, current_time_str, current_price, open_price, 
                                  high, low, current_volume, yesterday_close, 
                                  avg_5d_volume, avg_20d_volume, hist_close, hist_open, hist_ma5):
        """在分钟级别执行策略"""
        # 更新当日高低点
        if self.day_low is None or current_price < self.day_low:
            self.day_low = current_price
        if current_price > self.day_high:
            self.day_high = current_price
            
        # 更新持仓最高价
        if self.position and current_price > self.position_high:
            self.position_high = current_price
        
        # 计算条件参数
        m_days = self.p.m_days
        n_days = self.p.n_days
        a_days = self.p.a_days
        b_days = self.p.b_days
        
        # 条件1：前m天中有n天满足收盘价>开盘价且收盘价>5日均线
        condition1_count = 0
        for i in range(max(0, len(hist_close) - m_days), len(hist_close)):
            if i < len(hist_ma5):
                close = hist_close[i]
                open_p = hist_open[i]
                ma5 = hist_ma5[i]
                if close > open_p and close > ma5:
                    condition1_count += 1
        condition1 = condition1_count >= n_days
        
        # 条件2：前a天中有b天满足5日均线上升
        condition2_count = 0
        for i in range(max(0, len(hist_ma5) - a_days - 1), len(hist_ma5) - 1):
            if i + 1 < len(hist_ma5):
                if hist_ma5[i+1] > hist_ma5[i]:
                    condition2_count += 1
        condition2 = condition2_count >= b_days
        
        # 条件3：回踩确认
        condition3 = self.day_low < yesterday_close if self.day_low else False
        
        # 反弹确认
        rebound_confirm = current_price >= self.day_low * (1 + self.p.rebound_threshold) if self.day_low else True
        
        # 成交量过滤
        volume_filter = avg_5d_volume / avg_20d_volume < self.p.volume_ratio_threshold if avg_20d_volume > 0 else True
        
        # 资金管理
        cost_check = self.total_cost < self.p.max_cost
        
        # 价格检查（当前价格不低于上次买入价格）
        price_check = True
        if self.last_buy_price is not None and current_price < self.last_buy_price:
            price_check = False
        
        # ========== 买入条件检查 ==========
        if not self.position or self.position.size == 0:
            # 检查是否已经在当天买入过
            if self.last_buy_date == current_date:
                # 单日只能买入一次
                return
                
            # 执行买入
            if condition1 and condition2 and condition3 and rebound_confirm and volume_filter and cost_check and price_check:
                # 计算买入股数（100股整数倍）
                buy_shares = int(self.p.buy_amount / current_price) // 100 * 100
                if buy_shares >= 100:
                    self.log(f'[{current_time_str[:5]}] 买入信号: 价格={current_price:.2f}, 股数={buy_shares}')
                    self.log(f'  条件1: {condition1} ({condition1_count}/{m_days})')
                    self.log(f'  条件2: {condition2} ({condition2_count}/{a_days})')
                    self.log(f'  条件3: {condition3}')
                    self.order = self.buy(size=buy_shares)
                    self.last_buy_date = current_date
        else:
            # ========== 持仓状态下的操作 ==========
            position_size = self.position.size
            avg_cost = self.avg_cost
            profit_loss_ratio = (current_price - avg_cost) / avg_cost if avg_cost > 0 else 0
            
            # 计算从最高点回撤
            drawdown = (self.position_high - current_price) / self.position_high if self.position_high > 0 else 0
            
            # ========== 分批止盈检查 ==========
            volume_condition = current_volume > avg_5d_volume * self.p.sell_volume_ratio
            profit_condition = profit_loss_ratio > self.p.profit_loss_ratio_take_profit
            
            if volume_condition or profit_condition:
                sell_shares = position_size // 2
                if sell_shares > 0:
                    sell_shares = ((sell_shares + 99) // 100) * 100  # 向上取整到100股
                    self.log(f'[{current_time_str[:5]}] 分批止盈: 价格={current_price:.2f}, 股数={sell_shares}')
                    self.log(f'  放量条件: {volume_condition}, 盈亏率条件: {profit_condition}')
                    self.order = self.sell(size=sell_shares)
                    
            # ========== 做T条件检查 ==========
            elif not self.t_done_today and self.last_buy_date == current_date and self.today_buy_amount > 0:
                # 做T条件1：单日涨幅>5%且回落1%
                gain = (current_price / yesterday_close - 1)
                pullback = (self.day_high - current_price) / self.day_high if self.day_high > 0 else 0
                
                if gain > self.p.t_gain_threshold and pullback > self.p.t_pullback_threshold:
                    sell_shares = min(position_size, self.today_buy_amount)
                    if sell_shares > 0:
                        self.log(f'[{current_time_str[:5]}] 做T条件1: 涨幅={gain:.2%}, 回落={pullback:.2%}')
                        self.order = self.sell(size=sell_shares)
                        self.today_buy_amount -= sell_shares
                        self.t_done_today = True
                
                # 做T条件2：14:55涨幅>2%
                if current_time_str == '14:55:00':
                    if gain > self.p.t_1455_gain_threshold:
                        sell_shares = min(position_size, self.today_buy_amount)
                        if sell_shares > 0:
                            self.log(f'[{current_time_str[:5]}] 做T条件2: 涨幅={gain:.2%}')
                            self.order = self.sell(size=sell_shares)
                            self.today_buy_amount -= sell_shares
                            self.t_done_today = True
                    
            # ========== 清仓条件检查 ==========
            drawdown_condition = drawdown > self.p.max_drawdown_stop
            stop_loss_condition = profit_loss_ratio < self.p.profit_loss_ratio_stop_loss
            
            if drawdown_condition or stop_loss_condition:
                if drawdown_condition:
                    self.log(f'[{current_time_str[:5]}] 回撤清仓: 回撤={drawdown:.2%}, 最高价={self.position_high:.2f}')
                if stop_loss_condition:
                      self.log(f'[{current_time_str[:5]}] 止损清仓: 盈亏率={profit_loss_ratio:.2%}')
                self.order = self.close()
                self.total_cost = 0
                self.position_high = 0
                self.buy_count = 0
                
    def stop(self):
        """策略结束时的统计"""
        self.log('策略结束')
        self.log(f'最终市值: {self.broker.getvalue():.2f}')
        

def run_backtest():
    """运行回测"""
    # 创建Cerebro引擎
    cerebro = bt.Cerebro()
    
    # 设置初始资金
    cerebro.broker.setcash(100000.0)
    
    # 设置手续费（模拟A股）
    cerebro.broker.setcommission(commission=0.0003)  # 万分之三
    
    # 设置滑点
    cerebro.broker.set_slippage_perc(perc=0.001)
    
    # 加载数据
    try:
        # 尝试获取真实的分钟级数据
        import akshare as ak
        
        print("正在下载真实分钟级数据...")
        print(f"当前时间: {datetime.now()}")
        print(f"尝试获取的时间范围: 2025-12-01 09:30:00 到 2026-03-12 15:00:00")
        
        # 尝试获取ETF的分钟级数据
        try:
            # 尝试使用用户提供的正确接口
            try:
                print("尝试使用 ak.stock_zh_a_hist_min_em 接口...")
                df_minute = ak.stock_zh_a_hist_min_em(
                    symbol="159206",      # 股票代码
                    period="1",           # 1分钟线
                    start_date="2025-12-01 09:30:00",
                    end_date="2026-03-12 15:00:00",
                    adjust="qfq"          # 前复权
                )
                print(f"数据获取成功！数据形状: {df_minute.shape}")
                print(f"数据列名: {df_minute.columns.tolist()}")
                print(f"前5行数据:\n{df_minute.head()}")
            except Exception as e1:
                print(f"ak.stock_zh_a_hist_min_em 接口失败: {e1}")
                try:
                    print("尝试使用 ak.stock_zh_a_hist_min_em 接口（股票代码格式）...")
                    df_minute = ak.stock_zh_a_hist_min_em(
                        symbol="159206.SZ",      # 股票代码
                        period="1",           # 1分钟线
                        start_date="2025-12-01 09:30:00",
                        end_date="2026-03-12 15:00:00",
                        adjust="qfq"          # 前复权
                    )
                    print(f"数据获取成功！数据形状: {df_minute.shape}")
                except Exception as e2:
                    print(f"股票代码格式失败: {e2}")
                    # 尝试获取指数分钟数据
                    try:
                        print("尝试使用 ak.index_zh_a_hist_min_em 接口...")
                        df_minute = ak.index_zh_a_hist_min_em(
                            symbol="159206",      # 代码
                            period="1",
                            start_date="2025-12-01 09:30:00",
                            end_date="2026-03-12 15:00:00"
                        )
                        print(f"数据获取成功！数据形状: {df_minute.shape}")
                    except Exception as e3:
                        print(f"指数接口失败: {e3}")
                        # 所有接口都失败
                        raise Exception("无法获取分钟级数据")
            
            print("分钟级数据获取成功，共", len(df_minute), "条记录")
            
            # 处理分钟级数据
            print("处理分钟级数据...")
            
            # 检查数据结构
            print("数据列名:", df_minute.columns.tolist())
            print("数据形状:", df_minute.shape)
            
            # 处理时间列
            if '时间' in df_minute.columns:
                df_minute['datetime'] = pd.to_datetime(df_minute['时间'])
            elif 'datetime' in df_minute.columns:
                df_minute['datetime'] = pd.to_datetime(df_minute['datetime'])
            elif 'date' in df_minute.columns:
                df_minute['datetime'] = pd.to_datetime(df_minute['date'])
            elif 'trade_time' in df_minute.columns:
                df_minute['datetime'] = pd.to_datetime(df_minute['trade_time'])
            
            # 统一列名
            column_mapping = {
                'open': 'open',
                '开盘': 'open',
                'close': 'close',
                '收盘': 'close',
                'high': 'high',
                '最高': 'high',
                'low': 'low',
                '最低': 'low',
                'volume': 'volume',
                '成交量': 'volume',
                'vol': 'volume'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df_minute.columns:
                    df_minute.rename(columns={old_col: new_col}, inplace=True)
            
            # 确保必要的列存在
            required_cols = ['datetime', 'open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df_minute.columns:
                    print(f"警告: 缺少列 {col}")
                    if col == 'open':
                        df_minute[col] = df_minute['close'] * 0.999
                    elif col == 'high':
                        df_minute[col] = df_minute['close'] * 1.01
                    elif col == 'low':
                        df_minute[col] = df_minute['close'] * 0.99
                    elif col == 'volume':
                        df_minute[col] = 1000000
            
            # 设置索引
            df_minute.set_index('datetime', inplace=True)
            
            # 按时间排序
            df_minute.sort_index(inplace=True)
            
            print(f"处理后的数据形状: {df_minute.shape}")
            print(f"时间范围: {df_minute.index.min()} 到 {df_minute.index.max()}")
            print(f"数据预览:\n{df_minute.head()}")
            
            # 创建Backtrader数据源（分钟级）
            data = bt.feeds.PandasData(
                dataname=df_minute,
                open='open',
                high='high',
                low='low',
                close='close',
                volume='volume',
                openinterest=-1,
                timeframe=bt.TimeFrame.Minutes,
                compression=1
            )
            
            cerebro.adddata(data)
            print("分钟级数据源创建成功")
            
        except Exception as e:
            print(f"分钟级数据获取失败: {e}")
            print("尝试使用其他数据源...")
            
            # 尝试使用tushare获取分钟级数据
            try:
                import tushare as ts
                print("尝试使用tushare获取分钟级数据...")
                
                # 设置tushare token（如果有）
                # ts.set_token('your_token_here')
                pro = ts.pro_api()
                
                # 获取分钟级数据
                df_minute = pro.fut_minute(ts_code="159206.SZ", start_date="20251201", end_date="20260312")
                print("tushare数据获取成功，共", len(df_minute), "条记录")
                
                # 处理数据
                df_minute['datetime'] = pd.to_datetime(df_minute['trade_time'])
                df_minute.rename(columns={
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'vol': 'volume'
                }, inplace=True)
                
                df_minute.set_index('datetime', inplace=True)
                df_minute.sort_index(inplace=True)
                
                # 创建数据源
                data = bt.feeds.PandasData(
                    dataname=df_minute,
                    open='open',
                    high='high',
                    low='low',
                    close='close',
                    volume='volume',
                    openinterest=-1,
                    timeframe=bt.TimeFrame.Minutes,
                    compression=1
                )
                
                cerebro.adddata(data)
                print("tushare分钟级数据源创建成功")
                
            except Exception as e2:
                print(f"tushare数据获取失败: {e2}")
                print("使用日级数据 + 真实分钟级模拟...")
                
                # 使用日级数据作为基础，生成更真实的分钟级数据
                # 尝试获取日级数据
                try:
                    df_daily = ak.fund_etf_em(symbol="159206", period="daily", 
                                              start_date="20251201", end_date="20260312",
                                              adjust="qfq")
                    
                    print("日级数据获取成功，共", len(df_daily), "条记录")
                    
                    # 处理日级数据
                    if '日期' in df_daily.columns:
                        df_daily['date'] = pd.to_datetime(df_daily['日期'])
                    df_daily.set_index('date', inplace=True)
                    
                    df_daily.rename(columns={
                        '开盘': 'open',
                        '收盘': 'close',
                        '最高': 'high',
                        '最低': 'low',
                        '成交量': 'volume'
                    }, inplace=True)
                    
                    # 生成更真实的分钟级数据
                    minute_data = []
                    
                    for date, row in df_daily.iterrows():
                        # 确保是交易日
                        if date.weekday() < 5:  # 周一到周五
                            # 生成240个分钟数据点
                            for minute in range(240):
                                # 计算时间
                                hour = 9 + (minute + 30) // 60
                                minute_of_hour = (minute + 30) % 60
                                
                                # 确保在交易时间内
                                if (hour == 9 and minute_of_hour >= 30) or \
                                   (10 <= hour <= 11) or \
                                   (hour == 11 and minute_of_hour <= 30) or \
                                   (hour == 13 and minute_of_hour >= 30) or \
                                   (14 <= hour <= 14) or \
                                   (hour == 15 and minute_of_hour == 0):
                                    
                                    # 基于真实的日数据生成分钟级价格
                                    # 使用更真实的价格路径
                                    progress = minute / 240.0
                                    
                                    # 生成更真实的价格波动
                                    # 开盘后价格波动较大，中午和收盘前也有波动
                                    volatility = 0.0008
                                    if minute < 30:  # 开盘前30分钟
                                        volatility = 0.0015
                                    elif minute > 210:  # 收盘前30分钟
                                        volatility = 0.0012
                                    
                                    # 计算价格趋势
                                    trend = (row['close'] - row['open']) * progress
                                    random_factor = np.random.normal(0, volatility)
                                    
                                    # 计算当前价格
                                    if minute == 0:
                                        current_price = row['open']
                                    else:
                                        prev_price = minute_data[-1]['close']
                                        price_change = trend - (row['close'] - row['open']) * ((minute - 1) / 240.0)
                                        current_price = prev_price + price_change + random_factor
                                    
                                    # 确保价格在当日高低点之间
                                    current_price = max(row['low'], min(row['high'], current_price))
                                    
                                    # 计算成交量（根据时间分布）
                                    volume_distribution = 1.0
                                    if minute < 30:  # 开盘
                                        volume_distribution = 2.5
                                    elif minute < 120:  # 上午
                                        volume_distribution = 1.2
                                    elif minute < 180:  # 下午开盘
                                        volume_distribution = 1.5
                                    else:  # 收盘
                                        volume_distribution = 2.0
                                    
                                    minute_volume = (row['volume'] / 240) * volume_distribution * np.random.uniform(0.8, 1.2)
                                    
                                    # 创建分钟数据
                                    minute_data.append({
                                        'datetime': date + pd.Timedelta(hours=hour, minutes=minute_of_hour),
                                        'open': current_price,
                                        'high': max(current_price, current_price * (1 + np.random.normal(0, 0.0005))),
                                        'low': min(current_price, current_price * (1 - np.random.normal(0, 0.0005))),
                                        'close': current_price,
                                        'volume': minute_volume
                                    })
                    
                    # 创建分钟级DataFrame
                    df_minute = pd.DataFrame(minute_data)
                    df_minute.set_index('datetime', inplace=True)
                    df_minute.sort_index(inplace=True)
                    
                    print("生成真实分钟级模拟数据成功，共", len(df_minute), "条记录")
                    
                    # 创建数据源
                    data = bt.feeds.PandasData(
                        dataname=df_minute,
                        open='open',
                        high='high',
                        low='low',
                        close='close',
                        volume='volume',
                        openinterest=-1,
                        timeframe=bt.TimeFrame.Minutes,
                        compression=1
                    )
                    
                    cerebro.adddata(data)
                    print("分钟级模拟数据源创建成功")
                    
                except Exception as e3:
                    print(f"日级数据获取失败: {e3}")
                    print("使用纯模拟分钟级数据...")
                    
                    # 创建纯模拟分钟级数据
                    dates = pd.date_range('2025-12-01', '2026-03-12')
                    minute_data = []
                    base_price = 1.5
                    
                    for date in dates:
                        if date.weekday() < 5:  # 周一到周五
                            # 生成当日高低开收
                            change = np.random.normal(0, 0.02)
                            close = base_price * (1 + change)
                            open_price = close * (1 - np.random.normal(0, 0.01))
                            high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
                            low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
                            volume = np.random.normal(100000000, 50000000)
                            
                            # 生成分钟数据
                            for minute in range(240):
                                hour = 9 + (minute + 30) // 60
                                minute_of_hour = (minute + 30) % 60
                                
                                progress = minute / 240.0
                                volatility = 0.0008
                                if minute < 30:
                                    volatility = 0.0015
                                elif minute > 210:
                                    volatility = 0.0012
                                
                                trend = (close - open_price) * progress
                                random_factor = np.random.normal(0, volatility)
                                
                                if minute == 0:
                                    current_price = open_price
                                else:
                                    prev_price = minute_data[-1]['close']
                                    price_change = trend - (close - open_price) * ((minute - 1) / 240.0)
                                    current_price = prev_price + price_change + random_factor
                                
                                current_price = max(low, min(high, current_price))
                                
                                volume_distribution = 1.0
                                if minute < 30:
                                    volume_distribution = 2.5
                                elif minute < 120:
                                    volume_distribution = 1.2
                                elif minute < 180:
                                    volume_distribution = 1.5
                                else:
                                    volume_distribution = 2.0
                                
                                minute_volume = (volume / 240) * volume_distribution * np.random.uniform(0.8, 1.2)
                                
                                minute_data.append({
                                    'datetime': date + pd.Timedelta(hours=hour, minutes=minute_of_hour),
                                    'open': current_price,
                                    'high': max(current_price, current_price * (1 + np.random.normal(0, 0.0005))),
                                    'low': min(current_price, current_price * (1 - np.random.normal(0, 0.0005))),
                                    'close': current_price,
                                    'volume': minute_volume
                                })
                            
                            base_price = close
                    
                    df_minute = pd.DataFrame(minute_data)
                    df_minute.set_index('datetime', inplace=True)
                    df_minute.sort_index(inplace=True)
                    
                    print("纯模拟分钟级数据创建成功，共", len(df_minute), "条记录")
                    
                    data = bt.feeds.PandasData(
                        dataname=df_minute,
                        open='open',
                        high='high',
                        low='low',
                        close='close',
                        volume='volume',
                        openinterest=-1,
                        timeframe=bt.TimeFrame.Minutes,
                        compression=1
                    )
                    
                    cerebro.adddata(data)
                    print("纯模拟分钟级数据源创建成功")
        
    except Exception as e:
        print(f"数据获取失败: {e}")
        print("使用最后备用方案 - 纯模拟分钟级数据...")
        
        # 创建纯模拟分钟级数据
        dates = pd.date_range('2025-12-01', '2026-03-12')
        minute_data = []
        base_price = 1.5
        
        for date in dates:
            if date.weekday() < 5:  # 周一到周五
                # 生成当日高低开收
                change = np.random.normal(0, 0.02)
                close = base_price * (1 + change)
                open_price = close * (1 - np.random.normal(0, 0.01))
                high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
                low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
                volume = np.random.normal(100000000, 50000000)
                
                # 生成分钟数据
                for minute in range(240):
                    hour = 9 + (minute + 30) // 60
                    minute_of_hour = (minute + 30) % 60
                    
                    progress = minute / 240.0
                    volatility = 0.0008
                    if minute < 30:
                        volatility = 0.0015
                    elif minute > 210:
                        volatility = 0.0012
                    
                    trend = (close - open_price) * progress
                    random_factor = np.random.normal(0, volatility)
                    
                    if minute == 0:
                        current_price = open_price
                    else:
                        prev_price = minute_data[-1]['close']
                        price_change = trend - (close - open_price) * ((minute - 1) / 240.0)
                        current_price = prev_price + price_change + random_factor
                    
                    current_price = max(low, min(high, current_price))
                    
                    volume_distribution = 1.0
                    if minute < 30:
                        volume_distribution = 2.5
                    elif minute < 120:
                        volume_distribution = 1.2
                    elif minute < 180:
                        volume_distribution = 1.5
                    else:
                        volume_distribution = 2.0
                    
                    minute_volume = (volume / 240) * volume_distribution * np.random.uniform(0.8, 1.2)
                    
                    minute_data.append({
                        'datetime': date + pd.Timedelta(hours=hour, minutes=minute_of_hour),
                        'open': current_price,
                        'high': max(current_price, current_price * (1 + np.random.normal(0, 0.0005))),
                        'low': min(current_price, current_price * (1 - np.random.normal(0, 0.0005))),
                        'close': current_price,
                        'volume': minute_volume
                    })
                
                base_price = close
        
        df_minute = pd.DataFrame(minute_data)
        df_minute.set_index('datetime', inplace=True)
        df_minute.sort_index(inplace=True)
        
        print("备用模拟分钟级数据创建成功，共", len(df_minute), "条记录")
        
        data = bt.feeds.PandasData(
            dataname=df_minute,
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1,
            timeframe=bt.TimeFrame.Minutes,
            compression=1
        )
        
        cerebro.adddata(data)
    
    # 添加策略
    cerebro.addstrategy(TrendFollowingStrategy)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # 运行回测
    print('\n' + '='*60)
    print('开始回测')
    print(f'初始资金: {cerebro.broker.getvalue():.2f}')
    print('='*60)
    
    results = cerebro.run()
    strat = results[0]
    
    # 输出结果
    print('\n' + '='*60)
    print('回测结果')
    print('='*60)
    print(f'最终市值: {cerebro.broker.getvalue():.2f}')
    print(f'总收益率: {(cerebro.broker.getvalue()/100000 - 1)*100:.2f}%')
    
    # 获取分析结果
    sharpe = strat.analyzers.sharpe.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    returns = strat.analyzers.returns.get_analysis()
    trades = strat.analyzers.trades.get_analysis()
    
    print(f'夏普比率: {sharpe.get("sharperatio", "N/A")}')
    print(f'最大回撤: {drawdown.get("max", {}).get("drawdown", "N/A")}%')
    print(f'年化收益率: {returns.get("rnorm100", "N/A")}%')
    
    if trades.get("total", {}).get("total", 0) > 0:
        print(f'交易次数: {trades["total"]["total"]}')
        print(f'盈利次数: {trades.get("won", {}).get("total", 0)}')
        print(f'亏损次数: {trades.get("lost", {}).get("total", 0)}')
    
    # 输出详细交易记录
    if hasattr(strat, 'trade_history') and strat.trade_history:
        print('\n' + '='*60)
        print('详细交易记录')
        print('='*60)
        print(f"{'时间':<20} {'类型':<8} {'价格':<10} {'数量':<10} {'金额':<15}")
        print('-'*60)
        total_buy_cost = 0
        total_sell_value = 0
        for trade in strat.trade_history:
            dt_str = trade['datetime'].strftime('%Y-%m-%d %H:%M:%S')
            trade_type = trade['type']
            price = trade['price']
            size = trade['size']
            if trade_type == 'buy':
                amount = trade['cost']
                total_buy_cost += amount
                print(f"{dt_str:<20} {trade_type:<8} {price:<10.2f} {size:<10} {amount:<15.2f}")
            else:
                amount = trade['value']
                total_sell_value += amount
                print(f"{dt_str:<20} {trade_type:<8} {price:<10.2f} {size:<10} {amount:<15.2f}")
        print('-'*60)
        print(f"{'合计':<20} {'买入':<8} {'':<10} {'':<10} {total_buy_cost:<15.2f}")
        print(f"{'合计':<20} {'卖出':<8} {'':<10} {'':<10} {total_sell_value:<15.2f}")
        print(f"{'净盈利':<20} {'':<8} {'':<10} {'':<10} {(total_sell_value - total_buy_cost):<15.2f}")
    
    print('='*60)
    
    # 绘制图表
    try:
        cerebro.plot(style='candlestick', barup='red', bardown='green')
    except:
        pass


if __name__ == '__main__':
    run_backtest()
