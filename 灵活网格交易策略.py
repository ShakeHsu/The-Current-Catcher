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
    g.security = "688111.SS"  # 金山办公
    g.realized_pnl = 0  # 累计落袋盈亏（全局变量）
    
    # 网格交易参数
    g.grid_base_price = 350  # 基准价格（中心参考点）
    g.grid_interval_type = "absolute"  # 网格间隔类型："absolute"（绝对值）或 "percentage"（百分比）
    g.grid_interval_value = 5  # 网格间距数值：绝对值模式下为金额，百分比模式下为小数（如0.01表示1%）
    g.buy_value = 100000  # 每次买入金额（元）
    g.sell_value = 100000  # 每次卖出金额（元）
    g.grid_levels_up = 3  # 向上网格层数
    g.grid_levels_down = 3  # 向下网格层数
    
    # 风控参数
    g.total_funds = 1000000  # 总资金
    g.reserve_funds = g.total_funds * 0.2  # 预留资金（20%）
    g.available_funds = g.total_funds - g.reserve_funds  # 可用资金
    g.max_holdings = int(g.available_funds / g.grid_base_price * 0.8)  # 最大持仓量
    g.stop_loss_pct = 0.15  # 总亏损15%时止损
    g.stop_sell_when_no_position = True  # 持仓耗尽时停止卖出
    
    # 生成网格线（包含配对关系）
    g.grid_lines = generate_grid_lines(
        g.grid_base_price, 
        g.grid_interval_type, 
        g.grid_interval_value,
        g.grid_levels_up, 
        g.grid_levels_down
    )
    
    # 股票相关变量
    g.stock_info = {
        g.security: {
            'total_cost': 0,  # 累计买入成本
            'avg_cost': 0,  # 平均成本
            'last_buy_date': None,  # 上次买入日期
            'last_sell_date': None,  # 上次卖出日期
            'today_buy_amount': 0,  # 当日买入量
            'today_buy_cost': 0,  # 当日买入成本（含佣金）
            'today_sell_amount': 0,  # 当日卖出量
            'today_sell_income': 0,  # 当日卖出收入（含佣金和印花税）
            'last_date': None,  # 上次处理的日期
            'buy_count': 0,  # 总买入次数
            'sell_count': 0,  # 总卖出次数
            'current_holdings': 0,  # 当前持仓量
            'initial_position_built': False,  # 是否已建立初始仓位
        }
    }
    
    # 打印初始化信息
    print(f"[{datetime.datetime.now()}] 灵活网格交易策略初始化完成，股票: {g.security}")
    print(f"[{datetime.datetime.now()}] 网格参数：基准价格={g.grid_base_price:.2f}, 间隔类型={g.grid_interval_type}, 间隔数值={g.grid_interval_value}")
    print(f"[{datetime.datetime.now()}] 网格层数：向上={g.grid_levels_up}层, 向下={g.grid_levels_down}层")
    print(f"[{datetime.datetime.now()}] 交易金额：买入={g.buy_value}元, 卖出={g.sell_value}元")
    print(f"[{datetime.datetime.now()}] 资金配置：总资金={g.total_funds}元, 预留资金={g.reserve_funds:.2f}元, 可用资金={g.available_funds:.2f}元")
    print(f"[{datetime.datetime.now()}] 风控参数：最大持仓={g.max_holdings}股, 止损比例={g.stop_loss_pct*100:.1f}%")
    print(f"[{datetime.datetime.now()}] 配对解锁机制：每条网格线触发后锁定，配对网格线触发后解锁")
    print(f"[{datetime.datetime.now()}] 网格线及配对关系：")
    for line in g.grid_lines:
        direction = "卖出" if line['level'] > 0 else ("买入" if line['level'] < 0 else "基准")
        pair_info = f", 配对级别={line['pair_level']}" if line['pair_level'] is not None else ""
        print(f"[{datetime.datetime.now()}]   级别{line['level']}: {line['price']:.2f}元 ({direction}){pair_info}")

