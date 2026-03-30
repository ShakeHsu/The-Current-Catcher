import pywencai
import pandas as pd
import time

# 你的Cookie
WENCAI_COOKIE = "other_uid=Ths_iwencai_Xuangu_k4qvq1khzdevbwgecun9t6775b4f7vn6; _clck=1ip2uf6%7C2%7Cg4s%7C0%7C0; cid=143938aa9bcb410be5834a191e11c8151774911832; u_ukey=A10702B8689642C6BE607730E11E6E4A; u_uver=1.0.0; u_dpass=JyMgZyUfHqLo%2Fjbp3ekJF827qjMnyAQkldXci8Bmh0bmAAsjPpzpO9oaOJfbvNsrHi80LrSsTFH9a%2B6rtRvqGg%3D%3D; u_did=AEE15556ACB74060AF01BD7772002A25; u_ttype=WEB; ttype=WEB; user=MDpteF81MjExNTYwMDg6Ok5vbmU6NTAwOjUzMTE1NjAwODo3LDExMTExMTExMTExLDQwOzQ0LDExLDQwOzYsMSw0MDs1LDEsNDA7MSwxMDEsNDA7MiwxLDQwOzMsMSw0MDs1LDEsNDA7OCwwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMSw0MDsxMDIsMSw0MDoxNjo6OjUyMTE1NjAwODoxNzc0OTExODUzOjo6MTU4NzYxNDgyMDo2MDQ4MDA6MDoxMjUzM2UyYmRiNWY5YTJlNDRkOGFmYzQxNzgwMGRkOWM6ZGVmYXVsdF81OjA%3D; userid=521156008; u_name=mx_521156008; escapename=mx_521156008; ticket=aa08bf075e828fd246b146a78a473621; user_status=0; utk=fe6206a0bcc89b9d1071e5f6a13edeae; sess_tk=eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6InNlc3NfdGtfMSIsImJ0eSI6InNlc3NfdGsifQ.eyJqdGkiOiI5Y2RkMDA3ODQxZmM4YTRkZTRhMmY5YjViZGUyMzMyNTEiLCJpYXQiOjE3NzQ5MTE4NTMsImV4cCI6MTc3NTUxNjY1Mywic3ViIjoiNTIxMTU2MDA4IiwiaXNzIjoidXBhc3MuaXdlbmNhaS5jb20iLCJhdWQiOiIyMDIwMTExODUyODg5MDcyIiwiYWN0Ijoib2ZjIiwiY3VocyI6ImFjYTJjYTM4ZmY5OWM0NmI1ODUyZmZiNzE1MzgzMTVlNzI2N2JlNDJiN2QzYjA1ZTQyNmJkYmVjMDQ2ZjkyMDAifQ.p_Dm3JpcRXzjZZ6bhCNBAuLFBRdFfhnNSDm8SPec86GJ1fnkINtX01QqFBXSWVDIuwf7nreRUh8Ke0RXBebqWQ; cuc=v007v5szt1rw; THSSESSID=50d7a45db509c6209c56772d0d; v=A3JSAx9kT0cuoHN6a-xILAKlw7NRA3M9qAdqwTxPniUQzxxtJJPGrXiXukIP"

# ========== 筛选条件（自然语言描述）==========
QUERY = """
    沪深A股，
    总市值小于100亿，
    总股本小于2亿，
    上市天数小于1460天（上市4年），
    毛利率大于40%，
    研发投入占营业收入比例大于15%，
    （营业收入同比增长率大于20% 或 归母净利润同比增长率大于20%）
"""

# 可选的备用查询（更简洁的表达）
QUERY_SIMPLE = """
    总市值<100亿，
    总股本<2亿，
    上市时间<4年，
    毛利率>40%，
    研发占比>15%，
    (营收增长>20% 或 净利润增长>20%)
"""

def filter_stocks():
    """获取并筛选股票"""
    print("=" * 80)
    print("小市值高成长股票筛选器")
    print("=" * 80)
    print("\n筛选条件：")
    print("  ✓ 市值 < 100亿")
    print("  ✓ 总股本 < 2亿")
    print("  ✓ 上市时间 < 4年")
    print("  ✓ 毛利率 > 40%")
    print("  ✓ 研发占比 > 15%")
    print("  ✓ 营收增速 > 20% 或 净利润增速 > 20%")
    print("\n" + "-" * 80)
    
    print("正在从问财获取数据...")
    
    try:
        # 使用问财查询
        result = pywencai.get(
            query=QUERY,
            cookie=WENCAI_COOKIE,
            loop=True,              # 获取全部数据
            sort_key="总市值",       # 按市值排序
            sort_order="asc",       # 从小到大
            sleep=1.5              # 请求间隔1.5秒
        )
        
        if result is None or result.empty:
            print("\n未找到符合条件的股票，尝试使用简化查询...")
            result = pywencai.get(
                query=QUERY_SIMPLE,
                cookie=WENCAI_COOKIE,
                loop=True,
                sort_key="总市值",
                sort_order="asc",
                sleep=1.5
            )
        
        return result
        
    except Exception as e:
        print(f"\n获取数据失败: {e}")
        print("\n可能原因：")
        print("1. Cookie已过期，请重新获取")
        print("2. 网络连接问题")
        print("3. 筛选条件语法问题")
        return None

