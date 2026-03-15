# The Current Catcher - 量化交易策略

## 项目介绍

这是一个基于Backtrader的量化交易策略，实现了以下功能：

- 趋势跟随策略
- 分钟级交易
- 分批止盈
- 做T策略
- 风险控制（止损/止盈）
- 单日一次买入限制

## 快速开始

### 1. 环境准备

#### 安装依赖

```bash
# 安装Python依赖
pip install backtrader pandas numpy akshare matplotlib python-dotenv

# 安装Git（如果未安装）
# 访问 https://git-scm.com/download/win 下载并安装
```

#### 配置环境变量

在项目根目录创建 `.env` 文件：

```env
# .env 文件 - 这个文件永远不会上传到GitHub
GITHUB_TOKEN=你的GitHub个人访问令牌
GITHUB_REPO=ShakeHsu/The-Current-Catcher
```

**获取GitHub Token：**
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 勾选 "repo" 权限
4. 生成并复制Token到 `.env` 文件

### 2. 从GitHub获取代码

#### 方法1：使用批处理脚本

双击运行 `download_from_github.bat`

#### 方法2：使用Git命令

```bash
# 克隆仓库
git clone https://github.com/ShakeHsu/The-Current-Catcher.git

# 进入目录
cd The-Current-Catcher

# 拉取最新代码
git pull
```

### 3. 运行策略

#### 运行Backtrader回测

```bash
# 运行回测
python 顺势而为+激进+做T_backtrader.py
```

#### 测试数据获取

```bash
# 测试分钟级数据获取
python test_akshare_minute.py
```

## 项目结构

```
├── 顺势而为+激进+做T_backtrader.py  # 主策略文件（Backtrader版）
├── test_akshare_minute.py           # 分钟级数据测试
├── download_from_github.bat          # GitHub下载脚本
├── download_from_github.ps1          # GitHub下载脚本（PowerShell）
├── git_workflow.py                   # GitHub工作流程脚本
├── upload_to_github.py               # 上传到GitHub脚本
├── .env                              # 环境变量配置（不提交到GitHub）
├── .gitignore                        # Git忽略文件
├── GitHub上传指南.md                  # GitHub上传指南
├── 日常同步操作指南.md                 # 日常同步操作指南
├── GitHub下载和同步指南.md             # 下载和同步指南
└── 回测使用说明.md                    # 回测使用说明
```

## 策略参数

在 `顺势而为+激进+做T_backtrader.py` 中可以调整以下参数：

- `buy_amount`: 每次买入金额（默认10000元）
- `max_cost`: 持仓成本上限（默认200000元）
- `volume_ratio_threshold`: 买入时成交量过滤阈值（默认3）
- `sell_volume_ratio`: 卖出时放量阈值（默认1.5）
- `profit_loss_ratio_take_profit`: 盈亏率止盈阈值（默认15%）
- `max_drawdown_stop`: 从最高点回撤清仓阈值（默认5%）
- `profit_loss_ratio_stop_loss`: 盈亏率止损阈值（默认-5%）
- `m_days`: 买入条件参数（默认5天）
- `n_days`: 买入条件参数（默认3天）
- `a_days`: 买入条件参数（默认5天）
- `b_days`: 买入条件参数（默认3天）
- `t_gain_threshold`: 做T涨幅阈值（默认5%）
- `t_pullback_threshold`: 做T回落阈值（默认1%）
- `t_1455_gain_threshold`: 14:55做T涨幅阈值（默认2%）

## 日常同步工作流程

### 修改代码后上传

```bash
# 查看修改状态
git status

# 添加修改
git add .

# 提交修改
git commit -m "修改说明"

# 推送到GitHub
git push
```

### 获取最新代码

```bash
# 拉取最新代码
git pull
```

## 注意事项

1. **.env文件**：包含敏感信息，不会上传到GitHub
2. **Git配置**：首次使用需要配置Git用户名和邮箱
3. **网络连接**：需要稳定的网络连接获取数据
4. **数据来源**：使用AKShare获取股票数据
5. **回测结果**：仅供参考，不构成投资建议

## 技术栈

- Python 3.13+
- Backtrader（回测框架）
- Pandas（数据处理）
- NumPy（数值计算）
- AKShare（数据获取）
- Matplotlib（可视化）
- Python-dotenv（环境变量）

## 许可证

MIT License

## 联系方式

如有问题或建议，欢迎交流！