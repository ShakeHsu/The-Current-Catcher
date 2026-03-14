import datetime

def initialize(context):
    # 初始化策略
    g.security = "515180"  # 科创板ETF
    
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
        }
    }
    
    # 策略参数
    g.buy_amount = 10000  # 每次买入目标金额（元）
    g.max_cost = 200000  # 单只股票持仓成本上限（元）
    g.volume_ratio_threshold = 1.3  # 买入时成交量过滤阈值
    g.sell_volume_ratio = 1.3  # 卖出时放量阈值
    g.sell_gain_threshold = 0.03  # 卖出时涨幅阈值
    g.rebound_threshold = 0.0003  # 反弹阈值（0.03%）
    g.profit_loss_ratio_stop = -0.1  # 盈亏率止损阈值：-10%
    g.entry_drawdown_tolerance = -0.05  # 建仓回撤容忍度：-5%
    
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
    
    # 监控当日最低价（从开盘开始）
    if hasattr(data[security], 'low'):
        current_low = data[security].low
        # 检查是否是新的一天
        if stock_info['last_date'] != current_date:
            # 新的一天，重置当日最低价
            stock_info['day_low'] = current_low
            print(f"{current_time} - 新的一天，初始化当日最低价: {current_low}")
        else:
            # 更新当日最低价
            if stock_info['day_low'] is None or current_low < stock_info['day_low']:
                stock_info['day_low'] = current_low
                print(f"{current_time} - 更新当日最低价: {current_low}")
        day_low = stock_info['day_low']
    else:
        # 如果无法获取最低价，使用当前价格作为最低价
        day_low = current_price
        if stock_info['day_low'] is None:
            stock_info['day_low'] = day_low
    
    print(f"{current_time} - 当日最低价: {day_low}")
    
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
        hist = get_price(security, start_date=start_date, end_date=end_date, frequency='1d', fields=['close', 'volume'], fq='pre')
        
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
    
    # 加强趋势确认：前1天5日均线-前2天均线、前2天5日均线-前3天均线、前3天5日均线-前4天均线，这三个数至少有2个大于等于0
    diff1 = yesterday_ma5 - day_before_yesterday_ma5  # 前1天 - 前2天
    diff2 = day_before_yesterday_ma5 - three_days_ago_ma5  # 前2天 - 前3天
    diff3 = three_days_ago_ma5 - four_days_ago_ma5  # 前3天 - 前4天
    positive_count = sum(1 for diff in [diff1, diff2, diff3] if diff >= 0)
    trend_confirm = positive_count >= 2
    # 回踩确认：当日最低价 < 昨日5日均线
    pullback_confirm = day_low < yesterday_ma5
    # 反弹确认：当前最新价 >= 当日最低价 * (1 + g.rebound_threshold)（反弹0.03%）
    rebound_confirm = current_price >= day_low * (1 + g.rebound_threshold)
    # 成交量过滤：前5日均量 / 前20日均量 < 1.25
    volume_filter = avg_5d_volume / avg_20d_volume < g.volume_ratio_threshold
    # 资金管理：买入1万元（按规则取整），总持仓成本不超过20万元
    cost_check = stock_info['total_cost'] < g.max_cost
    # 建仓回撤容忍度：最新价格 > 最高买入价格 * (1 + 建仓回撤容忍度)
    # 首次买入时，highest_buy_price为None，默认为True
    if stock_info['highest_buy_price'] is not None:
        entry_drawdown_check = current_price > stock_info['highest_buy_price'] * (1 + g.entry_drawdown_tolerance)
    else:
        entry_drawdown_check = True
    
    print(f"{current_time} - 买入条件检查:")
    print(f"{current_time} -   趋势确认={trend_confirm} (满足条件数: {positive_count}/3)")
    print(f"{current_time} -   回踩确认={pullback_confirm}")
    print(f"{current_time} -   反弹确认={rebound_confirm}")
    print(f"{current_time} -   成交量过滤={volume_filter}")
    print(f"{current_time} -   资金管理={cost_check}")
    print(f"{current_time} -   建仓回撤容忍度={entry_drawdown_check}")
    print(f"{current_time} - 均线数据: 昨日MA5={yesterday_ma5:.2f}, 前日MA5={day_before_yesterday_ma5:.2f}, 前3天MA5={three_days_ago_ma5:.2f}, 前4天MA5={four_days_ago_ma5:.2f}")
    print(f"{current_time} - 均线差值: 前1-前2={diff1:.4f}, 前2-前3={diff2:.4f}, 前3-前4={diff3:.4f}")
    print(f"{current_time} - 价格数据: 当前价格={current_price:.2f}, 当日最低价={day_low:.2f}, 反弹阈值={day_low * (1 + g.rebound_threshold):.2f}")
    if stock_info['highest_buy_price'] is not None:
        print(f"{current_time} - 建仓回撤容忍度: 当前价格={current_price:.2f}, 最高买入价格={stock_info['highest_buy_price']:.2f}, 容忍度阈值={stock_info['highest_buy_price'] * (1 + g.entry_drawdown_tolerance):.2f}")
    print(f"{current_time} - 成交量数据: 前5日均量={avg_5d_volume:.0f}, 前20日均量={avg_20d_volume:.0f}, 近期成交量热度={avg_5d_volume/avg_20d_volume:.2f}")
    
    if trend_confirm and pullback_confirm and rebound_confirm and volume_filter and cost_check and entry_drawdown_check:
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
            print(f"{current_time} - 买入成功，累计成本: {stock_info['total_cost']:.2f}, 平均成本: {stock_info['avg_cost']:.2f}, 买入价格: {current_price:.2f}, 最高买入价格: {stock_info['highest_buy_price']:.2f}")
        except Exception as e:
            print(f"{current_time} - 买入失败: {e}")
    
    # 14:55 执行特殊操作
    if current_time.hour == 14 and current_time.minute == 55:
        # 趋势清仓暂时不用
        # if yesterday_ma60 <= day_before_yesterday_ma60:
        #     if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0:
        #         try:
        #             order_target(security, 0)
        #             stock_info['highest_buy_price'] = None
        #             stock_info['stop_loss_today'] = True  # 标记当日已执行止损清仓
        #         except:
        #             pass
        #         return
        
        # 分批止盈检查
        if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0:
            position = context.portfolio.positions[security]
            print(f"{current_time} - 分批止盈检查开始")
            print(f"{current_time} - 持仓信息: 持仓量={position.amount}, 平均成本={position.avg_cost if hasattr(position, 'avg_cost') else 'N/A'}")
            
            # 放量大涨检查
            volume_condition = current_volume > avg_5d_volume * g.sell_volume_ratio
            print(f"{current_time} - 成交量条件检查:")
            print(f"{current_time} -   当前成交量: {current_volume}")
            print(f"{current_time} -   5日均量: {avg_5d_volume}")
            print(f"{current_time} -   放量阈值: {avg_5d_volume * g.sell_volume_ratio}")
            print(f"{current_time} -   成交量条件: {volume_condition}")
            
            # 使用历史数据获取昨日收盘价
            print(f"{current_time} - 历史数据检查:")
            print(f"{current_time} -   历史数据长度: {len(hist)}")
            print(f"{current_time} -   昨日收盘价: {hist['close'][-1]}")
            
            if len(hist) >= 1:
                yesterday_close = hist['close'][-1]
                gain_condition = (current_price / yesterday_close - 1) > g.sell_gain_threshold
                print(f"{current_time} - 涨幅条件检查:")
                print(f"{current_time} -   当前价格: {current_price}")
                print(f"{current_time} -   昨日收盘价: {yesterday_close}")
                print(f"{current_time} -   涨幅: {(current_price / yesterday_close - 1):.4f}")
                print(f"{current_time} -   涨幅阈值: {g.sell_gain_threshold}")
                print(f"{current_time} -   涨幅条件: {gain_condition}")
            else:
                gain_condition = False
                print(f"{current_time} - 历史数据不足，无法计算涨幅")
            
            print(f"{current_time} - 止盈条件综合判断: volume_condition={volume_condition}, gain_condition={gain_condition}")
            
            if volume_condition and gain_condition:
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
    
    # 实时检查止损条件
    if context.portfolio.positions.get(security, None) is not None and context.portfolio.positions[security].amount > 0:
        try:
            position = context.portfolio.positions[security]
            # 使用全局avg_cost变量
            avg_cost = stock_info['avg_cost']
            
            # 计算当前浮动盈亏
            current_pnl = position.amount * (current_price - avg_cost)
            
            # 触发止损清仓：当最新价<持仓成本*（1+盈亏率止损阈值）时，清仓
            stop_loss_price = avg_cost * (1 + g.profit_loss_ratio_stop)
            if current_price < stop_loss_price:
                print(f"{current_time} - 触发止损清仓: 当前价格={current_price:.2f}, 止损价格={stop_loss_price:.2f}")
                order_target(security, 0)
                stock_info['total_cost'] = 0
                stock_info['highest_buy_price'] = None
                stock_info['stop_loss_today'] = True  # 标记当日已执行止损清仓
        except Exception as e:
            print(f"{current_time} - 止损检查失败: {e}")
    
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