"""AI分析控制器"""
import logging
from models.request_models import AIAnalysisRequest
from models.response_models import AIAnalysisResponse
from services.kline_service import KlineService
from services.ai_service import AIService

logger = logging.getLogger(__name__)


class AIAnalysisController:
    """AI分析控制器"""
    
    def __init__(self):
        """初始化控制器"""
        self.kline_service = KlineService()
        self.ai_service = AIService()
    
    async def handle_request(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
        """
        处理AI分析请求
        
        Args:
            request: AI分析请求
        
        Returns:
            AI分析响应
        """
        try:
            # 1. 构造完整的合约代码
            full_symbol = f"{request.symbol}{request.contract}"
            logger.info(f"开始AI分析: {full_symbol}, 周期: {request.period}")
            
            # 2. 获取K线数据（100根）
            klines_df = self.kline_service._fetch_klines(
                symbol=full_symbol,
                period=request.period,
                limit=100
            )
            
            if klines_df.empty:
                return AIAnalysisResponse(
                    success=False,
                    symbol=full_symbol,
                    period=request.period,
                    analysis="",
                    kline_count=0,
                    error=f"无法获取 {full_symbol} 的K线数据，请检查合约代码是否正确"
                )
            
            logger.info(f"成功获取 {len(klines_df)} 根K线数据")
            
            # 3. 格式化K线数据为文本
            kline_text = self.ai_service.format_klines_for_analysis(
                klines_df=klines_df,
                symbol=full_symbol,
                period=request.period
            )
            
            # 4. 调用AI进行分析
            logger.info("开始调用AI LLM进行分析...")
            analysis_result = await self.ai_service.analyze_with_llm(
                kline_data=kline_text,
                symbol=full_symbol,
                period=request.period,
                query=request.query
            )
            
            logger.info(f"AI分析完成，结果长度: {len(analysis_result)} 字符")
            
            # 5. 返回分析结果
            return AIAnalysisResponse(
                success=True,
                symbol=full_symbol,
                period=request.period,
                analysis=analysis_result,
                kline_count=len(klines_df)
            )
            
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return AIAnalysisResponse(
                success=False,
                symbol=f"{request.symbol}{request.contract}",
                period=request.period,
                analysis="",
                kline_count=0,
                error=str(e)
            )