// 检查卖出条件
function checkSellConditions(data, holding) {
  // 1. 趋势清仓线：今日60日均线小于昨日60日均线
  const ma60Today = data.ma60[data.ma60.length - 1];
  const ma60Yesterday = data.ma60[data.ma60.length - 2];
  
  if (ma60Today < ma60Yesterday) {
    return { shouldSell: true, type: 'trend' };
  }
  
  // 2. 分批止盈：当日即时成交额大于前5日平均成交额的1.5倍，且当日涨幅大于3%
  // 注意：这里应该在每天14:50检查
  const volumeCondition = data.todayVolume > data.volume5 * 1.5;
  const priceCondition = data.todayChange > 3;
  
  if (volumeCondition && priceCondition) {
    // 港股通特殊处理：若持仓股数等于或小于1手，则不执行分批止盈
    if (data.market === 'hk') {
      const sharesPerLot = data.sharesPerLot || 100;
      if (holding.amount <= sharesPerLot) {
        return { shouldSell: false };
      }
    }
    return { shouldSell: true, type: 'profit' };
  }
  
  return { shouldSell: false };
}

module.exports = { checkSellConditions };