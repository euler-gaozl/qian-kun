"""AI分析服务"""
import os
import logging
from typing import Optional
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class AIService:
    """AI服务类，负责调用LLM进行分析"""
    
    def __init__(self):
        """初始化AI服务"""
        self.api_base_url = os.getenv("AI_API_BASE_URL", "https://bmc-llm-relay.bluemediagroup.cn/v1")
        self.api_key = os.getenv("AI_API_KEY", "")
        self.model_id = os.getenv("AI_MODEL_ID", "DeepSeek-V3.1")
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "15000"))
        self.temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))
        self.timeout = int(os.getenv("AI_TIMEOUT", "300000")) / 1000  # 5分钟超时，转换为秒
        
        if not self.api_key:
            logger.warning("AI_API_KEY 未配置，AI分析功能将不可用")
    
    def create_system_prompt(self) -> str:
        """创建系统提示词"""
        return """你是资深期货分析师，15年实战经验。

要求：
- 直接给出判断，不要过多解释基础概念
- 使用专业术语，言简意赅
- 重点突出关键价位和操作建议
- 每个要点控制在2-3句话

风格：专业、简洁、直接。"""
    
    def create_analysis_prompt(self, kline_data: str, symbol: str, period: str, query: Optional[str] = None) -> str:
        """
        创建分析提示词
        
        Args:
            kline_data: 格式化的K线数据文本
            symbol: 合约代码
            period: K线周期
            query: 用户的分析需求
        
        Returns:
            完整的分析提示词
        """
        base_prompt = f"""K线数据：

{kline_data}

"""
        
        if query:
            base_prompt += f"""重点关注：{query}

"""
        
        base_prompt += """按以下格式输出（总计800-1200字）：

## 1. 趋势判断（2-3句）
- 当前趋势方向和强度
- 关键形态特征

## 2. 关键价位（列表形式）
- 阻力位：X, Y, Z（从近到远）
- 支撑位：A, B, C（从近到远）

## 3. 成交量（2句）
- 量价配合情况
- 是否有背离

## 4. 操作策略（精炼）
方向：做多/做空/观望
入场：具体价位区间
止损：具体价格
目标：T1/T2价格
理由：1-2句话说明

## 5. 风险（1-2个要点）

注意：直接给结论，不要铺垫和解释基础概念。"""
        
        return base_prompt
    
    async def analyze_with_llm(self, kline_data: str, symbol: str, period: str, query: Optional[str] = None) -> str:
        """
        使用LLM进行分析
        
        Args:
            kline_data: 格式化的K线数据
            symbol: 合约代码
            period: K线周期
            query: 用户查询
        
        Returns:
            AI分析结果文本
        
        Raises:
            Exception: 如果API调用失败
        """
        if not self.api_key:
            raise Exception("AI_API_KEY 未配置，无法进行AI分析")
        
        try:
            system_prompt = self.create_system_prompt()
            user_prompt = self.create_analysis_prompt(kline_data, symbol, period, query)
            
            # 构造OpenAI兼容的API请求
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model_id,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                        "stream": False
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                # 提取AI回复
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception("AI返回格式异常：缺少choices字段")
                
        except httpx.HTTPStatusError as e:
            logger.error(f"AI API HTTP错误: {e.response.status_code} - {e.response.text}")
            raise Exception(f"AI API调用失败 ({e.response.status_code}): {e.response.text}")
        except httpx.TimeoutException:
            logger.error("AI API请求超时")
            raise Exception("AI分析超时，请稍后重试")
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            raise Exception(f"AI分析失败: {str(e)}")
    
    def format_klines_for_analysis(self, klines_df, symbol: str, period: str) -> str:
        """
        将K线DataFrame格式化为适合AI分析的文本
        
        Args:
            klines_df: K线数据DataFrame
            symbol: 合约代码
            period: K线周期
        
        Returns:
            格式化的文本
        """
        if klines_df.empty:
            return f"{symbol} {period} 周期暂无K线数据"
        
        lines = [
            f"合约: {symbol}",
            f"周期: {period}",
            f"数据条数: {len(klines_df)}",
            f"时间范围: {klines_df['timestamp'].iloc[0]} 至 {klines_df['timestamp'].iloc[-1]}",
            "",
            "K线数据:",
            "",
            "时间\t\t\t开盘\t最高\t最低\t收盘\t成交量"
        ]
        lines.append("-" * 80)
        
        # 显示所有K线数据
        for _, row in klines_df.iterrows():
            timestamp = row['timestamp']
            line = f"{timestamp}\t{row['open']:.2f}\t{row['high']:.2f}\t{row['low']:.2f}\t{row['close']:.2f}\t{row['volume']:.0f}"
            lines.append(line)
        
        # 添加统计信息
        prices = klines_df['close'].values
        max_price = prices.max()
        min_price = prices.min()
        latest_price = prices[-1]
        price_change = latest_price - prices[0]
        price_change_pct = (price_change / prices[0]) * 100
        
        lines.append("")
        lines.append("统计信息:")
        lines.append(f"最新价格: {latest_price:.2f}")
        lines.append(f"期间最高: {max_price:.2f}")
        lines.append(f"期间最低: {min_price:.2f}")
        lines.append(f"价格变化: {'+' if price_change > 0 else ''}{price_change:.2f} ({price_change_pct:+.2f}%)")
        
        return "\n".join(lines)