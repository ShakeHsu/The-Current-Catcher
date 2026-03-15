const { fetchStockData } = require('./data');
const { checkBuyConditions } = require('./buy');
const { checkSellConditions } = require('./sell');
const { PositionManager } = require('./position');
const config = require('./config');

class TradingStrategy {
  constructor() {
    this.positionManager = new PositionManager();
    this.baseLine = config.initialCapital;
  }

  async run() {
    console.log('开始执行交易策略...');
    
    // 检查卖出条件
    await this.checkAndExecuteSell();
    
    // 检查总资金止损
    this.checkTotalCapitalStopLoss();
    
    // 检查买入条件
    if (this.positionManager.getTotalValue() < config.maxPositionValue) {
      await this.checkAndExecuteBuy();
    }
    
    console.log('策略执行完成');
  }

  async checkAndExecuteSell() {
    const holdings = this.positionManager.getHoldings();
    for (const [symbol, holding] of Object.entries(holdings)) {
      const data = await fetchStockData(symbol);
      if (!data) continue;
      
      const sellResult = checkSellConditions(data, holding);
      if (sellResult.shouldSell) {
        if (sellResult.type === 'trend') {
          // 趋势清仓
          this.positionManager.sellAll(symbol);
          console.log(`[趋势清仓] 卖出 ${symbol}`);
        } else if (sellResult.type === 'profit') {
          // 分批止盈
          this.positionManager.sellHalf(symbol);
          console.log(`[分批止盈] 卖出 ${symbol} 一半仓位`);
          // 重置基准线
          this.baseLine = this.positionManager.getTotalValue();
        }
      }
    }
  }

  checkTotalCapitalStopLoss() {
    const currentValue = this.positionManager.getTotalValue();
    if (currentValue <= this.baseLine - config.stopLossAmount) {
      console.log(`[总资金止损] 当前资产 ${currentValue}，低于基准线 ${this.baseLine} - ${config.stopLossAmount}，清仓所有股票`);
      this.positionManager.clearAll();
    }
  }

  async checkAndExecuteBuy() {
    // 这里应该遍历候选股票池
    // 为简化示例，仅以几个示例股票为例
    const candidates = config.candidateStocks;
    
    for (const symbol of candidates) {
      const data = await fetchStockData(symbol);
      if (!data) continue;
      
      if (checkBuyConditions(data)) {
        // 计算买入数量
        const buyAmount = this.calculateBuyAmount(data);
        if (buyAmount > 0) {
          this.positionManager.buy(symbol, buyAmount, data.currentPrice);
          console.log(`[买入] ${symbol}，数量 ${buyAmount}，价格 ${data.currentPrice}`);
        }
      }
    }
  }

  calculateBuyAmount(data) {
    if (data.market === 'hk') {
      // 港股通计算
      const targetAmount = config.targetBuyAmount;
      const hkdAmount = targetAmount * data.exchangeRate;
      const sharesPerLot = data.sharesPerLot || 100;
      const lots = Math.floor(hkdAmount / (data.currentPrice * sharesPerLot));
      return lots > 0 ? lots * sharesPerLot : sharesPerLot;
    } else {
      // A股计算
      const targetAmount = config.targetBuyAmount;
      const shares = Math.floor(targetAmount / data.currentPrice);
      return Math.max(100, Math.floor(shares / 100) * 100);
    }
  }
}

function runStrategy() {
  const strategy = new TradingStrategy();
  strategy.run();
  
  // 每天14:50执行检查
  setInterval(() => {
    const now = new Date();
    if (now.getHours() === 14 && now.getMinutes() === 50) {
      strategy.run();
    }
  }, 60000); // 每分钟检查一次
}

module.exports = { runStrategy };