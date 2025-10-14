# MCP服务器安装指南

## 快速安装 ⚡

```bash
cd mcp-server
./install-mcp.sh
```

## 安装步骤

### 1. 克隆项目
```bash
git clone <项目地址>
cd qian-kun
```

### 2. 运行安装脚本
```bash
cd mcp-server
./install-mcp.sh
```

### 3. 选择配置
脚本会提示选择:
- [1] 配置到Kilo (VSCode插件)
- [2] 配置到Claude Desktop
- [3] 两个都配置
- [4] 只显示配置信息(手动配置)

### 4. 输入API地址
- 本地开发: `http://localhost:8000` (默认)
- 远程服务器: `http://your-server:8000`

### 5. 重启AI应用
- 如果配置了Kilo: 重启VSCode
- 如果配置了Claude: 重启Claude Desktop

## 使用测试

重启后,在AI对话中测试:
```
帮我看一下rb2501的15分钟策略信号
```

如果返回策略结果,说明安装成功! ✅

## 常见问题

### Q: 提示"未安装Node.js"
A: 安装Node.js: https://nodejs.org/ (推荐LTS版本)

### Q: MCP工具未显示
A: 
1. 确认已重启AI应用
2. 检查后端服务是否运行: `curl http://localhost:8000/docs`
3. 查看配置文件是否正确

### Q: 查询失败
A:
1. 启动后端服务: `cd .. && ./start.sh`
2. 确认API地址正确
3. 检查品种代码和合约格式

## 手动配置

如果自动安装失败,可以手动配置:

### Kilo配置文件
```
~/Library/Application Support/Code/User/globalStorage/shengsuan-cloud.kilo-ssy/settings/mcp_settings.json
```

### Claude Desktop配置文件
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

### 配置内容
```json
{
  "mcpServers": {
    "qiankun-strategy": {
      "command": "node",
      "args": ["<你的项目绝对路径>/mcp-server/build/index.js"],
      "env": {
        "QIANKUN_API_URL": "http://localhost:8000"
      }
    }
  }
}
```

## 更多帮助

- 详细文档: [README.md](README.md)
- 使用指南: [QUICKSTART.md](QUICKSTART.md)
- 项目主页: [../README.md](../README.md)

## 技术支持

如有问题,请联系项目维护者或提Issue。