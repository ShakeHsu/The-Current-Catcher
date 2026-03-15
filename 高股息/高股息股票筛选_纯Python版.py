"""
高股息股票筛选策略 - 纯Python版本
不依赖任何第三方库，使用Python内置功能
"""

import csv
from datetime import datetime


def get_sample_data():
    """模拟股票数据"""
    print("使用模拟数据进行演示...")
    
    # 股票数据列表
    # 格式: [代码, 名称, 最新价, 股息率-TTM, 扣非净利润增长, PE-TTM, BBI, 
    #        2024年每股分红, 2025年归母净利润增长率, 近三年股利支付率]
    stocks = [
        ['600000', '浦发银行', 7.8, 6.5, 5.2, 5.2, 7.5, 0.51, 4.5, 30],
        ['600519', '贵州茅台', 1800, 1.5, 12.5, 35, 1750, 25.5, 10.2, 50],
        ['601318', '中国平安', 45, 5.2, 8.3, 6.8, 43, 2.34, 7.8, 45],
        ['000858', '五粮液', 160, 2.5, 10.1, 25, 155, 4.0, 9.5, 35],
        ['000333', '美的集团', 55, 3.0, 7.5, 12, 53, 1.65, 6.8, 40],
        ['600276', '恒瑞医药', 42, 1.8, 3.2, 28, 40, 0.76, 5.2, 25],
        ['601888', '中国中免', 180, 1.2, 15.8, 30, 170, 2.16, 12.5, 30],
        ['600887', '伊利股份', 28, 4.0, 6.7, 15, 26, 1.12, 7.2, 42],
        ['000002', '万科A', 12, 3.5, 4.3, 8.5, 11.5, 0.42, 5.5, 38],
        ['601668', '中国建筑', 6.5, 5.8, 2.8, 4.2, 6.2, 0.377, 3.2, 48],
        ['601398', '工商银行', 5.2, 5.5, 4.5, 5.8, 5.0, 0.293, 4.0, 32],
        ['601288', '农业银行', 4.1, 6.2, 3.8, 5.5, 4.0, 0.222, 3.5, 35],
        ['601939', '建设银行', 6.8, 5.8, 5.2, 6.2, 6.5, 0.389, 4.8, 33],
        ['601988', '中国银行', 4.5, 6.0, 4.0, 5.0, 4.3, 0.197, 3.8, 30],
        ['600036', '招商银行', 38, 4.5, 8.5, 8.5, 36, 1.738, 7.5, 38]
    ]
    
    return stocks


def filter_stocks_basic(stocks):
    """
    基础股票池筛选（排除法）
    1. 剔除风险警示类股票（ST、*ST）
    2. 剔除流动性枯竭标的
    3. 剔除特定板块（可选）
    """
    print("\n=== 基础股票池筛选（排除法）===")
    
    # 示例数据中假设都是正常交易的股票，跳过具体筛选
    print("基础筛选后剩余股票: {} 只".format(len(stocks)))
    return stocks


def filter_stocks_core(stocks):
    """
    核心筛选指标（多维度打分）
    1. 高股息维度：股息率（TTM）> 5%
    2. 盈利质量维度：扣非净利润增长 > 0
    3. 估值安全维度：市盈率（PE TTM）> 0
    4. 趋势过滤维度：昨日收盘价 > BBI（多空指标）
    """
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
        
        # 计算额外指标
        # 2025年预期每股分红 = 2024年每股分红 * (1 + 2025年前三季度归母净利润增长率)
        # 这里使用2025年归母净利润增长率作为近似值
        expected_dividend_2025 = dividend_2024 * (1 + growth_2025 / 100)
        
        # 自算股息率 = 2025年预期每股分红 / 最新收盘价
        calculated_dividend_rate = (expected_dividend_2025 / price) * 100
        
        # 目标价格 = 2025年预期每股分红 / 0.05（按5%股息率计算）
        target_price = expected_dividend_2025 / 0.05 if expected_dividend_2025 > 0 else 0
        
        # 上涨空间 = (目标价格 - 最新收盘价) / 最新收盘价 * 100
        upside_potential = ((target_price - price) / price) * 100
        
        # 添加到结果
        filtered_stocks.append({
            '股票代码': code,
            '股票名称': name,
            '最新收盘价': price,
            '股息率-TTM': dividend_rate,
            '扣非净利润增长': profit_growth,
            'PE-TTM': pe,
            'BBI': bbi,
            '2024年每股分红': dividend_2024,
            '2025年归母净利润增长率': growth_2025,
            '近三年股利支付率': payout_ratio,
            '2025年预期每股分红': expected_dividend_2025,
            '自算股息率': calculated_dividend_rate,
            '目标价格': target_price,
            '上涨空间': upside_potential
        })
    
    # 按股息率TTM排序（降序）
    filtered_stocks.sort(key=lambda x: x['股息率-TTM'], reverse=True)
    
    print("核心筛选后剩余股票: {} 只".format(len(filtered_stocks)))
    return filtered_stocks


