import pandas as pd
import akshare as ak
import numpy as np
import math

def debug_angle_calculation():
    """Debug the angle calculation for rb2601 120m data"""
    
    # Get rb2601 120-minute data
    print("Getting rb2601 120-minute data...")
    df = ak.futures_zh_minute_sina(symbol='rb2601', period='120')
    df.rename(columns={'datetime': 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # Convert to numeric
    for col in ['open', 'high', 'low', 'close']:
        df[col] = pd.to_numeric(df[col])
    
    # Filter to July 2025 period
    start_date = '2025-07-01'
    end_date = '2025-07-31' 
    df_filtered = df[(df.index >= start_date) & (df.index <= end_date)]
    
    print(f"Data from {start_date} to {end_date}: {len(df_filtered)} records")
    
    # Calculate SMA16
    df_filtered['sma16'] = df_filtered['close'].rolling(window=16).mean()
    
    # Debug normalization - NEW METHOD
    print("\n=== DEBUG NORMALIZATION (NEW METHOD) ===")
    first_valid_idx = df_filtered['sma16'].first_valid_index()
    if first_valid_idx is not None:
        base_price = df_filtered['sma16'].loc[first_valid_idx]
        print(f"Base price: {base_price:.2f}")
        
        # Calculate relative change rate
        df_filtered['ma_normalized'] = (df_filtered['sma16'] - base_price) / base_price * 1000
    else:
        df_filtered['ma_normalized'] = df_filtered['sma16'] * 0
    
    print(f"Normalized MA range: {df_filtered['ma_normalized'].min():.6f} - {df_filtered['ma_normalized'].max():.6f}")
    
    # Debug angle calculation
    print("\n=== DEBUG ANGLE CALCULATION ===")
    slope_lookback = 3
    angles = pd.Series(index=df_filtered.index, dtype=float)
    
    # Check specific dates
    target_dates = ['2025-07-09', '2025-07-16', '2025-07-25', '2025-07-31']
    
    for i in range(slope_lookback, len(df_filtered)):
        current_idx = i
        prev_idx = i - slope_lookback
        
        dx = slope_lookback
        y_current = df_filtered['ma_normalized'].iloc[current_idx]
        y_prev = df_filtered['ma_normalized'].iloc[prev_idx]
        dy = y_current - y_prev
        
        current_date = df_filtered.index[current_idx].strftime('%Y-%m-%d')
        
        # Print details for target dates
        if current_date in target_dates:
            print(f"\nDate: {current_date}")
            print(f"  Current MA: {df_filtered['sma16'].iloc[current_idx]:.2f}")
            print(f"  Previous MA: {df_filtered['sma16'].iloc[prev_idx]:.2f}")
            print(f"  Current MA normalized: {y_current:.8f}")
            print(f"  Previous MA normalized: {y_prev:.8f}")
            print(f"  dy: {dy:.8f}")
            print(f"  dx: {dx}")
        
        if dx != 0 and not (pd.isna(dy) or pd.isna(y_current) or pd.isna(y_prev)):
            slope = dy / dx
            angle_radians = math.atan(slope)
            angle_degrees = math.degrees(angle_radians)
            angles.iloc[current_idx] = angle_degrees
            
            if current_date in target_dates:
                print(f"  slope: {slope:.8f}")
                print(f"  angle_degrees: {angle_degrees:.4f}")
        else:
            if current_date in target_dates:
                print(f"  SKIPPED: dx={dx}, dy={dy}, y_current={y_current}, y_prev={y_prev}")
    
    df_filtered['slope_angle'] = angles
    
    # Show results for target dates
    print("\n=== RESULTS FOR TARGET DATES ===")
    for date_str in target_dates:
        try:
            date = pd.to_datetime(date_str)
            if date in df_filtered.index:
                row = df_filtered.loc[date]
                print(f"{date_str}: Close={row['close']:.2f}, SMA16={row['sma16']:.2f}, Angle={row['slope_angle']:.4f}°")
            else:
                print(f"{date_str}: Date not found in data")
        except:
            print(f"{date_str}: Error accessing data")
    
    # Show price movement
    print("\n=== PRICE MOVEMENT ===")
    july_data = df_filtered[df_filtered.index.month == 7]
    if len(july_data) > 0:
        print(f"July price range: {july_data['close'].min():.2f} - {july_data['close'].max():.2f}")
        print(f"First July close: {july_data['close'].iloc[0]:.2f}")
        print(f"Last July close: {july_data['close'].iloc[-1]:.2f}")
        print(f"Price change: {july_data['close'].iloc[-1] - july_data['close'].iloc[0]:.2f}")

if __name__ == '__main__':
    debug_angle_calculation()