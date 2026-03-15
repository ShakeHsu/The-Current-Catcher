import datetime

def initialize(context):
    """初始化策略"""
    # 策略参数
    g.security = "159206.SZ"  # 卫星ETF
    g.realized_pnl = 0  # 累计落袋盈亏（全局变量）
    g.pending_orders = {}  # 待处理的订单 {order_id: {'type': 't_sell', 'shares': 计划卖出量}}
    
    # 股票相关变量
    g.stock_info = {
        g.security: {
            'total_cost': 0,  # 累计买入成本
            'avg_cost': 0,  # 平均成本
            'last_buy_date': None,  # 上次买入日期
            'last_buy_price': None,  # 上次买入价格
            'day_low': None,  # 当日最低价
            'day_high': 0,  # 当日最高价
            'today_buy_amount': 0,  # 当日买入量
            't_done_today': False,  # 当日是否已执行做T
            'last_date': None,  # 上次处理的日期
            'daily_volume': 0,  # 当日累计成交量
        }
    }
    
    # 做T参数
    g.buy_amount = 10000  # 每次买入目标金额（元）
    g.max_cost = 200000  # 单只股票持仓成本上限（元）
    g.t_profit_threshold = 0.03  # 做T收益率阈值：3%
    g.t_pullback_threshold = 0.01  # 做T回落阈值：1%
    
    # 买入条件参数
    g.rebound_threshold = 0.0003  # 反弹阈值：0.03%
    g.m_days = 5  # 前m天
    g.n_days = 3  # 前m天中需要满足条件的天数
    g.a_days = 5  # 前a天
    g.b_days = 3  # 前a天中需要满足条件的天数
    
    # 打印初始化信息
    print(f"[{datetime.datetime.now()}] 做T策略初始化完成，股票: {g.security}")

def before_trading_start(context, data):
    """每个交易日开始前执行"""
    # 检查是否有昨天没卖完的股票
    if g.pending_orders:
        print(f"{datetime.datetime.now()} - 检查昨日未完成的订单: {list(g.pending_orders.keys())}")
        for order_id, order_info in list(g.pending_orders.items()):
            order = get_order(order_id)
            if order:
                if order.filled < order.amount:
                    print(f"{datetime.datetime.now()} - 未完全成交: 已卖{order.filled}股，剩余{order.amount - order.filled}股")
                    remaining_shares = order.amount - order.filled
                    new_order_id = order(g.security, -remaining_shares)
                    if new_order_id:
                        g.pending_orders[new_order_id] = order_info
                        print(f"{datetime.datetime.now()} - 继续处理昨日未完成卖出，新订单ID: {new_order_id}")
                else:
                    print(f"{datetime.datetime.now()} - 订单已全部成交，移除订单ID: {order_id}")
                    del g.pending_orders[order_id]
            else:
                print(f"{datetime.datetime.now()} - 订单不存在，移除订单ID: {order_id}")
                del g.pending_orders[order_id]

