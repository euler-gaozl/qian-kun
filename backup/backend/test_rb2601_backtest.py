import pandas as pd
import akshare as ak
from backtester import VectorizedBacktester, MA16Strategy

def test_rb2601_backtest():
    """Test rb2601 120-minute backtest with improved angle calculation"""
    
    print("Testing rb2601 120-minute backtest...")
    
    # Get rb2601 120-minute data for July 2025
    df = ak.futures_zh_minute_sina(symbol='rb2601', period='120')
    df.rename(columns={'datetime': 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Convert to numeric
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col])
    
    # Filter to July 2025 
    start_date = '2025-07-01'
    end_date = '2025-07-31'
    df_filtered = df[(df.index >= start_date) & (df.index <= end_date)].copy()
    
    print(f"Data period: {start_date} to {end_date}")
    print(f"Total records: {len(df_filtered)}")
    print(f"Price range: {df_filtered['close'].min():.2f} - {df_filtered['close'].max():.2f}")
    
    # Prepare data for backtester (MultiIndex columns)
    symbol = 'rb2601'
    df_filtered.columns = pd.MultiIndex.from_product([[symbol], df_filtered.columns])
    
    # Configure backtester
    config = {
        'initial_capital': 1000000.0,
        'start_date': start_date,
        'end_date': end_date,
        'data_frequency': '120m',
        'position_sizing_pct': 0.1
    }
    
    strategy = MA16Strategy()
    backtester = VectorizedBacktester(**config)
    
    # Run backtest
    print("\nRunning backtest...")
    results = backtester.run(df_filtered, strategy)
    
    # Print results
    if "kpis" in results:
        print("\n=== BACKTEST RESULTS ===")
        print(f"Total trades: {len(results['trade_log'])}")
        print("\nKey Performance Indicators:")
        for key, value in results['kpis'].items():
            print(f"  {key}: {value}")
        
        print("\n=== TRADE LOG ===")
        trade_log = results['trade_log']
        for i, trade in enumerate(trade_log[:10]):  # Show first 10 trades
            print(f"Trade {i+1}: {trade['entry_date']} - {trade['action']} at {trade['entry_price']:.2f}")
            if 'exit_date' in trade and trade['exit_date']:
                print(f"         Exit: {trade['exit_date']} at {trade['exit_price']:.2f}, P&L: {trade['pnl']:.2f}")
        
        # Show equity curve
        print(f"\n=== EQUITY CURVE (first/last 5 records) ===")
        equity_curve = results['equity_curve']
        print("First 5:")
        print(equity_curve.head())
        print("Last 5:")
        print(equity_curve.tail())
        
        # Check specific dates mentioned by user
        print(f"\n=== SPECIFIC DATE ANALYSIS ===")
        target_dates = ['2025-07-09', '2025-07-16', '2025-07-25', '2025-07-31']
        
        for date_str in target_dates:
            date = pd.to_datetime(date_str)
            # Check if we have trades on or near these dates
            trades_near_date = [t for t in trade_log if abs((pd.to_datetime(t['entry_date']) - date).days) <= 1]
            if trades_near_date:
                print(f"{date_str}: Found {len(trades_near_date)} trades nearby")
                for trade in trades_near_date:
                    print(f"  {trade['entry_date']}: {trade['action']} at {trade['entry_price']:.2f}")
            else:
                print(f"{date_str}: No trades found")
    else:
        print("Backtest failed:")
        print(results.get("message", "Unknown error"))

if __name__ == '__main__':
    test_rb2601_backtest()