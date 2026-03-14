import datetime

def initialize(context):
    # 初始化策略
    g.security = "159206.SZ"  # 卫星ETF
    
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
            'close_prices': [],  # 存储收盘价
            'volume_values': [],  # 存储成交量
            'daily_volume': 0,  # 当日累计成交量
            'last_date': None,  # 上次处理的日期
            'day_low': None,  # 当日最低价（从开盘开始监控）
            'today_buy_amount': 0,  # 当日买入量
            'day_high': 0,  # 当日最高价
            'buy_count': 0,  # 买入次数
            't_done_today': False,  # 当日是否已执行做T
            'position_high': 0,  # 持仓期间最高价（用于计算回撤）
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
    g.profit_loss_ratio_stop_loss = -0.05  # 盈亏率止损阈值：-5%
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
        
        # 暂时注释掉60日均线计算
        # # 计算60日均线
        # # 今日60日均线：前59天收盘 + 今天最新价
        # if len(hist) >= 59:
        #     ma60 = (hist['close'][-59:].sum() + current_price) / 60
        # else:
        #     ma60 = current_price
        # # 昨日60日均线：前60天收盘
        # if len(hist) >= 60:
        #     yesterday_ma60 = hist['close'][-60:].mean()
        # else:
        #     yesterday_ma60 = current_price
        # # 前日60日均线：前61天收盘的最后60天
        # if len(hist) >= 61:
        #     day_before_yesterday_ma60 = hist['close'][-61:-1].mean()
        # else:
        #     day_before_yesterday_ma60 = current_price
        # 暂时设置默认值
        # 删除60日均线相关变量赋值
        
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
    print(f"{current_time} - 检查买入条件，持仓量: {position_amount}, last_buy_date: {stock_info['last_buy_date']}, current_date: {current_date}")
    # 检查今天是否已经买过
    if stock_info['last_buy_date'] == current_date:
        print(f"{current_time} - 今天已经买过，跳过")
        return
    
    # 检查当日是否已执行止损清仓，若是则不再买入
    if stock_info['stop_loss_today']:
        print(f"{current_time} - 当日已执行止损清仓，跳过买入操作")
        return
    
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
            # 更新平均成本：总成本 / 总持仓
            position = context.portfolio.positions.get(security, None)
            if position and position.amount > 0:
                stock_info['avg_cost'] = stock_info['total_cost'] / position.amount
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
    
    # 14:55 执行特殊操作
    if current_time.hour == 14 and current_time.minute == 55:

        
        # 分批止盈检查（满足以下任意一条就卖出一半）
        if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0:
            position = context.portfolio.positions[security]
            print(f"{current_time} - 分批止盈检查开始")
            print(f"{current_time} - 持仓信息: 持仓量={position.amount}, 平均成本={position.avg_cost if hasattr(position, 'avg_cost') else 'N/A'}")
            
            # 计算当前盈亏率
            avg_cost = stock_info['avg_cost']
            profit_loss_ratio = (current_price - avg_cost) / avg_cost if avg_cost > 0 else 0
            
            # 条件1：放量大涨检查
            volume_condition = current_volume > avg_5d_volume * g.sell_volume_ratio
            print(f"{current_time} - 成交量条件检查:")
            print(f"{current_time} -   当前成交量: {current_volume}")
            print(f"{current_time} -   5日均量: {avg_5d_volume}")
            print(f"{current_time} -   放量阈值: {avg_5d_volume * g.sell_volume_ratio}")
            print(f"{current_time} -   成交量条件: {volume_condition}")
            
            # 条件2：盈亏率>15%检查
            profit_condition = profit_loss_ratio > g.profit_loss_ratio_take_profit
            print(f"{current_time} - 盈亏率条件检查:")
            print(f"{current_time} -   当前价格: {current_price}")
            print(f"{current_time} -   平均成本: {avg_cost}")
            print(f"{current_time} -   盈亏率: {profit_loss_ratio:.2%}")
            print(f"{current_time} -   盈亏率阈值: {g.profit_loss_ratio_take_profit:.2%}")
            print(f"{current_time} -   盈亏率条件: {profit_condition}")
            
            print(f"{current_time} - 止盈条件综合判断: volume_condition={volume_condition}, profit_condition={profit_condition}")
            
            # 满足任意一条就卖出一半
            if volume_condition or profit_condition:
                # 卖出一半
                try:
                    # 卖出一半
                    sell_shares = position.amount // 2
                    # 向上补足为100股的整数倍
                    if sell_shares % 100 != 0:
                        sell_shares = ((sell_shares + 99) // 100) * 100
                        print(f"{current_time} - 向上补足为100股整数倍: {sell_shares}")
                    
                    print(f"{current_time} - 执行卖出一半操作:")
                    print(f"{current_time} -   股票: {security}")
                    print(f"{current_time} -   卖出股数: {sell_shares}")
                    print(f"{current_time} -   剩余股数: {position.amount - sell_shares}")
                    
                    order(security, -sell_shares)
                    
                    # 计算当前浮动盈亏
                    if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0:
                        current_position = context.portfolio.positions[security]
                        # 使用全局avg_cost变量，卖出时保持不变
                        avg_cost = stock_info['avg_cost']
                        
                        current_pnl = current_position.amount * (current_price - avg_cost)
                        
                        # 更新total_cost为avg_cost乘以剩余持仓
                        stock_info['total_cost'] = avg_cost * current_position.amount
                        
                        print(f"{current_time} - 卖出成功后:")
                        print(f"{current_time} -   剩余持仓: {current_position.amount}")
                        print(f"{current_time} -   平均成本: {avg_cost}")
                        print(f"{current_time} -   总持仓成本: {stock_info['total_cost']:.2f}")
                        print(f"{current_time} -   浮动盈亏: {current_pnl:.2f}")
                except Exception as e:
                    print(f"{current_time} - 卖出失败: {e}")
                    import traceback
                    print(f"{current_time} - 错误详情: {traceback.format_exc()}")
            else:
                print(f"{current_time} - 止盈条件不满足，跳过卖出操作")
    
    # 做T条件检查
    if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0 and not stock_info['t_done_today']:
        position = context.portfolio.positions[security]
        # 做T条件1：当日已买入，单日涨幅>5%且回落1%
        if stock_info['last_buy_date'] == current_date and stock_info['today_buy_amount'] > 0:
            # 计算单日涨幅（基于昨日收盘价）
            if len(hist) >= 1:
                yesterday_close = hist['close'][-1]
                gain = (current_price / yesterday_close - 1)
                # 计算回落幅度
                pullback = (day_high - current_price) / day_high if day_high > 0 else 0
                
                print(f"{current_time} - 做T条件1检查: 单日涨幅={gain:.2%}, 回落={pullback:.2%}, 当日买入量={stock_info['today_buy_amount']}, 做T标记={stock_info['t_done_today']}")
                if gain > g.t_gain_threshold and pullback > g.t_pullback_threshold:
                    # 卖出当日买入量，不超过可卖量
                    sell_shares = min(position.amount, stock_info['today_buy_amount'])
                    if sell_shares > 0:
                        print(f"{current_time} - 做T条件1触发: 单日涨幅={gain:.2%}, 回落={pullback:.2%}")
                        print(f"{current_time} - 执行做T卖出: 股数={sell_shares}, 当日买入量={stock_info['today_buy_amount']}, 可卖量={position.amount}")
                        order(security, -sell_shares)
                        # 更新当日买入量
                        stock_info['today_buy_amount'] -= sell_shares
                        # 设置做T标记为True
                        stock_info['t_done_today'] = True
                        print(f"{current_time} - 做T卖出成功，剩余当日买入量: {stock_info['today_buy_amount']}, 做T标记: {stock_info['t_done_today']}")
        
        # 做T条件2：14:55涨幅>2%
        if current_time.hour == 14 and current_time.minute == 55 and not stock_info['t_done_today']:
            if len(hist) >= 1:
                yesterday_close = hist['close'][-1]
                gain = (current_price / yesterday_close - 1)
                print(f"{current_time} - 做T条件2检查: 涨幅={gain:.2%}, 当日买入量={stock_info['today_buy_amount']}, 做T标记={stock_info['t_done_today']}")
                if gain > g.t_1455_gain_threshold and stock_info['today_buy_amount'] > 0:
                    # 卖出当日买入量，不超过可卖量
                    sell_shares = min(position.amount, stock_info['today_buy_amount'])
                    if sell_shares > 0:
                        print(f"{current_time} - 做T条件2触发: 涨幅={gain:.2%}")
                        print(f"{current_time} - 执行做T卖出: 股数={sell_shares}, 当日买入量={stock_info['today_buy_amount']}, 可卖量={position.amount}")
                        order(security, -sell_shares)
                        # 更新当日买入量
                        stock_info['today_buy_amount'] -= sell_shares
                        # 设置做T标记为True
                        stock_info['t_done_today'] = True
                        print(f"{current_time} - 做T卖出成功，剩余当日买入量: {stock_info['today_buy_amount']}, 做T标记: {stock_info['t_done_today']}")
    
    # 实时检查清仓条件（满足以下任意一条就清仓）
    if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0:
        try:
            position = context.portfolio.positions[security]
            # 使用全局avg_cost变量
            avg_cost = stock_info['avg_cost']
            
            # 计算当前盈亏率
            profit_loss_ratio = (current_price - avg_cost) / avg_cost if avg_cost > 0 else 0
            
            # 更新持仓期间最高价
            if current_price > stock_info['position_high']:
                stock_info['position_high'] = current_price
            
            # 计算从最高点回撤
            drawdown = (stock_info['position_high'] - current_price) / stock_info['position_high'] if stock_info['position_high'] > 0 else 0
            
            # 条件1：股价从最高点回撤5%
            drawdown_condition = drawdown > g.max_drawdown_stop
            
            # 条件2：盈亏率小于-5%
            stop_loss_condition = profit_loss_ratio < g.profit_loss_ratio_stop_loss
            
            print(f"{current_time} - 清仓条件检查:")
            print(f"{current_time} -   持仓最高价: {stock_info['position_high']:.2f}, 当前价格: {current_price:.2f}, 回撤: {drawdown:.2%}")
            print(f"{current_time} -   盈亏率: {profit_loss_ratio:.2%}")
            print(f"{current_time} -   回撤条件(>5%): {drawdown_condition}, 止损条件(<-5%): {stop_loss_condition}")
            
            # 满足任意一条就清仓
            if drawdown_condition or stop_loss_condition:
                if drawdown_condition:
                    print(f"{current_time} - 触发回撤清仓: 当前价格={current_price:.2f}, 持仓最高价={stock_info['position_high']:.2f}, 回撤={drawdown:.2%}")
                if stop_loss_condition:
                    print(f"{current_time} - 触发止损清仓: 当前价格={current_price:.2f}, 平均成本={avg_cost:.2f}, 盈亏率={profit_loss_ratio:.2%}")
                order_target(security, 0)
                stock_info['total_cost'] = 0
                stock_info['highest_buy_price'] = None
                stock_info['position_high'] = 0  # 重置持仓最高价
                stock_info['stop_loss_today'] = True  # 标记当日已执行止损清仓
                stock_info['buy_count'] = 0  # 重置买入次数
        except Exception as e:
            print(f"{current_time} - 清仓检查失败: {e}")
    
    # 每次调用都更新close_prices列表，确保数据准确性
    stock_info['close_prices'].append(current_price)
    # 保持列表长度合理
    if len(stock_info['close_prices']) > 20:
        stock_info['close_prices'] = stock_info['close_prices'][-20:]
    print(f"{current_time} - 更新close_prices列表，长度: {len(stock_info['close_prices'])}")
    
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
            # 计算盈亏
            profit_loss = total_value - total_cost
            # 计算盈亏比例
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
    
    # 更新昨日均线值
    stock_info['yesterday_ma5'] = yesterday_ma5
    # 暂时注释掉60日均线更新
    # stock_info['yesterday_ma60'] = yesterday_ma60