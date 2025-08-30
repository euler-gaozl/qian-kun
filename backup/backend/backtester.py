import pandas as pd
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod
from collections import defaultdict
from math import floor

# --- 1. 辅助数据结构 ---

@dataclass
class Position:
    """ 用于记录单笔持仓的数据结构 """
    entry_time: datetime
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    lots: int
    margin_used: float
    contract_multiplier: int

@dataclass
class Trade:
    """ 用于记录一笔完整交易（开仓到平仓）的数据结构 """
    entry_time: datetime
    exit_time: datetime
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    lots: int
    profit_loss: float
    commission: float = 0.0 # 可选：为未来扩展保留

# --- 2. 策略基类 (Strategy Interface) ---

class Strategy(ABC):
    """ 策略接口基类 """
    def __init__(self):
        self.data = None
        self.signals = None

    def fit(self, data: pd.DataFrame):
        """ 策略可以预计算所有信号，以加速回测循环 """
        self.data = data.copy()
        self._calculate_indicators()
        self.signals = self._generate_signals()

    @abstractmethod
    def _calculate_indicators(self):
        """ 计算策略所需的技术指标 """
        pass

    @abstractmethod
    def _generate_signals(self) -> pd.Series:
        """
        生成交易信号序列。
        返回一个Pandas Series，索引为时间，值为 'buy', 'sell', 'close' 或 None。
        """
        pass

# --- 3. MA16 策略实现 ---

class MA16Strategy(Strategy):
    """ 均线方向回踩策略 - 使用切线斜率判断方向 """
    def __init__(self, ma_period=16, slope_lookback=3, angle_threshold=1):
        super().__init__()
        self.ma_period = ma_period
        self.slope_lookback = slope_lookback
        self.angle_threshold = angle_threshold  # 角度阈值（度）
        
    def _calculate_indicators(self):
        # 计算SMA
        self.data['sma16'] = self.data['close'].rolling(window=self.ma_period).mean()
        
        # 计算价格相对区间 (归一化到0-1之间)
        self.data['ma_normalized'] = self._normalize_price_series(self.data['sma16'])
        
        # 计算切线斜率和角度
        self.data['slope_angle'] = self._calculate_tangent_angle()
    
    def _normalize_price_series(self, price_series):
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
    
    def _calculate_tangent_angle(self):
        """计算均线的切线角度 - 基于百分比变化率"""
        import math
        
        angles = pd.Series(index=self.data.index, dtype=float)
        
        for i in range(self.slope_lookback, len(self.data)):
            # 取当前点和前slope_lookback个点
            current_idx = i
            prev_idx = i - self.slope_lookback
            
            # X轴：时间单位差
            dx = self.slope_lookback
            
            # Y轴：归一化价格差（现在是相对变化率*1000）
            y_current = self.data['ma_normalized'].iloc[current_idx]
            y_prev = self.data['ma_normalized'].iloc[prev_idx]
            dy = y_current - y_prev
            
            # 计算斜率和角度（弧度转度数）
            if dx != 0 and not (pd.isna(dy) or pd.isna(y_current) or pd.isna(y_prev)):
                slope = dy / dx  # dy是相对变化率差值，已经按比例缩放
                angle_radians = math.atan(slope)
                angle_degrees = math.degrees(angle_radians)
                angles.iloc[current_idx] = angle_degrees
        
        return angles

    def _generate_signals(self) -> pd.Series:
        # 确保有足够的数据来计算指标
        if 'sma16' not in self.data.columns or self.data['sma16'].isnull().all():
            return pd.Series(index=self.data.index, dtype=object)
            
        signals = pd.Series(index=self.data.index, dtype=object)
        
        # 从有足够数据的地方开始计算信号
        start_idx = max(self.ma_period, self.slope_lookback)
        
        for i in range(start_idx, len(self.data)):
            current_idx = self.data.index[i]
            
            # 获取当前K线数据
            current_high = self.data.loc[current_idx, 'high']
            current_low = self.data.loc[current_idx, 'low']
            current_sma = self.data.loc[current_idx, 'sma16']
            current_angle = self.data.loc[current_idx, 'slope_angle']
            
            # 如果sma或angle是NaN，跳过
            if pd.isna(current_sma) or pd.isna(current_angle):
                continue
                
            # 基于切线角度判断市场状态
            if current_angle > self.angle_threshold:
                market_state = 'uptrend'  # 上涨趋势
            elif current_angle < -self.angle_threshold:
                market_state = 'downtrend'  # 下跌趋势
            else:
                market_state = 'sideways'  # 横盘状态（±10度内）
            
            # 判断K线是否穿过均线
            kline_crosses_ma = (current_low <= current_sma <= current_high)
            
            # 基于市场状态和K线位置生成信号
            if market_state == 'uptrend' and kline_crosses_ma:
                # 上涨趋势中K线穿过均线 -> 做多信号
                signals[current_idx] = 'buy'
            elif market_state == 'downtrend' and kline_crosses_ma:
                # 下跌趋势中K线穿过均线 -> 做空信号
                signals[current_idx] = 'sell'
            elif market_state == 'sideways':
                # 横盘状态（±10度内） -> 平仓信号
                signals[current_idx] = 'close'
        
        return signals

