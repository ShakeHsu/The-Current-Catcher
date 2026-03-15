#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试获取真实的分钟级数据
"""

import akshare as ak
import pandas as pd

print("AKShare版本:", ak.__version__)

# 尝试方法1：使用fund_etf_em获取分钟级数据
print("\n方法1：尝试使用fund_etf_em获取分钟级数据")
try:
    # 先尝试获取日级数据
    df_daily = ak.fund_etf_em(symbol="159206", period="daily", 
                              start_date="20251201", end_date="20251205")
    print("日级数据获取成功:")
    print(df_daily.head())
    
except Exception as e:
    print("日级数据获取失败:", e)

# 尝试方法2：使用fund_etf_sina获取ETF数据
print("\n方法2：尝试使用fund_etf_sina获取ETF数据")
try:
    df_sina = ak.fund_etf_sina(symbol="159206")
    print("新浪ETF数据获取成功:")
    print(df_sina.head())
except Exception as e:
    print("新浪ETF数据获取失败:", e)

# 尝试方法3：使用股票接口获取分钟级数据
print("\n方法3：尝试使用股票分钟级数据接口")
try:
    # 注意：159206.SZ是ETF，可能需要使用股票接口
    df_stock = ak.stock_zh_a_minute(symbol="159206", period="1", adjust="qfq")
    print("股票分钟级数据获取成功:")
    print(df_stock.head())
except Exception as e:
    print("股票分钟级数据获取失败:", e)

print("\n测试完成")
