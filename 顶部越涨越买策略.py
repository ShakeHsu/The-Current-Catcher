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
            'buy_count': 0,  # 总买入次数
            'sell_check_today': False,  # 当日是否已检查卖出条件
        }
    }
    
    # 策略参数
    g.buy_value = 10000  # 每次买入目标金额（元）
    g.sell_value = 10000  # 每次卖出目标金额（元）
    g.max_cost = 200000  # 单只股票持仓成本上限（元）
    g.rebound_threshold = 0.0003  # 反弹阈值：0.03%
    g.ma60_ratio_buy = 1.05  # 买入时收盘价/60日均线阈值
    g.ma60_ratio_sell = 1.2  # 卖出时收盘价/60日均线阈值
    g.profit_threshold = 0.005  # 第2次买入后盈利阈值：0.5%
    
    # 打印初始化信息
    print(f"[{datetime.datetime.now()}] 顶部越涨越买策略初始化完成，股票: {g.security}")

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
        stock_info['sell_check_today'] = False
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
        # 增加数据获取的时间范围
        start_date = (current_date - datetime.timedelta(days=120)).strftime('%Y%m%d')
        hist = get_price(security, start_date=start_date, end_date=end_date, frequency='1d', fields=['close', 'open', 'volume'], fq='pre')
        if hist is None:
            print(f"{current_time} - 无法获取历史数据")
            return
        elif len(hist) < 10:
            print(f"{current_time} - 历史数据严重不足，当前数据长度: {len(hist)}")
            return
    except Exception as e:
        print(f"{current_time} - 获取历史数据失败: {e}")
        return
    
    # 计算60日均线（使用可用数据）
    if len(hist) >= 60:
        ma60 = hist['close'][-60:].mean()
    else:
        ma60 = hist['close'].mean()
        print(f"{current_time} - 数据不足60天，使用{len(hist)}天数据计算均线")
    
    # 计算5日均线
    ma5_list = []
    if len(hist) >= 5:
        for i in range(len(hist) - 4):
            ma5 = hist['close'][i:i+5].mean()
            ma5_list.append(ma5)
    
    # 计算前60日成交额中位数（使用可用数据）
    if len(hist) >= 60:
        amount_60d = (hist['close'] * hist['volume'])[-60:]
    else:
        amount_60d = (hist['close'] * hist['volume'])
        print(f"{current_time} - 数据不足60天，使用{len(hist)}天数据计算成交额中位数")
    amount_median = amount_60d.median()
    
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
    
    if can_buy:
        # 条件1：前5天中有至少3天满足收盘价/60日均线<1.05
        condition1_count = 0
        for i in range(max(0, len(hist)-5), len(hist)):
            close = hist['close'][i]
            if close / ma60 < g.ma60_ratio_buy:
                condition1_count += 1
        condition1 = condition1_count >= 3
        
        # 条件2：前5天中有至少3天5日均线呈上升趋势
        condition2_count = 0
        if len(ma5_list) >= 2:
            for i in range(max(0, len(ma5_list)-5), len(ma5_list)-1):
                if ma5_list[i+1] > ma5_list[i]:
                    condition2_count += 1
        condition2 = condition2_count >= 3
        
        # 条件3：当日最低价格低于昨日收盘价
        yesterday_close = hist['close'][-1]
        condition3 = day_low < yesterday_close
        
        # 条件4：反弹确认：当前最新价 >= 当日最低价 * (1 + g.rebound_threshold)
        rebound_confirm = current_price >= day_low * (1 + g.rebound_threshold)
        
        # 条件5：前5天中有至少3天成交额<前60日成交额中位数
        condition5_count = 0
        for i in range(max(0, len(hist)-5), len(hist)):
            amount = hist['close'][i] * hist['volume'][i]
            if amount < amount_median:
                condition5_count += 1
        condition5 = condition5_count >= 3
        
        print(f"{current_time} - 买入条件检查:")
        print(f"{current_time} -   条件1: 前5天中有至少3天满足收盘价/60日均线<{g.ma60_ratio_buy} = {condition1} (满足天数: {condition1_count}/5)")
        print(f"{current_time} -   条件2: 前5天中有至少3天5日均线呈上升趋势 = {condition2} (满足天数: {condition2_count}/5)")
        print(f"{current_time} -   条件3: 当日最低价格低于昨日收盘价 = {condition3}")
        print(f"{current_time} -   条件4: 反弹确认 = {rebound_confirm}")
        print(f"{current_time} -   条件5: 前5天中有至少3天成交额<前60日成交额中位数 = {condition5} (满足天数: {condition5_count}/5)")
        print(f"{current_time} - 价格数据: 当前价格={current_price:.2f}, 当日最低价={day_low:.2f}, 昨日收盘价={yesterday_close:.2f}, 60日均线={ma60:.2f}")
        
        # 当满足前5个条件后，再判断条件6
        if condition1 and condition2 and condition3 and rebound_confirm and condition5:
            # 条件6：价格大于上一次买入价格
            condition6 = True
            if stock_info['last_buy_price'] is not None:
                condition6 = current_price > stock_info['last_buy_price']
                print(f"{current_time} -   条件6: 价格大于上一次买入价格 = {condition6} (当前价格={current_price:.2f}, 上次买入价格={stock_info['last_buy_price']:.2f})")
            else:
                print(f"{current_time} -   条件6: 首次买入，自动满足")
            
            if condition6:
                # 计算买入股数：向上取整至100股整数倍
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
                    print(f"{current_time} - 买入成功，成交价格={execution_price:.2f}, 成交股数={filled_amount}, 买入金额={buy_value:.2f}, 佣金={buy_commission:.2f}, 实际买入成本={actual_buy_cost:.2f}, 累计成本: {stock_info['total_cost']:.2f}, 平均成本: {stock_info['avg_cost']:.2f}, 当日买入量: {stock_info['today_buy_amount']}, 总买入次数: {stock_info['buy_count']}")
                except Exception as e:
                    print(f"{current_time} - 买入失败: {e}")
    
    # 止损条件检查
    if position and position.amount > 0:
        # 条件1：第1次买入后，前5天中有至少3天收盘价低于60日均线且5日均线呈下降趋势，立即清仓
        if stock_info['buy_count'] == 1:
            close_below_ma60_count = 0
            for i in range(max(0, len(hist)-5), len(hist)):
                close = hist['close'][i]
                if close < ma60:
                    close_below_ma60_count += 1
            
            ma5_down_count = 0
            if len(ma5_list) >= 2:
                for i in range(max(0, len(ma5_list)-5), len(ma5_list)-1):
                    if ma5_list[i+1] < ma5_list[i]:
                        ma5_down_count += 1
            
            if close_below_ma60_count >= 3 and ma5_down_count >= 3:
                print(f"{current_time} - 止损条件1触发：第1次买入后，前5天中有至少3天收盘价低于60日均线且5日均线呈下降趋势")
                # 清仓
                sell_amount = position.amount
                try:
                    print(f"{current_time} - 执行清仓: {security}, 数量: {sell_amount}")
                    order(security, -sell_amount)
                    
                    # 使用当前价格和卖出数量
                    execution_price = current_price
                    filled_amount = sell_amount
                    
                    # 计算实际卖出所得（扣除佣金和印花税）
                    sell_value = filled_amount * execution_price
                    sell_commission = calculate_commission(sell_value)
                    stamp_tax = calculate_stamp_tax(sell_value, security)
                    actual_sell_income = sell_value - sell_commission - stamp_tax
                    
                    # 计算盈亏
                    profit_loss = actual_sell_income - stock_info['total_cost']
                    profit_loss_ratio = (profit_loss / stock_info['total_cost']) * 100 if stock_info['total_cost'] > 0 else 0
                    
                    # 更新累计落袋盈亏
                    g.realized_pnl += profit_loss
                    
                    print(f"{current_time} - 清仓成功：成交价格={execution_price:.2f}, 成交股数={filled_amount}, 卖出金额={sell_value:.2f}, 佣金={sell_commission:.2f}, 印花税={stamp_tax:.2f}, 实际卖出所得={actual_sell_income:.2f}")
                    print(f"{current_time} - 清仓盈亏={profit_loss:.2f}, 盈亏比例={profit_loss_ratio:.2f}%, 累计落袋盈亏={g.realized_pnl:.2f}")
                    
                    # 重置相关变量
                    stock_info['total_cost'] = 0
                    stock_info['avg_cost'] = 0
                    stock_info['last_buy_price'] = None
                    stock_info['buy_count'] = 0
                except Exception as e:
                    print(f"{current_time} - 清仓失败: {e}")
        
        # 条件2：第2次买入后，盈利小于0.5%，立即清仓
        elif stock_info['buy_count'] == 2:
            total_value = position.amount * current_price
            profit_loss = total_value - stock_info['total_cost']
            profit_loss_ratio = (profit_loss / stock_info['total_cost']) * 100 if stock_info['total_cost'] > 0 else 0
            
            if profit_loss_ratio < g.profit_threshold * 100:
                print(f"{current_time} - 止损条件2触发：第2次买入后，盈利小于{int(g.profit_threshold*100)}%")
                # 清仓
                sell_amount = position.amount
                try:
                    print(f"{current_time} - 执行清仓: {security}, 数量: {sell_amount}")
                    order(security, -sell_amount)
                    
                    # 使用当前价格和卖出数量
                    execution_price = current_price
                    filled_amount = sell_amount
                    
                    # 计算实际卖出所得（扣除佣金和印花税）
                    sell_value = filled_amount * execution_price
                    sell_commission = calculate_commission(sell_value)
                    stamp_tax = calculate_stamp_tax(sell_value, security)
                    actual_sell_income = sell_value - sell_commission - stamp_tax
                    
                    # 计算盈亏
                    profit_loss = actual_sell_income - stock_info['total_cost']
                    profit_loss_ratio = (profit_loss / stock_info['total_cost']) * 100 if stock_info['total_cost'] > 0 else 0
                    
                    # 更新累计落袋盈亏
                    g.realized_pnl += profit_loss
                    
                    print(f"{current_time} - 清仓成功：成交价格={execution_price:.2f}, 成交股数={filled_amount}, 卖出金额={sell_value:.2f}, 佣金={sell_commission:.2f}, 印花税={stamp_tax:.2f}, 实际卖出所得={actual_sell_income:.2f}")
                    print(f"{current_time} - 清仓盈亏={profit_loss:.2f}, 盈亏比例={profit_loss_ratio:.2f}%, 累计落袋盈亏={g.realized_pnl:.2f}")
                    
                    # 重置相关变量
                    stock_info['total_cost'] = 0
                    stock_info['avg_cost'] = 0
                    stock_info['last_buy_price'] = None
                    stock_info['buy_count'] = 0
                except Exception as e:
                    print(f"{current_time} - 清仓失败: {e}")
    
    # 止盈条件检查：14:55检查
    if current_time.hour == 14 and current_time.minute == 55 and position and position.amount > 0 and not stock_info['sell_check_today']:
        # 条件1：前5天中有至少3天满足收盘价/60日均线>1.2
        condition_sell_count = 0
        for i in range(max(0, len(hist)-5), len(hist)):
            close = hist['close'][i]
            if close / ma60 > g.ma60_ratio_sell:
                condition_sell_count += 1
        
        if condition_sell_count >= 3:
            print(f"{current_time} - 止盈条件1触发：前5天中有至少3天满足收盘价/60日均线>{g.ma60_ratio_sell}")
            # 计算卖出股数：按10000元计算
            sell_amount = (int(g.sell_value / current_price) + 99) // 100 * 100
            if sell_amount < 100:
                sell_amount = 100
            # 确保不超过持仓量
            sell_amount = min(sell_amount, position.amount)
            
            if sell_amount > 0:
                try:
                    print(f"{current_time} - 执行卖出: {security}, 数量: {sell_amount}")
                    order(security, -sell_amount)
                    
                    # 使用当前价格和卖出数量
                    execution_price = current_price
                    filled_amount = sell_amount
                    
                    # 计算实际卖出所得（扣除佣金和印花税）
                    sell_value = filled_amount * execution_price
                    sell_commission = calculate_commission(sell_value)
                    stamp_tax = calculate_stamp_tax(sell_value, security)
                    actual_sell_income = sell_value - sell_commission - stamp_tax
                    
                    # 计算卖出部分的成本
                    sell_cost = stock_info['avg_cost'] * filled_amount
                    # 计算盈亏
                    profit_loss = actual_sell_income - sell_cost
                    profit_loss_ratio = (profit_loss / sell_cost) * 100 if sell_cost > 0 else 0
                    
                    # 更新累计成本和平均成本
                    stock_info['total_cost'] -= sell_cost
                    new_position_amount = position.amount - filled_amount
                    if new_position_amount > 0:
                        stock_info['avg_cost'] = stock_info['total_cost'] / new_position_amount
                    else:
                        stock_info['total_cost'] = 0
                        stock_info['avg_cost'] = 0
                        stock_info['buy_count'] = 0
                    
                    # 更新累计落袋盈亏
                    g.realized_pnl += profit_loss
                    
                    print(f"{current_time} - 卖出成功：成交价格={execution_price:.2f}, 成交股数={filled_amount}, 卖出金额={sell_value:.2f}, 佣金={sell_commission:.2f}, 印花税={stamp_tax:.2f}, 实际卖出所得={actual_sell_income:.2f}")
                    print(f"{current_time} - 卖出盈亏={profit_loss:.2f}, 盈亏比例={profit_loss_ratio:.2f}%, 累计落袋盈亏={g.realized_pnl:.2f}")
                    print(f"{current_time} - 剩余持仓量: {new_position_amount}, 剩余成本: {stock_info['total_cost']:.2f}, 剩余平均成本: {stock_info['avg_cost']:.2f}")
                except Exception as e:
                    print(f"{current_time} - 卖出失败: {e}")
        
        # 标记当日已检查卖出条件
        stock_info['sell_check_today'] = True
    
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
            print(f"{current_time} -   总买入次数: {stock_info['buy_count']}")
        else:
            print(f"{current_time} - 收盘统计:")
            print(f"{current_time} -   股票: {security}")
            print(f"{current_time} -   持仓量: 0")
            print(f"{current_time} -   当前价格: {current_price:.2f}")
            print(f"{current_time} -   累计落袋盈亏: {g.realized_pnl:.2f}")
            print(f"{current_time} -   总买入次数: {stock_info['buy_count']}")
