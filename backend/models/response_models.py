"""响应数据模型"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class RealtimeStrategyResponse(BaseModel):
    """实时策略响应模型"""
    instrument: str = Field(..., description="合约代码")
    period: str = Field(..., description="操作周期")
    action: str = Field(..., description="操作建议：多、空、平仓、观望")
    price: float = Field(..., description="建议操作价格")
    timestamp: str = Field(..., description="信号生成时间")
    ma_value: Optional[float] = Field(None, description="当前MA值")
    signal_strength: Optional[str] = Field(None, description="信号强度")


class TradeRecord(BaseModel):
    """交易记录"""
    trade_id: int = Field(..., description="交易ID")
    open_time: str = Field(..., description="开仓时间")
    open_price: float = Field(..., description="开仓价格")
    close_time: Optional[str] = Field(None, description="平仓时间")
    close_price: Optional[float] = Field(None, description="平仓价格")
    direction: str = Field(..., description="交易方向：多/空")
    quantity: float = Field(..., description="交易手数")
    profit: Optional[float] = Field(None, description="盈亏金额")
    profit_pct: Optional[float] = Field(None, description="盈亏比例(%)")
    status: str = Field(..., description="状态：持仓中/已平仓")


class BacktestStatistics(BaseModel):
    """回测统计指标"""
    total_trades: int = Field(..., description="总交易次数")
    winning_trades: int = Field(..., description="盈利交易次数")
    losing_trades: int = Field(..., description="亏损交易次数")
    win_rate: float = Field(..., description="胜率(%)")
    profit_factor: float = Field(..., description="盈亏比")
    total_profit: float = Field(..., description="总盈亏金额")
    total_return: float = Field(..., description="总收益率(%)")
    max_drawdown: float = Field(..., description="最大回撤(%)")
    sharpe_ratio: float = Field(..., description="夏普比率")
    initial_capital: float = Field(..., description="初始资金")
    final_capital: float = Field(..., description="最终资金")
    avg_profit: float = Field(..., description="平均盈利")
    avg_loss: float = Field(..., description="平均亏损")
    max_consecutive_wins: int = Field(..., description="最大连续盈利次数")
    max_consecutive_losses: int = Field(..., description="最大连续亏损次数")


class BacktestResponse(BaseModel):
    """回测响应模型"""
    statistics: BacktestStatistics = Field(..., description="统计指标")
    trades: List[TradeRecord] = Field(..., description="交易记录列表")
    equity_curve: List[Dict[str, Any]] = Field(..., description="权益曲线数据")
    parameters: Dict[str, Any] = Field(..., description="回测参数")
    execution_time: float = Field(..., description="执行耗时(秒)")
    start_date: str = Field(..., description="回测开始日期")
    end_date: str = Field(..., description="回测结束日期")
    
    
class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
