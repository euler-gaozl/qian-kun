"""实时策略控制器"""
from typing import Dict, Any
import logging
from datetime import datetime
from services.kline_service import KlineService
from strategies.core_strategy import CoreStrategy
from models.domain_models import SignalType
from models.request_models import RealtimeStrategyRequest
from models.response_models import RealtimeStrategyResponse

logger = logging.getLogger(__name__)


class RealtimeStrategyController:
    """
    实时策略控制器
    处理实时策略请求，调用相关服务生成交易信号
    """
    
    def __init__(self):
        """初始化控制器"""
        self.kline_service = KlineService()
        self.core_strategy = CoreStrategy()
        
    def handle_request(self, request: RealtimeStrategyRequest) -> RealtimeStrategyResponse:
        """
        处理实时策略请求
        
        Args:
            request: 实时策略请求对象
            
        Returns:
            实时策略响应对象
        """
        try:
            # 拼接完整的合约代码
            full_symbol = f"{request.symbol}{request.contract}"
            logger.info(f"处理实时策略请求: {full_symbol}, 周期: {request.period}, MA周期: {request.ma_period}")
            
            # 获取K线数据和MA值列表
            ma_values = self.kline_service.get_klines_for_ma(
                symbol=full_symbol,
                period=request.period,
                ma_period=request.ma_period
            )
            
            if not ma_values or len(ma_values) < 3:
                logger.warning(f"MA数据不足: {full_symbol}")
                return RealtimeStrategyResponse(
                    instrument=full_symbol,
                    period=request.period,
                    action="观望",
                    price=0.0,
                    timestamp=datetime.now().isoformat(),
                    ma_value=ma_values[-1] if ma_values else None,
                    signal_strength="弱"
                )
            
            # 调用策略生成信号
            signal_type, market_state, reason = self.core_strategy.get_signal(ma_values)
            
            # 确定操作建议和价格
            if signal_type == SignalType.BUY:
                action = "多"
                price = ma_values[-1]  # 使用最新的MA值作为建议价格
                signal_strength = "强"
            elif signal_type == SignalType.SELL:
                action = "空"
                price = ma_values[-1]
                signal_strength = "强"
            elif signal_type == SignalType.CLOSE:
                action = "平仓"
                price = 0.0  # 市价平仓
                signal_strength = "中"
            else:  # HOLD
                action = "观望"
                price = 0.0
                signal_strength = "弱"
            # 计算平仓价（实时数据，无延迟）
            close_price = None
            ma16_current, ma15_current = self.kline_service.get_close_price_data(
                symbol=full_symbol,
                period=request.period,
                ma_period=request.ma_period
            )
            
            if ma16_current is not None and ma15_current is not None:
                # 公式：MA16 × 16 = MA15 × 15 + X
                # 反解：X = MA16 × 16 - MA15 × 15
                close_price = ma16_current * request.ma_period - ma15_current * (request.ma_period - 1)
                logger.info(f"计算平仓价(实时): ma16={ma16_current:.2f}, ma15={ma15_current:.2f}, close_price={close_price:.2f}")
            
            
            # 构造响应
            response = RealtimeStrategyResponse(
                instrument=full_symbol,
                period=request.period,
                action=action,
                price=round(price, 2) if price > 0 else 0.0,
                timestamp=datetime.now().isoformat(),
                ma_value=round(ma_values[-1], 2) if ma_values else None,
                signal_strength=signal_strength,
                close_price=round(close_price, 2) if close_price else None
            )
            
            logger.info(f"生成信号: {action} @ {response.price}, 原因: {reason}")
            return response
            
        except Exception as e:
            logger.error(f"处理实时策略请求失败: {e}")
            raise
    
    def reset(self):
        """重置控制器状态"""
        self.core_strategy.reset()
