"""市场信息工具类"""
from typing import Dict, List, Tuple
from datetime import datetime, time


class MarketInfo:
    """市场信息管理类"""
    
    # 品种信息映射表
    SYMBOLS = {
        # 上期所 (SHFE)
        'cu': {'name': '铜', 'exchange': 'SHFE', 'size': 5, 'margin': 0.08},
        'al': {'name': '铝', 'exchange': 'SHFE', 'size': 5, 'margin': 0.08},
        'zn': {'name': '锌', 'exchange': 'SHFE', 'size': 5, 'margin': 0.08},
        'pb': {'name': '铅', 'exchange': 'SHFE', 'size': 5, 'margin': 0.08},
        'ni': {'name': '镍', 'exchange': 'SHFE', 'size': 1, 'margin': 0.10},
        'sn': {'name': '锡', 'exchange': 'SHFE', 'size': 1, 'margin': 0.10},
        'au': {'name': '黄金', 'exchange': 'SHFE', 'size': 1000, 'margin': 0.08},
        'ag': {'name': '白银', 'exchange': 'SHFE', 'size': 15, 'margin': 0.09},
        'rb': {'name': '螺纹钢', 'exchange': 'SHFE', 'size': 10, 'margin': 0.09},
        'wr': {'name': '线材', 'exchange': 'SHFE', 'size': 10, 'margin': 0.08},
        'hc': {'name': '热轧卷板', 'exchange': 'SHFE', 'size': 10, 'margin': 0.09},
        'fu': {'name': '燃料油', 'exchange': 'SHFE', 'size': 10, 'margin': 0.10},
        'bu': {'name': '沥青', 'exchange': 'SHFE', 'size': 10, 'margin': 0.09},
        'ru': {'name': '天然橡胶', 'exchange': 'SHFE', 'size': 10, 'margin': 0.09},
        'sp': {'name': '纸浆', 'exchange': 'SHFE', 'size': 10, 'margin': 0.08},
        'ss': {'name': '不锈钢', 'exchange': 'SHFE', 'size': 5, 'margin': 0.08},
        
        # 大商所 (DCE)
        'c': {'name': '玉米', 'exchange': 'DCE', 'size': 10, 'margin': 0.07},
        'cs': {'name': '玉米淀粉', 'exchange': 'DCE', 'size': 10, 'margin': 0.07},
        'a': {'name': '豆一', 'exchange': 'DCE', 'size': 10, 'margin': 0.07},
        'b': {'name': '豆二', 'exchange': 'DCE', 'size': 10, 'margin': 0.07},
        'm': {'name': '豆粕', 'exchange': 'DCE', 'size': 10, 'margin': 0.07},
        'y': {'name': '豆油', 'exchange': 'DCE', 'size': 10, 'margin': 0.07},
        'p': {'name': '棕榈油', 'exchange': 'DCE', 'size': 10, 'margin': 0.08},
        'fb': {'name': '纤维板', 'exchange': 'DCE', 'size': 10, 'margin': 0.10},
        'bb': {'name': '胶合板', 'exchange': 'DCE', 'size': 500, 'margin': 0.10},
        'jd': {'name': '鸡蛋', 'exchange': 'DCE', 'size': 5, 'margin': 0.08},
        'rr': {'name': '粳米', 'exchange': 'DCE', 'size': 10, 'margin': 0.07},
        'lh': {'name': '生猪', 'exchange': 'DCE', 'size': 16, 'margin': 0.15},
        'l': {'name': '塑料', 'exchange': 'DCE', 'size': 5, 'margin': 0.07},
        'v': {'name': 'PVC', 'exchange': 'DCE', 'size': 5, 'margin': 0.07},
        'pp': {'name': '聚丙烯', 'exchange': 'DCE', 'size': 5, 'margin': 0.07},
        'j': {'name': '焦炭', 'exchange': 'DCE', 'size': 100, 'margin': 0.11},
        'jm': {'name': '焦煤', 'exchange': 'DCE', 'size': 60, 'margin': 0.11},
        'i': {'name': '铁矿石', 'exchange': 'DCE', 'size': 100, 'margin': 0.10},
        'eg': {'name': '乙二醇', 'exchange': 'DCE', 'size': 10, 'margin': 0.08},
        'pg': {'name': '液化石油气', 'exchange': 'DCE', 'size': 20, 'margin': 0.08},
        'eb': {'name': '苯乙烯', 'exchange': 'DCE', 'size': 5, 'margin': 0.08},
        
        # 郑商所 (CZCE)
        'sr': {'name': '白糖', 'exchange': 'CZCE', 'size': 10, 'margin': 0.07},
        'cf': {'name': '棉花', 'exchange': 'CZCE', 'size': 5, 'margin': 0.07},
        'cy': {'name': '棉纱', 'exchange': 'CZCE', 'size': 5, 'margin': 0.07},
        'wh': {'name': '强麦', 'exchange': 'CZCE', 'size': 20, 'margin': 0.07},
        'pm': {'name': '普麦', 'exchange': 'CZCE', 'size': 50, 'margin': 0.07},
        'ri': {'name': '早籼稻', 'exchange': 'CZCE', 'size': 20, 'margin': 0.07},
        'jr': {'name': '粳稻', 'exchange': 'CZCE', 'size': 20, 'margin': 0.07},
        'lr': {'name': '晚籼稻', 'exchange': 'CZCE', 'size': 20, 'margin': 0.07},
        'oi': {'name': '菜油', 'exchange': 'CZCE', 'size': 10, 'margin': 0.07},
        'rs': {'name': '菜籽', 'exchange': 'CZCE', 'size': 10, 'margin': 0.10},
        'rm': {'name': '菜粕', 'exchange': 'CZCE', 'size': 10, 'margin': 0.07},
        'ta': {'name': 'PTA', 'exchange': 'CZCE', 'size': 5, 'margin': 0.07},
        'ma': {'name': '甲醇', 'exchange': 'CZCE', 'size': 10, 'margin': 0.08},
        'fg': {'name': '玻璃', 'exchange': 'CZCE', 'size': 20, 'margin': 0.07},
        'sf': {'name': '硅铁', 'exchange': 'CZCE', 'size': 5, 'margin': 0.10},
        'sm': {'name': '锰硅', 'exchange': 'CZCE', 'size': 5, 'margin': 0.10},
        'zc': {'name': '动力煤', 'exchange': 'CZCE', 'size': 100, 'margin': 0.10},
        'ap': {'name': '苹果', 'exchange': 'CZCE', 'size': 10, 'margin': 0.08},
        'cj': {'name': '红枣', 'exchange': 'CZCE', 'size': 5, 'margin': 0.08},
        'ur': {'name': '尿素', 'exchange': 'CZCE', 'size': 20, 'margin': 0.07},
        'sa': {'name': '纯碱', 'exchange': 'CZCE', 'size': 20, 'margin': 0.07},
        'pf': {'name': '短纤', 'exchange': 'CZCE', 'size': 5, 'margin': 0.07},
        'pk': {'name': '花生', 'exchange': 'CZCE', 'size': 5, 'margin': 0.08},
        
        # 中金所 (CFFEX)
        'if': {'name': '沪深300', 'exchange': 'CFFEX', 'size': 300, 'margin': 0.12},
        'ic': {'name': '中证500', 'exchange': 'CFFEX', 'size': 200, 'margin': 0.14},
        'ih': {'name': '上证50', 'exchange': 'CFFEX', 'size': 300, 'margin': 0.12},
        'im': {'name': '中证1000', 'exchange': 'CFFEX', 'size': 200, 'margin': 0.14},
        'ts': {'name': '2年期国债', 'exchange': 'CFFEX', 'size': 20000, 'margin': 0.005},
        'tf': {'name': '5年期国债', 'exchange': 'CFFEX', 'size': 10000, 'margin': 0.012},
        't': {'name': '10年期国债', 'exchange': 'CFFEX', 'size': 10000, 'margin': 0.02},
        'tl': {'name': '30年期国债', 'exchange': 'CFFEX', 'size': 10000, 'margin': 0.03},
        
        # 广期所 (GFEX)
        'si': {'name': '工业硅', 'exchange': 'GFEX', 'size': 5, 'margin': 0.12},
        'lc': {'name': '碳酸锂', 'exchange': 'GFEX', 'size': 1, 'margin': 0.12},
    }
    
    # 交易时间映射
    TRADING_HOURS = {
        'default': [  # 默认商品期货交易时间
            ('09:00', '10:15'),
            ('10:30', '11:30'),
            ('13:30', '15:00'),
        ],
        'night': [  # 有夜盘的品种
            ('21:00', '23:00'),
        ],
        'night_extended': [  # 延长夜盘品种（如贵金属）
            ('21:00', '02:30'),
        ],
        'stock_index': [  # 股指期货
            ('09:30', '11:30'),
            ('13:00', '15:00'),
        ],
    }
    
    @classmethod
    def get_symbol_info(cls, symbol: str) -> Dict:
        """获取品种信息"""
        return cls.SYMBOLS.get(symbol.lower(), {})
    
    @classmethod
    def get_symbol_name(cls, symbol: str) -> str:
        """获取品种中文名称"""
        info = cls.get_symbol_info(symbol)
        return info.get('name', symbol)
    
    @classmethod
    def get_margin_rate(cls, symbol: str) -> float:
        """获取保证金比例"""
        info = cls.get_symbol_info(symbol)
        return info.get('margin', 0.10)
    
    @classmethod
    def get_contract_size(cls, symbol: str) -> float:
        """获取合约乘数"""
        info = cls.get_symbol_info(symbol)
        return info.get('size', 10)
    
    @classmethod
    def calculate_margin(cls, symbol: str, price: float, quantity: float) -> float:
        """计算保证金"""
        contract_size = cls.get_contract_size(symbol)
        margin_rate = cls.get_margin_rate(symbol)
        return price * contract_size * quantity * margin_rate
    
    @classmethod
    def calculate_position_size(cls, symbol: str, price: float, capital: float, position_pct: float) -> int:
        """计算开仓手数"""
        available_capital = capital * position_pct
        margin_per_lot = cls.calculate_margin(symbol, price, 1)
        if margin_per_lot > 0:
            return int(available_capital / margin_per_lot)
        return 0
    
    @classmethod
    def get_all_symbols(cls) -> List[Dict[str, str]]:
        """获取所有品种列表（供前端下拉框使用）"""
        result = []
        for symbol, info in cls.SYMBOLS.items():
            result.append({
                'value': symbol,
                'label': f"{info['name']} ({symbol.upper()})",
                'exchange': info['exchange']
            })
        return sorted(result, key=lambda x: x['exchange'])
