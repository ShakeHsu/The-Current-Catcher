import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# 设置中文字体
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 获取全市场股票列表
def get_all_stocks():
    try:
        # 获取A股列表
        stock_list = ak.stock_zh_a_spot_em()
        print(f"获取到 {len(stock_list)} 只股票")
        return stock_list
    except Exception as e:
        print(f"获取股票列表失败: {e}")
        return pd.DataFrame()

# 基础股票池筛选（排除法）
def filter_stocks_basic(stock_list):
    if stock_list.empty:
        return pd.DataFrame()
    
    print("\n=== 基础股票池筛选（排除法）===")
    
    # 1. 剔除风险警示类股票（ST、*ST）
    original_count = len(stock_list)
    stock_list = stock_list[~stock_list['名称'].str.contains('ST', na=False)]
    st_count = original_count - len(stock_list)
    print(f"剔除ST股票: {st_count} 只")
    
    # 2. 剔除流动性枯竭标的
    # 这里简化处理，实际应该根据成交量和换手率进行筛选
    # 暂时保留所有非ST股票
    
    # 3. 剔除特定板块（可选）
    # 可以根据需要剔除金融、地产或科创板等
    # 例如：stock_list = stock_list[~stock_list['行业'].isin(['银行', '房地产'])]
    
    print(f"基础筛选后剩余股票: {len(stock_list)} 只")
    return stock_list

# 计算BBI指标
def calculate_bbi(stock_code, days=20):
    try:
        # 获取历史K线数据
        df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", adjust="qfq")
        if len(df) < 20:
            return None
        
        # 计算BBI指标
        df['MA3'] = df['收盘'].rolling(window=3).mean()
        df['MA6'] = df['收盘'].rolling(window=6).mean()
        df['MA12'] = df['收盘'].rolling(window=12).mean()
        df['MA24'] = df['收盘'].rolling(window=24).mean()
        df['BBI'] = (df['MA3'] + df['MA6'] + df['MA12'] + df['MA24']) / 4
        
        return df['BBI'].iloc[-1]
    except Exception as e:
        # print(f"计算BBI失败 {stock_code}: {e}")
        return None