def generate_grid_lines(base_price, interval_type, interval_value, levels_up, levels_down):
    """生成网格线（包含配对关系）"""
    grid_lines = []
    
    if interval_type == "absolute":
        # 绝对值模式：固定金额间隔
        for level in range(-levels_down, levels_up + 1):
            price = base_price + level * interval_value
            # 确定配对关系：买入线（负级别）与卖出线（正级别）配对
            # 级别-1与级别1配对，级别-2与级别2配对，以此类推
            pair_level = -level if level != 0 else None
            
            grid_lines.append({
                'level': level,
                'price': price,
                'type': 'sell' if level > 0 else ('buy' if level < 0 else 'base'),
                'pair_level': pair_level,  # 配对网格线的级别
                'locked': False,  # 是否被锁定
                'triggered_count': 0  # 触发次数统计
            })
    elif interval_type == "percentage":
        # 百分比模式：按比例间隔
        for level in range(-levels_down, levels_up + 1):
            if level >= 0:
                price = base_price * (1 + interval_value) ** level
            else:
                price = base_price / (1 + interval_value) ** abs(level)
            
            pair_level = -level if level != 0 else None
            
            grid_lines.append({
                'level': level,
                'price': price,
                'type': 'sell' if level > 0 else ('buy' if level < 0 else 'base'),
                'pair_level': pair_level,
                'locked': False,
                'triggered_count': 0
            })
    
    return grid_lines

def find_grid_line_by_price(price, tolerance=0.02):
    """根据价格查找对应的网格线"""
    for line in g.grid_lines:
        if abs(price - line['price']) < tolerance:
            return line
    return None

def find_grid_line_by_level(level):
    """根据级别查找对应的网格线"""
    for line in g.grid_lines:
        if line['level'] == level:
            return line
    return None

