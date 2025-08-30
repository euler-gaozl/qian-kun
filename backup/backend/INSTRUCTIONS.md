# 如何使用和测试您的回测引擎

本文档将指导您如何使用已构建的回测框架进行您自己的量化策略测试。

## 核心文件概览

- `backtester.py`: 包含了回测引擎的核心逻辑 (`VectorizedBacktester`) 和策略的基类 (`Strategy`)。您的大部分新策略代码会在这里或一个新文件中定义。
- `run_backtest.py`: 这是您进行测试的**主入口脚本**。您将主要修改此文件来加载数据、选择策略并配置回测参数。

---

## 步骤一：加载您自己的数据

目前，`run_backtest.py` 使用 `generate_mock_data` 函数生成模拟数据。要使用您自己的真实数据，请按以下步骤操作：

1.  **准备您的数据文件**：假设您有一个名为 `my_data.csv` 的CSV文件，其中至少包含 `timestamp`, `open`, `high`, `low`, `close` 列。

2.  **修改 `run_backtest.py`**：
    找到 `main` 函数中的数据生成部分，并将其替换为从CSV加载数据的代码。

    **替换前**:
    ```python
    # --- 1. 生成模拟数据 ---
    print("生成模拟数据...")
    mock_data = generate_mock_data(symbol='rb2410', start='2023-01-01', end='2023-12-31')
    ```

    **替换后 (示例)**:
    ```python
    # --- 1. 加载您的真实数据 ---
    print("加载真实数据...")
    symbol = 'rb2410' # 定义您的合约代码
    df = pd.read_csv('path/to/your/my_data.csv', index_col='timestamp', parse_dates=True)
    
    # **重要**: 确保数据列格式符合引擎要求 (MultiIndex)
    df.columns = pd.MultiIndex.from_product([[symbol], df.columns])
    
    real_data = df
    print(f"数据已加载，共 {len(real_data)} 条记录。")
    ```
    **注意**: 请确保将 `path/to/your/my_data.csv` 替换为您的实际文件路径。回测引擎要求输入数据的列是 Pandas MultiIndex 格式，这是为了未来能同时回测多个品种。

---

## 步骤二：编写并测试新策略

框架的核心优势是策略和引擎分离。您可以轻松创建新策略进行测试。

1.  **在 `backtester.py` 中创建新策略类**：
    打开 `backtester.py`，在文件末尾添加一个新的策略类，让它继承自 `Strategy` 基类。

    **新策略模板 (例如：双均线交叉策略)**:
    ```python
    class DualMAStrategy(Strategy):
        """
        双均线交叉策略示例。
        当短期均线上穿长期均线时买入，下穿时卖出。
        """
        def __init__(self, short_window=5, long_window=20):
            super().__init__()
            self.short_window = short_window
            self.long_window = long_window

        def _calculate_indicators(self):
            """计算短期和长期移动平均线"""
            self.data['short_ma'] = self.data['close'].rolling(window=self.short_window).mean()
            self.data['long_ma'] = self.data['close'].rolling(window=self.long_window).mean()

        def _generate_signals(self) -> pd.Series:
            """生成交易信号"""
            signals = pd.Series(index=self.data.index, dtype=str)
            # 当短期均线上穿长期均线时，产生买入信号
            signals[self.data['short_ma'] > self.data['long_ma']] = 'buy'
            # 当短期均线下穿长期均线时，产生卖出信号
            signals[self.data['short_ma'] < self.data['long_ma']] = 'sell'
            
            # 为了简化，我们这里不生成 'close' 信号，让引擎在反向信号出现时自动平仓（需要对引擎做微小调整）
            # 或者更严谨地，定义明确的平仓逻辑
            return signals.ffill().fillna('close') # 填充信号，避免NaN
    ```

2.  **在 `run_backtest.py` 中使用新策略**：
    - 首先，从 `backtester` 导入您的新策略类。
    - 然后，在 `main` 函数中实例化它。

    **修改 `run_backtest.py`**:
    ```python
    # 在文件顶部导入
    from backtester import VectorizedBacktester, MA16Strategy, DualMAStrategy # <-- 添加您的新策略

    # ... 在 main 函数中 ...
    # --- 3. 实例化策略和回测引擎 ---
    # strategy = MA16Strategy() # 注释掉旧策略
    strategy = DualMAStrategy(short_window=10, long_window=30) # <-- 使用您的新策略
    backtester = VectorizedBacktester(**config)
    ```

---

## 步骤三：调整回测参数

在 `run_backtest.py` 的 `main` 函数中，有一个名为 `config` 的字典。您可以在这里轻松调整所有核心回测参数。

```python
# --- 2. 配置回测参数 ---
config = {
    'initial_capital': 2000000.0,      # 修改初始资金
    'start_date': '2022-01-01',        # 修改回测开始日期
    'end_date': '2022-12-31',          # 修改回测结束日期
    'data_frequency': '1H',            # 修改数据频率 (用于夏普比率等计算的年化因子)
    'position_sizing_pct': 0.25        # 修改仓位比例 (每次使用25%的权益)
}
```

---

## 总结

您的测试工作流程如下：
1.  修改 `run_backtest.py` 以加载您的**数据**。
2.  在 `backtester.py` 中创建您的**新策略**类。
3.  在 `run_backtest.py` 中实例化并选择您的**策略**。
4.  在 `run_backtest.py` 中调整**回测配置**。
5.  从终端运行命令: `conda activate qiankun && python backend/run_backtest.py`
6.  分析输出结果，并重复迭代。
