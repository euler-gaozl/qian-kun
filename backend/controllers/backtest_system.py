"""回测系统控制器"""
from typing import Dict, Any, List
import logging
from datetime import datetime
import pandas as pd
import time
from services.kline_service import KlineService
from strategies.core_strategy import CoreStrategy
from portfolio.portfolio_manager import PortfolioManager
from models.domain_models import SignalType
from models.request_models import BacktestRequest
from models.response_models import BacktestResponse, BacktestStatistics

logger = logging.getLogger(__name__)


class BacktestSystemController:
    """
    回测系统控制器
    负责执行完整的回测流程
    """
    
    def __init__(self):
        """初始化控制器"""
        self.kline_service = KlineService()
        self.core_strategy = None
        self.portfolio_manager = None
        
    def handle_request(self, request: BacktestRequest) -> BacktestResponse:
        """
        处理回测请求
        
        Args:
            request: 回测请求对象
            
        Returns:
            回测响应对象
        """
        start_time = time.time()
        
        try:
            # 拼接完整的合约代码
            full_symbol = f"{request.symbol}{request.contract}"
            logger.info(f"开始回测: {full_symbol}, 周期: {request.period}, "
                       f"日期: {request.start_date} 至 {request.end_date}")
            
            # 初始化策略和资金管理器
            self.core_strategy = CoreStrategy()
            self.portfolio_manager = PortfolioManager(
                initial_capital=request.initial_capital,
                position_pct=request.position_pct / 100.0
            )
            
            # 获取历史K线数据
            klines_df = self.kline_service.get_historical_klines(
                symbol=full_symbol,
                period=request.period,
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            if klines_df.empty or len(klines_df) < request.ma_period * 2:
                logger.error(f"历史数据不足: {full_symbol}")
                raise ValueError(f"历史数据不足，需要至少 {request.ma_period * 2} 根K线")
            
            # 计算所有K线的MA值
            klines_df = self.kline_service.calculate_ma_values_from_klines(klines_df, request.ma_period)
            klines_df[f'ma{request.ma_period}'].fillna(method='bfill', inplace=True)
            
            # 执行回测
            self._run_backtest(klines_df, request.symbol, full_symbol, request.ma_period)
            
            # 获取统计数据
            metrics = self.portfolio_manager.get_performance_metrics()
            
            # 构造统计对象
            statistics = BacktestStatistics(
                total_trades=metrics['total_trades'],
                winning_trades=metrics['winning_trades'],
                losing_trades=metrics['losing_trades'],
                win_rate=round(metrics['win_rate'], 2),
                profit_factor=round(metrics['profit_factor'], 2),
                total_profit=round(metrics['total_profit'], 2),
                total_return=round(metrics['total_return'], 2),
                max_drawdown=round(metrics['max_drawdown'], 2),
                sharpe_ratio=round(metrics['sharpe_ratio'], 2),
                initial_capital=metrics['initial_capital'],
                final_capital=round(metrics['final_capital'], 2),
                avg_profit=round(metrics['avg_profit'], 2),
                avg_loss=round(metrics['avg_loss'], 2),
                max_consecutive_wins=metrics['max_consecutive_wins'],
                max_consecutive_losses=metrics['max_consecutive_losses']
            )
            
            # 构造响应
            response = BacktestResponse(
                statistics=statistics,
                trades=self.portfolio_manager.trade_history,
                equity_curve=self.portfolio_manager.equity_curve,
                parameters={
                    'symbol': request.symbol,
                    'contract': request.contract,
                    'period': request.period,
                    'ma_period': request.ma_period,
                    'position_pct': request.position_pct
                },
                execution_time=round(time.time() - start_time, 2),
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            logger.info(f"回测完成: 总交易 {statistics.total_trades} 次, "
                       f"胜率 {statistics.win_rate}%, 总收益 {statistics.total_profit}")
            
            return response
            
        except Exception as e:
            logger.error(f"回测失败: {e}")
            raise
    
    def _run_backtest(self, klines_df: pd.DataFrame, symbol: str, contract: str, ma_period: int):
        """
        执行回测核心逻辑
        
        Args:
            klines_df: K线数据DataFrame（包含MA值）
            symbol: 品种代码
            contract: 合约代码
            ma_period: MA周期
        """
        # 需要 2n-1 个K线来计算n个MA值
        lookback = ma_period * 2 - 1
        
        # 从第 lookback 个K线开始遍历
        for i in range(lookback - 1, len(klines_df)):
            # 获取当前K线
            current_kline = klines_df.iloc[i]
            current_time = pd.to_datetime(current_kline['timestamp'])
            
            # 获取用于计算的K线切片（当前和之前的 lookback-1 个）
            kline_slice = klines_df.iloc[i - lookback + 1:i + 1]
            
            # 提取MA值列表
            ma_values = kline_slice[f'ma{ma_period}'].tolist()
            
            # 只使用最近的 ma_period 个MA值进行判断
            ma_values_for_signal = ma_values[-ma_period:] if len(ma_values) >= ma_period else ma_values
            
            # 获取交易信号
            signal_type, market_state, reason = self.core_strategy.get_signal(ma_values_for_signal)
            
            # 更新持仓价格（用于计算浮动盈亏）
            self.portfolio_manager.update_position_price(current_kline['close'], current_time)
            
            # 处理交易信号
            if signal_type == SignalType.BUY:
                # 检查MA价格是否在K线高低范围内（回踩条件）
                ma_price = ma_values_for_signal[-1]
                if current_kline['low'] <= ma_price <= current_kline['high']:
                    trade = self.portfolio_manager.open_position(
                        symbol=symbol,
                        contract=contract,
                        direction='long',
                        price=ma_price,
                        timestamp=current_time
                    )
                    # 只有开仓成功后才更新策略的持仓方向
                    if trade is not None:
                        self.core_strategy.position_direction = 'long'
                        logger.info(f"开多仓成功，更新持仓方向为long")
                    
            elif signal_type == SignalType.SELL:
                # 检查MA价格是否在K线高低范围内
                ma_price = ma_values_for_signal[-1]
                if current_kline['low'] <= ma_price <= current_kline['high']:
                    trade = self.portfolio_manager.open_position(
                        symbol=symbol,
                        contract=contract,
                        direction='short',
                        price=ma_price,
                        timestamp=current_time
                    )
                    # 只有开仓成功后才更新策略的持仓方向
                    if trade is not None:
                        self.core_strategy.position_direction = 'short'
                        logger.info(f"开空仓成功，更新持仓方向为short")
                    
            elif signal_type == SignalType.CLOSE:
                # 以收盘价平仓
                if self.portfolio_manager.current_position:
                    self.portfolio_manager.close_position(
                        price=current_kline['close'],
                        timestamp=current_time
                    )
                    # 平仓成功后清除策略的持仓方向
                    self.core_strategy.position_direction = None
                    logger.info(f"平仓成功，清除持仓方向")
        
        # 回测结束时，如果还有持仓，以最后一根K线的收盘价平仓
        if self.portfolio_manager.current_position:
            last_kline = klines_df.iloc[-1]
            last_time = pd.to_datetime(last_kline['timestamp'])
            self.portfolio_manager.close_position(
                price=last_kline['close'],
                timestamp=last_time
            )
            # 清除策略中的持仓方向
            self.core_strategy.position_direction = None
            logger.info("回测结束，平仓所有持仓")
