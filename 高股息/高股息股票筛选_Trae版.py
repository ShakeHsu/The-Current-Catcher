"""
高股息股票筛选策略 - Trae环境版本
使用第三方库：pandas, numpy, akshare, openpyxl
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 尝试导入akshare，如果失败则使用模拟数据
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
    print("✅ AKShare已加载，可以使用真实股票数据")
except ImportError:
    AKSHARE_AVAILABLE = False
    print("⚠️ AKShare未安装，将使用模拟数据")
    print("如需真实数据，请运行: pip install akshare")


def get_stock_data():
    """获取股票数据"""
    if AKSHARE_AVAILABLE:
        try:
            # 获取A股实时行情
            print("正在获取A股实时数据...")
            df = ak.stock_zh_a_spot_em()
            print(f"获取到 {len(df)} 只股票数据")
            return df
        except Exception as e:
            print(f"获取数据失败: {e}")
            return get_sample_data()
    else:
        return get_sample_data()


def get_sample_data():
    """模拟股票数据（当AKShare不可用时使用）"""
    print("使用模拟数据进行演示...")
    
    data = {
        '代码': ['600000', '600519', '601318', '000858', '000333', 
                '600276', '601888', '600887', '000002', '601668',
                '601398', '601288', '601939', '601988', '600036'],
        '名称': ['浦发银行', '贵州茅台', '中国平安', '五粮液', '美的集团',
                '恒瑞医药', '中国中免', '伊利股份', '万科A', '中国建筑',
                '工商银行', '农业银行', '建设银行', '中国银行', '招商银行'],
        '最新价': [7.8, 1800, 45, 160, 55, 42, 180, 28, 12, 6.5,
                  5.2, 4.1, 6.8, 4.5, 38],
        '股息率-TTM': [6.5, 1.5, 5.2, 2.5, 3.0, 1.8, 1.2, 4.0, 3.5, 5.8,
                     5.5, 6.2, 5.8, 6.0, 4.5],
        '扣非净利润增长': [5.2, 12.5, 8.3, 10.1, 7.5, 3.2, 15.8, 6.7, 4.3, 2.8,
                       4.5, 3.8, 5.2, 4.0, 8.5],
        'PE-TTM': [5.2, 35, 6.8, 25, 12, 28, 30, 15, 8.5, 4.2,
                 5.8, 5.5, 6.2, 5.0, 8.5],
        'BBI': [7.5, 1750, 43, 155, 53, 40, 170, 26, 11.5, 6.2,
               5.0, 4.0, 6.5, 4.3, 36],
        '2024年每股分红': [0.51, 25.5, 2.34, 4.0, 1.65, 0.76, 2.16, 1.12, 0.42, 0.377,
                       0.293, 0.222, 0.389, 0.197, 1.738],
        '2025年归母净利润增长率': [4.5, 10.2, 7.8, 9.5, 6.8, 5.2, 12.5, 7.2, 5.5, 3.2,
                             4.0, 3.5, 4.8, 3.8, 7.5],
        '近三年股利支付率': [30, 50, 45, 35, 40, 25, 30, 42, 38, 48,
                         32, 35, 33, 30, 38]
    }
    
    return pd.DataFrame(data)


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
        df = df[~df['名称'].str.contains('ST', na=False)]
        st_count = original_count - len(df)
        print(f"剔除ST股票: {st_count} 只")
    
    # 2. 剔除流动性枯竭标的（这里简化处理）
    # 实际应该根据成交量、换手率等进行筛选
    
    # 3. 剔除特定板块（可选）
    # 例如：剔除银行、地产等
    # df = df[~df['行业'].isin(['银行', '房地产'])]
    
    print(f"基础筛选后剩余股票: {len(df)} 只")
    return df


def filter_stocks_core(df):
    """
    核心筛选指标（多维度打分）
    1. 高股息维度：股息率（TTM）> 5%
    2. 盈利质量维度：扣非净利润增长 > 0
    3. 估值安全维度：市盈率（PE TTM）> 0
    4. 趋势过滤维度：昨日收盘价 > BBI（多空指标）
    """
    print("\n=== 核心筛选指标（多维度打分）===")
    
    # 1. 高股息维度：股息率（TTM）> 5%
    df = df[df['股息率-TTM'] > 5].copy()
    print(f"高股息筛选后（股息率>5%）: {len(df)} 只")
    
    # 2. 盈利质量维度：扣非净利润增长 > 0
    df = df[df['扣非净利润增长'] > 0].copy()
    print(f"盈利质量筛选后: {len(df)} 只")
    
    # 3. 估值安全维度：市盈率（PE TTM）> 0
    df = df[df['PE-TTM'] > 0].copy()
    print(f"估值安全筛选后: {len(df)} 只")
    
    # 4. 趋势过滤维度：昨日收盘价 > BBI（多空指标）
    df = df[df['最新价'] > df['BBI']].copy()
    print(f"趋势过滤后: {len(df)} 只")
    
    return df


def calculate_metrics(df):
    """计算额外指标"""
    print("\n=== 计算额外指标 ===")
    
    # 2025年预期每股分红 = 2024年每股分红 * (1 + 2025年前三季度归母净利润增长率)
    # 这里使用2025年归母净利润增长率作为近似值
    df['2025年预期每股分红'] = df['2024年每股分红'] * (1 + df['2025年归母净利润增长率'] / 100)
    
    # 重命名列
    df = df.rename(columns={'最新价': '最新收盘价'})
    
    # 自算股息率 = 2025年预期每股分红 / 最新收盘价
    df['自算股息率'] = (df['2025年预期每股分红'] / df['最新收盘价']) * 100
    
    # 目标价格 = 2025年预期每股分红 / 0.05（按5%股息率计算）
    df['目标价格'] = df['2025年预期每股分红'] / 0.05
    
    # 上涨空间 = (目标价格 - 最新收盘价) / 最新收盘价 * 100
    df['上涨空间'] = ((df['目标价格'] - df['最新收盘价']) / df['最新收盘价']) * 100
    
    return df


def export_results(df, filename='高股息股票筛选结果.xlsx'):
    """导出结果到Excel"""
    if df.empty:
        print("\n⚠️ 没有符合条件的股票，无法导出")
        return False
    
    try:
        # 选择要导出的列（按用户要求的顺序）
        export_columns = [
            '名称', '代码', '2024年每股分红', '2025年归母净利润增长率',
            '近三年股利支付率', '2025年预期每股分红', '最新收盘价', '股息率-TTM',
            '自算股息率', '目标价格'
        ]
        
        # 重命名列
        column_mapping = {
            '名称': '股票名称',
            '代码': '股票代码'
        }
        
        export_df = df[export_columns].copy()
        export_df = export_df.rename(columns=column_mapping)
        
        # 导出到Excel
        export_df.to_excel(filename, index=False, engine='openpyxl')
        print(f"\n✅ 结果已导出到: {filename}")
        print(f"   共导出 {len(export_df)} 只股票")
        return True
        
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")
        print("尝试导出为CSV格式...")
        try:
            csv_filename = filename.replace('.xlsx', '.csv')
            export_df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
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
    
    print("\n" + "="*80)
    print("筛选结果")
    print("="*80)
    
    # 显示前10只股票
    display_df = df[[
        '名称', '代码', '股息率-TTM', '自算股息率', 
        '最新收盘价', '目标价格', '上涨空间'
    ]].head(10)
    
    print(f"\n{'股票名称':<10} {'股票代码':<10} {'股息率TTM':<12} {'自算股息率':<12} {'最新收盘价':<10} {'目标价格':<10} {'上涨空间':<10}")
    print("-" * 80)
    
    for _, row in display_df.iterrows():
        print(f"{row['名称']:<10} {row['代码']:<10} {row['股息率-TTM']:<12.2f} {row['自算股息率']:<12.2f} {row['最新收盘价']:<10.2f} {row['目标价格']:<10.2f} {row['上涨空间']:<10.2f}%")
    
    print("\n" + "="*80)
    print(f"总计: {len(df)} 只股票符合筛选条件")
    print("="*80)


def main():
    """主函数"""
    print("="*80)
    print("高股息股票筛选策略")
    print("="*80)
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 获取股票数据
    df = get_stock_data()
    
    # 2. 基础股票池筛选（排除法）
    df = filter_stocks_basic(df)
    
    # 3. 核心筛选指标（多维度打分）
    df = filter_stocks_core(df)
    
    # 4. 计算额外指标
    df = calculate_metrics(df)
    
    # 5. 按股息率排序
    df = df.sort_values('股息率-TTM', ascending=False)
    
    # 6. 显示结果
    display_results(df)
    
    # 7. 导出到Excel
    export_results(df)
    
    print("\n" + "="*80)
    print("筛选完成！")
    print("="*80)


if __name__ == "__main__":
    main()