# 核心筛选指标
def filter_stocks_core(stock_list):
    if stock_list.empty:
        return pd.DataFrame()
    
    print("\n=== 核心筛选指标（多维度打分）===")
    
    # 准备筛选结果
    results = []
    total = len(stock_list)
    
    for i, row in stock_list.iterrows():
        stock_code = row['代码']
        stock_name = row['名称']
        
        if (i + 1) % 50 == 0:
            print(f"处理进度: {i + 1}/{total}")
        
        try:
            # 获取股票基本信息
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            
            # 获取财务数据
            finance_data = ak.stock_financial_analysis_indicator(symbol=stock_code)
            
            # 获取历史分红数据
            dividend_data = ak.stock_dividend(symbol=stock_code)
            
            # 1. 高股息维度：股息率（TTM）> 5%
            dividend_rate_ttm = None
            try:
                dividend_rate_ttm = float(stock_info[stock_info['item'] == '股息率-TTM']['value'].iloc[0])
            except:
                pass
            
            if dividend_rate_ttm is None or dividend_rate_ttm <= 5:
                continue
            
            # 2. 盈利质量维度：扣非净利润环比增长或单季度净利润同比增长率 > 0
            profit_growth = False
            try:
                # 获取利润表数据
                income_stmt = ak.stock_financial_income_sheet_by_report_em(symbol=stock_code, report_type="单季度")
                if not income_stmt.empty:
                    # 扣非净利润环比增长
                    if '扣除非经常性损益的净利润' in income_stmt.columns:
                        q1_profit = float(income_stmt['扣除非经常性损益的净利润'].iloc[0])
                        q2_profit = float(income_stmt['扣除非经常性损益的净利润'].iloc[1])
                        if q1_profit > q2_profit:
                            profit_growth = True
                    # 单季度净利润同比增长率 > 0
                    if '净利润同比增长率' in income_stmt.columns:
                        growth_rate = float(income_stmt['净利润同比增长率'].iloc[0])
                        if growth_rate > 0:
                            profit_growth = True
            except:
                pass
            
            if not profit_growth:
                continue
            
            # 3. 估值安全维度：市盈率（PE TTM）> 0且处于合理区间
            pe_ttm = None
            try:
                pe_ttm = float(stock_info[stock_info['item'] == '市盈率-TTM']['value'].iloc[0])
            except:
                pass
            
            if pe_ttm is None or pe_ttm <= 0:
                continue
            
            # 4. 趋势过滤维度：昨日收盘价 > BBI（多空指标）
            bbi = calculate_bbi(stock_code)
            if bbi is None:
                continue
            
            # 获取最新价格
            latest_price = row['最新价']
            if latest_price <= bbi:
                continue
            
            # 计算其他所需指标
            # 2024年每股分红
            dividend_2024 = 0
            try:
                dividend_2024 = float(dividend_data[dividend_data['分红年度'] == '2024-12-31']['每股股利(税前)'].iloc[0])
            except:
                pass
            
            # 2025年归母净利润增长率
            growth_rate_2025 = 0
            try:
                # 这里简化处理，实际应该获取2025年的预测数据
                # 暂时使用最近的同比增长率
                if '净利润同比增长率' in finance_data.columns:
                    growth_rate_2025 = float(finance_data['净利润同比增长率'].iloc[0])
            except:
                pass
            
            # 近三年股利支付率
            payout_ratio = 0
            try:
                if '股利支付率' in finance_data.columns:
                    payout_ratio = float(finance_data['股利支付率'].iloc[0])
            except:
                pass
            
            # 2025年预期每股分红
            expected_dividend_2025 = dividend_2024 * (1 + growth_rate_2025 / 100)
            
            # 自算股息率
            calculated_dividend_rate = (expected_dividend_2025 / latest_price) * 100 if latest_price > 0 else 0
            
            # 目标价格
            target_price = expected_dividend_2025 / 0.05 if expected_dividend_2025 > 0 else 0
            
            # 添加到结果
            results.append({
                '股票名称': stock_name,
                '股票代码': stock_code,
                '2024年每股分红': dividend_2024,
                '2025年归母净利润增长率': growth_rate_2025,
                '近三年股利支付率': payout_ratio,
                '2025年预期每股分红': expected_dividend_2025,
                '最新价格': latest_price,
                '股息率TTM': dividend_rate_ttm,
                '自算股息率': calculated_dividend_rate,
                '目标价格': target_price
            })
            
        except Exception as e:
            # print(f"处理股票 {stock_code} 失败: {e}")
            continue
    
    # 转换为DataFrame
    result_df = pd.DataFrame(results)
    
    # 按股息率TTM排序
    if not result_df.empty:
        result_df = result_df.sort_values('股息率TTM', ascending=False)
    
    print(f"核心筛选后剩余股票: {len(result_df)} 只")
    return result_df

# 导出到Excel
def export_to_excel(df, filename='高股息股票筛选结果.xlsx'):
    if df.empty:
        print("没有符合条件的股票，无法导出")
        return
    
    # 创建输出目录
    output_dir = '筛选结果'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 导出到Excel
    file_path = os.path.join(output_dir, filename)
    df.to_excel(file_path, index=False, encoding='utf-8-sig')
    print(f"\n结果已导出到: {file_path}")

# 主函数
def main():
    print("=== 高股息股票筛选策略 ===")
    
    # 1. 获取全市场股票列表
    stock_list = get_all_stocks()
    
    # 2. 基础股票池筛选（排除法）
    basic_stocks = filter_stocks_basic(stock_list)
    
    # 3. 核心筛选指标（多维度打分）
    core_stocks = filter_stocks_core(basic_stocks)
    
    # 4. 导出到Excel
    export_to_excel(core_stocks)
    
    # 5. 显示筛选结果
    if not core_stocks.empty:
        print("\n=== 筛选结果 ===")
        print(core_stocks[['股票名称', '股票代码', '股息率TTM', '自算股息率', '目标价格']].head(20))
    else:
        print("\n没有符合条件的高股息股票")

if __name__ == "__main__":
    main()