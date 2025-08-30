from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import akshare as ak
import traceback
import logging
import numpy as np
from datetime import datetime

# 导入新的回测引擎
from backtester import VectorizedBacktester, MA16Strategy

# 配置日志
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

def _normalize_price_series(price_series):
    """将价格序列归一化 - 使用百分比变化法"""
    # 不使用滑动窗口归一化，改用相对变化率
    # 以第一个有效值为基准，计算相对变化
    first_valid_idx = price_series.first_valid_index()
    if first_valid_idx is None:
        return price_series
    
    base_price = price_series.loc[first_valid_idx]
    if base_price == 0:
        return price_series * 0  # 避免除零
    
    # 计算相对于基准价格的变化率，然后缩放到合适的范围
    normalized = (price_series - base_price) / base_price * 1000  # 乘以1000放大变化
    return normalized

def _calculate_tangent_angle(data_df, slope_lookback):
    """计算均线的切线角度 - 基于百分比变化率"""
    import math
    
    angles = pd.Series(index=data_df.index, dtype=float)
    
    for i in range(slope_lookback, len(data_df)):
        # 取当前点和前slope_lookback个点
        current_idx = i
        prev_idx = i - slope_lookback
        
        # X轴：时间单位差
        dx = slope_lookback
        
        # Y轴：归一化价格差（现在是相对变化率*1000）
        y_current = data_df['ma_normalized'].iloc[current_idx]
        y_prev = data_df['ma_normalized'].iloc[prev_idx]
        dy = y_current - y_prev
        
        # 计算斜率和角度（弧度转度数）
        if dx != 0 and not (pd.isna(dy) or pd.isna(y_current) or pd.isna(y_prev)):
            slope = dy / dx  # dy是相对变化率差值，已经按比例缩放
            angle_radians = math.atan(slope)
            angle_degrees = math.degrees(angle_radians)
            angles.iloc[current_idx] = angle_degrees
    
    return angles

def get_futures_data(symbol, period, start_date, end_date, use_continuous):
    """
    动态获取期货K线数据，支持具体合约和主力连续合约，并正确处理分钟和日线周期。
    """
    symbol_to_fetch = symbol
    if use_continuous:
        product_code = ''.join(filter(str.isalpha, symbol))
        symbol_to_fetch = f"{product_code}0"

    df = pd.DataFrame()
    # 检查周期是分钟还是日
    if 'm' in period:
        # 获取分钟级别数据
        minutes = period.replace('m', '')
        df = ak.futures_zh_minute_sina(symbol=symbol_to_fetch, period=minutes)
        if df.empty: return pd.DataFrame()
        df.rename(columns={'datetime': 'date'}, inplace=True)
    else:
        # 获取日级别数据
        df = ak.futures_zh_daily_sina(symbol=symbol_to_fetch)
        if df.empty: return pd.DataFrame()

    # 统一处理和筛选
    df['date'] = pd.to_datetime(df['date'])
    df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
    
    if df.empty:
        return pd.DataFrame()

    df.set_index('date', inplace=True)
    
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col])

    # 对于非 '1d' 的日内重采样逻辑可以放在这里，但当前策略直接使用原生周期
    # ...

    return df