def export_to_csv(stocks, filename='高股息股票筛选结果.csv'):
    """导出结果到CSV文件"""
    if not stocks:
        print("\n⚠️ 没有符合条件的股票，无法导出")
        return False
    
    try:
        # 定义CSV表头（按用户要求的顺序）
        headers = [
            '股票名称', '股票代码', '2024年每股分红', '2025年归母净利润增长率',
            '近三年股利支付率', '2025年预期每股分红', '最新收盘价', '股息率-TTM',
            '自算股息率', '目标价格'
        ]
        
        # 写入CSV文件
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for stock in stocks:
                row = [
                    stock['股票名称'],
                    stock['股票代码'],
                    stock['2024年每股分红'],
                    stock['2025年归母净利润增长率'],
                    stock['近三年股利支付率'],
                    stock['2025年预期每股分红'],
                    stock['最新收盘价'],
                    stock['股息率-TTM'],
                    stock['自算股息率'],
                    stock['目标价格']
                ]
                writer.writerow(row)
        
        print("\n✅ 结果已导出到: {}".format(filename))
        print("   共导出 {} 只股票".format(len(stocks)))
        return True
        
    except Exception as e:
        print("\n❌ 导出失败: {}".format(e))
        return False


def display_results(stocks):
    """显示筛选结果"""
    if not stocks:
        print("\n没有符合条件的高股息股票")
        return
    
    print("\n" + "="*80)
    print("筛选结果")
    print("="*80)
    
    # 显示表头
    print("\n{:<10} {:<10} {:<12} {:<12} {:<10} {:<10} {:<10}".format(
        '股票名称', '股票代码', '股息率TTM', '自算股息率', '最新收盘价', '目标价格', '上涨空间'
    ))
    print("-" * 80)
    
    # 显示前10只股票
    for stock in stocks[:10]:
        print("{:<10} {:<10} {:<12.2f} {:<12.2f} {:<10.2f} {:<10.2f} {:<10.2f}%".format(
            stock['股票名称'],
            stock['股票代码'],
            stock['股息率-TTM'],
            stock['自算股息率'],
            stock['最新收盘价'],
            stock['目标价格'],
            stock['上涨空间']
        ))
    
    print("\n" + "="*80)
    print("总计: {} 只股票符合筛选条件".format(len(stocks)))
    print("="*80)


def main():
    """主函数"""
    print("="*80)
    print("高股息股票筛选策略 - 纯Python版本")
    print("="*80)
    print("运行时间: {}".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    # 1. 获取股票数据
    stocks = get_sample_data()
    print("获取到 {} 只股票数据".format(len(stocks)))
    
    # 2. 基础股票池筛选（排除法）
    stocks = filter_stocks_basic(stocks)
    
    # 3. 核心筛选指标（多维度打分）
    stocks = filter_stocks_core(stocks)
    
    # 4. 显示结果
    display_results(stocks)
    
    # 5. 导出到CSV
    export_to_csv(stocks)
    
    print("\n" + "="*80)
    print("筛选完成！")
    print("="*80)


if __name__ == "__main__":
    main()
