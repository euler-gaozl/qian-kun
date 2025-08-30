"""K线数据服务"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import akshare as ak
import logging

logger = logging.getLogger(__name__)


class KlineService:
    """K线数据服务类"""
    
    def __init__(self):
        """初始化K线服务"""
        self.cache = {}  # 简单的内存缓存
        
    def get_klines_for_ma(self, symbol: str, period: str, ma_period: int = 16) -> List[float]:
        """
        获取K线数据并计算MA值列表
        
        Args:
            symbol: 完整的合约代码，如 rb2501
            period: 周期，如 5m, 15m, 30m, 60m, 120m, 240m, 1d, 2d
            ma_period: MA周期，默认16
            
        Returns:
            MA值列表，从远到近排序
        """
        try:
            # 获取K线数据
            klines = self._fetch_klines(symbol, period, ma_period * 2)
            if klines.empty:
                logger.warning(f"无法获取 {symbol} 的K线数据")
                return []
            
            # 计算MA值
            ma_values = self._calculate_ma(klines, ma_period)
            
            # 返回最近n个MA值（从远到近）
            return ma_values[-ma_period:].tolist() if len(ma_values) >= ma_period else ma_values.tolist()
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return []
    
    def get_historical_klines(self, symbol: str, period: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取历史K线数据
        
        Args:
            symbol: 完整的合约代码
            period: 周期
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            # 根据周期类型选择不同的数据获取方法
            if 'm' in period:
                # 分钟级数据
                minutes = period.replace('m', '')
                df = ak.futures_zh_minute_sina(symbol=symbol, period=minutes)
                if not df.empty:
                    df.rename(columns={'datetime': 'timestamp'}, inplace=True)
            elif period == '1d':
                # 日线数据
                df = ak.futures_zh_daily_sina(symbol=symbol)
                if not df.empty:
                    df.rename(columns={'date': 'timestamp'}, inplace=True)
            elif period == '2d':
                # 2日数据，需要对日线数据进行重采样
                df = ak.futures_zh_daily_sina(symbol=symbol)
                if not df.empty:
                    df.rename(columns={'date': 'timestamp'}, inplace=True)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    # 重采样为2日
                    df = df.resample('2D').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    df.reset_index(inplace=True)
            else:
                logger.error(f"不支持的周期: {period}")
                return pd.DataFrame()
            
            if df.empty:
                return pd.DataFrame()
            
            # 转换时间戳并筛选日期范围
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            df = df[(df['timestamp'] >= start) & (df['timestamp'] <= end)]
            
            # 确保数据类型正确
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 按时间排序
            df.sort_values('timestamp', inplace=True)
            df.reset_index(drop=True, inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"获取历史K线数据失败: {e}")
            return pd.DataFrame()
    
    def _fetch_klines(self, symbol: str, period: str, limit: int) -> pd.DataFrame:
        """
        从数据源获取K线数据
        
        Args:
            symbol: 合约代码
            period: 周期
            limit: 获取数量
            
        Returns:
            DataFrame
        """
        try:
            if 'm' in period:
                # 分钟级数据
                minutes = period.replace('m', '')
                df = ak.futures_zh_minute_sina(symbol=symbol, period=minutes)
                if not df.empty:
                    df.rename(columns={'datetime': 'timestamp'}, inplace=True)
            elif period == '1d':
                # 日线数据
                df = ak.futures_zh_daily_sina(symbol=symbol)
                if not df.empty:
                    df.rename(columns={'date': 'timestamp'}, inplace=True)
            elif period == '2d':
                # 2日数据
                df = ak.futures_zh_daily_sina(symbol=symbol)
                if not df.empty:
                    df.rename(columns={'date': 'timestamp'}, inplace=True)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    df = df.resample('2D').agg({
                        'open': 'first',
                        'high': 'max',
                        'low': 'min',
                        'close': 'last',
                        'volume': 'sum'
                    }).dropna()
                    df.reset_index(inplace=True)
            else:
                return pd.DataFrame()
            
            if df.empty:
                return pd.DataFrame()
            
            # 转换数据类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 只返回最近的limit条数据
            if len(df) > limit:
                df = df.tail(limit)
            
            return df
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return pd.DataFrame()
    
    def _calculate_ma(self, df: pd.DataFrame, period: int) -> pd.Series:
        """
        计算移动平均值
        
        Args:
            df: K线数据DataFrame
            period: MA周期
            
        Returns:
            MA值Series
        """
        if 'close' not in df.columns:
            return pd.Series()
        
        return df['close'].rolling(window=period).mean()
    
    def calculate_ma_values_from_klines(self, df: pd.DataFrame, ma_period: int) -> pd.DataFrame:
        """
        为给定的K线数据计算MA值
        
        Args:
            df: K线数据
            ma_period: MA周期
            
        Returns:
            带有MA值的DataFrame
        """
        df = df.copy()
        df[f'ma{ma_period}'] = self._calculate_ma(df, ma_period)
        return df
