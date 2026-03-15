"""
高股息股票筛选策略 - 真实数据版本
使用AKShare获取真实的股票数据
"""

import pandas as pd
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


def get_real_time_data():
    """获取A股实时行情数据"""
    print("\n=== 获取A股实时行情 ===")
    try:
        # 获取A股实时行情
        df = ak.stock_zh_a_spot_em()
        print(f"✅ 获取到 {len(df)} 只股票的实时数据")
        return df
    except Exception as e:
        print(f"❌ 获取实时行情失败: {e}")
        return pd.DataFrame()


def get_dividend_data(stock_code):
    """获取股票分红数据"""
    try:
        # 获取分红数据
        dividend_df = ak.stock_dividend_cninfo(symbol=stock_code)
        if dividend_df is not None and not dividend_df.empty:
            # 获取最近一年的分红数据
            latest_dividend = dividend_df.iloc[0]
            return {
                'dividend_per_share': float(latest_dividend.get('每股派息', 0)),
                'dividend_year': latest_dividend.get('公告日期', '')
            }
    except Exception as e:
        # print(f"获取分红数据失败 {stock_code}: {e}")
        pass
    return {'dividend_per_share': 0, 'dividend_year': ''}


def get_financial_data(stock_code):
    """获取财务数据（净利润增长率等）"""
    try:
        # 获取主要财务指标
        finance_df = ak.stock_financial_analysis_indicator(symbol=stock_code)
        if finance_df is not None and not finance_df.empty:
            # 获取最新的财务数据
            latest = finance_df.iloc[0]
            return {
                'profit_growth': float(latest.get('净利润同比增长率', 0)),
                'payout_ratio': float(latest.get('股利支付率', 0)),
                'pe_ttm': float(latest.get('市盈率', 0))
            }
    except Exception as e:
        # print(f"获取财务数据失败 {stock_code}: {e}")
        pass
    return {'profit_growth': 0, 'payout_ratio': 0, 'pe_ttm': 0}


def get_stock_detail(stock_code):
    """获取股票详细信息"""
    try:
        # 获取个股信息
        info_df = ak.stock_individual_info_em(symbol=stock_code)
        if info_df is not None and not info_df.empty:
            info_dict = dict(zip(info_df['item'], info_df['value']))
            return {
                'dividend_rate_ttm': float(info_dict.get('股息率-TTM', 0)),
                'pe_ttm': float(info_dict.get('市盈率-动态', 0)),
                'total_market_value': float(info_dict.get('总市值', 0))
            }
    except Exception as e:
        # print(f"获取详细信息失败 {stock_code}: {e}")
        pass
    return {'dividend_rate_ttm': 0, 'pe_ttm': 0, 'total_market_value': 0}


def filter_stocks_basic(df):
    """
    基础股票池筛选（排除法）
    1. 剔除风险警示类股票（ST、*ST）
    2. 剔除流动性枯竭标的
    3. 剔除特定板块（可选）
    """
    print("\n=== 基础股票池筛选（排除法）===")
    
    original_count = len(df)
    
    # 1. 剔除风险警示类股票（ST、*ST）
    if '名称' in df.columns:
        df = df[~df['名称'].str.contains('ST|退市', na=False)]
        st_count = original_count - len(df)
        print(f"剔除ST/退市股票: {st_count} 只")
    
    # 2. 剔除北交所股票（代码以8或4开头）
    if '代码' in df.columns:
        df = df[~df['代码'].str.match(r'^[84]', na=False)]
    
    # 3. 剔除科创板（代码以688开头，可选）
    # df = df[~df['代码'].str.startswith('688', na=False)]
    
    print(f"基础筛选后剩余股票: {len(df)} 只")
    return df


def process_stock_data(df):
    """处理股票数据，获取详细信息"""
    print("\n=== 获取详细财务数据 ===")
    
    results = []
    total = len(df)
    
    for i, row in df.iterrows():
        stock_code = row['代码']
        stock_name = row['名称']
        current_price = row['最新价']
        
        if (i + 1) % 100 == 0:
            print(f"处理进度: {i + 1}/{total}")
        
        try:
            # 获取详细信息
            detail = get_stock_detail(stock_code)
            
            # 获取分红数据
            dividend_info = get_dividend_data(stock_code)
            
            # 获取财务数据
            finance_info = get_financial_data(stock_code)
            
            # 使用实时数据中的股息率
            dividend_rate_ttm = detail.get('dividend_rate_ttm', 0)
            if dividend_rate_ttm == 0 and '股息率' in row:
                dividend_rate_ttm = float(row['股息率']) if pd.notna(row['股息率']) else 0
            
            # 获取PE
            pe_ttm = detail.get('pe_ttm', 0)
            if pe_ttm == 0:
                pe_ttm = finance_info.get('pe_ttm', 0)
            
            # 获取净利润增长率
            profit_growth = finance_info.get('profit_growth', 0)
            
            # 获取股利支付率
            payout_ratio = finance_info.get('payout_ratio', 0)
            
            # 获取2024年每股分红
            dividend_2024 = dividend_info.get('dividend_per_share', 0)
            
            # 添加到结果
            results.append({
                '股票代码': stock_code,
                '股票名称': stock_name,
                '最新收盘价': current_price,
                '股息率-TTM': dividend_rate_ttm,
                '扣非净利润增长': profit_growth,
                'PE-TTM': pe_ttm,
                '2024年每股分红': dividend_2024,
                '2025年归母净利润增长率': profit_growth,  # 使用当前增长率作为预测
                '近三年股利支付率': payout_ratio
            })
            
            # 添加延迟，避免请求过快
            time.sleep(0.1)
            
        except Exception as e:
            # print(f"处理股票 {stock_code} 失败: {e}")
            continue
    
    result_df = pd.DataFrame(results)
    print(f"✅ 成功获取 {len(result_df)} 只股票的详细数据")
    return result_df


