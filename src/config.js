// 策略配置
const config = {
  // 资金管理
  initialCapital: 100000, // 初始资金
  targetBuyAmount: 10000, // 每次买入目标金额
  maxPositionValue: 200000, // 总持仓上限
  stopLossAmount: 10000, // 总资金止损金额
  
  // 候选股票池
  candidateStocks: [
    '600519', // 贵州茅台
    '000858', // 五粮液
    '000001', // 平安银行
    'HK00700', // 腾讯控股
    'HK09988'  // 阿里巴巴
  ]
};

module.exports = config;