def display_results(df):
    """展示筛选结果"""
    if df is None or df.empty:
        print("\n未找到符合条件的股票")
        return
    
    print(f"\n✓ 共找到 {len(df)} 只符合条件的股票")
    print("\n" + "=" * 80)
    print("筛选结果详情（按市值从小到大排序）")
    print("=" * 80)
    
    # 选择要显示的列（根据实际返回的列名调整）
    display_cols = []
    col_mapping = {
        '股票代码': '代码',
        '股票简称': '名称',
        '最新价': '现价',
        '总市值': '市值(亿)',
        '总股本': '总股本(亿)',
        '毛利率': '毛利率(%)',
        '研发投入占营业收入比例': '研发占比(%)',
        '营业收入同比增长率': '营收增速(%)',
        '归母净利润同比增长率': '净利润增速(%)',
        '上市天数': '上市天数'
    }
    
    # 找出实际存在的列
    for orig, display in col_mapping.items():
        if orig in df.columns:
            display_cols.append(orig)
    
    if display_cols:
        display_df = df[display_cols].copy()
        
        # 格式化数值列
        for col in display_cols:
            if col in ['总市值', '总股本']:
                # 市值和股本转换为亿
                if display_df[col].dtype in ['float64', 'int64']:
                    display_df[col] = display_df[col].map(lambda x: f"{x/100000000:.2f}" if pd.notna(x) else "N/A")
            elif display_df[col].dtype in ['float64', 'int64']:
                display_df[col] = display_df[col].map(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
        
        # 重命名列
        display_df.columns = [col_mapping.get(c, c) for c in display_cols]
        
        # 打印表格
        print(display_df.to_string(index=False))
    else:
        # 如果列名不匹配，显示全部
        print("返回的数据列：", df.columns.tolist())
        print("\n前10条数据：")
        print(df.head(10).to_string())
    
    # 统计分析
    print("\n" + "=" * 80)
    print("统计分析")
    print("=" * 80)
    
    if '总市值' in df.columns:
        df['总市值_亿'] = df['总市值'] / 100000000
        print(f"市值范围: {df['总市值_亿'].min():.2f}亿 ~ {df['总市值_亿'].max():.2f}亿")
        print(f"平均市值: {df['总市值_亿'].mean():.2f}亿")
    
    if '毛利率' in df.columns:
        print(f"平均毛利率: {df['毛利率'].mean():.2f}%")
        print(f"最高毛利率: {df['毛利率'].max():.2f}%")
    
    if '营业收入同比增长率' in df.columns:
        print(f"平均营收增速: {df['营业收入同比增长率'].mean():.2f}%")
        print(f"最高营收增速: {df['营业收入同比增长率'].max():.2f}%")

def save_to_file(df, filename="growth_small_cap_stocks.csv"):
    """保存结果到CSV文件"""
    if df is None or df.empty:
        return
    
    try:
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n✓ 结果已保存到: {filename}")
        
        # 同时保存一个简化的版本
        if '股票代码' in df.columns and '股票简称' in df.columns:
            simple = df[['股票代码', '股票简称', '总市值', '毛利率', '营业收入同比增长率']].copy()
            simple.columns = ['代码', '名称', '市值(元)', '毛利率(%)', '营收增速(%)']
            simple.to_csv("growth_stocks_simple.csv", index=False, encoding='utf-8-sig')
            print(f"✓ 简化版已保存到: growth_stocks_simple.csv")
            
    except Exception as e:
        print(f"保存文件失败: {e}")

def main():
    """主程序"""
    # 1. 获取数据
    stocks = filter_stocks()
    
    # 2. 显示结果
    if stocks is not None and not stocks.empty:
        display_results(stocks)
        
        # 3. 询问是否保存
        print("\n" + "-" * 80)
        save_choice = input("是否保存结果到CSV文件？(y/n): ")
        if save_choice.lower() == 'y':
            save_to_file(stocks)
    else:
        print("\n未找到符合条件的股票")
        print("\n建议：")
        print("1. 放宽筛选条件试试（如研发占比降到10%）")
        print("2. 检查Cookie是否有效")
        print("3. 检查网络连接")
    
    print("\n筛选完成！")

# 运行
if __name__ == "__main__":
    main()