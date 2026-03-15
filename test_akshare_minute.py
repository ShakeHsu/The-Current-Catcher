#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试AKShare获取真实分钟级数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime

print("=" * 60)
print("测试AKShare获取真实分钟级数据")
print("=" * 60)
print(f"当前时间: {datetime.now()}")
print(f"尝试获取的时间范围: 2025-12-01 09:30:00 到 2026-03-12 15:00:00")
print()

# 尝试使用用户提供的正确接口
try:
    print("尝试使用 ak.stock_zh_a_hist_min_em 接口...")
    df_minute = ak.stock_zh_a_hist_min_em(
        symbol="159206",      # 股票代码
        period="1",           # 1分钟线
        start_date="2025-12-01 09:30:00",
        end_date="2026-03-12 15:00:00",
        adjust="qfq"          # 前复权
    )
    print(f"✓ 数据获取成功！")
    print(f"数据形状: {df_minute.shape}")
    print(f"数据列名: {df_minute.columns.tolist()}")
    print(f"\n前5行数据:")
    print(df_minute.head())
    print(f"\n后5行数据:")
    print(df_minute.tail())
    print(f"\n数据类型:")
    print(df_minute.dtypes)
    
except Exception as e:
    print(f"✗ ak.stock_zh_a_hist_min_em 接口失败: {e}")
    print()
    
    try:
        print("尝试使用 ak.stock_zh_a_hist_min_em 接口（股票代码格式）...")
        df_minute = ak.stock_zh_a_hist_min_em(
            symbol="159206.SZ",      # 股票代码
            period="1",           # 1分钟线
            start_date="2025-12-01 09:30:00",
            end_date="2026-03-12 15:00:00",
            adjust="qfq"          # 前复权
        )
        print(f"✓ 数据获取成功！")
        print(f"数据形状: {df_minute.shape}")
        print(f"数据列名: {df_minute.columns.tolist()}")
        print(f"\n前5行数据:")
        print(df_minute.head())
        
    except Exception as e2:
        print(f"✗ 股票代码格式失败: {e2}")
        print()
        
        # 尝试获取指数分钟数据
        try:
            print("尝试使用 ak.index_zh_a_hist_min_em 接口...")
            df_minute = ak.index_zh_a_hist_min_em(
                symbol="159206",      # 代码
                period="1",
                start_date="2025-12-01 09:30:00",
                end_date="2026-03-12 15:00:00"
            )
            print(f"✓ 数据获取成功！")
            print(f"数据形状: {df_minute.shape}")
            print(f"数据列名: {df_minute.columns.tolist()}")
            print(f"\n前5行数据:")
            print(df_minute.head())
            
        except Exception as e3:
            print(f"✗ 指数接口失败: {e3}")
            print("\n所有接口都失败，无法获取分钟级数据")

print()
print("=" * 60)
print("测试完成")
print("=" * 60)