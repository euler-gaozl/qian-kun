"""领域数据模型"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SignalType(str, Enum):
    """信号类型枚举"""
    BUY = "buy"      # 做多
    SELL = "sell"    # 做空
    CLOSE = "close"  # 平仓
    HOLD = "hold"    # 观望


class MarketState(str, Enum):
    """市场状态枚举"""
    UPTREND = "uptrend"      # 上涨趋势
    DOWNTREND = "downtrend"  # 下跌趋势
    SIDEWAYS = "sideways"    # 横盘


class Position(BaseModel):
    """持仓信息"""
    symbol: str = Field(..., description="品种代码")
    contract: str = Field(..., description="合约代码")
    direction: str = Field(..., description="持仓方向：多/空")
    quantity: float = Field(..., description="持仓手数")
    open_price: float = Field(..., description="开仓均价")
    open_time: datetime = Field(..., description="开仓时间")
    current_price: Optional[float] = Field(None, description="当前价格")
    unrealized_pnl: Optional[float] = Field(None, description="未实现盈亏")
    margin_used: float = Field(..., description="占用保证金")


class KLine(BaseModel):
    """K线数据"""
    timestamp: datetime = Field(..., description="时间戳")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    ma_value: Optional[float] = Field(None, description="MA值")


class Signal(BaseModel):
    """交易信号"""
    timestamp: datetime = Field(..., description="信号时间")
    signal_type: SignalType = Field(..., description="信号类型")
    price: float = Field(..., description="信号价格")
    ma_values: List[float] = Field(..., description="MA值列表")
    market_state: MarketState = Field(..., description="市场状态")
    strength: Optional[str] = Field(None, description="信号强度")
    reason: Optional[str] = Field(None, description="信号原因")


class ContractInfo(BaseModel):
    """合约信息"""
    symbol: str = Field(..., description="品种代码")
    name: str = Field(..., description="品种名称")
    exchange: str = Field(..., description="交易所")
    contract_size: float = Field(..., description="合约乘数")
    margin_rate: float = Field(..., description="保证金比例")
    min_change: float = Field(..., description="最小变动价位")
    trading_hours: List[str] = Field(..., description="交易时间段")
