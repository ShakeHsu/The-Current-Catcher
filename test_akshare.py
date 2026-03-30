import akshare as ak
import datetime

print(f"[{datetime.datetime.now()}] 测试AkShare是否正常工作...")

try:
    # 测试获取A股股票列表
    print("测试获取A股股票列表...")
    stock_info = ak.stock_info_a_code_name()
    print(f"成功获取{len(stock_info)}只A股股票")
    print("前5只股票:")
    print(stock_info.head())
    
    # 测试获取实时行情
    print("\n测试获取实时行情...")
    stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
    print(f"成功获取{len(stock_zh_a_spot_em_df)}只股票的实时行情")
    print("前5只股票的行情:")
    print(stock_zh_a_spot_em_df[['代码', '名称', '最新价', '总市值', '总股本']].head())
    
    # 测试获取财务数据
    print("\n测试获取财务数据...")
    # 选择一只股票进行测试
    test_stock = stock_info['code'].iloc[0]
    print(f"测试股票: {test_stock}")
    
    stock_financial_analysis_indicator_df = ak.stock_financial_analysis_indicator(symbol=test_stock)
    print(f"成功获取财务指标数据")
    print("财务指标:")
    print(stock_financial_analysis_indicator_df.head())
    
    print(f"\n[{datetime.datetime.now()}] AkShare测试成功！")
except Exception as e:
    print(f"[{datetime.datetime.now()}] AkShare测试失败: {e}")
