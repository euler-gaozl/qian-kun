# 乾坤期货策略 MCP 服务器

MCP服务器用于查询实时策略信号和AI深度分析。

## 快速配置

### 1. 编译
```bash
cd mcp-server && npm install && npm run build
```

### 2. 配置MCP

**配置文件位置**：
- macOS: `~/Library/Application Support/Code/User/globalStorage/shengsuan-cloud.kilo-ssy/settings/mcp_settings.json`
- Windows: `%APPDATA%\Code\User\globalStorage\shengsuan-cloud.kilo-ssy\settings\mcp_settings.json`

**配置内容**（替换路径为你的实际项目路径）：
```json
{
  "mcpServers": {
    "qiankun-strategy": {
      "command": "node",
      "args": [
        "/path/to/your/project/mcp-server/build/index.js"
      ],
      "env": {
        "QIANKUN_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

### 3. 启动
```bash
# 启动后端
./start.sh

# 重启Kilo Code
CMD+Shift+P → Developer: Reload Window
```

## 使用

**查询策略**：
```
查询rb2601的15分钟、30分钟、60分钟策略信号
```

**AI分析**：
```
使用AI分析rb2601，周期1d
```

**注意**：AI配置在后端 `backend/.env` 文件中，不是MCP配置。