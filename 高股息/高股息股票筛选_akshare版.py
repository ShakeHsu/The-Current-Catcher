"""
高股息股票筛选策略 - AKShare真实数据版本
使用AKShare获取真实的股票数据，不依赖pandas
"""

import csv
from datetime import datetime
import time

# 尝试导入akshare
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
    print("✅ AKShare已加载")
except ImportError:
    AKSHARE_AVAILABLE = False
    print("❌ AKShare未安装，请先运行: pip install akshare")
    exit(1)


def safe_float(value):
    """安全转换为浮点数"""
    try:
        if value is None or str(value).strip() == '' or str(value).strip() == '-':
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def get_real_time_data():
    """获取A股实时行情数据"""
    print("\n=== 获取A股实时行情 ===")
    try:
        # 获取A股实时行情
        df = ak.stock_zh_a_spot_em()
        print(f"✅ 获取到 {len(df)} 只股票的实时数据")
        
        # 转换为字典列表
        stocks = []
        for _, row in df.iterrows():
            stocks.append({
                '代码': str(row['代码']),
                '名称': str(row['名称']),
                '最新价': safe_float(row['最新价']),
                '涨跌幅': safe_float(row['涨跌幅']),
                '换手率': safe_float(row['换手率']),
                '市盈率-动态': safe_float(row['市盈率-动态']),
                '股息率': safe_float(row['股息率'])
            })
        return stocks
    except Exception as e:
        print(f"❌ 获取实时行情失败: {e}")
        return []


def filter_stocks_basic(stocks):
    """
    基础股票池筛选（排除法）
    """
    print("\n=== 基础股票池筛选（排除法）===")
    
    original_count = len(stocks)
    filtered = []
    
    for stock in stocks:
        # 1. 剔除风险警示类股票（ST、*ST）
        if 'ST' in stock['名称'] or '退市' in stock['名称']:
            continue
        
        # 2. 剔除北交所股票（代码以8或4开头）
        if stock['代码'].startswith('8') or stock['代码'].startswith('4'):
            continue
        
        # 3. 剔除价格为0或无效的股票
        if stock['最新价'] <= 0:
            continue
        
        filtered.append(stock)
    
    print(f"剔除ST/无效股票: {original_count - len(filtered)} 只")
    print(f"基础筛选后剩余: {len(filtered)} 只")
    return filtered


def get_stock_financial_data(stock_code):
    """获取股票财务数据"""
    try:
        # 获取主要财务指标
        finance_df = ak.stock_financial_analysis_indicator(symbol=stock_code)
        if finance_df is not None and not finance_df.empty:
            latest = finance_df.iloc[0]
            return {
                'profit_growth': float(latest.get('净利润同比增长率', 0) or 0),
                'payout_ratio': float(latest.get('股利支付率', 0) or 0),
                'pe_ttm': float(latest.get('市盈率', 0) or 0),
                'eps': float(latest.get('基本每股收益', 0) or 0)
            }
    except Exception as e:
        pass
    return {'profit_growth': 0, 'payout_ratio': 0, 'pe_ttm': 0, 'eps': 0}


def get_dividend_history(stock_code):
    """获取分红历史"""
    try:
        # 获取分红数据
        dividend_df = ak.stock_dividend_cninfo(symbol=stock_code)
        if dividend_df is not None and not dividend_df.empty:
            # 获取最近一年的分红
            latest = dividend_df.iloc[0]
            dividend = float(latest.get('每股派息', 0) or 0)
            return dividend
    except Exception as e:
        pass
    return 0


def process_stocks(stocks, max_stocks=50):
    """处理股票数据，获取详细信息"""
    print(f"\n=== 获取详细财务数据（前{max_stocks}只）===")
    
    results = []
    count = min(len(stocks), max_stocks)
    
    for i, stock in enumerate(stocks[:max_stocks]):
        if (i + 1) % 10 == 0:
            print(f"处理进度: {i + 1}/{count}")
        
        try:
            stock_code = stock['代码']
            
            # 获取财务数据
            finance = get_stock_financial_data(stock_code)
            
            # 获取分红数据
            dividend_2024 = get_dividend_history(stock_code)
            
            # 使用实时数据中的股息率
            dividend_rate_ttm = stock.get('股息率', 0)
            if dividend_rate_ttm == 0:
                # 计算股息率
                if dividend_2024 > 0 and stock['最新价'] > 0:
                    dividend_rate_ttm = (dividend_2024 / stock['最新价']) * 100
            
            # 获取PE
            pe_ttm = stock.get('市盈率-动态', 0)
            if pe_ttm == 0:
                pe_ttm = finance.get('pe_ttm', 0)
            
            # 获取净利润增长率
            profit_growth = finance.get('profit_growth', 0)
            
            # 获取股利支付率
            payout_ratio = finance.get('payout_ratio', 0)
            
            results.append({
                '股票代码': stock_code,
                '股票名称': stock['名称'],
                '最新收盘价': stock['最新价'],
                '股息率-TTM': dividend_rate_ttm,
                '扣非净利润增长': profit_growth,
                'PE-TTM': pe_ttm,
                '2024年每股分红': dividend_2024,
                '2025年归母净利润增长率': profit_growth,
                '近三年股利支付率': payout_ratio
            })
            
            # 添加延迟
            time.sleep(0.05)
            
        except Exception as e:
            continue
    
    print(f"✅ 成功获取 {len(results)} 只股票的详细数据")
    return results


