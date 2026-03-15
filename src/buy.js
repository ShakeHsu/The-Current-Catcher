// 检查买入条件
function checkBuyConditions(data) {
  // 1. 趋势确认：今日5日均线大于昨日5日均线，且今日60日均线大于昨日60日均线
  const ma5Today = data.ma5[data.ma5.length - 1];
  const ma5Yesterday = data.ma5[data.ma5.length - 2];
  const ma60Today = data.ma60[data.ma60.length - 1];
  const ma60Yesterday = data.ma60[data.ma60.length - 2];
  
  const trendCondition = ma5Today > ma5Yesterday && ma60Today > ma60Yesterday;
  if (!trendCondition) return false;
  
  // 2. 价格位置：当前股价低于今日5日均线
  const pricePositionCondition = data.currentPrice < ma5Today;
  if (!pricePositionCondition) return false;
  
  // 3. 底部启动：当前股价从当日最低价的反弹幅度达到或超过0.2%
  const reboundPercentage = (data.currentPrice - data.todayLow) / data.todayLow * 100;
  const bottomStartCondition = reboundPercentage >= 0.2;
  if (!bottomStartCondition) return false;
  
  // 4. 成交量过滤：前5日平均成交额除以20日平均成交额小于1.25
  const volumeRatio = data.volume5 / data.volume20;
  const volumeCondition = volumeRatio < 1.25;
  if (!volumeCondition) return false;
  
  return true;
}

module.exports = { checkBuyConditions };