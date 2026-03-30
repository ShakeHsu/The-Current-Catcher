import requests
import pandas as pd
import time

def get_stocks_from_wencai(query, max_pages=5):
    """
    通过问财移动端API获取股票数据，无需Cookie
    query: 选股条件，如 "总市值<100亿，毛利率>40%"
    max_pages: 最大页数（每页100条）
    """
    url = "https://www.iwencai.com/unifiedwap/unified-wap/v2/result/get-robot-data"
    
    all_data = []
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        "Referer": "https://www.iwencai.com/",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    
    for page in range(1, max_pages + 1):
        payload = {
            "question": query,
            "perpage": 100,  # 每页最大100条
            "page": page,
            "retry_type": "no"
        }
        
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            result = response.json()
            
            if result.get("data"):
                data_list = result["data"].get("data", [])
                if not data_list:
                    break
                all_data.extend(data_list)
                print(f"第{page}页获取{len(data_list)}条，累计{len(all_data)}条")
                time.sleep(0.5)  # 避免请求过快
            else:
                break
        except Exception as e:
            print(f"第{page}页获取失败: {e}")
            break
    
    if all_data:
        df = pd.DataFrame(all_data)
        return df
    return None

# 使用示例
query = "总市值<100亿，总股本<2亿，上市天数<1460天，毛利率>40%，研发投入占营业收入比例>15%，(营业收入同比增长率>20% 或 归母净利润同比增长率>20%)"
df = get_stocks_from_wencai(query)

if df is not None:
    print(f"共获取{len(df)}只股票")
    # 显示关键列（根据实际返回调整）
    display_cols = ['证券代码', '证券简称', '总市值', '毛利率', '研发投入占营业收入比例', '营业收入同比增长率']
    available = [c for c in display_cols if c in df.columns]
    print(df[available].head(10))
    df.to_csv("wencai_stocks.csv", index=False, encoding='utf-8-sig')
else:
    print("未获取到数据")