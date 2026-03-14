import datetime

def initialize(context):
    # 初始化策略
    g.security = "159206.SZ"  # 卫星ETF
    g.realized_pnl = 0  # 累计落袋盈亏（全局变量）
    g.pending_orders = {}  # 待处理的订单 {order_id: {'type': 't_sell'/'clear', 'shares': 计划卖出量}}
    
    # 初始化股票相关变量
    g.stock_info = {
        g.security: {
            'total_cost': 0,  # 累计买入成本
            'avg_cost': 0,  # 平均成本
            'yesterday_ma5': None,  # 昨日5日均线
            'yesterday_ma60': None,  # 昨日60日均线
            'last_buy_date': None,  # 上次买入日期
            'last_buy_price': None,  # 上次买入价格
            'highest_buy_price': None,  # 最高买入价格
            'stop_loss_today': False,  # 当日是否已执行止损清仓
            'volume_values': [],  # 存储成交量
            'daily_volume': 0,  # 当日累计成交量
            'last_date': None,  # 上次处理的日期
            'day_low': None,  # 当日最低价（从开盘开始监控）
            'today_buy_amount': 0,  # 当日买入量
            'day_high': 0,  # 当日最高价
            'buy_count': 0,  # 买入次数
            't_done_today': False,  # 当日是否已执行做T
            'position_high': 0,  # 持仓期间最高价（用于计算回撤）
            'last_position_amount': 0,  # 上一次的持仓量（用于计算实际卖出量）
        }
    }
    
    # 策略参数
    g.buy_amount = 10000  # 每次买入目标金额（元）
    g.max_cost = 200000  # 单只股票持仓成本上限（元）
    g.volume_ratio_threshold = 3  # 买入时成交量过滤阈值
    g.sell_volume_ratio = 1.5  # 卖出时放量阈值
    g.sell_gain_threshold = 0.03  # 卖出时涨幅阈值
    g.rebound_threshold = 0.0003  # 反弹阈值（0.03%）
    # 分批止盈参数
    g.profit_loss_ratio_take_profit = 0.15  # 盈亏率止盈阈值：15%
    # 清仓参数
    g.max_drawdown_stop = 0.05  # 从最高点回撤清仓阈值：5%
    g.profit_loss_ratio_stop_loss = 0.05  # 盈亏率止损阈值：5%
    # 买入条件参数
    g.m_days = 5  # 前m天
    g.n_days = 3  # 前m天中需要满足条件的天数
    g.a_days = 5  # 前a天
    g.b_days = 3  # 前a天中需要满足条件的天数
    # 做T参数
    g.t_gain_threshold = 0.05  # 做T涨幅阈值：5%
    g.t_pullback_threshold = 0.01  # 做T回落阈值：1%
    g.t_1455_gain_threshold = 0.02  # 14:55做T涨幅阈值：2%
    
    # 打印初始化信息
    print(f"[{datetime.datetime.now()}] 策略初始化完成，股票: {g.security}")
    # 再次打印确认初始化执行
    print("=== 初始化函数执行完毕 ===")

def before_trading_start(context, data):
    # 检查是否有昨天没卖完的股票
    if g.pending_orders:
        print(f"{datetime.datetime.now()} - 检查昨日未完成的订单: {list(g.pending_orders.keys())}")
        for order_id, order_info in list(g.pending_orders.items()):
            # 获取订单信息
            order = get_order(order_id)
            if order:
                # 如果未全部成交
                if order.filled < order.amount:
                    print(f"{datetime.datetime.now()} - 未完全成交: 已卖{order.filled}股，剩余{order.amount - order.filled}股")
                    # 继续尝试卖出剩余部分
                    remaining_shares = order.amount - order.filled
                    order_id = order_target(g.security, context.portfolio.positions[g.security].amount - remaining_shares)
                    if order_id:
                        g.pending_orders[order_id] = order_info
                        print(f"{datetime.datetime.now()} - 继续处理昨日未完成清仓，新订单ID: {order_id}")
                else:
                    # 已全部成交，从待处理订单中移除
                    print(f"{datetime.datetime.now()} - 订单已全部成交，移除订单ID: {order_id}")
                    del g.pending_orders[order_id]
            else:
                # 订单不存在，从待处理订单中移除
                print(f"{datetime.datetime.now()} - 订单不存在，移除订单ID: {order_id}")
                del g.pending_orders[order_id]