# --- 4. VectorizedBacktester 核心类 ---

class VectorizedBacktester:
    """
    事件驱动的向量化期货回测引擎。
    """
    def __init__(self, initial_capital: float, start_date: str, end_date: str, 
                 data_frequency: str, position_sizing_pct: float):
        self.initial_capital = float(initial_capital)
        self.cash = float(initial_capital)
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.data_frequency = data_frequency
        self.position_sizing_pct = position_sizing_pct

        self.positions = defaultdict(list)
        self.completed_trades = []
        self.equity_curve = []
        self.symbols = []

    def _get_instrument_info(self, symbol: str):
        """ 辅助函数：获取品种的保证金率和合约乘数 """
        info = {
            # 上海期货交易所
            'cu': {'margin_rate': 0.12, 'multiplier': 5},      # 铜
            'al': {'margin_rate': 0.10, 'multiplier': 5},      # 铝
            'zn': {'margin_rate': 0.10, 'multiplier': 5},      # 锌
            'pb': {'margin_rate': 0.10, 'multiplier': 5},      # 铅
            'ni': {'margin_rate': 0.15, 'multiplier': 1},      # 镍
            'sn': {'margin_rate': 0.12, 'multiplier': 1},      # 锡
            'au': {'margin_rate': 0.08, 'multiplier': 1000},   # 黄金
            'ag': {'margin_rate': 0.10, 'multiplier': 15},     # 白银
            'rb': {'margin_rate': 0.10, 'multiplier': 10},     # 螺纹钢
            'hc': {'margin_rate': 0.10, 'multiplier': 10},     # 热轧卷板
            'sc': {'margin_rate': 0.12, 'multiplier': 1000},   # 原油
            'fu': {'margin_rate': 0.12, 'multiplier': 10},     # 燃料油
            'bu': {'margin_rate': 0.12, 'multiplier': 10},     # 石油沥青
            'ru': {'margin_rate': 0.12, 'multiplier': 10},     # 天然橡胶
            'sp': {'margin_rate': 0.12, 'multiplier': 10},     # 纸浆
            
            # 大连商品交易所
            'a': {'margin_rate': 0.08, 'multiplier': 10},      # 黄大豆1号
            'b': {'margin_rate': 0.08, 'multiplier': 10},      # 黄大豆2号
            'm': {'margin_rate': 0.08, 'multiplier': 10},      # 豆粕
            'y': {'margin_rate': 0.08, 'multiplier': 10},      # 豆油
            'p': {'margin_rate': 0.08, 'multiplier': 10},      # 棕榈油
            'c': {'margin_rate': 0.08, 'multiplier': 10},      # 玉米
            'cs': {'margin_rate': 0.08, 'multiplier': 10},     # 玉米淀粉
            'jd': {'margin_rate': 0.10, 'multiplier': 5},      # 鸡蛋
            'i': {'margin_rate': 0.10, 'multiplier': 100},     # 铁矿石
            'j': {'margin_rate': 0.12, 'multiplier': 100},     # 焦炭
            'jm': {'margin_rate': 0.12, 'multiplier': 60},     # 焦煤
            'l': {'margin_rate': 0.08, 'multiplier': 5},       # 聚乙烯
            'v': {'margin_rate': 0.08, 'multiplier': 5},       # 聚氯乙烯
            'pp': {'margin_rate': 0.08, 'multiplier': 5},      # 聚丙烯
            'eg': {'margin_rate': 0.08, 'multiplier': 10},     # 乙二醇
            'eb': {'margin_rate': 0.08, 'multiplier': 5},      # 苯乙烯
            
            # 郑州商品交易所
            'SR': {'margin_rate': 0.08, 'multiplier': 10},     # 白糖
            'CF': {'margin_rate': 0.08, 'multiplier': 5},      # 棉花
            'TA': {'margin_rate': 0.08, 'multiplier': 5},      # PTA
            'MA': {'margin_rate': 0.08, 'multiplier': 10},     # 甲醇
            'SA': {'margin_rate': 0.08, 'multiplier': 20},     # 纯碱
            'OI': {'margin_rate': 0.08, 'multiplier': 10},     # 菜籽油
            'RM': {'margin_rate': 0.08, 'multiplier': 10},     # 菜籽粕
            'FG': {'margin_rate': 0.08, 'multiplier': 20},     # 玻璃
            'AP': {'margin_rate': 0.10, 'multiplier': 10},     # 苹果
            'CJ': {'margin_rate': 0.10, 'multiplier': 5},      # 红枣
            
            # 广州期货交易所
            'si': {'margin_rate': 0.12, 'multiplier': 1},      # 工业硅
            'lc': {'margin_rate': 0.12, 'multiplier': 1},      # 碳酸锂
        }
        product_code = ''.join(filter(str.isalpha, symbol))
        return info.get(product_code, {'margin_rate': 0.15, 'multiplier': 10})

    def _update_equity(self, current_timestamp, current_prices: pd.Series):
        """ 在每个时间点更新总权益 """
        unrealized_pnl = 0
        for symbol, pos_list in self.positions.items():
            if not pos_list or symbol not in current_prices: continue
            
            current_price = current_prices[symbol]
            multiplier = pos_list[0].contract_multiplier
            
            for pos in pos_list:
                pnl_per_lot = (current_price - pos.entry_price) * multiplier
                if pos.direction == 'short':
                    pnl_per_lot *= -1
                unrealized_pnl += pnl_per_lot * pos.lots
        
        current_equity = self.cash + unrealized_pnl
        self.equity_curve.append({'timestamp': current_timestamp, 'equity': current_equity})
        return current_equity

    def run(self, data: pd.DataFrame, strategy: Strategy):
        """ 执行回测的核心循环 """
        self.symbols = data.columns.get_level_values(0).unique()
        data = data.loc[self.start_date:self.end_date].copy()
        
        all_signals = {}
        for symbol in self.symbols:
            symbol_data = data[symbol].copy()
            strategy.fit(symbol_data)
            all_signals[symbol] = strategy.signals
        
        # 记录每个品种的最近开仓时间，用于去重（前4个K线内不重复开仓）
        last_entry_times = {}
        
        def can_enter_position(symbol, current_index, signal_type):
            """检查是否可以开仓（避免4个K线内重复开同方向仓位）"""
            if symbol not in last_entry_times:
                return True
            
            last_entries = last_entry_times[symbol]
            current_time = data.index[current_index]
            
            # 检查最近4个K线内是否有同方向的开仓
            for entry_time, entry_signal in last_entries:
                if entry_signal == signal_type:
                    # 计算K线间隔
                    time_diff_bars = current_index - data.index.get_loc(entry_time)
                    if time_diff_bars <= 4:
                        return False
            return True

        for i in range(len(data) - 1):
            current_time = data.index[i]

            # --- 交易时间过滤 ---
            time_only = current_time.time()
            is_trading_hour = (
                (pd.to_datetime('09:00').time() <= time_only <= pd.to_datetime('11:30').time()) or
                (pd.to_datetime('13:30').time() <= time_only <= pd.to_datetime('15:00').time()) or
                (pd.to_datetime('21:00').time() <= time_only <= pd.to_datetime('23:00').time())
            )
            # 如果是日线数据，则总是认为是交易时间
            if self.data_frequency not in ['5m', '15m', '30m', '60m', '120m', '240m']:
                is_trading_hour = True

            next_bar_open_prices = data.iloc[i+1].xs('open', level=1)
            current_prices = data.iloc[i].xs('close', level=1)
            current_equity = self._update_equity(current_time, current_prices)

            if is_trading_hour:
                for symbol in self.symbols:
                    if current_time not in all_signals[symbol].index: continue
                    signal = all_signals[symbol].loc[current_time]
                    
                    if pd.isna(signal): continue  # 跳过空信号
                    
                    if signal == 'buy':
                        # 买信号处理
                        if symbol in self.positions and self.positions[symbol]:
                            # 检查当前持仓方向
                            current_direction = self.positions[symbol][0].direction
                            if current_direction == 'short':
                                # 当前持空仓，出现买信号 -> 强制平空
                                self._execute_close_position(symbol, current_prices[symbol], current_time)
                                # 平空后可以开多仓
                                can_open = True
                            else:
                                # 持多仓，检查是否可以加仓（去重逻辑）
                                can_open = can_enter_position(symbol, i, 'buy')
                        else:
                            # 无持仓，可以开仓
                            can_open = True
                        
                        # 开多仓
                        if can_open:
                            self._execute_open_position(symbol, signal, next_bar_open_prices[symbol], current_equity, current_time)
                            # 记录开仓时间
                            if symbol not in last_entry_times:
                                last_entry_times[symbol] = []
                            last_entry_times[symbol].append((current_time, 'buy'))
                            # 只保留最近10次记录，避免列表过长
                            if len(last_entry_times[symbol]) > 10:
                                last_entry_times[symbol] = last_entry_times[symbol][-10:]
                    
                    elif signal == 'sell':
                        # 卖信号处理
                        if symbol in self.positions and self.positions[symbol]:
                            # 检查当前持仓方向
                            current_direction = self.positions[symbol][0].direction
                            if current_direction == 'long':
                                # 当前持多仓，出现卖信号 -> 强制平多
                                self._execute_close_position(symbol, current_prices[symbol], current_time)
                                # 平多后可以开空仓
                                can_open = True
                            else:
                                # 持空仓，检查是否可以加仓（去重逻辑）
                                can_open = can_enter_position(symbol, i, 'sell')
                        else:
                            # 无持仓，可以开仓
                            can_open = True
                        
                        # 开空仓
                        if can_open:
                            self._execute_open_position(symbol, signal, next_bar_open_prices[symbol], current_equity, current_time)
                            # 记录开仓时间
                            if symbol not in last_entry_times:
                                last_entry_times[symbol] = []
                            last_entry_times[symbol].append((current_time, 'sell'))
                            # 只保留最近10次记录，避免列表过长
                            if len(last_entry_times[symbol]) > 10:
                                last_entry_times[symbol] = last_entry_times[symbol][-10:]
                    
                    elif signal == 'close':
                        # 平仓信号
                        if symbol in self.positions and self.positions[symbol]:
                            self._execute_close_position(symbol, current_prices[symbol], current_time)
        
        return self._calculate_performance_metrics()

    def _execute_open_position(self, symbol, signal, entry_price, current_equity, timestamp):
        info = self._get_instrument_info(symbol)
        margin_per_lot = entry_price * info['multiplier'] * info['margin_rate']
        
        if margin_per_lot <= 0: return

        capital_to_use = current_equity * self.position_sizing_pct
        num_lots = floor(capital_to_use / margin_per_lot)

        if num_lots > 0 and self.cash >= num_lots * margin_per_lot:
            direction = 'long' if signal == 'buy' else 'short'
            margin_used = num_lots * margin_per_lot
            self.cash -= margin_used
            
            new_position = Position(
                entry_time=timestamp, symbol=symbol, direction=direction,
                entry_price=entry_price, lots=num_lots, margin_used=margin_used,
                contract_multiplier=info['multiplier']
            )
            self.positions[symbol].append(new_position)

    def _execute_close_position(self, symbol, exit_price, timestamp):
        if symbol in self.positions and self.positions[symbol]:
            positions_to_close = self.positions[symbol].copy()
            self.positions[symbol] = []  # 清空持仓
            
            total_lots, total_entry_value, total_margin_used = 0, 0, 0
            for pos in positions_to_close:
                total_lots += pos.lots
                total_entry_value += pos.entry_price * pos.lots
                total_margin_used += pos.margin_used
            
            if total_lots == 0: return

            avg_entry_price = total_entry_value / total_lots
            direction = positions_to_close[0].direction
            multiplier = positions_to_close[0].contract_multiplier
            
            pnl = (exit_price - avg_entry_price) * total_lots * multiplier
            if direction == 'short': pnl *= -1
            
            self.cash += total_margin_used + pnl
            
            self.completed_trades.append(Trade(
                entry_time=positions_to_close[0].entry_time, exit_time=timestamp,
                symbol=symbol, direction=direction, entry_price=avg_entry_price,
                exit_price=exit_price, lots=total_lots, profit_loss=pnl
            ))

    def _calculate_performance_metrics(self):
        trade_log = pd.DataFrame([vars(t) for t in self.completed_trades])
        equity_curve = pd.DataFrame(self.equity_curve).set_index('timestamp')
        
        if trade_log.empty or equity_curve.empty:
            return {"message": "No trades were executed or not enough data for equity curve."}

        total_return_pct = (equity_curve['equity'].iloc[-1] / self.initial_capital - 1) * 100
        
        winning_trades = trade_log[trade_log['profit_loss'] > 0]
        losing_trades = trade_log[trade_log['profit_loss'] < 0]
        
        win_rate = len(winning_trades) / len(trade_log) if not trade_log.empty else 0
        
        avg_profit = winning_trades['profit_loss'].mean() if not winning_trades.empty else 0
        avg_loss = abs(losing_trades['profit_loss'].mean()) if not losing_trades.empty else 0
        profit_loss_ratio = avg_profit / avg_loss if avg_loss > 0 else np.inf

        equity_curve['returns'] = equity_curve['equity'].pct_change().fillna(0)
        if equity_curve['returns'].std() > 0:
            sharpe_ratio = (equity_curve['returns'].mean() / equity_curve['returns'].std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        equity_curve['peak'] = equity_curve['equity'].cummax()
        equity_curve['drawdown'] = (equity_curve['equity'] - equity_curve['peak']) / equity_curve['peak']
        max_drawdown = equity_curve['drawdown'].min() * 100

        return {
            "trade_log": trade_log,
            "kpis": {
                "yield_pct": f"{total_return_pct:.2f}%",
                "win_rate": f"{win_rate:.2%}",
                "profit_loss_ratio": f"{profit_loss_ratio:.2f}",
                "sharpe_ratio": f"{sharpe_ratio:.2f}",
                "max_drawdown": f"{max_drawdown:.2f}%",
                "total_trades": len(trade_log)
            },
            "equity_curve": equity_curve
        }
