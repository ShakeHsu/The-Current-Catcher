const axios = require('axios');

// 模拟数据获取函数
// 实际应用中应该替换为真实的API调用
async function fetchStockData(symbol) {
  // 模拟数据
  // 实际应用中需要从API获取真实数据
  return {
    symbol: symbol,
    currentPrice: 15.6,
    todayLow: 15.2,
    ma5: [15.3, 15.4, 15.5, 15.5, 15.6], // 最近5天的5日均线
    ma60: [14.8, 14.9, 15.0, 15.1, 15.2], // 最近5天的60日均线
    volume5: 10000000, // 前5日平均成交额
    volume20: 9000000, // 前20日平均成交额
    todayVolume: 12000000, // 今日成交额
    todayChange: 3.5, // 今日涨幅
    market: symbol.startsWith('HK') ? 'hk' : 'cn', // 市场类型
    sharesPerLot: symbol.startsWith('HK') ? 1000 : 100, // 港股每手股数
    exchangeRate: 0.9 // 港币兑人民币汇率
  };
}

// 计算移动平均线
function calculateMA(prices, period) {
  if (prices.length < period) {
    return [];
  }
  const result = [];
  for (let i = period - 1; i < prices.length; i++) {
    const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
    result.push(sum / period);
  }
  return result;
}

module.exports = { fetchStockData, calculateMA };