@app.route('/api/strategy', methods=['POST'])
def run_strategy():
    try:
        data = request.get_json()
        instrument_code = data.get('instrument')
        period = data.get('period')

        if not instrument_code or not period:
            return jsonify({"error": "缺少合约代码或周期参数"}), 400

        # 修复：为实时策略提供一个独立的、快速的数据获取路径
        if 'm' in period:
            minutes = period.replace('m', '')
            hist_df = ak.futures_zh_minute_sina(symbol=instrument_code, period=minutes)
            hist_df.rename(columns={'datetime': 'date'}, inplace=True)
        else:
            hist_df = ak.futures_zh_daily_sina(symbol=instrument_code)


        if len(hist_df) < 17:
            return jsonify({"error": f"数据不足，无法在周期 {period} 上生成信号。"}), 404

        for col in ['open', 'high', 'low', 'close']:
            hist_df[col] = pd.to_numeric(hist_df[col])
        
        # 策略参数
        ma_period = 16
        slope_lookback = 3
        angle_threshold = 1  # 角度阈值（度）
        
        # 计算SMA
        hist_df['sma16'] = hist_df['close'].rolling(window=ma_period).mean()
        
        # 计算价格相对区间 (归一化)
        hist_df['ma_normalized'] = _normalize_price_series(hist_df['sma16'])
        
        # 计算切线角度
        hist_df['slope_angle'] = _calculate_tangent_angle(hist_df, slope_lookback)
        
        # 获取最新数据点
        latest_data = hist_df.iloc[-1]
        
        action_en = "hold"
        price = latest_data['close']
        
        # 检查数据有效性
        if pd.isna(latest_data['sma16']) or pd.isna(latest_data['slope_angle']):
            # 数据不足，返回观望
            pass
        else:
            # 获取当前数据
            current_sma = latest_data['sma16']
            current_angle = latest_data['slope_angle']
            
            # 基于切线角度判断市场状态
            if current_angle > angle_threshold:
                market_state = 'uptrend'  # 上涨趋势
            elif current_angle < -angle_threshold:
                market_state = 'downtrend'  # 下跌趋势
            else:
                market_state = 'sideways'  # 横盘状态（±10度内）
            
            # 实时策略逻辑：根据趋势方向直接给出建议和目标价
            if market_state == 'uptrend':
                # 上涨趋势 -> 建议做多，目标价为16均线
                action_en = 'buy'
                price = current_sma
            elif market_state == 'downtrend':
                # 下跌趋势 -> 建议做空，目标价为16均线
                action_en = 'sell'
                price = current_sma
            elif market_state == 'sideways':
                # 横盘状态 -> 观望，返回收盘价
                action_en = 'hold'
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
def run_backtest_new():
    try:
        data = request.get_json()
        
        # 解析前端传来的所有参数
        instrument_code = data.get('instrument')
        period = data.get('period')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        initial_capital = float(data.get('initial_capital', 1000000))
        position_sizing_pct = float(data.get('position_sizing_pct', 10)) / 100.0
        use_continuous = data.get('use_continuous_contract', False)

        if not all([instrument_code, period, start_date, end_date]):
            return jsonify({"error": "缺少回测参数"}), 400

        # 1. 获取历史数据
        symbol_to_fetch = instrument_code
        if use_continuous:
            # 如果使用加权合约，从具体合约代码中提取品种代码 (e.g., cu2410 -> cu)
            symbol_to_fetch = ''.join(filter(str.isalpha, instrument_code))

        hist_df = get_futures_data(symbol_to_fetch, period, start_date, end_date, use_continuous)

        if hist_df.empty or len(hist_df) < 17:
            return jsonify({"error": "在指定时间范围内数据不足，无法进行回测。"}), 404
        
        # 2. 准备回测引擎所需的数据格式 (MultiIndex)
        hist_df.columns = pd.MultiIndex.from_product([[instrument_code], hist_df.columns])

        # 3. 配置并实例化回测引擎和策略
        config = {
            'initial_capital': initial_capital,
            'start_date': start_date,
            'end_date': end_date,
            'data_frequency': period,
            'position_sizing_pct': position_sizing_pct
        }
        strategy = MA16Strategy()
        backtester = VectorizedBacktester(**config)

        # 4. 运行回测
        results = backtester.run(hist_df, strategy)

        # 5. 格式化结果为JSON
        if "kpis" in results:
            # 将DataFrame转换为JSON兼容的格式
            results['trade_log'] = results['trade_log'].to_dict(orient='records')
            results['equity_curve'] = results['equity_curve'].reset_index().to_dict(orient='records')
            return jsonify(results)
        else:
            return jsonify({"error": results.get("message", "回测失败")}), 500

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"回测时发生严重错误: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
