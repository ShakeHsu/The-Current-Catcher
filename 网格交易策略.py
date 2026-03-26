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
    g.security = "159825.SZ"  # 农业ETF
    g.realized_pnl = 0  # 累计落袋盈亏（全局变量）
    g.pending_orders = {}  # 待处理的订单
    
    # 股票相关变量
    g.stock_info = {
        g.security: {
            'total_cost': 0,  # 累计买入成本
            'avg_cost': 0,  # 平均成本
            'last_buy_date': None,  # 上次买入日期
            'last_buy_price': None,  # 上次买入价格
            'last_sell_date': None,  # 上次卖出日期
            'last_sell_price': None,  # 上次卖出价格
            'day_low': None,  # 当日最低价
            'day_high': 0,  # 当日最高价
            'today_buy_amount': 0,  # 当日买入量
            'today_buy_cost': 0,  # 当日买入成本（含佣金）
            'today_sell_amount': 0,  # 当日卖出量
            'today_sell_income': 0,  # 当日卖出收入（含佣金和印花税）
            'last_date': None,  # 上次处理的日期
            'daily_volume': 0,  # 当日累计成交量
            'buy_count': 0,  # 总买入次数
            'sell_count': 0,  # 总卖出次数
        }
    }
    
    # 非对称网格交易参数
    g.grid_base_price = 1.5  # 网格基准价格
    g.grid_interval = 0.05  # 网格间隔（元）
    g.grid_levels_down = 15  # 向下网格层数
    g.grid_levels_up = 10  # 向上网格层数
    g.buy_value = 12000  # 每次买入目标金额（元）
    g.sell_value = 8000  # 每次卖出目标金额（元）
    g.max_cost = 200000  # 单只股票持仓成本上限（元）
    g.min_price = g.grid_base_price - g.grid_interval * g.grid_levels_down  # 最低价格
    g.max_price = g.grid_base_price + g.grid_interval * g.grid_levels_up  # 最高价格
    
    # 打印初始化信息
    print(f"[{datetime.datetime.now()}] 非对称网格交易策略初始化完成，股票: {g.security}")
    print(f"[{datetime.datetime.now()}] 网格参数：基准价格={g.grid_base_price:.2f}, 间隔={g.grid_interval:.2f}")
    print(f"[{datetime.datetime.now()}] 网格层数：向下={g.grid_levels_down}层, 向上={g.grid_levels_up}层")
    print(f"[{datetime.datetime.now()}] 交易金额：买入={g.buy_value}元, 卖出={g.sell_value}元")
    print(f"[{datetime.datetime.now()}] 价格范围：{g.min_price:.2f} - {g.max_price:.2f}")

