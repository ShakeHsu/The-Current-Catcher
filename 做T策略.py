import datetime

def calculate_commission(amount):
    """计算佣金"""
    commission = amount * 0.00012
    return max(commission, 5)  # 每笔最低5元

def calculate_stamp_tax(amount, security):
    """计算印花税"""
    if security.endswith('.SS') or security.endswith('.SZ'):
        # ETF代码特征：51、56、159、50、58开头
        etf_prefixes = ['51', '56', '159', '50', '58']
        is_etf = any(security.startswith(prefix) for prefix in etf_prefixes)
        if is_etf:
            return 0  # ETF不收印花税
        else:
            return amount * 0.0005  # 普通股票卖出时收取
    else:
        return 0  # 其他情况不收印花税

def initialize(context):
    """初始化策略"""
    # 策略参数
    g.security = "159206.SZ"  # 卫星ETF
    g.realized_pnl = 0  # 累计落袋盈亏（全局变量）
    g.total_t_profit = 0  # 累计T操作净利润
    
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
            'today_buy_cost': 0,  # 当日买入成本（含佣金）
            't_done_today': False,  # 当日是否已执行做T
            'buy_count': 0,  # 总买入次数
            'last_date': None,  # 上次处理的日期
            'daily_volume': 0,  # 当日累计成交量
        }
    }
    
    # 做T参数
    g.buy_value = 10000  # 每次买入目标金额（元）
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
        stock_info['today_buy_cost'] = 0
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
    
    # 检查是否是第1次买入
    can_buy = True
    if stock_info['last_buy_date'] == current_date:
        print(f"{current_time} - 今天已经买入过，跳过")
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
                buy_amount = (int(g.buy_value / current_price) + 99) // 100 * 100
                if buy_amount < 100:
                    buy_amount = 100
            else:
                buy_amount = (int(g.buy_value / current_price) + 99) // 100 * 100
                if buy_amount < 100:
                    buy_amount = 100
            
            # 执行买入
            try:
                print(f"{current_time} - 执行买入: {security}, 数量: {buy_amount}")
                order(security, buy_amount)
                
                # 使用当前价格和买入数量
                execution_price = current_price
                filled_amount = buy_amount
                
                # 计算实际买入成本（含佣金）
                buy_value = filled_amount * execution_price
                buy_commission = calculate_commission(buy_value)
                actual_buy_cost = buy_value + buy_commission
                
                # 更新累计成本
                stock_info['total_cost'] += actual_buy_cost
                # 更新当日买入成本
                stock_info['today_buy_cost'] += actual_buy_cost
                # 更新平均成本
                new_position_amount = position_amount + filled_amount
                if new_position_amount > 0:
                    stock_info['avg_cost'] = stock_info['total_cost'] / new_position_amount
                # 更新买入信息
                stock_info['last_buy_date'] = current_date
                stock_info['last_buy_price'] = execution_price
                stock_info['today_buy_amount'] += filled_amount
                stock_info['buy_count'] += 1
                print(f"{current_time} - 买入成功，成交价格={execution_price:.2f}, 成交股数={filled_amount}, 买入金额={buy_value:.2f}, 佣金={buy_commission:.2f}, 实际买入成本={actual_buy_cost:.2f}, 累计成本: {stock_info['total_cost']:.2f}, 平均成本: {stock_info['avg_cost']:.2f}, 当日买入量: {stock_info['today_buy_amount']}, 当日买入次数: {stock_info['buy_count']}")
            except Exception as e:
                print(f"{current_time} - 买入失败: {e}")
    
    # 做T逻辑
    if position and position.amount > 0 and not stock_info['t_done_today']:
        # 检查当日是否已买入且不是第1次买入
        if stock_info['last_buy_date'] == current_date and stock_info['today_buy_amount'] > 0 and stock_info['buy_count'] > 1:
            # 计算做T毛利=（最新价格-当日买入价格）/当日买入价格
            t_gross_profit_rate = (current_price - stock_info['last_buy_price']) / stock_info['last_buy_price']
            
            # 计算回落幅度
            pullback = (day_high - current_price) / day_high if day_high > 0 else 0
            
            print(f"{current_time} - 做T数据：当前价格={current_price:.2f}, 当日买入价格={stock_info['last_buy_price']:.2f}, 做T毛利={t_gross_profit_rate:.2%}, 当日最高价={day_high:.2f}, 回落={pullback:.2%}")
            
            # 条件1：做T毛利>3%且回落>1%
            if t_gross_profit_rate > g.t_profit_threshold and pullback > g.t_pullback_threshold:
                print(f"{current_time} - 做T条件1触发：做T收益率>3%且回落>1%")
                # 卖出当日买入量
                sell_amount = stock_info['today_buy_amount']
                if sell_amount > 0:
                    # 提交卖出订单
                    order(security, -sell_amount)
                    
                    # 使用当前价格和卖出数量
                    execution_price = current_price
                    filled_amount = sell_amount
                    
                    print(f"{current_time} - 执行做T卖出：实际卖出数量={filled_amount}, 实际卖出价格={execution_price:.2f}")
                    
                    # 计算实际卖出所得（扣除佣金和印花税）
                    sell_value = filled_amount * execution_price
                    sell_commission = calculate_commission(sell_value)
                    stamp_tax = calculate_stamp_tax(sell_value, security)
                    actual_sell_income = sell_value - sell_commission - stamp_tax
                    
                    # 计算T操作净利润和收益率
                    t_net_profit = actual_sell_income - stock_info['today_buy_cost']
                    t_profit_rate_actual = t_net_profit / stock_info['today_buy_cost'] if stock_info['today_buy_cost'] > 0 else 0
                    
                    # 更新累计T操作净利润
                    g.total_t_profit += t_net_profit
                    
                    # 更新累计成本
                    stock_info['total_cost'] -= stock_info['today_buy_cost']
                    
                    print(f"{current_time} - 做T卖出成功：成交价格={execution_price:.2f}, 成交股数={filled_amount}, 卖出金额={sell_value:.2f}, 佣金={sell_commission:.2f}, 印花税={stamp_tax:.2f}, 实际卖出所得={actual_sell_income:.2f}")
                    print(f"{current_time} - T操作净利润={t_net_profit:.2f}, T操作收益率={t_profit_rate_actual:.2%}, 累计T操作净利润={g.total_t_profit:.2f}")
                    print(f"{current_time} - 当日买入成本={stock_info['today_buy_cost']:.2f}, 累计成本={stock_info['total_cost']:.2f}")
                    
                    # 重置当日买入信息
                    stock_info['today_buy_amount'] = 0
                    stock_info['today_buy_cost'] = 0
                    
                    # 设置做T标记为True，当日不再执行
                    stock_info['t_done_today'] = True
            else:
                print(f"{current_time} - 做T条件1不满足：做T收益率={t_profit_rate:.2%} (>3%:{t_profit_rate > g.t_profit_threshold}), 回落={pullback:.2%} (>1%:{pullback > g.t_pullback_threshold})")
            
            # 条件2：14:55固定时间，直接卖出
            if current_time.hour == 14 and current_time.minute == 55 and not stock_info['t_done_today'] and stock_info['buy_count'] > 1:
                print(f"{current_time} - 做T条件2触发：14:55固定时间")
                # 卖出当日买入量
                sell_amount = stock_info['today_buy_amount']
                if sell_amount > 0:
                    # 提交卖出订单
                    order(security, -sell_amount)
                    
                    # 使用当前价格和卖出数量
                    execution_price = current_price
                    filled_amount = sell_amount
                    
                    print(f"{current_time} - 执行做T卖出：实际卖出数量={filled_amount}, 实际卖出价格={execution_price:.2f}")
                    
                    # 计算实际卖出所得（扣除佣金和印花税）
                    sell_value = filled_amount * execution_price
                    sell_commission = calculate_commission(sell_value)
                    stamp_tax = calculate_stamp_tax(sell_value, security)
                    actual_sell_income = sell_value - sell_commission - stamp_tax
                    
                    # 计算T操作净利润和收益率
                    t_net_profit = actual_sell_income - stock_info['today_buy_cost']
                    t_profit_rate_actual = t_net_profit / stock_info['today_buy_cost'] if stock_info['today_buy_cost'] > 0 else 0
                    
                    # 更新累计T操作净利润
                    g.total_t_profit += t_net_profit
                    
                    # 更新累计成本
                    stock_info['total_cost'] -= stock_info['today_buy_cost']
                    
                    print(f"{current_time} - 做T卖出成功：成交价格={execution_price:.2f}, 成交股数={filled_amount}, 卖出金额={sell_value:.2f}, 佣金={sell_commission:.2f}, 印花税={stamp_tax:.2f}, 实际卖出所得={actual_sell_income:.2f}")
                    print(f"{current_time} - T操作净利润={t_net_profit:.2f}, T操作收益率={t_profit_rate_actual:.2%}, 累计T操作净利润={g.total_t_profit:.2f}")
                    print(f"{current_time} - 当日买入成本={stock_info['today_buy_cost']:.2f}, 累计成本={stock_info['total_cost']:.2f}")
                    
                    # 重置当日买入信息
                    stock_info['today_buy_amount'] = 0
                    stock_info['today_buy_cost'] = 0
                    
                    # 设置做T标记为True，当日不再执行
                    stock_info['t_done_today'] = True
        else:
            print(f"{current_time} - 做T检查跳过：当日未买入或买入量为0")
    
    # 收盘时计算并显示统计信息
    if current_time.hour == 15 and current_time.minute == 0:
        position = context.portfolio.positions.get(security, None)
        if position and position.amount > 0:
            total_value = position.amount * current_price
            profit_loss = total_value - stock_info['total_cost']
            profit_loss_ratio = (profit_loss / stock_info['total_cost']) * 100 if stock_info['total_cost'] > 0 else 0

            print(f"{current_time} - 收盘统计:")
            print(f"{current_time} -   股票: {security}")
            print(f"{current_time} -   持仓量: {position.amount}")  
            print(f"{current_time} -   当前价格: {current_price:.2f}")
            print(f"{current_time} -   持仓平均成本: {stock_info['avg_cost']:.2f}")
            print(f"{current_time} -   总市值: {total_value:.2f}")
            print(f"{current_time} -   持仓成本: {stock_info['total_cost']:.2f}")
            print(f"{current_time} -   盈亏: {profit_loss:.2f}")
            print(f"{current_time} -   盈亏比例: {profit_loss_ratio:.2f}%")
            print(f"{current_time} -   累计T操作净利润: {g.total_t_profit:.2f}")
        else:
            print(f"{current_time} - 收盘统计:")
            print(f"{current_time} -   股票: {security}")
            print(f"{current_time} -   持仓量: 0")
            print(f"{current_time} -   当前价格: {current_price:.2f}")
            print(f"{current_time} -   累计T操作净利润: {g.total_t_profit:.2f}")
