class PositionManager {
  constructor() {
    this.holdings = {}; // 持仓信息
    this.cash = 100000; // 初始现金
  }

  // 买入股票
  buy(symbol, amount, price) {
    const cost = amount * price;
    if (this.cash < cost) {
      console.log(`[错误] 现金不足，需要 ${cost}，可用 ${this.cash}`);
      return false;
    }

    if (!this.holdings[symbol]) {
      this.holdings[symbol] = {
        amount: 0,
        averagePrice: 0
      };
    }

    const totalCost = this.holdings[symbol].amount * this.holdings[symbol].averagePrice + cost;
    const totalAmount = this.holdings[symbol].amount + amount;
    
    this.holdings[symbol].amount = totalAmount;
    this.holdings[symbol].averagePrice = totalCost / totalAmount;
    this.cash -= cost;
    
    return true;
  }

  // 卖出股票
  sell(symbol, amount, price) {
    if (!this.holdings[symbol] || this.holdings[symbol].amount < amount) {
      console.log(`[错误] 持仓不足，需要 ${amount}，可用 ${this.holdings[symbol]?.amount || 0}`);
      return false;
    }

    const revenue = amount * price;
    this.holdings[symbol].amount -= amount;
    this.cash += revenue;

    if (this.holdings[symbol].amount === 0) {
      delete this.holdings[symbol];
    }

    return true;
  }

  // 卖出全部
  sellAll(symbol) {
    if (!this.holdings[symbol]) return false;
    const amount = this.holdings[symbol].amount;
    // 假设当前价格为平均成本价
    const price = this.holdings[symbol].averagePrice;
    return this.sell(symbol, amount, price);
  }

  // 卖出一半
  sellHalf(symbol) {
    if (!this.holdings[symbol]) return false;
    let amount = Math.floor(this.holdings[symbol].amount / 2);
    
    // 港股通特殊处理：按整手卖出
    // 这里简化处理，实际应用中需要根据具体股票的每手股数计算
    if (symbol.startsWith('HK')) {
      const sharesPerLot = 1000; // 假设每手1000股
      amount = Math.floor(amount / sharesPerLot) * sharesPerLot;
      if (amount === 0) return false;
    }
    
    // 假设当前价格为平均成本价
    const price = this.holdings[symbol].averagePrice;
    return this.sell(symbol, amount, price);
  }

  // 清仓所有股票
  clearAll() {
    for (const symbol in this.holdings) {
      this.sellAll(symbol);
    }
  }

  // 获取持仓信息
  getHoldings() {
    return this.holdings;
  }

  // 获取总市值
  getTotalValue() {
    let totalValue = this.cash;
    for (const symbol in this.holdings) {
      // 假设当前价格为平均成本价
      const price = this.holdings[symbol].averagePrice;
      totalValue += this.holdings[symbol].amount * price;
    }
    return totalValue;
  }

  // 获取现金
  getCash() {
    return this.cash;
  }
}

module.exports = { PositionManager };