def unlock_pair_grid_line(triggered_line):
    """解锁配对的网格线"""
    if triggered_line['pair_level'] is not None:
        pair_line = find_grid_line_by_level(triggered_line['pair_level'])
        if pair_line and pair_line['locked']:
            pair_line['locked'] = False
            pair_direction = "卖出" if pair_line['level'] > 0 else "买入"
            triggered_direction = "卖出" if triggered_line['level'] > 0 else "买入"
            print(f"[{datetime.datetime.now()}] 配对解锁：级别{triggered_line['level']}的{triggered_direction}线触发，解锁级别{pair_line['level']}的{pair_direction}线")
            return True
    return False

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
        stock_info['today_buy_amount'] = 0
        stock_info['today_buy_cost'] = 0
        stock_info['today_sell_amount'] = 0
        stock_info['today_sell_income'] = 0
        stock_info['last_date'] = current_date
    
    # 获取持仓信息
    position = context.portfolio.positions.get(security, None)
    position_amount = position.amount if position else 0
    stock_info['current_holdings'] = position_amount
    
    # 风控检查：总亏损止损
    if position_amount > 0:
        total_value = position_amount * current_price
        total_loss = stock_info['total_cost'] - total_value
        if total_loss > g.total_funds * g.stop_loss_pct:
            print(f"{current_time} - 触发总亏损止损：总亏损={total_loss:.2f} > 总资金的{int(g.stop_loss_pct*100)}%={g.total_funds*g.stop_loss_pct:.2f}")
            try:
                print(f"{current_time} - 执行止损卖出: {security}, 数量: {position_amount}")
                order(security, -position_amount)
                
                execution_price = current_price
                filled_amount = position_amount
                
                sell_value_actual = filled_amount * execution_price
                sell_commission = calculate_commission(sell_value_actual)
                stamp_tax = calculate_stamp_tax(sell_value_actual, security)
                actual_sell_income = sell_value_actual - sell_commission - stamp_tax
                
                sell_cost = stock_info['avg_cost'] * filled_amount
                profit_loss = actual_sell_income - sell_cost
                profit_loss_ratio = (profit_loss / sell_cost) * 100 if sell_cost > 0 else 0
                
                stock_info['total_cost'] = 0
                stock_info['avg_cost'] = 0
                g.realized_pnl += profit_loss
                
                stock_info['last_sell_date'] = current_date
                stock_info['today_sell_amount'] += filled_amount
                stock_info['today_sell_income'] += actual_sell_income
                stock_info['sell_count'] += 1
                
                print(f"{current_time} - 止损卖出成功：成交价格={execution_price:.2f}, 成交股数={filled_amount}, 卖出金额={sell_value_actual:.2f}, 佣金={sell_commission:.2f}, 印花税={stamp_tax:.2f}, 实际卖出所得={actual_sell_income:.2f}")
                print(f"{current_time} - 止损盈亏={profit_loss:.2f}, 盈亏比例={profit_loss_ratio:.2f}%, 累计落袋盈亏={g.realized_pnl:.2f}")
                print(f"{current_time} - 持仓已清空，策略暂停")
            except Exception as e:
                print(f"{current_time} - 止损卖出失败: {e}")
            return
    
    # 查找当前价格对应的网格线
    grid_line = find_grid_line_by_price(current_price)
    
    if grid_line is None:
        return
    
    # 初始仓位建立逻辑
    if not stock_info['initial_position_built']:
        if grid_line['type'] == 'base':
            # 在基准价格附近建立初始仓位
            # 计算需要覆盖所有卖出网格的仓位
            total_sell_value = g.sell_value * g.grid_levels_up
            initial_buy_amount = int(total_sell_value / current_price / 100) * 100
            initial_buy_amount = min(initial_buy_amount, g.max_holdings)
            
            if initial_buy_amount < 100:
                initial_buy_amount = 100
            
            try:
                print(f"{current_time} - 建立初始仓位: {security}, 数量: {initial_buy_amount}")
                order(security, initial_buy_amount)
                
                execution_price = current_price
                filled_amount = initial_buy_amount
                
                buy_value = filled_amount * execution_price
                buy_commission = calculate_commission(buy_value)
                actual_buy_cost = buy_value + buy_commission
                
                stock_info['total_cost'] += actual_buy_cost
                stock_info['today_buy_cost'] += actual_buy_cost
                new_position_amount = position_amount + filled_amount
                if new_position_amount > 0:
                    stock_info['avg_cost'] = stock_info['total_cost'] / new_position_amount
                
                stock_info['last_buy_date'] = current_date
                stock_info['today_buy_amount'] += filled_amount
                stock_info['buy_count'] += 1
                stock_info['initial_position_built'] = True
                
                print(f"{current_time} - 初始仓位建立成功，成交价格={execution_price:.2f}, 成交股数={filled_amount}, 买入金额={buy_value:.2f}, 佣金={buy_commission:.2f}, 实际买入成本={actual_buy_cost:.2f}, 累计成本: {stock_info['total_cost']:.2f}, 平均成本: {stock_info['avg_cost']:.2f}")
                print(f"{current_time} - 初始仓位已建立，开始网格交易")
            except Exception as e:
                print(f"{current_time} - 初始仓位建立失败: {e}")
        return
    
    # 网格交易逻辑
    if stock_info['initial_position_built']:
        if grid_line['type'] == 'buy' and not grid_line['locked']:
            # 买入网格线触发（未锁定状态）
            available_funds = g.available_funds - stock_info['total_cost']
            if available_funds >= g.buy_value and position_amount < g.max_holdings:
                buy_amount = int(g.buy_value / current_price / 100) * 100
                buy_amount = min(buy_amount, g.max_holdings - position_amount)
                
                if buy_amount > 0:
                    try:
                        print(f"{current_time} - 触发买入网格线: 级别{grid_line['level']}, 价格={grid_line['price']:.2f}")
                        order(security, buy_amount)
                        
                        execution_price = current_price
                        filled_amount = buy_amount
                        
                        buy_value = filled_amount * execution_price
                        buy_commission = calculate_commission(buy_value)
                        actual_buy_cost = buy_value + buy_commission
                        
                        stock_info['total_cost'] += actual_buy_cost
                        stock_info['today_buy_cost'] += actual_buy_cost
                        new_position_amount = position_amount + filled_amount
                        if new_position_amount > 0:
                            stock_info['avg_cost'] = stock_info['total_cost'] / new_position_amount
                        
                        stock_info['last_buy_date'] = current_date
                        stock_info['today_buy_amount'] += filled_amount
                        stock_info['buy_count'] += 1
                        
                        # 锁定当前买入线，解锁配对卖出线
                        grid_line['locked'] = True
                        grid_line['triggered_count'] += 1
                        unlock_pair_grid_line(grid_line)
                        
                        print(f"{current_time} - 网格买入成功，成交价格={execution_price:.2f}, 成交股数={filled_amount}, 买入金额={buy_value:.2f}, 佣金={buy_commission:.2f}, 实际买入成本={actual_buy_cost:.2f}")
                        print(f"{current_time} - 级别{grid_line['level']}买入线已锁定，等待配对卖出线触发后解锁")
                    except Exception as e:
                        print(f"{current_time} - 网格买入失败: {e}")
            else:
                if available_funds < g.buy_value:
                    print(f"{current_time} - 资金不足，无法买入")
                if position_amount >= g.max_holdings:
                    print(f"{current_time} - 持仓达到上限，无法买入")
        
        elif grid_line['type'] == 'sell' and not grid_line['locked']:
            # 卖出网格线触发（未锁定状态）
            sell_amount = int(g.sell_value / current_price / 100) * 100
            sell_amount = min(sell_amount, position_amount)
            
            if sell_amount > 0:
                try:
                    print(f"{current_time} - 触发卖出网格线: 级别{grid_line['level']}, 价格={grid_line['price']:.2f}")
                    order(security, -sell_amount)
                    
                    execution_price = current_price
                    filled_amount = sell_amount
                    
                    sell_value_actual = filled_amount * execution_price
                    sell_commission = calculate_commission(sell_value_actual)
                    stamp_tax = calculate_stamp_tax(sell_value_actual, security)
                    actual_sell_income = sell_value_actual - sell_commission - stamp_tax
                    
                    sell_cost = stock_info['avg_cost'] * filled_amount
                    profit_loss = actual_sell_income - sell_cost
                    profit_loss_ratio = (profit_loss / sell_cost) * 100 if sell_cost > 0 else 0
                    
                    stock_info['total_cost'] -= sell_cost
                    new_position_amount = position_amount - filled_amount
                    if new_position_amount > 0:
                        stock_info['avg_cost'] = stock_info['total_cost'] / new_position_amount
                    else:
                        stock_info['total_cost'] = 0
                        stock_info['avg_cost'] = 0
                    
                    g.realized_pnl += profit_loss
                    
                    stock_info['last_sell_date'] = current_date
                    stock_info['today_sell_amount'] += filled_amount
                    stock_info['today_sell_income'] += actual_sell_income
                    stock_info['sell_count'] += 1
                    
                    # 锁定当前卖出线，解锁配对买入线
                    grid_line['locked'] = True
                    grid_line['triggered_count'] += 1
                    unlock_pair_grid_line(grid_line)
                    
                    print(f"{current_time} - 网格卖出成功：成交价格={execution_price:.2f}, 成交股数={filled_amount}, 卖出金额={sell_value_actual:.2f}, 佣金={sell_commission:.2f}, 印花税={stamp_tax:.2f}, 实际卖出所得={actual_sell_income:.2f}")
                    print(f"{current_time} - 卖出盈亏={profit_loss:.2f}, 盈亏比例={profit_loss_ratio:.2f}%, 累计落袋盈亏={g.realized_pnl:.2f}")
                    print(f"{current_time} - 级别{grid_line['level']}卖出线已锁定，等待配对买入线触发后解锁")
                    print(f"{current_time} - 剩余持仓量: {new_position_amount}, 剩余成本: {stock_info['total_cost']:.2f}, 剩余平均成本: {stock_info['avg_cost']:.2f}")
                except Exception as e:
                    print(f"{current_time} - 网格卖出失败: {e}")
            else:
                if g.stop_sell_when_no_position:
                    print(f"{current_time} - 持仓不足，停止卖出")
                else:
                    print(f"{current_time} - 持仓不足，跳过卖出")
        
        elif grid_line['locked']:
            # 网格线已锁定，跳过
            direction = "买入" if grid_line['type'] == 'buy' else "卖出"
            print(f"{current_time} - 级别{grid_line['level']}的{direction}线已锁定，跳过触发")
    
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
            print(f"{current_time} -   可用资金: {g.available_funds - stock_info['total_cost']:.2f}")
            
            # 显示网格线状态
            print(f"{current_time} - 网格线状态:")
            for line in g.grid_lines:
                if line['type'] != 'base':
                    direction = "卖出" if line['level'] > 0 else "买入"
                    status = "已锁定" if line['locked'] else "可触发"
                    pair_level = line['pair_level']
                    print(f"{current_time} -   级别{line['level']}: {line['price']:.2f}元 ({direction}) - {status}, 配对级别={pair_level}, 触发次数={line['triggered_count']}")
        else:
            print(f"{current_time} - 收盘统计: 无持仓")
            print(f"{current_time} -   落袋盈亏: {g.realized_pnl:.2f}")
            print(f"{current_time} -   今日买入: {stock_info['today_buy_amount']}股, 成本: {stock_info['today_buy_cost']:.2f}")
            print(f"{current_time} -   今日卖出: {stock_info['today_sell_amount']}股, 收入: {stock_info['today_sell_income']:.2f}")
            print(f"{current_time} -   总买入次数: {stock_info['buy_count']}, 总卖出次数: {stock_info['sell_count']}")
            print(f"{current_time} -   可用资金: {g.available_funds:.2f}")
            
            # 显示网格线状态
            print(f"{current_time} - 网格线状态:")
            for line in g.grid_lines:
                if line['type'] != 'base':
                    direction = "卖出" if line['level'] > 0 else "买入"
                    status = "已锁定" if line['locked'] else "可触发"
                    pair_level = line['pair_level']
                    print(f"{current_time} -   级别{line['level']}: {line['price']:.2f}元 ({direction}) - {status}, 配对级别={pair_level}, 触发次数={line['triggered_count']}")
