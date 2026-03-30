import akshare as ak

print("Testing AkShare...")

# 测试获取A股股票代码和名称
print("\n1. Testing stock_info_a_code_name...")
try:
    stock_info = ak.stock_info_a_code_name()
    print(f"Success! Got {len(stock_info)} stocks")
    print("First 5 stocks:")
    print(stock_info.head())
except Exception as e:
    print(f"Error: {e}")

print("\nTesting completed.")
