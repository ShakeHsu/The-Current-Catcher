import csv

# 示例股票数据
sample_stocks = [
    ['600000', '浦发银行', 7.8, 6.5, 5.2, 5.2, 7.5, 0.51, 4.5, 30],
    ['600519', '贵州茅台', 1800, 1.5, 12.5, 35, 1750, 25.5, 10.2, 50],
    ['601318', '中国平安', 45, 5.2, 8.3, 6.8, 43, 2.34, 7.8, 45],
    ['000858', '五粮液', 160, 2.5, 10.1, 25, 155, 4.0, 9.5, 35],
    ['000333', '美的集团', 55, 3.0, 7.5, 12, 53, 1.65, 6.8, 40],
    ['600276', '恒瑞医药', 42, 1.8, 3.2, 28, 40, 0.76, 5.2, 25],
    ['601888', '中国中免', 180, 1.2, 15.8, 30, 170, 2.16, 12.5, 30],
    ['600887', '伊利股份', 28, 4.0, 6.7, 15, 26, 1.12, 7.2, 42],
    ['000002', '万科A', 12, 3.5, 4.3, 8.5, 11.5, 0.42, 5.5, 38],
    ['601668', '中国建筑', 6.5, 5.8, 2.8, 4.2, 6.2, 0.377, 3.2, 48]
]

# 基础股票池筛选（排除法）
def filter_stocks_basic(stocks):
    print("\n=== 基础股票池筛选（排除法）===")
    # 示例数据中假设都是正常交易的股票，跳过具体筛选
    print("基础筛选后剩余股票: {} 只".format(len(stocks)))
    return stocks

# 核心筛选指标
def filter_stocks_core(stocks):
    print("\n=== 核心筛选指标（多维度打分）===")
    
    filtered_stocks = []
    
    for stock in stocks:
        code, name, price, dividend_rate, profit_growth, pe, bbi, dividend_2024, growth_2025, payout_ratio = stock
        
        # 1. 高股息维度：股息率（TTM）> 5%
        if dividend_rate <= 5:
            continue
        
        # 2. 盈利质量维度：扣非净利润增长 > 0
        if profit_growth <= 0:
            continue
        
        # 3. 估值安全维度：市盈率（PE TTM）> 0
        if pe <= 0:
            continue
        
        # 4. 趋势过滤维度：昨日收盘价 > BBI（多空指标）
        if price <= bbi:
            continue
        
        # 计算其他所需指标
        expected_dividend_2025 = dividend_2024 * (1 + growth_2025 / 100)
        calculated_dividend_rate = (expected_dividend_2025 / price) * 100
        target_price = expected_dividend_2025 / 0.05 if expected_dividend_2025 > 0 else 0
        
        # 添加到结果
        filtered_stocks.append([
            name, code, dividend_2024, growth_2025, payout_ratio, 
            expected_dividend_2025, price, dividend_rate, calculated_dividend_rate, target_price
        ])
    
    # 按股息率TTM排序
    filtered_stocks.sort(key=lambda x: x[7], reverse=True)
    
    print("核心筛选后剩余股票: {} 只".format(len(filtered_stocks)))
    return filtered_stocks

# 导出到CSV（模拟Excel）
def export_to_csv(stocks, filename='高股息股票筛选结果.csv'):
    if not stocks:
        print("没有符合条件的股票，无法导出")
        return
    
    # 导出到CSV（不使用os模块）
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        # 写入表头
        writer.writerow(['股票名称', '股票代码', '2024年每股分红', '2025年归母净利润增长率', 
                       '近三年股利支付率', '2025年预期每股分红', '最新价格', '股息率TTM', 
                       '自算股息率', '目标价格'])
        # 写入数据
        for stock in stocks:
            writer.writerow(stock)
    
    print("\n结果已导出到: {}".format(filename))

# 主函数
def main():
    print("=== 高股息股票筛选策略 ===")
    
    # 1. 获取股票数据（使用示例数据）
    print("获取到 {} 只股票".format(len(sample_stocks)))
    
    # 2. 基础股票池筛选（排除法）
    basic_stocks = filter_stocks_basic(sample_stocks)
    
    # 3. 核心筛选指标（多维度打分）
    core_stocks = filter_stocks_core(basic_stocks)
    
    # 4. 导出到CSV
    export_to_csv(core_stocks)
    
    # 5. 显示筛选结果
    if core_stocks:
        print("\n=== 筛选结果 ===")
        print("股票名称       股票代码       股息率TTM     自算股息率      目标价格")
        print("-" * 60)
        for stock in core_stocks:
            name, code, _, _, _, _, price, dividend_rate, calculated_rate, target_price = stock
            print("{:<10} {:<10} {:<10.2f} {:<10.2f} {:<10.2f}".format(
                name, code, dividend_rate, calculated_rate, target_price))
    else:
        print("\n没有符合条件的高股息股票")

if __name__ == "__main__":
    main()