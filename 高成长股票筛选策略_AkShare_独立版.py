import datetime
import pandas as pd
import akshare as ak
import os
import time

class GlobalVars:
    """全局变量类"""
    def __init__(self):
        # 筛选参数
        self.max_market_cap = 100 * 100000000  # 市值小于100亿
        self.max_total_shares = 2 * 100000000  # 股本小于2亿
        self.max_listing_years = 4  # 上市时间小于4年
        self.min_gross_margin = 0.40  # 毛利率高于40%
        self.min_rd_ratio = 0.15  # 研发投入占营收15%以上
        self.min_growth_rate = 0.20  # 业绩增速20%以上
        
        # 输出设置
        self.output_format = 'detailed'  # 输出格式：'simple'或'detailed'
        self.excel_output = True  # 是否导出Excel
        self.excel_path = os.path.join(os.path.dirname(__file__), '高成长股票筛选结果.xlsx')
        
        # 存储筛选结果
        self.filtered_stocks = []

def get_a_stock_list():
    """获取A股股票列表"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用AkShare获取A股股票列表
            stock_info = ak.stock_info_a_code_name()
            stocks = stock_info['code'].tolist()
            return stocks
        except Exception as e:
            print(f"[{datetime.datetime.now()}] 获取A股列表失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return []

def get_hk_stock_list():
    """获取港股通股票列表"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用AkShare获取港股通股票列表
            # 尝试不同的函数名
            try:
                hk_stock_info = ak.stock_hk_hold_stock互联互通标的()
            except:
                try:
                    hk_stock_info = ak.stock_hk_hold_stock()
                except:
                    hk_stock_info = ak.stock_hk_spot()
            
            # 提取股票代码
            if '代码' in hk_stock_info.columns:
                hk_stocks = hk_stock_info['代码'].tolist()
            elif 'symbol' in hk_stock_info.columns:
                hk_stocks = hk_stock_info['symbol'].tolist()
            else:
                # 如果无法获取港股通列表，返回空列表
                return []
            
            # 筛选港股通股票（通常以.HK结尾）
            hk_stocks = [stock for stock in hk_stocks if isinstance(stock, str) and stock.endswith('.HK')]
            return hk_stocks
        except Exception as e:
            print(f"[{datetime.datetime.now()}] 获取港股通列表失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return []

def get_stock_basic_info(security):
    """获取股票基本信息"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用AkShare获取股票基本信息
            # 对于A股
            if security.startswith(('6', '0', '3')) and len(security) == 6:
                # 获取上市日期
                stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
                stock_data = stock_zh_a_spot_em_df[stock_zh_a_spot_em_df['代码'] == security]
                if not stock_data.empty:
                    name = stock_data['名称'].iloc[0]
                    # 尝试获取上市日期
                    try:
                        stock_info = ak.stock_info_company_info_em(symbol=security)
                        start_date = stock_info.get('上市日期', None)
                    except:
                        start_date = None
                    return {
                        'code': security,
                        'name': name,
                        'start_date': start_date,
                    }
            # 对于港股
            elif security.endswith('.HK'):
                try:
                    stock_hk_spot_df = ak.stock_hk_spot()
                    stock_data = stock_hk_spot_df[stock_hk_spot_df['代码'] == security]
                    if not stock_data.empty:
                        name = stock_data['名称'].iloc[0]
                        return {
                            'code': security,
                            'name': name,
                            'start_date': None,  # AkShare可能无法直接获取港股上市日期
                        }
                except:
                    pass
            return None
        except Exception as e:
            print(f"[{datetime.datetime.now()}] 获取{security}基本信息失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return None

def get_market_cap(security, date):
    """获取市值"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用AkShare获取市值
            if security.startswith(('6', '0', '3')) and len(security) == 6:
                stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
                stock_data = stock_zh_a_spot_em_df[stock_zh_a_spot_em_df['代码'] == security]
                if not stock_data.empty:
                    # 获取市值（亿元）并转换为元
                    market_cap = stock_data['总市值'].iloc[0] * 100000000
                    return market_cap
            return None
        except Exception as e:
            print(f"[{datetime.datetime.now()}] 获取{security}市值失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return None

def get_total_shares(security, date):
    """获取总股本"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用AkShare获取总股本
            if security.startswith(('6', '0', '3')) and len(security) == 6:
                stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
                stock_data = stock_zh_a_spot_em_df[stock_zh_a_spot_em_df['代码'] == security]
                if not stock_data.empty:
                    # 获取总股本（亿股）并转换为股
                    total_shares = stock_data['总股本'].iloc[0] * 100000000
                    return total_shares
            return None
        except Exception as e:
            print(f"[{datetime.datetime.now()}] 获取{security}股本失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return None

def get_listing_years(security, current_date):
    """获取上市年限"""
    try:
        info = get_stock_basic_info(security)
        if info is None or info['start_date'] is None:
            return None
        
        start_date = info['start_date']
        if isinstance(start_date, str):
            try:
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            except:
                return None
        elif isinstance(start_date, datetime.datetime):
            start_date = start_date.date()
        
        years = (current_date - start_date).days / 365.25
        return years
    except Exception as e:
        print(f"[{datetime.datetime.now()}] 获取{security}上市时间失败: {e}")
        return None

def get_gross_margin(security, date):
    """获取毛利率"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用AkShare获取财务数据
            if security.startswith(('6', '0', '3')) and len(security) == 6:
                # 获取最新的财务数据
                stock_financial_analysis_indicator_df = ak.stock_financial_analysis_indicator(symbol=security)
                if not stock_financial_analysis_indicator_df.empty:
                    # 获取最新的毛利率数据
                    gross_margin = stock_financial_analysis_indicator_df['毛利率'].iloc[0]
                    if not pd.isna(gross_margin):
                        # 确保返回的是小数形式
                        if gross_margin > 1:
                            return gross_margin / 100
                        return gross_margin
            return None
        except Exception as e:
            print(f"[{datetime.datetime.now()}] 获取{security}毛利率失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return None

def get_rd_ratio(security, date):
    """获取研发投入占营收比例"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用AkShare获取财务数据
            if security.startswith(('6', '0', '3')) and len(security) == 6:
                # 获取利润表数据
                stock_profit_statement_df = ak.stock_profit_statement(symbol=security)
                if not stock_profit_statement_df.empty:
                    # 获取最新的研发费用和营收
                    latest_data = stock_profit_statement_df.iloc[0]
                    revenue = latest_data.get('营业总收入', None)
                    rd_expense = latest_data.get('研发费用', None)
                    
                    if revenue is not None and rd_expense is not None and not pd.isna(revenue) and not pd.isna(rd_expense) and revenue != 0:
                        return rd_expense / revenue
            return None
        except Exception as e:
            print(f"[{datetime.datetime.now()}] 获取{security}研发投入比例失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return None

def get_revenue_growth(security, date):
    """获取营收增速"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用AkShare获取财务数据
            if security.startswith(('6', '0', '3')) and len(security) == 6:
                # 获取财务指标数据
                stock_financial_analysis_indicator_df = ak.stock_financial_analysis_indicator(symbol=security)
                if not stock_financial_analysis_indicator_df.empty:
                    # 获取最新的营收增速数据
                    revenue_growth = stock_financial_analysis_indicator_df['营业收入同比增长率'].iloc[0]
                    if not pd.isna(revenue_growth):
                        # 确保返回的是小数形式
                        if revenue_growth > 1:
                            return revenue_growth / 100
                        return revenue_growth
            return None
        except Exception as e:
            print(f"[{datetime.datetime.now()}] 获取{security}营收增速失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return None

def get_profit_growth(security, date):
    """获取归母净利润增速"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 使用AkShare获取财务数据
            if security.startswith(('6', '0', '3')) and len(security) == 6:
                # 获取财务指标数据
                stock_financial_analysis_indicator_df = ak.stock_financial_analysis_indicator(symbol=security)
                if not stock_financial_analysis_indicator_df.empty:
                    # 获取最新的净利润增速数据
                    profit_growth = stock_financial_analysis_indicator_df['净利润同比增长率'].iloc[0]
                    if not pd.isna(profit_growth):
                        # 确保返回的是小数形式
                        if profit_growth > 1:
                            return profit_growth / 100
                        return profit_growth
            return None
        except Exception as e:
            print(f"[{datetime.datetime.now()}] 获取{security}净利润增速失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                return None

def filter_stock(security, current_date, g):
    """筛选单个股票"""
    result = {
        'code': security,
        'passed': True,
        'reasons': [],
        'data': {}
    }
    
    # 获取基本信息
    basic_info = get_stock_basic_info(security)
    if basic_info is None:
        result['passed'] = False
        result['reasons'].append('无法获取基本信息')
        return result
    
    result['data']['name'] = basic_info['name']
    
    # 条件1：市值 < 100亿
    market_cap = get_market_cap(security, current_date)
    if market_cap is None:
        result['passed'] = False
        result['reasons'].append('无法获取市值数据')
        return result
    
    result['data']['market_cap'] = market_cap
    if market_cap >= g.max_market_cap:
        result['passed'] = False
        result['reasons'].append(f'市值{market_cap/100000000:.2f}亿 >= 100亿')
    
    # 条件2：股本 < 2亿
    total_shares = get_total_shares(security, current_date)
    if total_shares is None:
        result['passed'] = False
        result['reasons'].append('无法获取股本数据')
        return result
    
    result['data']['total_shares'] = total_shares
    if total_shares >= g.max_total_shares:
        result['passed'] = False
        result['reasons'].append(f'股本{total_shares/100000000:.2f}亿 >= 2亿')
    
    # 条件3：上市时间 < 4年
    listing_years = get_listing_years(security, current_date)
    if listing_years is None:
        result['passed'] = False
        result['reasons'].append('无法获取上市时间')
        return result
    
    result['data']['listing_years'] = listing_years
    if listing_years >= g.max_listing_years:
        result['passed'] = False
        result['reasons'].append(f'上市时间{listing_years:.2f}年 >= 4年')
    
    # 条件4：毛利率 > 40%
    gross_margin = get_gross_margin(security, current_date)
    if gross_margin is None:
        result['passed'] = False
        result['reasons'].append('无法获取毛利率数据')
        return result
    
    result['data']['gross_margin'] = gross_margin
    if gross_margin <= g.min_gross_margin:
        result['passed'] = False
        result['reasons'].append(f'毛利率{gross_margin*100:.2f}% <= 40%')
    
    # 条件5：研发投入/营收 > 15%
    rd_ratio = get_rd_ratio(security, current_date)
    if rd_ratio is None:
        result['passed'] = False
        result['reasons'].append('无法获取研发投入数据')
        return result
    
    result['data']['rd_ratio'] = rd_ratio
    if rd_ratio <= g.min_rd_ratio:
        result['passed'] = False
        result['reasons'].append(f'研发投入占比{rd_ratio*100:.2f}% <= 15%')
    
    # 条件6：营收增速 > 20% 或 归母净利润增速 > 20%
    revenue_growth = get_revenue_growth(security, current_date)
    profit_growth = get_profit_growth(security, current_date)
    
    result['data']['revenue_growth'] = revenue_growth
    result['data']['profit_growth'] = profit_growth
    
    revenue_pass = revenue_growth is not None and revenue_growth > g.min_growth_rate
    profit_pass = profit_growth is not None and profit_growth > g.min_growth_rate
    
    if not revenue_pass and not profit_pass:
        result['passed'] = False
        revenue_str = f'{revenue_growth*100:.2f}%' if revenue_growth else 'N/A'
        profit_str = f'{profit_growth*100:.2f}%' if profit_growth else 'N/A'
        result['reasons'].append(f'营收增速{revenue_str} <= 20% 且 净利润增速{profit_str} <= 20%')
    
    return result

def export_to_excel(filtered_stocks, excel_path):
    """导出筛选结果到Excel"""
    try:
        if not filtered_stocks:
            print("没有符合条件的股票，无法导出Excel")
            return
        
        # 准备导出数据
        export_data = []
        for stock in filtered_stocks:
            data = stock['data']
            export_data.append({
                '代码': stock['code'],
                '名称': data['name'],
                '市值(亿)': data['market_cap']/100000000,
                '股本(亿)': data['total_shares']/100000000,
                '上市年限': data['listing_years'],
                '毛利率(%)': data['gross_margin']*100,
                '研发占比(%)': data['rd_ratio']*100,
                '营收增速(%)': data['revenue_growth']*100 if data['revenue_growth'] else None,
                '利润增速(%)': data['profit_growth']*100 if data['profit_growth'] else None
            })
        
        # 创建DataFrame
        df = pd.DataFrame(export_data)
        
        # 导出到Excel
        df.to_excel(excel_path, index=False, encoding='utf-8')
        print(f"筛选结果已导出到: {excel_path}")
    except Exception as e:
        print(f"导出Excel失败: {e}")

def main():
    """主函数"""
    # 初始化全局变量
    g = GlobalVars()
    
    print(f"[{datetime.datetime.now()}] 高成长股票筛选策略（AkShare版）初始化完成")
    print(f"[{datetime.datetime.now()}] 筛选条件：")
    print(f"[{datetime.datetime.now()}]   - 市值 < 100亿")
    print(f"[{datetime.datetime.now()}]   - 股本 < 2亿")
    print(f"[{datetime.datetime.now()}]   - 上市时间 < 4年")
    print(f"[{datetime.datetime.now()}]   - 毛利率 > 40%")
    print(f"[{datetime.datetime.now()}]   - 研发投入/营收 > 15%")
    print(f"[{datetime.datetime.now()}]   - 营收增速 > 20% 或 归母净利润增速 > 20%")
    
    current_time = datetime.datetime.now()
    current_date = current_time.date()
    
    print(f"\n[{current_time}] 开始执行高成长股票筛选...")
    
    # 获取A股和港股通股票列表
    a_stocks = get_a_stock_list()
    hk_stocks = get_hk_stock_list()
    all_stocks = list(set(a_stocks + hk_stocks))
    
    print(f"[{current_time}] 共获取{len(all_stocks)}只股票（A股{len(a_stocks)}只，港股通{len(hk_stocks)}只）")
    
    # 筛选符合条件的股票
    filtered_stocks = []
    failed_stocks = []
    
    total = len(all_stocks)
    # 限制处理数量，避免运行时间过长
    max_stocks = 1000  # 最多处理1000只股票
    processed_stocks = all_stocks[:max_stocks]
    
    print(f"[{current_time}] 开始筛选，共处理{len(processed_stocks)}只股票")
    
    for i, security in enumerate(processed_stocks):
        if i % 100 == 0:
            print(f"[{current_time}] 正在筛选... ({i}/{len(processed_stocks)})")
        
        result = filter_stock(security, current_date, g)
        
        if result['passed']:
            filtered_stocks.append(result)
        else:
            failed_stocks.append(result)
    
    # 输出筛选结果
    print(f"\n[{current_time}] 筛选完成！")
    print(f"[{current_time}] 符合条件的股票：{len(filtered_stocks)}只")
    print(f"[{current_time}] 不符合条件的股票：{len(failed_stocks)}只")
    
    if filtered_stocks:
        print(f"\n[{current_time}] 符合条件的股票列表：")
        print("-" * 120)
        
        if g.output_format == 'detailed':
            # 详细输出
            print(f"{'代码':<12} {'名称':<12} {'市值(亿)':<12} {'股本(亿)':<10} {'上市年限':<10} {'毛利率':<10} {'研发占比':<10} {'营收增速':<10} {'利润增速':<10}")
            print("-" * 120)
            
            for stock in filtered_stocks:
                data = stock['data']
                print(f"{stock['code']:<12} {data['name']:<12} {data['market_cap']/100000000:<12.2f} {data['total_shares']/100000000:<10.2f} {data['listing_years']:<10.2f} {data['gross_margin']*100:<10.2f}% {data['rd_ratio']*100:<10.2f}% ", end='')
                
                if data['revenue_growth']:
                    print(f"{data['revenue_growth']*100:<10.2f}% ", end='')
                else:
                    print(f"{'N/A':<10} ", end='')
                
                if data['profit_growth']:
                    print(f"{data['profit_growth']*100:<10.2f}%")
                else:
                    print(f"{'N/A':<10}")
        else:
            # 简洁输出
            for stock in filtered_stocks:
                data = stock['data']
                print(f"{stock['code']} - {data['name']}")
        
        print("-" * 120)
        
        # 保存到全局变量
        g.filtered_stocks = filtered_stocks
        
        # 输出统计信息
        print(f"\n[{current_time}] 统计信息：")
        avg_market_cap = sum(s['data']['market_cap'] for s in filtered_stocks) / len(filtered_stocks)
        avg_gross_margin = sum(s['data']['gross_margin'] for s in filtered_stocks) / len(filtered_stocks)
        avg_rd_ratio = sum(s['data']['rd_ratio'] for s in filtered_stocks) / len(filtered_stocks)
        
        print(f"[{current_time}]   平均市值：{avg_market_cap/100000000:.2f}亿")
        print(f"[{current_time}]   平均毛利率：{avg_gross_margin*100:.2f}%")
        print(f"[{current_time}]   平均研发投入占比：{avg_rd_ratio*100:.2f}%")
        
        # 导出到Excel
        if g.excel_output:
            export_to_excel(filtered_stocks, g.excel_path)
    else:
        print(f"\n[{current_time}] 没有符合条件的股票")
        g.filtered_stocks = []
    
    # 输出总结
    print(f"\n[{current_time}] 筛选结果总结：")
    print(f"[{current_time}] 共筛选出{len(filtered_stocks)}只符合条件的股票")
    
    for stock in filtered_stocks[:10]:  # 只显示前10只
        data = stock['data']
        print(f"[{current_time}]   {stock['code']} - {data['name']}")
    
    if len(filtered_stocks) > 10:
        print(f"[{current_time}]   ... 还有{len(filtered_stocks)-10}只股票")

if __name__ == "__main__":
    main()
