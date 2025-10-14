# 乾坤策略 MCP 服务器 - 快速开始

## 问题排查

### 如果遇到 404 错误

MCP服务器已经修复并测试通过。如果你在使用时遇到404错误,请检查以下配置:

#### 1. 确认后端服务正在运行

```bash
# 测试后端API是否正常
curl -X POST http://localhost:8000/api/realtime \
  -H "Content-Type: application/json" \
  -d '{"symbol":"rb","contract":"2601","period":"1d","ma_period":16}'
```

如果返回JSON数据,说明后端正常。

#### 2. 检查你的对话工具MCP配置

**关键配置项:**

```json
{
  "mcpServers": {
    "qiankun-strategy": {
      "command": "node",
      "args": [
        "/Users/euler/workspace/python/github/qian-kun/mcp-server/build/index.js"
      ],
      "env": {
        "QIANKUN_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

**重点检查:**
1. `QIANKUN_API_URL` 必须是 `http://localhost:8000` (不要加 `/api/realtime`)
2. 路径必须指向 `build/index.js` 文件
3. 确保没有拼写错误

#### 3. 常见错误配置示例

❌ **错误 1: API_URL包含了路径**
```json
"env": {
  "QIANKUN_API_URL": "http://localhost:8000/api/realtime"  // 错误!
}
```

✅ **正确:**
```json
"env": {
  "QIANKUN_API_URL": "http://localhost:8000"  // 正确!
}
```

❌ **错误 2: 使用了错误的端口**
```json
"env": {
  "QIANKUN_API_URL": "http://localhost:3000"  // 错误! 应该是8000
}
```

❌ **错误 3: 没有设置环境变量**
```json
{
  "command": "node",
  "args": ["/path/to/build/index.js"]
  // 缺少 env 配置!
}
```

#### 4. 重启对话工具

修改配置后,**必须完全重启**你的对话工具(如Claude Desktop、Cursor等),让新配置生效。

## 手动测试MCP服务器

你可以手动测试MCP服务器是否正常工作:

```bash
cd /Users/euler/workspace/python/github/qian-kun/mcp-server

# 测试单个查询
QIANKUN_API_URL="http://localhost:8000" node build/index.js <<< '{
  "jsonrpc":"2.0",
  "id":1,
  "method":"tools/call",
  "params":{
    "name":"query_realtime_strategy",
    "arguments":{
      "queries":[
        {"symbol":"rb","contract":"2601","period":"1d","ma_period":16}
      ]
    }
  }
}'
```

如果看到成功的查询结果,说明MCP服务器本身没问题,问题在于对话工具的配置。

## 完整配置示例

### Claude Desktop 配置

配置文件位置: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "qiankun-strategy": {
      "command": "node",
      "args": [
        "/Users/euler/workspace/python/github/qian-kun/mcp-server/build/index.js"
      ],
      "env": {
        "QIANKUN_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Cursor 配置

配置文件位置: `~/.cursor/mcp_settings.json`

```json
{
  "mcpServers": {
    "qiankun-strategy": {
      "command": "node",
      "args": [
        "/Users/euler/workspace/python/github/qian-kun/mcp-server/build/index.js"
      ],
      "env": {
        "QIANKUN_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## 使用示例

配置成功后,你可以这样使用:

```
查询rb2601的1日线信号

查询rb2501的120分钟、240分钟、1日线和2日线信号

帮我分析一下i2505在不同周期的交易信号
```

MCP工具会自动解析你的自然语言请求,并返回所有查询结果。