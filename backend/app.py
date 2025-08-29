from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import akshare as ak
import traceback
import logging
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

def get_dynamic_kline(instrument, period):
    """
    根据周期动态获取K线数据。
    """
    if 'm' in period:
        minutes = period.replace('m', '')
        return ak.futures_zh_minute_sina(symbol=instrument, period=minutes)
    else:
        df = ak.futures_zh_daily_sina(symbol=instrument)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        if period == '1d':
            return df.reset_index()
        
        # 移除3d和4d
        resample_map = {'2d': '2D', '1w': 'W'}
        rule = resample_map.get(period)
        if not rule: return pd.DataFrame()

        resampled_df = df['close'].resample(rule).last()
        resampled_df = pd.DataFrame(resampled_df)
        resampled_df['open'] = df['open'].resample(rule).first()
        resampled_df['high'] = df['high'].resample(rule).max()
        resampled_df['low'] = df['low'].resample(rule).min()
        return resampled_df.dropna().reset_index()

@app.route('/api/strategy', methods=['POST'])
def run_strategy():
    try:
        data = request.get_json()
        instrument_code = data.get('instrument')
        period = data.get('period')

        if not instrument_code or not period:
            return jsonify({"error": "缺少合约代码或周期参数"}), 400

        hist_df = get_dynamic_kline(instrument_code, period)
        
        if 'datetime' in hist_df.columns:
            hist_df.rename(columns={'datetime': 'date'}, inplace=True)
        
        if len(hist_df) < 17:
            return jsonify({"error": f"数据不足，无法在周期 {period} 上生成信号。"}), 404

        for col in ['open', 'high', 'low', 'close']:
            hist_df[col] = pd.to_numeric(hist_df[col])
        
        hist_df['ma16'] = hist_df['close'].rolling(window=16).mean()
        hist_df['ma_slope'] = hist_df['ma16'].diff()
        
        slope_threshold = hist_df['ma16'].mean() * 0.0005
        hist_df['direction'] = np.where(hist_df['ma_slope'] > slope_threshold, 'up', 
                                       np.where(hist_df['ma_slope'] < -slope_threshold, 'down', 'flat'))
        
        latest_data = hist_df.iloc[-1]
        action_en = "hold"
        price = 0

        if latest_data['direction'] == 'up':
            action_en = 'buy'
            price = latest_data['ma16']
        elif latest_data['direction'] == 'down':
            action_en = 'sell'
            price = latest_data['ma16']
        elif latest_data['direction'] == 'flat':
            action_en = 'close'
            price = latest_data['close']

        action_map = {'buy': '多开', 'sell': '空开', 'close': '平仓', 'hold': '观望'}
        action_cn = action_map.get(action_en, '观望')

        response = {
            "instrument": instrument_code,
            "period": period,
            "action": action_cn,
            "price": round(price, 2),
            "timestamp": pd.to_datetime(latest_data['date']).isoformat()
        }
        return jsonify(response)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"生成策略时发生错误: {e}"}), 500

@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    data = request.get_json()
    instrument_code = data.get('instrument')
    period = data.get('period')
    start_date_str = data.get('start_date', '')
    end_date_str = data.get('end_date', '')
    initial_capital = float(data.get('initial_capital', 100000))
    
    if not all([instrument_code, period, start_date_str, end_date_str]):
        return jsonify({"error": "缺少回测参数"}), 400

    try:
        hist_df = get_dynamic_kline(instrument_code, period)
        
        if 'datetime' in hist_df.columns:
            hist_df.rename(columns={'datetime': 'date'}, inplace=True)
        
        hist_df['date_str'] = pd.to_datetime(hist_df['date']).dt.strftime('%Y-%m-%d')
        mask = (hist_df['date_str'] >= start_date_str) & (hist_df['date_str'] <= end_date_str)
        hist_df = hist_df.loc[mask].copy()

        if len(hist_df) < 17:
            return jsonify({"error": f"数据不足，无法在周期 {period} 上进行回测。"}), 404

        for col in ['open', 'high', 'low', 'close']:
            hist_df[col] = pd.to_numeric(hist_df[col])
        
        hist_df['ma16'] = hist_df['close'].rolling(window=16).mean()
        hist_df['ma_slope'] = hist_df['ma16'].diff()
        
        slope_threshold = hist_df['ma16'].mean() * 0.0005
        hist_df['direction'] = np.where(hist_df['ma_slope'] > slope_threshold, 'up', 
                                       np.where(hist_df['ma_slope'] < -slope_threshold, 'down', 'flat'))
        
        capital = initial_capital
        position = 0
        entry_price = 0
        trade_log = []

        for i in range(16, len(hist_df)):
            current_row = hist_df.iloc[i]
            
            if position == 0:
                if current_row['direction'] == 'up' and current_row['low'] <= current_row['ma16']:
                    entry_price = current_row['ma16']
                    position = capital / entry_price
                    trade_log.append(f"{current_row['date_str']}: 开多 @ {entry_price:.2f}")
                elif current_row['direction'] == 'down' and current_row['high'] >= current_row['ma16']:
                    entry_price = current_row['ma16']
                    position = - (capital / entry_price)
                    trade_log.append(f"{current_row['date_str']}: 开空 @ {entry_price:.2f}")
            
            elif position != 0:
                if current_row['direction'] == 'flat':
                    exit_price = current_row['close'] # 修正平仓价格
                    if position > 0:
                        capital = position * exit_price
                        trade_log.append(f"{current_row['date_str']}: 平多仓 @ {exit_price:.2f}")
                    else:
                        profit = (entry_price - exit_price) * abs(position)
                        capital_at_entry = abs(position) * entry_price
                        capital = capital_at_entry + profit
                        trade_log.append(f"{current_row['date_str']}: 平空仓 @ {exit_price:.2f}")
                    position = 0
                    entry_price = 0

        if position > 0:
            final_capital = position * hist_df['close'].iloc[-1]
        elif position < 0:
            profit = (entry_price - hist_df['close'].iloc[-1]) * abs(position)
            capital_at_entry = abs(position) * entry_price
            final_capital = capital_at_entry + profit
        else:
            final_capital = capital

        total_return = (final_capital - initial_capital) / initial_capital
        daily_returns = hist_df['close'].pct_change().dropna()
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() != 0 else 0

        response = {
            "instrument": instrument_code,
            "time_range": f"{start_date_str} to {end_date_str}",
            "initial_capital": initial_capital,
            "final_capital": round(final_capital, 2),
            "total_return_pct": round(total_return * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "trade_count": len(trade_log),
            "trades": trade_log[-10:]
        }
        return jsonify(response)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"回测时发生错误: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
