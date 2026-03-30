import requests
import pandas as pd
import time
import json

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
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    
    for page in range(1, max_pages + 1):
        payload = {
            "question": query,
            "perpage": 100,
            "page": page,
            "retry_type": "no",
            "source": "Ths_iwencai_Xuangu",
            "version": "2.0"
        }
        
        try:
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            
            # 先打印响应内容，看看返回了什么
            if page == 1:
                print(f"响应状态码: {response.status_code}")
                print(f"响应内容前500字符: {response.text[:500]}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # 尝试不同的数据路径
                    data_list = None
                    if 'data' in result:
                        if 'answer' in result['data']:
                            answer = result['data']['answer']
                            if isinstance(answer, list) and len(answer) > 0:
                                if 'txt' in answer[0]:
                                    txt_data = answer[0]['txt']
                                    if 'content' in txt_data:
                                        content = txt_data['content']
                                        if isinstance(content, list):
                                            data_list = content
                    
                    if data_list:
                        all_data.extend(data_list)
                        print(f"第{page}页获取{len(data_list)}条，累计{len(all_data)}条")
                        time.sleep(0.5)
                    else:
                        print(f"第{page}页未找到数据")
                        if page == 1:
                            print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)[:1000]}")
                        break
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
                    print(f"响应内容: {response.text[:500]}")
                    break
            else:
                print(f"请求失败，状态码: {response.status_code}")
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

print("=" * 70)
print("问财API测试")
print("=" * 70)
print(f"\n查询条件: {query}\n")

df = get_stocks_from_wencai(query)

if df is not None:
    print(f"\n✓ 共获取{len(df)}只股票")
    print("\n数据列名:")
    print(df.columns.tolist())
    print("\n前5条数据:")
    print(df.head())
    df.to_csv("wencai_stocks.csv", index=False, encoding='utf-8-sig')
    print("\n✓ 已保存到 wencai_stocks.csv")
else:
    print("\n✗ 未获取到数据")
