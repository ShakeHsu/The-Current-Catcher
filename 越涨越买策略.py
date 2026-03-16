import datetime

# 计算佣金
def calculate_commission(amount):
    """计算佣金"""
    commission = amount * 0.00012
    return max(commission, 5)  # 每笔最低5元

# 计算印花税
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
    g.pending_orders = {}  # 待处理的订单
    
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
            'last_date': None,  # 上次处理的日期
            'daily_volume': 0,  # 当日累计成交量
            'volume_values': [],  # 存储成交量
        }
    }
    
    # 策略参数
    g.buy_value = 10000  # 每次买入目标金额（元）
    g.max_cost = 200000  # 单只股票持仓成本上限（元）
    g.volume_days_short = 3  # 短期均量天数
    g.volume_days_long = 20  # 长期均量天数
    g.volume_ratio_threshold = 1.0  # 成交量过滤阈值
    g.ma5_ratio_threshold = 0.02  # 最新价/5日均线阈值
    
    # 买入条件参数
    g.rebound_threshold = 0.0003  # 反弹阈值：0.03%
    
    # 打印初始化信息
    print(f"[{datetime.datetime.now()}] 越涨越买策略初始化完成，股票: {g.security}")

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
        stock_info['volume_values'].append(period_volume)
        if len(stock_info['volume_values']) > 60:
            stock_info['volume_values'] = stock_info['volume_values'][-60:]
    except Exception as e:
        print(f"{current_time} - 获取成交量失败: {e}")
        return
    
    # 获取历史数据
    try:
        end_date = current_date.strftime('%Y%m%d')
        start_date = (current_date - datetime.timedelta(days=60)).strftime('%Y%m%d')
        hist = get_price(security, start_date=start_date, end_date=end_date, frequency='1d', fields=['close', 'volume'], fq='pre')
        if hist is None or len(hist) < max(g.volume_days_long, 5):
            print(f"{current_time} - 历史数据不足")
            return
    except Exception as e:
        print(f"{current_time} - 获取历史数据失败: {e}")
        return
    
    # 计算5日均线
    ma5 = hist['close'][-5:].mean()
    
    # 计算前3日均量和前20日均量
    avg_3d_volume = hist['volume'][-3:].mean()
    avg_20d_volume = hist['volume'][-20:].mean()
    volume_ratio = avg_3d_volume / avg_20d_volume if avg_20d_volume > 0 else 0
    
    # 买入逻辑
    position = context.portfolio.positions.get(security, None)
    position_amount = position.amount if position else 0
    
    # 检查今天是否已经买入
    can_buy = True
    if stock_info['last_buy_date'] == current_date:
        print(f"{current_time} - 今天已经买入过，跳过")
        can_buy = False
    
    # 资金管理：总持仓成本不超过上限
    if stock_info['total_cost'] >= g.max_cost:
        print(f"{current_time} - 持仓成本已达上限，跳过买入")
        can_buy = False
    
    # 盘中买入条件
    if can_buy and current_time.hour < 14:
        print(f"{current_time} - 盘中买入检查:")
        print(f"{current_time} -   成交量过滤: 前3日均量/前20日均量 = {volume_ratio:.2f}")
        
        # 成交量过滤
        if volume_ratio >= g.volume_ratio_threshold:
            # 计算买入股数：向上取整至100股整数倍
            buy_amount = (int(g.buy_value / current_price) + 99) // 100 * 100
            if buy_amount < 100:
                buy_amount = 100
            
            # 执行买入
            try:
                print(f"{current_time} - 执行盘中买入: {security}, 数量: {buy_amount}")
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
                print(f"{current_time} - 买入成功，成交价格={execution_price:.2f}, 成交股数={filled_amount}, 买入金额={buy_value:.2f}, 佣金={buy_commission:.2f}, 实际买入成本={actual_buy_cost:.2f}, 累计成本: {stock_info['total_cost']:.2f}, 平均成本: {stock_info['avg_cost']:.2f}, 当日买入量: {stock_info['today_buy_amount']}")
            except Exception as e:
                print(f"{current_time} - 买入失败: {e}")
        else:
            print(f"{current_time} - 成交量过滤不满足，跳过买入")
    
    # 尾盘14:55买入条件
    elif can_buy and current_time.hour == 14 and current_time.minute == 55:
        print(f"{current_time} - 尾盘买入检查:")
        print(f"{current_time} -   成交量过滤: 前3日均量/前20日均量 = {volume_ratio:.2f}")
        print(f"{current_time} -   最新价/5日均线 = {current_price/ma5:.2f} (<2%: {current_price/ma5 < 1.02})")
        
        # 成交量过滤和价格/5日均线过滤
        if volume_ratio >= g.volume_ratio_threshold and current_price / ma5 < 1.02:
            # 计算买入股数：向上取整至100股整数倍
            buy_amount = (int(g.buy_value / current_price) + 99) // 100 * 100
            if buy_amount < 100:
                buy_amount = 100
            
            # 执行买入
            try:
                print(f"{current_time} - 执行尾盘买入: {security}, 数量: {buy_amount}")
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
                print(f"{current_time} - 买入成功，成交价格={execution_price:.2f}, 成交股数={filled_amount}, 买入金额={buy_value:.2f}, 佣金={buy_commission:.2f}, 实际买入成本={actual_buy_cost:.2f}, 累计成本: {stock_info['total_cost']:.2f}, 平均成本: {stock_info['avg_cost']:.2f}, 当日买入量: {stock_info['today_buy_amount']}")
            except Exception as e:
                print(f"{current_time} - 买入失败: {e}")
        else:
            print(f"{current_time} - 尾盘买入条件不满足，跳过买入")
    
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
            print(f"{current_time} -   持仓盈亏: {profit_loss:.2f}")
            print(f"{current_time} -   持仓盈亏比例: {profit_loss_ratio:.2f}%")
            print(f"{current_time} -   累计落袋盈亏: {g.realized_pnl:.2f}")
        else:
            print(f"{current_time} - 收盘统计:")
            print(f"{current_time} -   股票: {security}")
            print(f"{current_time} -   持仓量: 0")
            print(f"{current_time} -   当前价格: {current_price:.2f}")
            print(f"{current_time} -   累计落袋盈亏: {g.realized_pnl:.2f}")
