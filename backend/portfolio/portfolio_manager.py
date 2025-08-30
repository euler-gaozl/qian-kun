"""投资组合管理器"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from utils.market_info import MarketInfo
from models.domain_models import Position
from models.response_models import TradeRecord

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    投资组合管理器
    负责资金管理、持仓管理、交易记录和性能统计
    """
    
    def __init__(self, initial_capital: float, position_pct: float = 0.1):
        """
        初始化投资组合管理器
        
        Args:
            initial_capital: 初始资金
            position_pct: 每次开仓占用资金比例
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position_pct = position_pct
        
        # 持仓管理
        self.current_position: Optional[Position] = None
        self.position_history: List[Position] = []
        
        # 交易记录
        self.trade_history: List[TradeRecord] = []
        self.trade_id_counter = 0
        
        # 统计数据
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.max_drawdown = 0.0
        self.peak_capital = initial_capital
        
        # 权益曲线
        self.equity_curve = []
        self._update_equity_curve(datetime.now(), initial_capital)
    
    def calculate_position_size(self, symbol: str, price: float) -> int:
        """
        计算开仓手数
        
        Args:
            symbol: 品种代码
            price: 当前价格
            
        Returns:
            可开仓手数
        """
        available_capital = self.current_capital * self.position_pct
        return MarketInfo.calculate_position_size(symbol, price, available_capital, 1.0)
    
    def open_position(self, symbol: str, contract: str, direction: str, 
                     price: float, timestamp: datetime) -> Optional[TradeRecord]:
        """
        开仓
        
        Args:
            symbol: 品种代码
            contract: 合约代码
            direction: 方向（多/空）
            price: 开仓价格
            timestamp: 开仓时间
            
        Returns:
            交易记录
        """
        # 如果已有持仓，先平仓
        if self.current_position:
            self.close_position(price, timestamp)
        
        # 计算开仓手数
        quantity = self.calculate_position_size(symbol, price)
        if quantity <= 0:
            logger.warning(f"资金不足，无法开仓: symbol={symbol}, price={price}")
            return None
        
        # 计算占用保证金
        margin_used = MarketInfo.calculate_margin(symbol, price, quantity)
        
        # 创建持仓
        self.current_position = Position(
            symbol=symbol,
            contract=contract,
            direction=direction,
            quantity=quantity,
            open_price=price,
            open_time=timestamp,
            margin_used=margin_used
        )
        
        # 创建交易记录
        self.trade_id_counter += 1
        trade = TradeRecord(
            trade_id=self.trade_id_counter,
            open_time=timestamp.isoformat(),
            open_price=price,
            direction='多' if direction == 'long' else '空',
            quantity=quantity,
            status='持仓中',
            close_time=None,
            close_price=None,
            profit=None,
            profit_pct=None
        )
        
        self.trade_history.append(trade)
        self.total_trades += 1
        
        logger.info(f"开仓成功: {contract} {direction} {quantity}手 @ {price}")
        return trade
    
    def close_position(self, price: float, timestamp: datetime) -> Optional[TradeRecord]:
        """
        平仓
        
        Args:
            price: 平仓价格
            timestamp: 平仓时间
            
        Returns:
            更新后的交易记录
        """
        if not self.current_position:
            logger.warning("无持仓可平")
            return None
        
        position = self.current_position
        
        # 计算盈亏
        contract_size = MarketInfo.get_contract_size(position.symbol)
        if position.direction == 'long':
            profit_per_lot = (price - position.open_price) * contract_size
        else:  # short
            profit_per_lot = (position.open_price - price) * contract_size
        
        total_profit = profit_per_lot * position.quantity
        profit_pct = (total_profit / position.margin_used) * 100 if position.margin_used > 0 else 0
        
        # 更新资金
        self.current_capital += total_profit
        self.total_profit += total_profit
        
        # 更新统计
        if total_profit > 0:
            self.winning_trades += 1
        elif total_profit < 0:
            self.losing_trades += 1
        
        # 更新交易记录
        if self.trade_history:
            last_trade = self.trade_history[-1]
            if last_trade.status == '持仓中':
                last_trade.close_time = timestamp.isoformat()
                last_trade.close_price = price
                last_trade.profit = total_profit
                last_trade.profit_pct = profit_pct
                last_trade.status = '已平仓'
        
        # 保存到历史
        self.position_history.append(position)
        self.current_position = None
        
        # 更新权益曲线
        self._update_equity_curve(timestamp, self.current_capital)
        
        logger.info(f"平仓成功: {position.contract} @ {price}, 盈亏: {total_profit:.2f}")
        return last_trade if self.trade_history else None
    
    def update_position_price(self, price: float, timestamp: datetime):
        """
        更新持仓当前价格（用于计算浮动盈亏）
        
        Args:
            price: 当前价格
            timestamp: 时间戳
        """
        if not self.current_position:
            return
        
        position = self.current_position
        contract_size = MarketInfo.get_contract_size(position.symbol)
        
        # 计算未实现盈亏
        if position.direction == 'long':
            unrealized_pnl = (price - position.open_price) * contract_size * position.quantity
        else:
            unrealized_pnl = (position.open_price - price) * contract_size * position.quantity
        
        position.current_price = price
        position.unrealized_pnl = unrealized_pnl
        
        # 更新权益曲线
        current_equity = self.current_capital + unrealized_pnl
        self._update_equity_curve(timestamp, current_equity)
    
    def _update_equity_curve(self, timestamp: datetime, equity: float):
        """更新权益曲线"""
        self.equity_curve.append({
            'timestamp': timestamp.isoformat(),
            'equity': equity,
            'capital': self.current_capital,
            'drawdown': self._calculate_drawdown(equity)
        })
        
        # 更新峰值和最大回撤
        if equity > self.peak_capital:
            self.peak_capital = equity
        
        drawdown = self._calculate_drawdown(equity)
        if drawdown < self.max_drawdown:
            self.max_drawdown = drawdown
    
    def _calculate_drawdown(self, current_equity: float) -> float:
        """计算回撤率"""
        if self.peak_capital <= 0:
            return 0
        return ((current_equity - self.peak_capital) / self.peak_capital) * 100
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            性能指标字典
        """
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        # 计算盈亏比
        winning_amount = 0
        losing_amount = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        current_consecutive_wins = 0
        current_consecutive_losses = 0
        
        for trade in self.trade_history:
            if trade.profit is not None:
                if trade.profit > 0:
                    winning_amount += trade.profit
                    current_consecutive_wins += 1
                    current_consecutive_losses = 0
                    max_consecutive_wins = max(max_consecutive_wins, current_consecutive_wins)
                elif trade.profit < 0:
                    losing_amount += abs(trade.profit)
                    current_consecutive_losses += 1
                    current_consecutive_wins = 0
                    max_consecutive_losses = max(max_consecutive_losses, current_consecutive_losses)
        
        profit_factor = (winning_amount / losing_amount) if losing_amount > 0 else float('inf') if winning_amount > 0 else 0
        avg_profit = (winning_amount / self.winning_trades) if self.winning_trades > 0 else 0
        avg_loss = (losing_amount / self.losing_trades) if self.losing_trades > 0 else 0
        
        # 计算总收益率
        total_return = ((self.current_capital - self.initial_capital) / self.initial_capital * 100) if self.initial_capital > 0 else 0
        
        # 计算夏普比率（简化版）
        if len(self.equity_curve) > 1:
            returns = []
            for i in range(1, len(self.equity_curve)):
                prev_equity = self.equity_curve[i-1]['equity']
                curr_equity = self.equity_curve[i]['equity']
                if prev_equity > 0:
                    returns.append((curr_equity - prev_equity) / prev_equity)
            
            if returns:
                import numpy as np
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = (mean_return / std_return * np.sqrt(252)) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_profit': self.total_profit,
            'total_return': total_return,
            'max_drawdown': abs(self.max_drawdown),
            'sharpe_ratio': sharpe_ratio,
            'initial_capital': self.initial_capital,
            'final_capital': self.current_capital,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses
        }
    
    def reset(self):
        """重置投资组合状态"""
        self.current_capital = self.initial_capital
        self.current_position = None
        self.position_history.clear()
        self.trade_history.clear()
        self.trade_id_counter = 0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0.0
        self.max_drawdown = 0.0
        self.peak_capital = self.initial_capital
        self.equity_curve = []
        self._update_equity_curve(datetime.now(), self.initial_capital)
