import pandas as pd
import akshare as ak
from backtester import MA16Strategy

def debug_signal_generation():
    """Debug why signals are not being generated"""
    
    print("Debugging signal generation for rb2601...")
    
    # Get data
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
    
    print(f"Data records: {len(df_filtered)}")
    
    # Prepare data for strategy (MultiIndex)
    symbol = 'rb2601'
    df_multi = df_filtered.copy()
    df_multi.columns = pd.MultiIndex.from_product([[symbol], df_multi.columns])
    
    # Create and run strategy
    strategy = MA16Strategy()
    symbol_data = df_multi[symbol].copy()
    strategy.fit(symbol_data)
    
    # Check indicators
    print(f"\n=== INDICATORS DEBUG ===")
    print(f"SMA16 calculated: {'sma16' in strategy.data.columns}")
    print(f"MA normalized calculated: {'ma_normalized' in strategy.data.columns}")  
    print(f"Slope angle calculated: {'slope_angle' in strategy.data.columns}")
    
    if 'sma16' in strategy.data.columns:
        sma_valid = strategy.data['sma16'].notna().sum()
        print(f"Valid SMA16 values: {sma_valid}/{len(strategy.data)}")
        
    if 'slope_angle' in strategy.data.columns:
        angle_valid = strategy.data['slope_angle'].notna().sum()
        print(f"Valid angle values: {angle_valid}/{len(strategy.data)}")
        print(f"Angle range: {strategy.data['slope_angle'].min():.2f}° - {strategy.data['slope_angle'].max():.2f}°")
        
        # Show angles for specific dates
        print(f"\n=== ANGLE VALUES ===")
        july_data = strategy.data[strategy.data.index.month == 7]
        print(july_data[['close', 'sma16', 'slope_angle']].head(10))
    
    # Get generated signals
    signals = strategy.signals
    print(f"\n=== SIGNALS DEBUG ===")
    print(f"Total signals generated: {len(signals)}")
    
    # Count signal types
    signal_counts = signals.value_counts()
    print("Signal distribution:")
    for signal_type, count in signal_counts.items():
        print(f"  {signal_type}: {count}")
    
    # Show signals with context
    print(f"\n=== SIGNAL DETAILS ===")
    non_null_signals = signals[signals.notna()]
    print(f"Non-null signals: {len(non_null_signals)}")
    
    for i, (date, signal) in enumerate(non_null_signals.items()):
        if i < 10:  # Show first 10 signals
            row = strategy.data.loc[date]
            print(f"{date}: {signal} | Price: {row['close']:.2f} | SMA: {row['sma16']:.2f} | Angle: {row['slope_angle']:.2f}°")
    
    # Check angle threshold
    print(f"\n=== ANGLE THRESHOLD ANALYSIS ===")
    print(f"Strategy angle threshold: ±{strategy.angle_threshold}°")
    
    uptrend_count = (strategy.data['slope_angle'] > strategy.angle_threshold).sum()
    downtrend_count = (strategy.data['slope_angle'] < -strategy.angle_threshold).sum()
    sideways_count = (abs(strategy.data['slope_angle']) <= strategy.angle_threshold).sum()
    
    print(f"Uptrend periods (>{strategy.angle_threshold}°): {uptrend_count}")
    print(f"Downtrend periods (<-{strategy.angle_threshold}°): {downtrend_count}")
    print(f"Sideways periods (±{strategy.angle_threshold}°): {sideways_count}")

if __name__ == '__main__':
    debug_signal_generation()