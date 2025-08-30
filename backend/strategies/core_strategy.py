"""核心策略算法"""
from typing import List, Tuple, Optional
from enum import Enum
import logging
from models.domain_models import SignalType, MarketState

logger = logging.getLogger(__name__)


class CoreStrategy:
    """
    核心策略类 - 基于MA连续性判断的策略
    
    开仓条件：MA值必须连续n次单调递增（做多）或递减（做空）
    平仓条件：连续两次停顿或反向运动
    """
    
    def __init__(self):
        """初始化策略"""
        self.last_signal = None
        self.position_direction = None
        
    def get_signal(self, ma_list: List[float]) -> Tuple[SignalType, MarketState, Optional[str]]:
        """
        根据MA值列表判断交易信号
        
        Args:
            ma_list: MA值列表，从远到近排序（索引0是最远的，-1是最近的）
            
        Returns:
            (信号类型, 市场状态, 原因说明)
        """
        if not ma_list or len(ma_list) < 3:
            logger.warning("MA数据不足，无法生成信号")
            return SignalType.HOLD, MarketState.SIDEWAYS, "数据不足"
        
        print(ma_list)

        # 检查连续性
        is_continuous_up = self._check_continuous_up(ma_list)
        is_continuous_down = self._check_continuous_down(ma_list)
        should_close = self._check_should_close(ma_list)
        
        print(is_continuous_up, is_continuous_down, should_close)

        # 判断市场状态
        if is_continuous_up:
            market_state = MarketState.UPTREND
        elif is_continuous_down:
            market_state = MarketState.DOWNTREND
        else:
            market_state = MarketState.SIDEWAYS

        print(market_state, self.position_direction)
        
        # 生成交易信号
        if should_close:
            # 观望且有持仓需要平仓
            return SignalType.CLOSE, market_state, "连续性中断，平仓"
        
        if is_continuous_up:
            # 连续上涨，开多仓
            return SignalType.BUY, market_state, f"MA连续{len(ma_list)}次上涨"
        
        if is_continuous_down:
            # 连续下跌，开空仓
            return SignalType.SELL, market_state, f"MA连续{len(ma_list)}次下跌"
        
        # 默认观望
        return SignalType.HOLD, market_state, "不满足开仓条件"
    
    def _check_continuous_up(self, ma_list: List[float]) -> bool:
        """
        检查是否连续上涨
        要求：每个MA值都严格大于前一个
        """
        if len(ma_list) < 2:
            return False
        
        for i in range(5, len(ma_list)-1):
            if ma_list[i] >= ma_list[i+1]:
                return False
        return True
    
    def _check_continuous_down(self, ma_list: List[float]) -> bool:
        """
        检查是否连续下跌
        要求：每个MA值都严格小于前一个
        """
        if len(ma_list) < 2:
            return False
        
        for i in range(5, len(ma_list)-1):
            if ma_list[i] <= ma_list[i+1]:
                return False
        return True
    
    def _check_should_close(self, ma_list: List[float]) -> bool:
        """
        检查是否应该平仓
        条件：连续两次停顿或反向（ma[0] <= ma[1] 且 ma[1] <= ma[2]）
        """
        if len(ma_list) < 3:
            return False
        
        # 检查最近的3个MA值
        recent = ma_list[-3:]
        
        # 如果当前有多仓，检查是否出现连续两次非上涨
        if self.position_direction == 'long':
            if recent[2] <= recent[1] and recent[1] <= recent[0]:
                return True
        
        # 如果当前有空仓，检查是否出现连续两次非下跌
        if self.position_direction == 'short':
            if recent[2] >= recent[1] and recent[1] >= recent[0]:
                return True
        
        return False
    
    def reset(self):
        """重置策略状态"""
        self.last_signal = None
        self.position_direction = None


class MAStrategy(CoreStrategy):
    """
    MA均线策略（继承自核心策略）
    可以在这里添加特定的MA策略逻辑
    """
    
    def __init__(self, ma_period: int = 16):
        """
        初始化MA策略
        
        Args:
            ma_period: MA周期
        """
        super().__init__()
        self.ma_period = ma_period
    
    def validate_ma_period(self) -> bool:
        """验证MA周期是否合法"""
        return 15 <= self.ma_period <= 21