def handle_data(context, data):
    """核心交易逻辑"""
    security = g.security
    stock_info = g.stock_info[security]
    
    # 获取当前时间
    current_time = context.current_dt
    current_date = current_time.date()
    
    # 获取当前价格
    try:
        current_price = data[security].close
    except Exception as e:
        print(f"{current_time} - 获取价格失败: {e}")
        return
    
    # 初始化当日数据
    if stock_info['last_date'] != current_date:
        stock_info['day_low'] = current_price
        stock_info['day_high'] = current_price
        stock_info['today_buy_amount'] = 0
        stock_info['today_buy_cost'] = 0
        stock_info['today_sell_amount'] = 0
        stock_info['today_sell_income'] = 0
        stock_info['last_date'] = current_date
        stock_info['daily_volume'] = 0
    else:
        # 更新当日最高价和最低价
        if current_price < stock_info['day_low']:
            stock_info['day_low'] = current_price
        if current_price > stock_info['day_high']:
            stock_info['day_high'] = current_price
    
    # 累计当日成交量
    try:
        current_volume = data[security].volume
        stock_info['daily_volume'] += current_volume
    except Exception as e:
        print(f"{current_time} - 获取成交量失败: {e}")
    
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
    
    # 获取持仓信息
    position = context.portfolio.positions.get(security, None)
    position_amount = position.amount if position else 0
    
    # 计算当前网格位置
    current_grid = round((current_price - g.grid_base_price) / g.grid_interval)
    
    # 买入逻辑：价格下跌到网格下限
    if current_price > g.min_price and position_amount == 0:
        # 首次建仓
        buy_amount = (int(g.buy_value / current_price) + 99) // 100 * 100
        if buy_amount < 100:
            buy_amount = 100
        
        # 执行买入
        try:
            print(f"{current_time} - 执行建仓: {security}, 数量: {buy_amount}")
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
            print(f"{current_time} - 建仓成功，成交价格={execution_price:.2f}, 成交股数={filled_amount}, 买入金额={buy_value:.2f}, 佣金={buy_commission:.2f}, 实际买入成本={actual_buy_cost:.2f}, 累计成本: {stock_info['total_cost']:.2f}, 平均成本: {stock_info['avg_cost']:.2f}, 当日买入量: {stock_info['today_buy_amount']}, 总买入次数: {stock_info['buy_count']}")
        except Exception as e:
            print(f"{current_time} - 建仓失败: {e}")
    elif position_amount > 0:
        # 网格交易逻辑
        # 计算当前持仓的网格位置
        avg_cost_grid = round((stock_info['avg_cost'] - g.grid_base_price) / g.grid_interval)
        
        # 卖出条件：价格上涨到网格上限
        if current_price < g.max_price and current_grid > avg_cost_grid + 1:
            # 卖出部分仓位
            sell_value = g.sell_value
            sell_amount = (int(sell_value / current_price) + 99) // 100 * 100
            if sell_amount < 100:
                sell_amount = 100
            # 确保不超过持仓量
            sell_amount = min(sell_amount, position_amount)
            
            if sell_amount > 0:
                try:
                    print(f"{current_time} - 执行卖出: {security}, 数量: {sell_amount}")
                    order(security, -sell_amount)
                    
                    # 使用当前价格和卖出数量
                    execution_price = current_price
                    filled_amount = sell_amount
                    
                    # 计算实际卖出所得（扣除佣金和印花税）
                    sell_value_actual = filled_amount * execution_price
                    sell_commission = calculate_commission(sell_value_actual)
                    stamp_tax = calculate_stamp_tax(sell_value_actual, security)
                    actual_sell_income = sell_value_actual - sell_commission - stamp_tax
                    
                    # 计算卖出部分的成本
                    sell_cost = stock_info['avg_cost'] * filled_amount
                    # 计算盈亏
                    profit_loss = actual_sell_income - sell_cost
                    profit_loss_ratio = (profit_loss / sell_cost) * 100 if sell_cost > 0 else 0
                    
                    # 更新累计成本和平均成本
                    stock_info['total_cost'] -= sell_cost
                    new_position_amount = position_amount - filled_amount
                    if new_position_amount > 0:
                        stock_info['avg_cost'] = stock_info['total_cost'] / new_position_amount
                    else:
                        stock_info['total_cost'] = 0
                        stock_info['avg_cost'] = 0
                    
                    # 更新累计落袋盈亏
                    g.realized_pnl += profit_loss
                    
                    # 更新卖出信息
                    stock_info['last_sell_date'] = current_date
                    stock_info['last_sell_price'] = execution_price
                    stock_info['today_sell_amount'] += filled_amount
                    stock_info['today_sell_income'] += actual_sell_income
                    stock_info['sell_count'] += 1
                    
                    print(f"{current_time} - 卖出成功：成交价格={execution_price:.2f}, 成交股数={filled_amount}, 卖出金额={sell_value_actual:.2f}, 佣金={sell_commission:.2f}, 印花税={stamp_tax:.2f}, 实际卖出所得={actual_sell_income:.2f}")
                    print(f"{current_time} - 卖出盈亏={profit_loss:.2f}, 盈亏比例={profit_loss_ratio:.2f}%, 累计落袋盈亏={g.realized_pnl:.2f}")
                    print(f"{current_time} - 剩余持仓量: {new_position_amount}, 剩余成本: {stock_info['total_cost']:.2f}, 剩余平均成本: {stock_info['avg_cost']:.2f}")
                except Exception as e:
                    print(f"{current_time} - 卖出失败: {e}")
        
        # 买入条件：价格下跌到网格下限
        if current_price > g.min_price and current_grid < avg_cost_grid - 1:
            # 买入部分仓位
            buy_amount = (int(g.buy_value / current_price) + 99) // 100 * 100
            if buy_amount < 100:
                buy_amount = 100
            
            # 资金管理：总持仓成本不超过上限
            estimated_cost = buy_amount * current_price + calculate_commission(buy_amount * current_price)
            if stock_info['total_cost'] + estimated_cost > g.max_cost:
                print(f"{current_time} - 持仓成本已达上限，跳过买入")
                return
            
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
    
    # 收盘时计算并显示统计信息
    if current_time.hour == 15 and current_time.minute == 0:
        position = context.portfolio.positions.get(security, None)
        if position and position.amount > 0:
            current_price = data[security].close
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
            print(f"{current_time} -   落袋盈亏: {g.realized_pnl:.2f}")
            print(f"{current_time} -   今日买入: {stock_info['today_buy_amount']}股, 成本: {stock_info['today_buy_cost']:.2f}")
            print(f"{current_time} -   今日卖出: {stock_info['today_sell_amount']}股, 收入: {stock_info['today_sell_income']:.2f}")
            print(f"{current_time} -   总买入次数: {stock_info['buy_count']}, 总卖出次数: {stock_info['sell_count']}")
        else:
            print(f"{current_time} - 收盘统计: 无持仓")
            print(f"{current_time} -   落袋盈亏: {g.realized_pnl:.2f}")
            print(f"{current_time} -   今日买入: {stock_info['today_buy_amount']}股, 成本: {stock_info['today_buy_cost']:.2f}")
            print(f"{current_time} -   今日卖出: {stock_info['today_sell_amount']}股, 收入: {stock_info['today_sell_income']:.2f}")
            print(f"{current_time} -   总买入次数: {stock_info['buy_count']}, 总卖出次数: {stock_info['sell_count']}")