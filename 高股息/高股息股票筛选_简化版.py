import pandas as pd
import numpy as np
import os

# 由于环境限制，这里创建一个示例数据和简化的筛选逻辑
def get_sample_stocks():
    """创建示例股票数据"""
    data = {
        '代码': ['600000', '600519', '601318', '000858', '000333', '600276', '601888', '600887', '000002', '601668'],
        '名称': ['浦发银行', '贵州茅台', '中国平安', '五粮液', '美的集团', '恒瑞医药', '中国中免', '伊利股份', '万科A', '中国建筑'],
        '最新价': [7.8, 1800, 45, 160, 55, 42, 180, 28, 12, 6.5],
        '股息率-TTM': [6.5, 1.5, 5.2, 2.5, 3.0, 1.8, 1.2, 4.0, 3.5, 5.8],
        '扣非净利润增长': [5.2, 12.5, 8.3, 10.1, 7.5, 3.2, 15.8, 6.7, 4.3, 2.8],
        'PE-TTM': [5.2, 35, 6.8, 25, 12, 28, 30, 15, 8.5, 4.2],
        'BBI': [7.5, 1750, 43, 155, 53, 40, 170, 26, 11.5, 6.2],
        '2024年每股分红': [0.51, 25.5, 2.34, 4.0, 1.65, 0.76, 2.16, 1.12, 0.42, 0.377],
        '2025年归母净利润增长率': [4.5, 10.2, 7.8, 9.5, 6.8, 5.2, 12.5, 7.2, 5.5, 3.2],
        '近三年股利支付率': [30, 50, 45, 35, 40, 25, 30, 42, 38, 48]
    }
    return pd.DataFrame(data)

# 基础股票池筛选（排除法）
def filter_stocks_basic(stock_list):
    print("\n=== 基础股票池筛选（排除法）===")
    
    # 1. 剔除风险警示类股票（ST、*ST）
    # 示例数据中没有ST股票，跳过
    
    # 2. 剔除流动性枯竭标的
    # 示例数据中假设都是正常交易的股票，跳过
    
    # 3. 剔除特定板块（可选）
    # 示例数据中包含不同行业，跳过
    
    print(f"基础筛选后剩余股票: {len(stock_list)} 只")
    return stock_list

# 核心筛选指标
def filter_stocks_core(stock_list):
    print("\n=== 核心筛选指标（多维度打分）===")
    
    # 1. 高股息维度：股息率（TTM）> 5%
    stock_list = stock_list[stock_list['股息率-TTM'] > 5]
    print(f"高股息筛选后: {len(stock_list)} 只")
    
    # 2. 盈利质量维度：扣非净利润增长 > 0
    stock_list = stock_list[stock_list['扣非净利润增长'] > 0]
    print(f"盈利质量筛选后: {len(stock_list)} 只")
    
    # 3. 估值安全维度：市盈率（PE TTM）> 0
    stock_list = stock_list[stock_list['PE-TTM'] > 0]
    print(f"估值安全筛选后: {len(stock_list)} 只")
    
    # 4. 趋势过滤维度：昨日收盘价 > BBI（多空指标）
    stock_list = stock_list[stock_list['最新价'] > stock_list['BBI']]
    print(f"趋势过滤后: {len(stock_list)} 只")
    
    # 计算其他所需指标
    stock_list['2025年预期每股分红'] = stock_list['2024年每股分红'] * (1 + stock_list['2025年归母净利润增长率'] / 100)
    stock_list['自算股息率'] = (stock_list['2025年预期每股分红'] / stock_list['最新价']) * 100
    stock_list['目标价格'] = stock_list['2025年预期每股分红'] / 0.05
    
    # 按股息率TTM排序
    stock_list = stock_list.sort_values('股息率-TTM', ascending=False)
    
    return stock_list

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
    
    # 1. 获取股票数据（使用示例数据）
    stock_list = get_sample_stocks()
    print(f"获取到 {len(stock_list)} 只股票")
    
    # 2. 基础股票池筛选（排除法）
    basic_stocks = filter_stocks_basic(stock_list)
    
    # 3. 核心筛选指标（多维度打分）
    core_stocks = filter_stocks_core(basic_stocks)
    
    # 4. 导出到Excel
    export_to_excel(core_stocks)
    
    # 5. 显示筛选结果
    if not core_stocks.empty:
        print("\n=== 筛选结果 ===")
        print(core_stocks[['股票名称', '股票代码', '股息率TTM', '自算股息率', '目标价格']])
    else:
        print("\n没有符合条件的高股息股票")

if __name__ == "__main__":
    main()