def handle_data(context, data):
    """核心交易逻辑"""
    security = g.security
    stock_info = g.stock_info[security]
    
    # 获取当前时间
    current_time = context.current_dt
    current_date = current_time.date()
    
    # 获取当前价格
    if not hasattr(data[security], 'close'):
        print(f"{current_time} - 无法获取股票价格")
        return
    current_price = data[security].close
    
    # 检查待处理的订单
    if g.pending_orders:
        for order_id, order_info in list(g.pending_orders.items()):
            order = get_order(order_id)
            if order:
                if order.filled < order.amount:
                    print(f"{current_time} - 订单未完全成交: 订单ID={order_id}, 已成交={order.filled}股, 剩余={order.amount - order.filled}股")
                else:
                    actual_sell_shares = order.filled
                    if actual_sell_shares > 0:
                        sell_amount = order_info['price'] * actual_sell_shares
                        realized_pnl = sell_amount - order_info['avg_cost'] * actual_sell_shares
                        g.realized_pnl += realized_pnl
                        stock_info['total_cost'] -= order_info['avg_cost'] * actual_sell_shares
                        print(f"{current_time} - 做T卖出确认：实际卖出量={actual_sell_shares}, 卖出金额={sell_amount:.2f}, 落袋盈亏={realized_pnl:.2f}, 累计落袋盈亏={g.realized_pnl:.2f}")
                    del g.pending_orders[order_id]
            else:
                del g.pending_orders[order_id]
    
    # 监控当日最低价和最高价
    if hasattr(data[security], 'low'):
        current_low = data[security].low
    else:
        current_low = current_price
    
    if hasattr(data[security], 'high'):
        current_high = data[security].high
    else:
        current_high = current_price
    
    # 检查是否是新的一天
    if stock_info['last_date'] != current_date:
        stock_info['day_low'] = current_low
        stock_info['day_high'] = current_high
        stock_info['today_buy_amount'] = 0
        stock_info['t_done_today'] = False
        stock_info['daily_volume'] = 0
        stock_info['last_date'] = current_date
        print(f"{current_time} - 新的一天，初始化当日最低价: {current_low}, 最高价: {current_high}")
    else:
        if stock_info['day_low'] is None or current_low < stock_info['day_low']:
            stock_info['day_low'] = current_low
        if stock_info['day_high'] is None or current_high > stock_info['day_high']:
            stock_info['day_high'] = current_high
    
    day_low = stock_info['day_low']
    day_high = stock_info['day_high']
    
    # 获取成交量
    try:
        if hasattr(data[security], 'volume'):
            period_volume = data[security].volume
        elif hasattr(data[security], 'vol'):
            period_volume = data[security].vol
        else:
            print(f"{current_time} - 无法获取成交量")
            return
        stock_info['daily_volume'] += period_volume
    except Exception as e:
        print(f"{current_time} - 获取成交量失败: {e}")
        return
    
    # 获取历史数据
    try:
        end_date = current_date.strftime('%Y%m%d')
        start_date = (current_date - datetime.timedelta(days=30)).strftime('%Y%m%d')
        hist = get_price(security, start_date=start_date, end_date=end_date, frequency='1d', fields=['close', 'open'], fq='pre')
        if hist is None or len(hist) < 1:
            print(f"{current_time} - 历史数据不足")
            return
    except Exception as e:
        print(f"{current_time} - 获取历史数据失败: {e}")
        return
    
    # 买入逻辑
    position = context.portfolio.positions.get(security, None)
    position_amount = position.amount if position else 0
    
    # 检查今天是否已经买过
    can_buy = True
    if stock_info['last_buy_date'] == current_date:
        print(f"{current_time} - 今天已经买过，跳过买入")
        can_buy = False
    
    # 资金管理：总持仓成本不超过上限
    if stock_info['total_cost'] >= g.max_cost:
        print(f"{current_time} - 持仓成本已达上限，跳过买入")
        can_buy = False
    
    if can_buy:
        # 计算前m天的条件满足情况：收盘价-开盘价>0且收盘价-5日均线>0
        m_days = g.m_days
        n_days = g.n_days
        condition1_count = 0
        
        # 计算前a天的5日均线上升情况：5日均线-前1天的5日均线>0
        a_days = g.a_days
        b_days = g.b_days
        condition2_count = 0
        
        # 计算历史5日均线
        ma5_list = []
        if len(hist) >= max(m_days, a_days + 1):
            # 计算每天的5日均线
            for i in range(len(hist) - 4):
                ma5 = hist['close'][i:i+5].mean()
                ma5_list.append(ma5)
            
            # 检查前m天的条件1：收盘价-开盘价>0且收盘价-5日均线>0
            start_idx = max(4, len(hist) - m_days)  # 从第4天开始，因为前4天没有5日均线
            end_idx = len(hist)
            for i in range(start_idx, end_idx):
                # 计算对应的ma5索引：i-4
                ma5_idx = i - 4
                if ma5_idx >= 0 and ma5_idx < len(ma5_list):
                    close = hist['close'][i]
                    open_price = hist['open'][i]
                    ma5 = ma5_list[ma5_idx]
                    if (close - open_price > 0) and (close - ma5 > 0):
                        condition1_count += 1
            
            # 检查前a天的条件2：5日均线-前1天的5日均线>0
            if len(ma5_list) >= 2:  # 至少需要2个数据点来计算变化
                start_idx = max(0, len(ma5_list) - a_days - 1)
                end_idx = len(ma5_list) - 1
                for i in range(start_idx, end_idx):
                    if i + 1 < len(ma5_list):
                        if ma5_list[i+1] - ma5_list[i] > 0:
                            condition2_count += 1
        
        # 条件1：前m天中有n天满足收盘价>开盘价且收盘价>5日均线
        condition1 = condition1_count >= n_days
        
        # 条件2：前a天中有b天满足5日均线上升
        condition2 = condition2_count >= b_days
        
        # 条件3：当日价格低于昨日收盘价
        yesterday_close = hist['close'][-1]
        condition3 = current_price < yesterday_close
        
        # 条件4：反弹确认：当前最新价 >= 当日最低价 * (1 + g.rebound_threshold)
        rebound_confirm = current_price >= day_low * (1 + g.rebound_threshold)
        
        print(f"{current_time} - 买入条件检查:")
        print(f"{current_time} -   条件1: 前{m_days}天中有{n_days}天满足收盘价>开盘价且收盘价>5日均线 = {condition1} (满足天数: {condition1_count}/{m_days})")
        print(f"{current_time} -   条件2: 前{a_days}天中有{b_days}天满足5日均线上升 = {condition2} (满足天数: {condition2_count}/{a_days})")
        print(f"{current_time} -   条件3: 当日价格低于昨日收盘价 = {condition3}")
        print(f"{current_time} -   条件4: 反弹确认 = {rebound_confirm}")
        print(f"{current_time} - 价格数据: 当前价格={current_price:.2f}, 当日最低价={day_low:.2f}, 昨日收盘价={yesterday_close:.2f}, 反弹阈值={day_low * (1 + g.rebound_threshold):.2f}")
        
        if condition1 and condition2 and condition3 and rebound_confirm:
            # 计算买入股数：向上取整至100股整数倍
            if security.endswith('.SS') or security.endswith('.SZ'):
                buy_shares = (int(g.buy_amount / current_price) + 99) // 100 * 100
                if buy_shares < 100:
                    buy_shares = 100
            else:
                buy_shares = (int(g.buy_amount / current_price) + 99) // 100 * 100
                if buy_shares < 100:
                    buy_shares = 100
            
            # 执行买入
            try:
                print(f"{current_time} - 执行买入: {security}, 股数: {buy_shares}")
                order(security, buy_shares)
                # 更新累计成本
                stock_info['total_cost'] += buy_shares * current_price
                # 更新平均成本
                new_position_amount = position_amount + buy_shares
                if new_position_amount > 0:
                    stock_info['avg_cost'] = stock_info['total_cost'] / new_position_amount
                else:
                    stock_info['avg_cost'] = current_price
                # 更新买入信息
                stock_info['last_buy_date'] = current_date
                stock_info['last_buy_price'] = current_price
                stock_info['today_buy_amount'] += buy_shares
                print(f"{current_time} - 买入成功，累计成本: {stock_info['total_cost']:.2f}, 平均成本: {stock_info['avg_cost']:.2f}, 当日买入量: {stock_info['today_buy_amount']}")
            except Exception as e:
                print(f"{current_time} - 买入失败: {e}")
    
    # 做T逻辑
    if position and position.amount > 0 and not stock_info['t_done_today']:
        # 检查当日是否已买入
        if stock_info['last_buy_date'] == current_date and stock_info['today_buy_amount'] > 0:
            yesterday_close = hist['close'][-1]
            gain = (current_price / yesterday_close - 1)
            
            # 计算做T收益率
            if stock_info['avg_cost'] > 0:
                t_profit_rate = (current_price - stock_info['avg_cost']) / stock_info['avg_cost']
            else:
                t_profit_rate = 0
            
            # 计算回落幅度
            pullback = (day_high - current_price) / day_high if day_high > 0 else 0
            
            print(f"{current_time} - 做T数据：当前价格={current_price:.2f}, 持仓成本={stock_info['avg_cost']:.2f}, 做T收益率={t_profit_rate:.2%}, 当日最高价={day_high:.2f}, 回落={pullback:.2%}")
            
            # 条件1：做T收益率>3%且回落>1%
            if t_profit_rate > g.t_profit_threshold and pullback > g.t_pullback_threshold:
                print(f"{current_time} - 做T条件1触发：做T收益率>3%且回落>1%")
                # 卖出当日买入量，不超过可卖量
                sell_shares = min(position.amount, stock_info['today_buy_amount'])
                if sell_shares > 0:
                    print(f"{current_time} - 执行做T卖出：股数={sell_shares}, 当日买入量={stock_info['today_buy_amount']}, 可卖量={position.amount}")
                    # 提交卖出订单
                    order_id = order(security, -sell_shares)
                    if order_id:
                        g.pending_orders[order_id] = {
                            'type': 't_sell',
                            'shares': sell_shares,
                            'price': current_price,
                            'avg_cost': stock_info['avg_cost']
                        }
                        print(f"{current_time} - 做T卖出订单已提交，订单ID: {order_id}")
                    # 设置做T标记为True，当日不再执行
                    stock_info['t_done_today'] = True
            else:
                print(f"{current_time} - 做T条件1不满足：做T收益率={t_profit_rate:.2%} (>3%:{t_profit_rate > g.t_profit_threshold}), 回落={pullback:.2%} (>1%:{pullback > g.t_pullback_threshold})")
            
            # 条件2：14:55固定时间，直接卖出
            if current_time.hour == 14 and current_time.minute == 55 and not stock_info['t_done_today']:
                print(f"{current_time} - 做T条件2触发：14:55固定时间")
                # 卖出当日买入量，不超过可卖量
                sell_shares = min(position.amount, stock_info['today_buy_amount'])
                if sell_shares > 0:
                    print(f"{current_time} - 执行做T卖出：股数={sell_shares}, 当日买入量={stock_info['today_buy_amount']}, 可卖量={position.amount}")
                    # 提交卖出订单
                    order_id = order(security, -sell_shares)
                    if order_id:
                        g.pending_orders[order_id] = {
                            'type': 't_sell',
                            'shares': sell_shares,
                            'price': current_price,
                            'avg_cost': stock_info['avg_cost']
                        }
                        print(f"{current_time} - 做T卖出订单已提交，订单ID: {order_id}")
                    # 设置做T标记为True，当日不再执行
                    stock_info['t_done_today'] = True
        else:
            print(f"{current_time} - 做T检查跳过：当日未买入或买入量为0")
    
    # 收盘时计算并显示统计信息
    if current_time.hour == 15 and current_time.minute == 0:
        position = context.portfolio.positions.get(security, None)
        if position and position.amount > 0:
            total_value = position.amount * current_price
            position_cost = stock_info['avg_cost']
            total_cost = position_cost * position.amount
            profit_loss = total_value - total_cost
            profit_loss_ratio = (profit_loss / total_cost) * 100 if total_cost > 0 else 0

            print(f"{current_time} - 收盘统计:")
            print(f"{current_time} -   股票: {security}")
            print(f"{current_time} -   持仓量: {position.amount}")
            print(f"{current_time} -   当前价格: {current_price:.2f}")
            print(f"{current_time} -   持仓平均成本: {position_cost:.2f}")
            print(f"{current_time} -   总市值: {total_value:.2f}")
            print(f"{current_time} -   持仓成本: {total_cost:.2f}")
            print(f"{current_time} -   盈亏: {profit_loss:.2f}")
            print(f"{current_time} -   盈亏比例: {profit_loss_ratio:.2f}%")
            print(f"{current_time} -   累计落袋盈亏: {g.realized_pnl:.2f}")
        else:
            print(f"{current_time} - 收盘统计:")
            print(f"{current_time} -   股票: {security}")
            print(f"{current_time} -   持仓量: 0")
            print(f"{current_time} -   当前价格: {current_price:.2f}")
            print(f"{current_time} -   累计落袋盈亏: {g.realized_pnl:.2f}")
