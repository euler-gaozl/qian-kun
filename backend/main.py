"""FastAPI主应用"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from dotenv import load_dotenv
import logging
import os
from pathlib import Path

# 导入控制器
from controllers.realtime_strategy import RealtimeStrategyController
from controllers.backtest_system import BacktestSystemController
from controllers.ai_analysis import AIAnalysisController

# 导入服务
from services.kline_service import KlineService

# 导入模型
from models.request_models import RealtimeStrategyRequest, BacktestRequest, AIAnalysisRequest
from models.response_models import ErrorResponse
from utils.market_info import MarketInfo

# 配置日志（需要先配置日志才能使用logger）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量（从backend目录）
backend_dir = Path(__file__).parent
env_path = backend_dir / '.env'
load_dotenv(dotenv_path=env_path)

# 打印AI配置状态（用于调试）
if os.getenv('AI_API_KEY'):
    logger.info(f"AI配置已加载: {os.getenv('AI_API_BASE_URL')}, Model: {os.getenv('AI_MODEL_ID')}")
else:
    logger.warning("AI_API_KEY未配置，AI分析功能将不可用")

# 创建FastAPI应用
app = FastAPI(
    title="乾坤量化交易系统 API",
    description="前后端分离的金融量化交易系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS - 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*", "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化控制器
realtime_controller = RealtimeStrategyController()
backtest_controller = BacktestSystemController()
ai_controller = AIAnalysisController()


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "乾坤量化交易系统 API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs - API文档",
            "realtime": "/api/realtime - 实时策略信号",
            "backtest": "/api/backtest - 历史回测",
            "ai_analysis": "/api/ai-analysis - AI深度分析",
            "symbols": "/api/symbols - 获取所有品种列表",
            "klines": "/api/klines/{symbol}/{contract} - 获取K线数据"
        }
    }


@app.get("/api/symbols")
async def get_symbols():
    """获取所有支持的品种列表"""
    try:
        symbols = MarketInfo.get_all_symbols()
        return {
            "success": True,
            "data": symbols,
            "total": len(symbols)
        }
    except Exception as e:
        logger.error(f"获取品种列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/realtime")
async def realtime_strategy(request: RealtimeStrategyRequest):
    """
    实时策略端点
    
    根据品种、周期、合约和MA参数生成实时交易信号
    """
    try:
        logger.info(f"收到实时策略请求: {request.symbol}{request.contract}")
        response = realtime_controller.handle_request(request)
        return response.dict()
    except ValidationError as e:
        logger.error(f"参数验证失败: {e}")
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="ValidationError",
                message="请求参数验证失败",
                details=e.errors()
            ).dict()
        )
    except Exception as e:
        logger.error(f"处理实时策略请求失败: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError",
                message=str(e)
            ).dict()
        )


@app.post("/api/backtest")
async def backtest_strategy(request: BacktestRequest):
    """
    回测系统端点
    
    执行历史数据回测并返回详细的交易记录和统计指标
    """
    try:
        logger.info(f"收到回测请求: {request.symbol}{request.contract}, "
                   f"日期: {request.start_date} 至 {request.end_date}")
        response = backtest_controller.handle_request(request)
        return response.dict()
    except ValidationError as e:
        logger.error(f"参数验证失败: {e}")
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="ValidationError",
                message="请求参数验证失败",
                details=e.errors()
            ).dict()
        )
    except ValueError as e:
        logger.error(f"回测参数错误: {e}")
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="ValueError",
                message=str(e)
            ).dict()
        )
    except Exception as e:
        logger.error(f"处理回测请求失败: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError",
                message=str(e)
            ).dict()
        )


@app.get("/api/klines/{symbol}/{contract}")
async def get_klines(
    symbol: str,
    contract: str,
    period: str = "15m",
    limit: int = 100
):
    """
    获取 K 线数据
    
    Args:
        symbol: 品种代码（如 rb）
        contract: 合约代码（如 2501）
        period: 周期
        limit: 获取数量
    
    Returns:
        K线数据列表
    """
    try:
        full_symbol = f"{symbol}{contract}"
        kline_service = KlineService()
        df = kline_service._fetch_klines(full_symbol, period, limit)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="无法获取K线数据")
        
        # 转换为 JSON 格式
        klines = []
        for _, row in df.iterrows():
            klines.append({
                "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"])
            })
        
        return {
            "success": True,
            "symbol": full_symbol,
            "period": period,
            "count": len(klines),
            "klines": klines
        }
    except HTTPException:
        raise

@app.post("/api/ai-analysis")
async def ai_analysis(request: AIAnalysisRequest):
    """
    AI深度分析端点
    
    使用AI大模型对期货合约进行深度技术分析，包括：
    - 当前走势分析
    - 支撑与阻力位识别
    - 技术指标分析
    - 未来走势预判
    - 具体操作建议
    """
    try:
        logger.info(f"收到AI分析请求: {request.symbol}{request.contract}, 周期: {request.period}")
        response = await ai_controller.handle_request(request)
        return response.dict()
    except ValidationError as e:
        logger.error(f"参数验证失败: {e}")
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="ValidationError",
                message="请求参数验证失败",
                details=e.errors()
            ).dict()
        )
    except Exception as e:
        logger.error(f"处理AI分析请求失败: {e}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError",
                message=str(e)
            ).dict()
        )

    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("乾坤量化交易系统启动")
    logger.info(f"API文档地址: http://localhost:8000/docs")
    logger.info(f"系统就绪，等待请求...")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("乾坤量化交易系统关闭")


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量读取配置
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
