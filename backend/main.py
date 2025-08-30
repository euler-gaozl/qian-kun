"""FastAPI主应用"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from dotenv import load_dotenv
import logging
import os

# 导入控制器
from controllers.realtime_strategy import RealtimeStrategyController
from controllers.backtest_system import BacktestSystemController

# 导入模型
from models.request_models import RealtimeStrategyRequest, BacktestRequest
from models.response_models import ErrorResponse
from utils.market_info import MarketInfo

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            "symbols": "/api/symbols - 获取所有品种列表"
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