def handle_data(context, data):
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
    print(f"{current_time} - 股票: {security}, 价格: {current_price}")
    
    # 检查待处理的订单（处理部分成交情况）
    if g.pending_orders:
        for order_id, order_info in list(g.pending_orders.items()):
            # 获取订单信息
            order = get_order(order_id)
            if order:
                # 如果未全部成交
                if order.filled < order.amount:
                    print(f"{current_time} - 订单未完全成交: 订单ID={order_id}, 已成交={order.filled}股, 剩余={order.amount - order.filled}股")
                    # 计算实际成交的卖出量
                    actual_sell_shares = order.filled
                    if actual_sell_shares > 0:
                        # 使用实际成交量计算落袋盈亏
                        sell_amount = order_info['price'] * actual_sell_shares
                        realized_pnl = sell_amount - order_info['avg_cost'] * actual_sell_shares
                        g.realized_pnl += realized_pnl
                        # 更新总成本：总成本-=平均成本*实际卖出量
                        stock_info['total_cost'] -= order_info['avg_cost'] * actual_sell_shares
                        # 判断是做T卖出还是清仓
                        if order_info['type'] == 'clear':
                            print(f"{current_time} - 清仓部分成交：计划清仓量={order_info['shares']}, 实际清仓量={actual_sell_shares}, 卖出金额={sell_amount:.2f}, 落袋盈亏={realized_pnl:.2f}, 累计落袋盈亏={g.realized_pnl:.2f}")
                            # 如果全部清仓，重置相关变量
                            if actual_sell_shares == stock_info['last_position_amount']:
                                stock_info['total_cost'] = 0
                                stock_info['avg_cost'] = 0
                                stock_info['highest_buy_price'] = None
                                stock_info['position_high'] = 0
                                stock_info['stop_loss_today'] = True
                                stock_info['buy_count'] = 0
                        else:
                            print(f"{current_time} - 做T卖出部分成交：计划卖出量={order_info['shares']}, 实际卖出量={actual_sell_shares}, 卖出金额={sell_amount:.2f}, 落袋盈亏={realized_pnl:.2f}, 累计落袋盈亏={g.realized_pnl:.2f}")
                else:
                    # 已全部成交
                    print(f"{current_time} - 订单已全部成交: 订单ID={order_id}, 成交量={order.filled}股")
                    # 计算实际成交的卖出量
                    actual_sell_shares = order.filled
                    if actual_sell_shares > 0:
                        # 使用实际成交量计算落袋盈亏
                        sell_amount = order_info['price'] * actual_sell_shares
                        realized_pnl = sell_amount - order_info['avg_cost'] * actual_sell_shares
                        g.realized_pnl += realized_pnl
                        # 更新总成本：总成本-=平均成本*实际卖出量
                        stock_info['total_cost'] -= order_info['avg_cost'] * actual_sell_shares
                        # 判断是做T卖出还是清仓
                        if order_info['type'] == 'clear':
                            print(f"{current_time} - 清仓确认：计划清仓量={order_info['shares']}, 实际清仓量={actual_sell_shares}, 卖出金额={sell_amount:.2f}, 落袋盈亏={realized_pnl:.2f}, 累计落袋盈亏={g.realized_pnl:.2f}")
                            # 清仓后重置相关变量
                            stock_info['total_cost'] = 0
                            stock_info['avg_cost'] = 0
                            stock_info['highest_buy_price'] = None
                            stock_info['position_high'] = 0
                            stock_info['stop_loss_today'] = True
                            stock_info['buy_count'] = 0
                        else:
                            print(f"{current_time} - 做T卖出确认：计划卖出量={order_info['shares']}, 实际卖出量={actual_sell_shares}, 卖出金额={sell_amount:.2f}, 落袋盈亏={realized_pnl:.2f}, 累计落袋盈亏={g.realized_pnl:.2f}")
                    # 从待处理订单中移除
                    del g.pending_orders[order_id]
            else:
                # 订单不存在，从待处理订单中移除
                print(f"{current_time} - 订单不存在，移除订单ID: {order_id}")
                del g.pending_orders[order_id]
    
    # 监控当日最低价和最高价（从开盘开始）
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
        # 新的一天，重置当日最低价、最高价、买入量和做T标记
        stock_info['day_low'] = current_low
        stock_info['day_high'] = current_high
        stock_info['today_buy_amount'] = 0
        stock_info['t_done_today'] = False
        print(f"{current_time} - 新的一天，初始化当日最低价: {current_low}, 最高价: {current_high}, 买入量: 0, 做T标记: False")
    else:
        # 更新当日最低价
        if stock_info['day_low'] is None or current_low < stock_info['day_low']:
            stock_info['day_low'] = current_low
            print(f"{current_time} - 更新当日最低价: {current_low}")
        # 更新当日最高价
        if stock_info['day_high'] is None or current_high > stock_info['day_high']:
            stock_info['day_high'] = current_high
            print(f"{current_time} - 更新当日最高价: {current_high}")
    
    day_low = stock_info['day_low']
    day_high = stock_info['day_high']
    
    print(f"{current_time} - 当日最低价: {day_low}, 最高价: {day_high}")
    
    # 获取成交量（使用累加方式计算当日累计成交量）
    try:
        # 检查是否是新的一天
        if stock_info['last_date'] != current_date:
            # 新的一天，重置当日累计成交量
            stock_info['daily_volume'] = 0
            stock_info['last_date'] = current_date
            stock_info['stop_loss_today'] = False  # 重置当日止损标记
            print(f"{current_time} - 新的一天，重置当日累计成交量和止损标记")
        
        # 获取当前周期的成交量
        if hasattr(data[security], 'volume'):
            period_volume = data[security].volume
            print(f"{current_time} - 获取当前分钟成交量: {period_volume}")

        elif hasattr(data[security], 'vol'):
            period_volume = data[security].vol
            print(f"{current_time} - 获取当前分钟成交量(vol): {period_volume}")
        else:
            print(f"{current_time} - 无法获取成交量")
            return
        
        # 累加到当日累计成交量
        stock_info['daily_volume'] += period_volume
        current_volume = stock_info['daily_volume']
        print(f"{current_time} - 当日累计成交量: {current_volume}")
    except Exception as e:
        print(f"{current_time} - 获取当日累计成交量失败: {e}")
        return
    
    # 使用PTrade的get_price函数获取历史数据
    try:
        # 计算日期范围，考虑交易日因素，增加天数
        import datetime
        end_date = current_date.strftime('%Y%m%d')
        # 增加到120天，确保有足够的交易日
        start_date = (current_date - datetime.timedelta(days=120)).strftime('%Y%m%d')
        
        print(f"{current_time} - 尝试获取历史数据，开始日期: {start_date}, 结束日期: {end_date}")
        
        # 获取历史数据，使用正确的成交量字段
        hist = get_price(security, start_date=start_date, end_date=end_date, frequency='1d', fields=['close', 'open', 'volume'], fq='pre')
        
        if hist is None:
            print(f"{current_time} - 无法获取历史数据，返回为空")
            return
        
        print(f"{current_time} - 成功获取历史数据，数据长度: {len(hist)}, 开始日期: {hist.index[0].strftime('%Y-%m-%d')}, 结束日期: {hist.index[-1].strftime('%Y-%m-%d')}")
        
        # 确保有足够的数据计算均线
        if len(hist) < 8:
            print(f"{current_time} - 历史数据不足8天，当前有{len(hist)}天")
            return
        
        # 计算均线
        # 昨日5日均线：前5天收盘
        if len(hist) >= 5:
            yesterday_ma5 = hist['close'][-5:].mean()
        else:
            yesterday_ma5 = current_price
        # 前日5日均线：前6天收盘的最后5天
        if len(hist) >= 6:
            day_before_yesterday_ma5 = hist['close'][-6:-1].mean()
        else:
            day_before_yesterday_ma5 = current_price
        # 前3天5日均线：前7天收盘的最后5天
        if len(hist) >= 7:
            three_days_ago_ma5 = hist['close'][-7:-2].mean()
        else:
            three_days_ago_ma5 = current_price
        # 前4天5日均线：前8天收盘的最后5天
        if len(hist) >= 8:
            four_days_ago_ma5 = hist['close'][-8:-3].mean()
        else:
            four_days_ago_ma5 = current_price
        
        
        # 计算前5日、前10日、前20日和前60日平均成交量
        avg_5d_volume = hist['volume'][-5:].mean()
        avg_20d_volume = hist['volume'][-20:].mean()
        
        print(f"{current_time} - 成功计算技术指标")
    except Exception as e:
        print(f"{current_time} - 无法获取历史数据: {e}")
        import traceback
        print(f"{current_time} - 错误详情: {traceback.format_exc()}")
        return
    
    # 打印技术指标
    print(f"{current_time} - 昨日MA5: {yesterday_ma5:.2f}")
    print(f"{current_time} - 近期成交量热度: {avg_5d_volume/avg_20d_volume:.2f}")
    
    # 检查买入条件
    position = context.portfolio.positions.get(security, None)
    position_amount = position.amount if position else 0
    print(f"{current_time} - 检查买入条件，持仓量: {position_amount}, 上次买入日期: {stock_info['last_buy_date']}")
    
    # 检查今天是否已经买过
    can_buy = True
    if stock_info['last_buy_date'] == current_date:
        print(f"{current_time} - 今天已经买过，跳过买入")
        can_buy = False
    
    # 检查当日是否已执行止损清仓，若是则不再买入
    if stock_info['stop_loss_today']:
        print(f"{current_time} - 当日已执行止损清仓，跳过买入操作")
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
        if len(hist) >= max(m_days, a_days + 1):
            # 计算每天的5日均线
            ma5_list = []
            for i in range(len(hist) - 4):
                ma5 = hist['close'][i:i+5].mean()
                ma5_list.append(ma5)
            
            # 检查前m天的条件1：收盘价-开盘价>0且收盘价-5日均线>0
            # 确保i在ma5_list的有效范围内
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
            # 确保有足够的ma5数据
            if len(ma5_list) >= 2:  # 至少需要2个数据点来计算变化
                # 计算前a天的开始索引，确保不小于0
                start_idx = max(0, len(ma5_list) - a_days - 1)
                end_idx = len(ma5_list) - 1
                for i in range(start_idx, end_idx):
                    if i + 1 < len(ma5_list):
                        if ma5_list[i+1] - ma5_list[i] > 0:
                            condition2_count += 1
        
        # 条件1：前m天中有n天满足收盘价-开盘价>0且收盘价-5日均线>0
        condition1 = condition1_count >= n_days
        
        # 条件2：前a天中有b天满足5日均线-前1天的5日均线>0
        condition2 = condition2_count >= b_days
        
        # 条件3：回踩确认：当日最低价 < 昨日收盘价
        if len(hist) >= 1:
            yesterday_close = hist['close'][-1]
            condition3 = day_low < yesterday_close
        else:
            condition3 = False
        
        # 反弹确认：当前最新价 >= 当日最低价 * (1 + g.rebound_threshold)（反弹0.03%）
        rebound_confirm = current_price >= day_low * (1 + g.rebound_threshold)
        
        # 成交量过滤：前5日均量 / 前20日均量 < 1.25
        volume_filter = avg_5d_volume / avg_20d_volume < g.volume_ratio_threshold
        
        # 资金管理：买入1万元（按规则取整），总持仓成本不超过20万元
        cost_check = stock_info['total_cost'] < g.max_cost
        
        print(f"{current_time} - 买入条件检查:")
        print(f"{current_time} -   条件1: 前{m_days}天中有{n_days}天满足收盘价>开盘价且收盘价>5日均线 = {condition1} (满足天数: {condition1_count}/{m_days})")
        print(f"{current_time} -   条件2: 前{a_days}天中有{b_days}天满足5日均线上升 = {condition2} (满足天数: {condition2_count}/{a_days})")
        print(f"{current_time} -   条件3: 回踩确认（当日最低价 < 昨日收盘价） = {condition3}")
        print(f"{current_time} -   反弹确认={rebound_confirm}")
        print(f"{current_time} -   成交量过滤={volume_filter}")
        print(f"{current_time} -   资金管理={cost_check}")
        if len(hist) >= 1:
            print(f"{current_time} - 价格数据: 当前价格={current_price:.2f}, 当日最低价={day_low:.2f}, 昨日收盘价={yesterday_close:.2f}, 反弹阈值={day_low * (1 + g.rebound_threshold):.2f}")
        else:
            print(f"{current_time} - 价格数据: 当前价格={current_price:.2f}, 当日最低价={day_low:.2f}, 反弹阈值={day_low * (1 + g.rebound_threshold):.2f}")
        print(f"{current_time} - 成交量数据: 前5日均量={avg_5d_volume:.0f}, 前20日均量={avg_20d_volume:.0f}, 近期成交量热度={avg_5d_volume/avg_20d_volume:.2f}")
        
        # 检查当前价格是否小于上次买入价格
        price_check = True
        if stock_info['last_buy_price'] is not None and current_price < stock_info['last_buy_price']:
            price_check = False
            print(f"{current_time} - 当前价格({current_price:.2f})小于上次买入价格({stock_info['last_buy_price']:.2f})，当日不再买入")
        
        if condition1 and condition2 and condition3 and rebound_confirm and volume_filter and cost_check and price_check:
            # 计算买入股数
            if security.endswith('.SS') or security.endswith('.SZ'):
                # A股：向下取整至100股整数倍
                buy_shares = int(g.buy_amount / current_price) // 100 * 100
                if buy_shares < 100:
                    buy_shares = 100
            else:
                # 港股通：按每手100股计算
                buy_shares = int(g.buy_amount / current_price) // 100 * 100
                if buy_shares < 100:
                    buy_shares = 100
            
            # 执行买入
            try:
                print(f"{current_time} - 执行买入: {security}, 股数: {buy_shares}")
                order(security, buy_shares)
                # 更新累计成本
                stock_info['total_cost'] += buy_shares * current_price
                # 计算新的平均成本：(总成本) / (原有持仓 + 新买入量)
                # 避免依赖position对象的实时更新
                position = context.portfolio.positions.get(security, None)
                if position:
                    new_position_amount = position.amount + buy_shares
                    if new_position_amount > 0:
                        stock_info['avg_cost'] = stock_info['total_cost'] / new_position_amount
                else:
                    # 首次买入
                    stock_info['avg_cost'] = current_price
                # 更新上次买入日期和价格
                stock_info['last_buy_date'] = current_date
                stock_info['last_buy_price'] = current_price
                # 更新最高买入价格
                if stock_info['highest_buy_price'] is None or current_price > stock_info['highest_buy_price']:
                    stock_info['highest_buy_price'] = current_price
                # 更新持仓期间最高价（用于计算回撤）
                if stock_info['position_high'] == 0 or current_price > stock_info['position_high']:
                    stock_info['position_high'] = current_price
                # 记录当日买入量
                stock_info['today_buy_amount'] += buy_shares
                # 增加买入次数
                stock_info['buy_count'] += 1
                print(f"{current_time} - 买入成功，累计成本: {stock_info['total_cost']:.2f}, 平均成本: {stock_info['avg_cost']:.2f}, 买入价格: {current_price:.2f}, 最高买入价格: {stock_info['highest_buy_price']:.2f}, 持仓最高价: {stock_info['position_high']:.2f}, 当日买入量: {stock_info['today_buy_amount']}, 买入次数: {stock_info['buy_count']}")
            except Exception as e:
                print(f"{current_time} - 买入失败: {e}")
 
    # # 14:55 执行特殊操作
    # if current_time.hour == 14 and current_time.minute == 55:

        
    #     # 分批止盈检查（满足以下任意一条就卖出一半）
    #     if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0:
    #         position = context.portfolio.positions[security]
    #         print(f"{current_time} - 分批止盈检查开始")
    #         print(f"{current_time} - 持仓信息: 持仓量={position.amount}, 平均成本={position.avg_cost if hasattr(position, 'avg_cost') else 'N/A'}")
            
    #         # 计算当前盈亏率
    #         avg_cost = stock_info['avg_cost']
    #         profit_loss_ratio = (current_price - avg_cost) / avg_cost if avg_cost > 0 else 0
            
    #         # 条件1：放量大涨检查
    #         volume_condition = current_volume > avg_5d_volume * g.sell_volume_ratio
    #         print(f"{current_time} - 成交量条件检查:")
    #         print(f"{current_time} -   当前成交量: {current_volume}")
    #         print(f"{current_time} -   5日均量: {avg_5d_volume}")
    #         print(f"{current_time} -   放量阈值: {avg_5d_volume * g.sell_volume_ratio}")
    #         print(f"{current_time} -   成交量条件: {volume_condition}")
            
    #         # 条件2：盈亏率>15%检查
    #         profit_condition = profit_loss_ratio > g.profit_loss_ratio_take_profit
    #         print(f"{current_time} - 盈亏率条件检查:")
    #         print(f"{current_time} -   当前价格: {current_price}")
    #         print(f"{current_time} -   平均成本: {avg_cost}")
    #         print(f"{current_time} -   盈亏率: {profit_loss_ratio:.2%}")
    #         print(f"{current_time} -   盈亏率阈值: {g.profit_loss_ratio_take_profit:.2%}")
    #         print(f"{current_time} -   盈亏率条件: {profit_condition}")
            
    #         print(f"{current_time} - 止盈条件综合判断: volume_condition={volume_condition}, profit_condition={profit_condition}")
            
    #         # 满足任意一条就卖出一半
    #         if volume_condition or profit_condition:
    #             # 卖出一半
    #             try:
    #                 # 卖出一半
    #                 sell_shares = position.amount // 2
    #                 # 向上补足为100股的整数倍
    #                 if sell_shares % 100 != 0:
    #                     sell_shares = ((sell_shares + 99) // 100) * 100
    #                     print(f"{current_time} - 向上补足为100股整数倍: {sell_shares}")
                    
    #                 print(f"{current_time} - 执行卖出一半操作:")
    #                 print(f"{current_time} -   股票: {security}")
    #                 print(f"{current_time} -   卖出股数: {sell_shares}")
    #                 print(f"{current_time} -   剩余股数: {position.amount - sell_shares}")
                    
    #                 order(security, -sell_shares)
                    
    #                 # 计算当前浮动盈亏
    #                 if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0:
    #                     current_position = context.portfolio.positions[security]
    #                     # 使用全局avg_cost变量，卖出时保持不变
    #                     avg_cost = stock_info['avg_cost']
                        
    #                     current_pnl = current_position.amount * (current_price - avg_cost)
                        
    #                     # 更新total_cost为avg_cost乘以剩余持仓
    #                     stock_info['total_cost'] = avg_cost * current_position.amount
                        
    #                     print(f"{current_time} - 卖出成功后:")
    #                     print(f"{current_time} -   剩余持仓: {current_position.amount}")
    #                     print(f"{current_time} -   平均成本: {avg_cost}")
    #                     print(f"{current_time} -   总持仓成本: {stock_info['total_cost']:.2f}")
    #                     print(f"{current_time} -   浮动盈亏: {current_pnl:.2f}")
    #             except Exception as e:
    #                 print(f"{current_time} - 卖出失败: {e}")
    #                 import traceback
    #                 print(f"{current_time} - 错误详情: {traceback.format_exc()}")
    #         else:
    #             print(f"{current_time} - 止盈条件不满足，跳过卖出操作")
    
    # 做T条件检查
    print(f"{current_time} - 做T条件检查：持仓存在={context.portfolio.positions.get(security, None) is not None}, 持仓量={context.portfolio.positions.get(security, None).amount if context.portfolio.positions.get(security, None) else 0}, 做T标记={stock_info['t_done_today']}")
    if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0 and not stock_info['t_done_today']:
        position = context.portfolio.positions[security]
        
        # 检查当日是否已买入
        print(f"{current_time} - 做T条件检查：last_buy_date={stock_info['last_buy_date']}, current_date={current_date}, today_buy_amount={stock_info['today_buy_amount']}")
        if stock_info['last_buy_date'] == current_date and stock_info['today_buy_amount'] > 0:
            print(f"{current_time} - 做T检查：当日已买入，买入量={stock_info['today_buy_amount']}, 做T标记={stock_info['t_done_today']}")
            
            # 计算单日涨幅（基于昨日收盘价）
            if len(hist) >= 1:
                yesterday_close = hist['close'][-1]
                gain = (current_price / yesterday_close - 1)
                print(f"{current_time} - 做T数据：当前价格={current_price:.2f}, 昨日收盘价={yesterday_close:.2f}, 涨幅={gain:.2%}, 当日最高价={day_high:.2f}")
                
                # 条件1：涨幅大于5%并回落1%
                if gain > g.t_gain_threshold:
                    # 计算回落幅度
                    pullback = (day_high - current_price) / day_high if day_high > 0 else 0
                    print(f"{current_time} - 做T条件1检查：涨幅={gain:.2%} (>5%:{gain > g.t_gain_threshold}), 回落={pullback:.2%} (>1%:{pullback > g.t_pullback_threshold})")
                    
                    if pullback > g.t_pullback_threshold:
                        # 卖出当日买入量，不超过可卖量
                        sell_shares = min(position.amount, stock_info['today_buy_amount'])
                        if sell_shares > 0:
                            print(f"{current_time} - 做T条件1触发：涨幅>5%且回落>1%")
                            print(f"{current_time} - 执行做T卖出：股数={sell_shares}, 当日买入量={stock_info['today_buy_amount']}, 可卖量={position.amount}")
                            # 记录卖出前的持仓量
                            stock_info['last_position_amount'] = position.amount
                            # 提交卖出订单
                            order_id = order(security, -sell_shares)
                            if order_id:
                                # 记录订单信息
                                g.pending_orders[order_id] = {
                                    'type': 't_sell',
                                    'shares': sell_shares,
                                    'price': current_price,
                                    'avg_cost': stock_info['avg_cost']
                                }
                                print(f"{current_time} - 做T卖出订单已提交，订单ID: {order_id}, 计划卖出量：{sell_shares}")
                            # 设置做T标记为True，当日不再执行
                            stock_info['t_done_today'] = True
                    else:
                        print(f"{current_time} - 做T条件1不满足：涨幅>5%但回落<=1%")
                else:
                    print(f"{current_time} - 做T条件1不满足：涨幅<=5%")
                
                # 条件2：14:55 涨幅大于2%（独立检查）
                if current_time.hour == 14 and current_time.minute == 55 and not stock_info['t_done_today']:
                    print(f"{current_time} - 做T条件2检查：涨幅={gain:.2%} (>2%:{gain > g.t_1455_gain_threshold})")
                    if gain > g.t_1455_gain_threshold:
                        # 卖出当日买入量，不超过可卖量
                        sell_shares = min(position.amount, stock_info['today_buy_amount'])
                        if sell_shares > 0:
                            print(f"{current_time} - 做T条件2触发：14:55且涨幅>2%")
                            print(f"{current_time} - 执行做T卖出：股数={sell_shares}, 当日买入量={stock_info['today_buy_amount']}, 可卖量={position.amount}")
                            # 记录卖出前的持仓量
                            stock_info['last_position_amount'] = position.amount
                            # 提交卖出订单
                            order_id = order(security, -sell_shares)
                            if order_id:
                                # 记录订单信息
                                g.pending_orders[order_id] = {
                                    'type': 't_sell',
                                    'shares': sell_shares,
                                    'price': current_price,
                                    'avg_cost': stock_info['avg_cost']
                                }
                                print(f"{current_time} - 做T卖出订单已提交，订单ID: {order_id}, 计划卖出量：{sell_shares}")
                            # 设置做T标记为True，当日不再执行
                            stock_info['t_done_today'] = True
                    else:
                        print(f"{current_time} - 做T条件2不满足：涨幅<=2%")
            else:
                print(f"{current_time} - 做T检查失败：历史数据不足")
        else:
            print(f"{current_time} - 做T检查跳过：当日未买入或买入量为0，买入日期={stock_info['last_buy_date']}, 当日={current_date}, 买入量={stock_info['today_buy_amount']}")
    
    # 实时检查清仓条件（满足以下任意一条就清仓）
    if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0:
        try:
            position = context.portfolio.positions[security]
            # 使用全局avg_cost变量
            avg_cost = stock_info['avg_cost']
            
            # 计算当前盈亏率
            profit_loss_ratio = (avg_cost-current_price ) / avg_cost if avg_cost > 0 else 0
            
            # 更新持仓期间最高价
            if current_price > stock_info['position_high']:
                stock_info['position_high'] = current_price
            
            # 计算从最高点回撤
            drawdown = (stock_info['position_high'] - current_price) / stock_info['position_high'] if stock_info['position_high'] > 0 else 0
            
            # 条件1：股价从最高点回撤5%
            drawdown_condition = drawdown > g.max_drawdown_stop
            
            # 条件2：亏损率大于5%
            stop_loss_condition = profit_loss_ratio > g.profit_loss_ratio_stop_loss
            
            print(f"{current_time} - 清仓条件检查:")
            print(f"{current_time} -   持仓期间最高价: {stock_info['position_high']:.2f}, 当前价格: {current_price:.2f}, 回撤: {drawdown:.2%}")
            print(f"{current_time} -   亏损率: {profit_loss_ratio:.2%}")
            print(f"{current_time} -   回撤条件(>5%): {drawdown_condition}, 止损条件(>5%): {stop_loss_condition}")
            
            # 满足任意一条就清仓
            if drawdown_condition or stop_loss_condition:
                if drawdown_condition:
                    print(f"{current_time} - 触发回撤清仓: 当前价格={current_price:.2f}, 持仓期间最高价={stock_info['position_high']:.2f}, 回撤={drawdown:.2%}")
                if stop_loss_condition:
                    print(f"{current_time} - 触发止损清仓: 当前价格={current_price:.2f}, 平均成本={avg_cost:.2f}, 亏损率={profit_loss_ratio:.2%}")
                # 记录清仓前的持仓量
                stock_info['last_position_amount'] = position.amount
                # 提交清仓订单
                order_id = order_target(security, 0)
                if order_id:
                    # 记录订单信息
                    g.pending_orders[order_id] = {
                        'type': 'clear',
                        'shares': position.amount,
                        'price': current_price,
                        'avg_cost': stock_info['avg_cost']
                    }
                    print(f"{current_time} - 清仓订单已提交，订单ID: {order_id}, 计划清仓量：{position.amount}")
                # 设置做T标记为True，防止重复操作
                stock_info['t_done_today'] = True
        except Exception as e:
            print(f"{current_time} - 清仓检查失败: {e}")
    
    # 收盘时计算并显示总市值、盈亏、盈亏比例、持仓量
    if current_time.hour == 15 and current_time.minute == 0:
        position = context.portfolio.positions.get(security, None)
        if position and position.amount > 0:
            # 计算总市值
            total_value = position.amount * current_price
            # 使用全局avg_cost变量
            position_cost = stock_info['avg_cost']
            # 计算持仓总成本
            total_cost = position_cost * position.amount
            # 计算持仓盈亏
            profit_loss = total_value - total_cost
            # 计算持仓盈亏比例
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
    
    # 更新昨日均线值
    stock_info['yesterday_ma5'] = yesterday_ma5
    # 暂时注释掉60日均线更新
    # stock_info['yesterday_ma60'] = yesterday_ma60