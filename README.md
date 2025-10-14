# 乾坤量化交易系统

一个基于Vue 3 + FastAPI的前后端分离的金融量化交易系统。

## 系统架构

- **前端**: Vue 3 + Element Plus + Vite
- **后端**: FastAPI + Python 3.10+
- **数据源**: AkShare

## 功能特性

### 1. 实时策略
- 支持五大交易所全部品种
- 多周期支持（5分钟到2日）
- MA均线策略（15-21可调）
- 实时生成交易信号

### 2. 回测系统
- 历史数据回测
- 详细的统计指标
- 权益曲线图表
- 完整的交易记录

### 3. MCP服务器（AI对话集成）
- 支持通过LLM对话查询策略信号
- 批量查询多个品种/合约/周期
- 自然语言交互
- 多轮持续查询

## 快速开始

### 🚀 一键启动（推荐）

**macOS/Linux系统：**
```bash
# 启动前后端服务
./start.sh

# 停止所有服务
./stop.sh
```

启动脚本会自动：
- ✅ 检查并创建Python虚拟环境
- ✅ 安装所有依赖（首次运行）
- ✅ 同时启动后端和前端服务
- ✅ 检测端口占用并提示
- ✅ 后台运行，生成日志文件

访问地址：
- 前端界面: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

查看日志：
```bash
# 查看后端日志
tail -f logs/backend.log

# 查看前端日志
tail -f logs/frontend.log
```

### 📝 手动启动（备选方案）

#### 后端启动

1. 创建并激活虚拟环境：
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
```

2. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

3. 启动API服务：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API将在 http://localhost:8000 启动
API文档地址: http://localhost:8000/docs

#### 前端启动

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

前端将在 http://localhost:5173 启动

## 使用说明

### 实时策略
1. 选择品种（如螺纹钢）
2. 选择操作周期（如15分钟）
3. 选择合约（自动生成未来12个月）
4. 选择均线周期（默认MA16）
5. 点击"发起请求"获取交易信号

### 回测系统
1. 填写基本参数（品种、周期、合约、均线）
2. 选择回测日期范围
3. 设置初始资金和开仓比例
4. 点击"开始回测"
5. 查看回测报告：
   - 统计指标（收益率、胜率、盈亏比等）
   - 权益曲线图
   - 详细交易记录

## MCP服务器使用

### 什么是MCP服务器？

MCP (Model Context Protocol) 服务器让你可以在LLM对话工具中直接查询策略信号，无需打开网页界面。

### 团队成员安装MCP (推荐)

MCP服务器已包含在项目中，位于 `mcp-server/` 目录。

**一键安装:**
```bash
cd mcp-server
./install-mcp.sh
```

**安装脚本特性:**
- ✅ 自动检测项目路径(无需手动配置)
- ✅ 自动安装依赖和编译
- ✅ 支持配置到Kilo或Claude Desktop
- ✅ 支持自定义API地址(本地/远程)
- ✅ 智能合并现有配置

**使用流程:**
1. 克隆项目: `git clone <项目地址>`
2. 安装MCP: `cd mcp-server && ./install-mcp.sh`
3. 选择配置选项(Kilo/Claude/两者)
4. 输入API地址(默认localhost:8000)
5. 重启对应的AI应用
6. 开始使用!

### 手动配置说明

如需手动配置，配置文件位置:
```
~/Library/Application Support/Code/User/globalStorage/shengsuan-cloud.kilo-ssy/settings/mcp_settings.json
```

配置示例(需要修改路径为你的项目路径):
```json
{
  "mcpServers": {
    "qiankun-strategy": {
      "command": "node",
      "args": ["<你的项目路径>/mcp-server/build/index.js"],
      "env": {
        "QIANKUN_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### 使用示例

在支持MCP的LLM对话工具中，你可以用自然语言查询：

**单品种多周期查询：**
```
你: 帮我看一下螺纹钢rb2505在15分钟、30分钟、60分钟的策略信号

返回: 自动批量查询三个周期的信号并展示
```

**多品种查询：**
```
你: 同时查一下rb2501、i2505、hc2501的日线信号

返回: 批量查询三个品种的信号
```

**持续多轮查询：**
```
你: 先看rb2501的15分钟信号
→ [返回结果]

你: 再看30分钟和60分钟的
→ [追加查询]

你: 顺便看一下i2505的日线
→ [继续追加]
```

### MCP服务器开发

如需修改MCP服务器代码：

```bash
cd mcp-server
npm run build  # 重新编译
```

详细文档见：[`mcp-server/README.md`](mcp-server/README.md)

## 项目结构

```
qian-kun/
├── backend/
│   ├── main.py                 # FastAPI主应用
│   ├── controllers/             # 控制器
│   ├── services/               # 服务层
│   ├── strategies/             # 策略算法
│   ├── portfolio/              # 资金管理
│   ├── models/                 # 数据模型
│   └── utils/                  # 工具类
├── frontend/
│   ├── src/
│   │   ├── App.vue             # 主应用组件
│   │   ├── main.js             # 入口文件
│   │   └── components/         # Vue组件
│   │       ├── RealtimeStrategy.vue  # 实时策略
│   │       ├── BacktestSystem.vue    # 回测系统
│   │       └── BacktestReport.vue    # 回测报告
│   └── package.json
├── mcp-server/                  # MCP服务器
│   ├── src/                     # TypeScript源码
│   ├── build/                   # 编译输出
│   ├── package.json
│   └── README.md
└── README.md
```

## 核心策略说明

### MA连续性策略
- **开仓条件**: MA值连续n次单调递增（做多）或递减（做空）
- **平仓条件**: 连续两次停顿或反向运动
- **回踩验证**: 只有当MA价格在K线高低范围内才开仓

## 支持的品种

系统支持五大交易所全部品种：
- **上期所(SHFE)**: 铜、铝、锌、铅、镍、锡、黄金、白银、螺纹钢等
- **大商所(DCE)**: 玉米、豆粕、豆油、铁矿石、焦炭、焦煤等
- **郑商所(CZCE)**: 白糖、棉花、PTA、甲醇、动力煤等
- **中金所(CFFEX)**: 沪深300、中证500、上证50、国债期货等
- **广期所(GFEX)**: 工业硅、碳酸锂等

## 注意事项

1. 确保Python环境为3.10+
2. 确保已安装Node.js 16+
3. 数据源依赖网络连接
4. 首次运行可能需要较长时间获取数据

## 开发者

- 架构设计：基于设计文档完全重构
- 技术实现：前后端分离架构
- 策略算法：MA连续性判断

## License

MIT