def filter_high_dividend_stocks(stocks):
    """高股息筛选"""
    print("\n=== 高股息核心筛选 ===")
    
    original_count = len(stocks)
    filtered = []
    
    for stock in stocks:
        # 1. 股息率 > 5%
        if stock['股息率-TTM'] <= 5:
            continue
        
        # 2. 净利润增长 > 0
        if stock['扣非净利润增长'] <= 0:
            continue
        
        # 3. PE TTM > 0
        if stock['PE-TTM'] <= 0:
            continue
        
        # 4. 有分红记录
        if stock['2024年每股分红'] <= 0:
            continue
        
        filtered.append(stock)
    
    print(f"股息率>5%: {len(filtered)}/{original_count} 只")
    return filtered


def calculate_metrics(stocks):
    """计算额外指标"""
    print("\n=== 计算额外指标 ===")
    
    for stock in stocks:
        # 2025年预期每股分红 = 2024年每股分红 * (1 + 增长率)
        growth_rate = stock['2025年归母净利润增长率']
        stock['2025年预期每股分红'] = stock['2024年每股分红'] * (1 + growth_rate / 100)
        
        # 自算股息率 = 2025年预期每股分红 / 最新收盘价
        if stock['最新收盘价'] > 0:
            stock['自算股息率'] = (stock['2025年预期每股分红'] / stock['最新收盘价']) * 100
        else:
            stock['自算股息率'] = 0
        
        # 目标价格 = 2025年预期每股分红 / 0.05
        stock['目标价格'] = stock['2025年预期每股分红'] / 0.05 if stock['2025年预期每股分红'] > 0 else 0
        
        # 上涨空间
        if stock['最新收盘价'] > 0:
            stock['上涨空间'] = ((stock['目标价格'] - stock['最新收盘价']) / stock['最新收盘价']) * 100
        else:
            stock['上涨空间'] = 0
    
    # 按股息率排序
    stocks.sort(key=lambda x: x['股息率-TTM'], reverse=True)
    
    return stocks


def export_to_csv(stocks, filename='高股息股票筛选结果_真实数据.csv'):
    """导出结果到CSV"""
    if not stocks:
        print("\n⚠️ 没有符合条件的股票，无法导出")
        return False
    
    try:
        # 定义CSV表头
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
        
        print(f"\n✅ 结果已导出到: {filename}")
        print(f"   共导出 {len(stocks)} 只股票")
        return True
        
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")
        return False


def display_results(stocks):
    """显示筛选结果"""
    if not stocks:
        print("\n没有符合条件的高股息股票")
        return
    
    print("\n" + "="*100)
    print("筛选结果")
    print("="*100)
    
    # 显示表头
    print(f"\n{'股票名称':<10} {'股票代码':<10} {'股息率TTM':<12} {'自算股息率':<12} {'最新收盘价':<10} {'目标价格':<10} {'上涨空间':<10}")
    print("-" * 100)
    
    # 显示前20只股票
    for stock in stocks[:20]:
        print(f"{stock['股票名称']:<10} {stock['股票代码']:<10} {stock['股息率-TTM']:<12.2f} {stock['自算股息率']:<12.2f} {stock['最新收盘价']:<10.2f} {stock['目标价格']:<10.2f} {stock['上涨空间']:<10.2f}%")
    
    print("\n" + "="*100)
    print(f"总计: {len(stocks)} 只股票符合筛选条件")
    print("="*100)


def main():
    """主函数"""
    print("="*100)
    print("高股息股票筛选策略 - AKShare真实数据版本")
    print("="*100)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 获取实时行情数据
    stocks = get_real_time_data()
    if not stocks:
        print("❌ 无法获取数据，程序退出")
        return
    
    # 2. 基础筛选
    stocks = filter_stocks_basic(stocks)
    
    # 3. 获取详细数据（限制数量以加快速度）
    print("\n注意：获取详细财务数据需要较长时间...")
    stocks = process_stocks(stocks, max_stocks=100)
    
    # 4. 高股息筛选
    stocks = filter_high_dividend_stocks(stocks)
    
    # 5. 计算额外指标
    stocks = calculate_metrics(stocks)
    
    # 6. 显示结果
    display_results(stocks)
    
    # 7. 导出到CSV
    export_to_csv(stocks)
    
    print("\n" + "="*100)
    print("筛选完成！")
    print("="*100)


if __name__ == "__main__":
    main()
