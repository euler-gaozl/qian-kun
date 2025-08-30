import pandas as pd
import numpy as np
from backtester import VectorizedBacktester, MA16Strategy

def generate_mock_data(symbol='rb2410', start='2023-01-01', end='2023-12-31'):
    """
    生成模拟的期货OHLCV数据。
    """
    dates = pd.to_datetime(pd.date_range(start, end, freq='D'))
    price = 1000 + np.random.randn(len(dates)).cumsum()
    
    df = pd.DataFrame({
        'open': price + np.random.uniform(-5, 5, len(dates)),
        'high': price + np.random.uniform(0, 10, len(dates)),
        'low': price + np.random.uniform(-10, 0, len(dates)),
        'close': price,
        'volume': np.random.randint(100, 1000, len(dates))
    }, index=dates)
    
    # 确保 high 是最高价, low 是最低价
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    # 创建 MultiIndex columns 以匹配回测引擎的输入格式
    df.columns = pd.MultiIndex.from_product([[symbol], df.columns])
    
    return df

def main():
    """
    主函数：配置并运行回测。
    """
    # --- 1. 生成模拟数据 ---
    # 在实际应用中，您会从文件或数据库加载真实数据
    print("生成模拟数据...")
    mock_data = generate_mock_data(symbol='rb2410', start='2023-01-01', end='2023-12-31')
    print(f"数据已生成，共 {len(mock_data)} 条记录。")
    print("-" * 30)

    # --- 2. 配置回测参数 ---
    config = {
        'initial_capital': 1000000.0,
        'start_date': '2023-01-15', # 留出一些数据用于计算初始MA
        'end_date': '2023-12-31',
        'data_frequency': '1D',
        'position_sizing_pct': 0.1 # 每次使用10%的权益开仓
    }
    print("回测配置:")
    for key, value in config.items():
        print(f"- {key}: {value}")
    print("-" * 30)

    # --- 3. 实例化策略和回测引擎 ---
    strategy = MA16Strategy()
    backtester = VectorizedBacktester(**config)

    # --- 4. 运行回测 ---
    print("开始运行回测...")
    results = backtester.run(mock_data, strategy)
    print("回测完成！")
    print("=" * 50)

    # --- 5. 打印回测结果 ---
    if "kpis" in results:
        print("📈 关键性能指标 (KPIs):")
        for key, value in results['kpis'].items():
            print(f"- {key.replace('_', ' ').title()}: {value}")
        print("-" * 30)

        print("📊 资金曲线 (Equity Curve) - 前5条记录:")
        print(results['equity_curve'].head())
        print("-" * 30)

        print("📋 交易日志 (Trade Log) - 前5条记录:")
        print(results['trade_log'].head())
        print("-" * 30)
    else:
        print(results.get("message", "回测未产生有效结果。"))

if __name__ == '__main__':
    main()