def filter_high_dividend_stocks(df):
    """
    高股息筛选
    1. 股息率（TTM）> 5%
    2. 盈利质量：净利润增长 > 0
    3. 估值安全：PE TTM > 0
    4. 有分红记录
    """
    print("\n=== 高股息核心筛选 ===")
    
    original_count = len(df)
    
    # 1. 股息率 > 5%
    df = df[df['股息率-TTM'] > 5].copy()
    print(f"股息率>5%: {len(df)}/{original_count} 只")
    
    # 2. 净利润增长 > 0
    df = df[df['扣非净利润增长'] > 0].copy()
    print(f"净利润增长>0: {len(df)} 只")
    
    # 3. PE TTM > 0
    df = df[df['PE-TTM'] > 0].copy()
    print(f"PE>0: {len(df)} 只")
    
    # 4. 有分红记录
    df = df[df['2024年每股分红'] > 0].copy()
    print(f"有分红记录: {len(df)} 只")
    
    return df


def calculate_metrics(df):
    """计算额外指标"""
    print("\n=== 计算额外指标 ===")
    
    # 2025年预期每股分红 = 2024年每股分红 * (1 + 2025年前三季度归母净利润增长率)
    df['2025年预期每股分红'] = df['2024年每股分红'] * (1 + df['2025年归母净利润增长率'] / 100)
    
    # 自算股息率 = 2025年预期每股分红 / 最新收盘价
    df['自算股息率'] = (df['2025年预期每股分红'] / df['最新收盘价']) * 100
    
    # 目标价格 = 2025年预期每股分红 / 0.05（按5%股息率计算）
    df['目标价格'] = df['2025年预期每股分红'] / 0.05
    
    # 上涨空间 = (目标价格 - 最新收盘价) / 最新收盘价 * 100
    df['上涨空间'] = ((df['目标价格'] - df['最新收盘价']) / df['最新收盘价']) * 100
    
    return df


def export_results(df, filename='高股息股票筛选结果_真实数据.xlsx'):
    """导出结果到Excel"""
    if df.empty:
        print("\n⚠️ 没有符合条件的股票，无法导出")
        return False
    
    try:
        # 选择要导出的列（按用户要求的顺序）
        export_columns = [
            '股票名称', '股票代码', '2024年每股分红', '2025年归母净利润增长率',
            '近三年股利支付率', '2025年预期每股分红', '最新收盘价', '股息率-TTM',
            '自算股息率', '目标价格'
        ]
        
        # 按股息率排序
        df = df.sort_values('股息率-TTM', ascending=False)
        
        # 导出到Excel
        df[export_columns].to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✅ 结果已导出到: {filename}")
        print(f"   共导出 {len(df)} 只股票")
        return True
        
    except Exception as e:
        print(f"\n❌ 导出Excel失败: {e}")
        print("尝试导出为CSV格式...")
        try:
            csv_filename = filename.replace('.xlsx', '.csv')
            df[export_columns].to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"✅ 已导出为CSV: {csv_filename}")
            return True
        except Exception as e2:
            print(f"❌ CSV导出也失败: {e2}")
            return False


def display_results(df):
    """显示筛选结果"""
    if df.empty:
        print("\n没有符合条件的高股息股票")
        return
    
    print("\n" + "="*100)
    print("筛选结果")
    print("="*100)
    
    # 显示前20只股票
    display_df = df.head(20)
    
    print(f"\n{'股票名称':<10} {'股票代码':<10} {'股息率TTM':<12} {'自算股息率':<12} {'最新收盘价':<10} {'目标价格':<10} {'上涨空间':<10}")
    print("-" * 100)
    
    for _, row in display_df.iterrows():
        print(f"{row['股票名称']:<10} {row['股票代码']:<10} {row['股息率-TTM']:<12.2f} {row['自算股息率']:<12.2f} {row['最新收盘价']:<10.2f} {row['目标价格']:<10.2f} {row['上涨空间']:<10.2f}%")
    
    print("\n" + "="*100)
    print(f"总计: {len(df)} 只股票符合筛选条件")
    print("="*100)


def main():
    """主函数"""
    print("="*100)
    print("高股息股票筛选策略 - 真实数据版本")
    print("="*100)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 获取实时行情数据
    df = get_real_time_data()
    if df.empty:
        print("❌ 无法获取数据，程序退出")
        return
    
    # 2. 基础筛选
    df = filter_stocks_basic(df)
    
    # 3. 获取详细数据（这里会花费较长时间）
    print("\n注意：获取详细财务数据需要较长时间，请耐心等待...")
    df = process_stock_data(df.head(100))  # 先处理前100只进行测试
    
    # 4. 高股息筛选
    df = filter_high_dividend_stocks(df)
    
    # 5. 计算额外指标
    df = calculate_metrics(df)
    
    # 6. 显示结果
    display_results(df)
    
    # 7. 导出到Excel
    export_results(df)
    
    print("\n" + "="*100)
    print("筛选完成！")
    print("="*100)


if __name__ == "__main__":
    main()
