const { checkBuyConditions } = require('./src/buy');
const { checkSellConditions } = require('./src/sell');
const { PositionManager } = require('./src/position');

// 测试买入条件
function testBuyConditions() {
  console.log('测试买入条件...');
  
  // 测试通过的情况
  const testData1 = {
    currentPrice: 15.5,
    todayLow: 15.2,
    ma5: [15.3, 15.4, 15.5, 15.5, 15.6],
    ma60: [14.8, 14.9, 15.0, 15.1, 15.2],
    volume5: 10000000,
    volume20: 9000000
  };
  
  const result1 = checkBuyConditions(testData1);
  console.log('测试1 (符合条件):', result1);
  
  // 测试趋势条件不满足的情况
  const testData2 = {
    currentPrice: 15.5,
    todayLow: 15.2,
    ma5: [15.6, 15.5, 15.5, 15.4, 15.3], // 5日均线下降
    ma60: [14.8, 14.9, 15.0, 15.1, 15.2],
    volume5: 10000000,
    volume20: 9000000
  };
  
  const result2 = checkBuyConditions(testData2);
  console.log('测试2 (趋势条件不满足):', result2);
  
  // 测试价格位置条件不满足的情况
  const testData3 = {
    currentPrice: 15.7, // 高于5日均线
    todayLow: 15.2,
    ma5: [15.3, 15.4, 15.5, 15.5, 15.6],
    ma60: [14.8, 14.9, 15.0, 15.1, 15.2],
    volume5: 10000000,
    volume20: 9000000
  };
  
  const result3 = checkBuyConditions(testData3);
  console.log('测试3 (价格位置条件不满足):', result3);
}

// 测试卖出条件
function testSellConditions() {
  console.log('\n测试卖出条件...');
  
  // 测试趋势清仓条件
  const testData1 = {
    ma60: [15.2, 15.1, 15.0, 14.9, 14.8], // 60日均线下降
    todayVolume: 12000000,
    volume5: 8000000,
    todayChange: 2.5
  };
  
  const holding1 = { amount: 1000 };
  const result1 = checkSellConditions(testData1, holding1);
  console.log('测试1 (趋势清仓):', result1);
  
  // 测试分批止盈条件
  const testData2 = {
    ma60: [14.8, 14.9, 15.0, 15.1, 15.2],
    todayVolume: 15000000, // 大于前5日平均的1.5倍
    volume5: 8000000,
    todayChange: 3.5 // 大于3%
  };
  
  const holding2 = { amount: 1000 };
  const result2 = checkSellConditions(testData2, holding2);
  console.log('测试2 (分批止盈):', result2);
  
  // 测试港股通分批止盈特殊处理
  const testData3 = {
    ma60: [14.8, 14.9, 15.0, 15.1, 15.2],
    todayVolume: 15000000,
    volume5: 8000000,
    todayChange: 3.5,
    market: 'hk',
    sharesPerLot: 1000
  };
  
  const holding3 = { amount: 1000 }; // 刚好1手
  const result3 = checkSellConditions(testData3, holding3);
  console.log('测试3 (港股通1手不执行止盈):', result3);
}

// 测试仓位管理
function testPositionManager() {
  console.log('\n测试仓位管理...');
  
  const pm = new PositionManager();
  console.log('初始现金:', pm.getCash());
  
  // 测试买入
  pm.buy('600519', 100, 1500);
  console.log('买入后现金:', pm.getCash());
  console.log('持仓:', pm.getHoldings());
  
  // 测试卖出
  pm.sell('600519', 50, 1600);
  console.log('卖出后现金:', pm.getCash());
  console.log('持仓:', pm.getHoldings());
  
  // 测试卖出一半
  pm.sellHalf('600519');
  console.log('卖出一半后现金:', pm.getCash());
  console.log('持仓:', pm.getHoldings());
  
  // 测试清仓
  pm.clearAll();
  console.log('清仓后现金:', pm.getCash());
  console.log('持仓:', pm.getHoldings());
}

// 运行测试
testBuyConditions();
testSellConditions();
testPositionManager();
console.log('\n测试完成');
