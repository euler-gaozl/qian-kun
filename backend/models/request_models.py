"""请求数据模型"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from utils.market_info import MarketInfo


class RealtimeStrategyRequest(BaseModel):
    """实时策略请求模型"""
    symbol: str = Field(..., description="品种代码，如 rb（螺纹钢）")
    period: str = Field(..., description="操作周期，如 5m, 15m, 30m, 60m, 120m, 240m, 1d, 2d")
    contract: str = Field(..., description="合约代码，如 2501")
    ma_period: int = Field(default=16, ge=15, le=21, description="均线周期，15-21之间")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """验证并规范化品种代码"""
        # 验证品种是否存在（不区分大小写）
        symbol_info = MarketInfo.get_symbol_info(v)
        if not symbol_info:
            raise ValueError(f'不支持的品种代码: {v}')
        # 中金所品种保持大写，其他交易所品种转为小写
        if symbol_info.get('exchange') == 'CFFEX':
            return v.upper()
        else:
            return v.lower()
    
    @validator('period')
    def validate_period(cls, v):
        """验证周期格式"""
        valid_periods = ['5m', '15m', '30m', '60m', '120m', '240m', '1d', '2d']
        if v not in valid_periods:
            raise ValueError(f'周期必须是以下之一: {", ".join(valid_periods)}')
        return v
    
    @validator('contract')
    def validate_contract(cls, v):
        """验证合约格式（4位数字）"""
        if not v.isdigit() or len(v) != 4:
            raise ValueError('合约必须是4位数字，如 2501')
        return v


class BacktestRequest(BaseModel):
    """回测请求模型"""
    symbol: str = Field(..., description="品种代码")
    period: str = Field(..., description="操作周期")
    contract: str = Field(..., description="合约代码")
    start_date: str = Field(..., description="回测开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(..., description="回测结束日期，格式：YYYY-MM-DD")
    ma_period: int = Field(default=16, ge=15, le=21, description="均线周期")
    initial_capital: float = Field(default=100000.0, gt=0, description="初始资金")
    position_pct: float = Field(default=10.0, gt=0, le=100, description="每次开仓比例(%)") 
    use_continuous: bool = Field(default=False, description="是否使用主力连续合约")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        """验证并规范化品种代码"""
        # 验证品种是否存在（不区分大小写）
        symbol_info = MarketInfo.get_symbol_info(v)
        if not symbol_info:
            raise ValueError(f'不支持的品种代码: {v}')
        # 中金所品种保持大写，其他交易所品种转为小写
        if symbol_info.get('exchange') == 'CFFEX':
            return v.upper()
        else:
            return v.lower()
    
    @validator('period')
    def validate_period(cls, v):
        """验证周期格式"""
        valid_periods = ['5m', '15m', '30m', '60m', '120m', '240m', '1d', '2d']
        if v not in valid_periods:
            raise ValueError(f'周期必须是以下之一: {", ".join(valid_periods)}')
        return v
    
    @validator('start_date', 'end_date')
    def validate_date(cls, v):
        """验证日期格式"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('日期格式必须为 YYYY-MM-DD')
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """验证日期范围"""
        if 'start_date' in values:
            if v <= values['start_date']:
                raise ValueError('结束日期必须晚于开始日期')
        return v
