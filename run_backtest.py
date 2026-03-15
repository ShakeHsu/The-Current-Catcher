#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
回测运行脚本
回测时间：2025.12.1 - 2026.3.12
"""

from ptrade import backtest

# 回测配置
config = {
    'start_date': '20251201',  # 回测开始日期
    'end_date': '20260312',    # 回测结束日期
    'initial_capital': 100000, # 初始资金：10万元
    'benchmark': '000300.SH',  # 基准：沪深300
    'frequency': 'minute',     # 回测频率：分钟级
}

# 运行回测
if __name__ == '__main__':
    print("=" * 60)
    print("开始回测")
    print(f"回测时间：{config['start_date']} - {config['end_date']}")
    print(f"初始资金：{config['initial_capital']}元")
    print(f"交易标的：159206.SZ (卫星ETF)")
    print("=" * 60)
    
    # 加载策略
    strategy_file = '顺势而为+激进+做T.py'
    
    # 执行回测
    result = backtest.run(
        strategy_file=strategy_file,
        start_date=config['start_date'],
        end_date=config['end_date'],
        initial_capital=config['initial_capital'],
        benchmark=config['benchmark'],
        frequency=config['frequency']
    )
    
    # 输出回测结果
    print("\n" + "=" * 60)
    print("回测结果")
    print("=" * 60)
    print(f"总收益率：{result.get('total_return', 'N/A')}")
    print(f"年化收益率：{result.get('annual_return', 'N/A')}")
    print(f"最大回撤：{result.get('max_drawdown', 'N/A')}")
    print(f"夏普比率：{result.get('sharpe_ratio', 'N/A')}")
    print(f"胜率：{result.get('win_rate', 'N/A')}")
    print(f"交易次数：{result.get('trade_count', 'N/A')}")
    print("=" * 60)
