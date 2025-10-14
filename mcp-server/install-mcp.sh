#!/bin/bash

# 乾坤期货MCP服务器自动安装脚本
# 用于团队成员在本地一键配置MCP服务器

set -e

echo "=================================="
echo "🚀 乾坤期货MCP服务器安装脚本"
echo "=================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
MCP_BUILD_PATH="$SCRIPT_DIR/build/index.js"

echo -e "${YELLOW}📁 项目路径:${NC} $PROJECT_ROOT"
echo -e "${YELLOW}📦 MCP路径:${NC} $MCP_BUILD_PATH"
echo ""

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ 错误: 未安装Node.js${NC}"
    echo "请先安装Node.js: https://nodejs.org/"
    exit 1
fi

echo -e "${GREEN}✅ Node.js版本:${NC} $(node --version)"

# 检查npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ 错误: 未安装npm${NC}"
    exit 1
fi

echo -e "${GREEN}✅ npm版本:${NC} $(npm --version)"
echo ""

# 安装依赖和编译
echo "📦 检查MCP服务器依赖..."
cd "$SCRIPT_DIR"

if [ ! -d "node_modules" ]; then
    echo "正在安装依赖..."
    npm install
else
    echo -e "${GREEN}✅ 依赖已安装${NC}"
fi

# 编译
if [ ! -f "build/index.js" ]; then
    echo "正在编译MCP服务器..."
    npm run build
else
    echo -e "${GREEN}✅ MCP服务器已编译${NC}"
fi

echo ""
echo "=================================="
echo "🔧 开始配置MCP客户端"
echo "=================================="
echo ""

# 配置选择
echo "请选择要配置的MCP客户端:"
echo "1) Kilo (VSCode插件)"
echo "2) Claude Desktop"
echo "3) 两个都配置"
echo "4) 只显示配置信息(手动配置)"
echo ""
read -p "请输入选项 [1-4]: " choice

# API地址配置
read -p "后端API地址 (默认 http://localhost:8000): " api_url
api_url=${api_url:-http://localhost:8000}

# MCP配置JSON
MCP_CONFIG=$(cat <<EOF
{
  "qiankun-strategy": {
    "command": "node",
    "args": [
      "$MCP_BUILD_PATH"
    ],
    "env": {
      "QIANKUN_API_URL": "$api_url"
    },
    "disabled": false,
    "alwaysAllow": [],
    "disabledTools": []
  }
}
EOF
)

# 配置Kilo
configure_kilo() {
    local config_file="$HOME/Library/Application Support/Code/User/globalStorage/shengsuan-cloud.kilo-ssy/settings/mcp_settings.json"
    
    echo ""
    echo "配置Kilo MCP服务器..."
    
    # 创建目录
    mkdir -p "$(dirname "$config_file")"
    
    # 读取现有配置或创建新配置
    if [ -f "$config_file" ]; then
        # 使用node来合并JSON
        node <<NODEJS
const fs = require('fs');
const configFile = '$config_file';
const newServer = $MCP_CONFIG;

let config = {};
try {
    config = JSON.parse(fs.readFileSync(configFile, 'utf8'));
} catch (e) {
    config = { mcpServers: {} };
}

if (!config.mcpServers) {
    config.mcpServers = {};
}

config.mcpServers['qiankun-strategy'] = newServer['qiankun-strategy'];

fs.writeFileSync(configFile, JSON.stringify(config, null, 2));
console.log('✅ Kilo配置已更新');
NODEJS
    else
        # 创建新配置
        echo "{\"mcpServers\": $MCP_CONFIG}" | node -e "console.log(JSON.stringify(JSON.parse(require('fs').readFileSync(0, 'utf-8')), null, 2))" > "$config_file"
        echo -e "${GREEN}✅ Kilo配置已创建${NC}"
    fi
    
    echo -e "${YELLOW}📍 配置文件:${NC} $config_file"
    echo -e "${YELLOW}🔄 请重启VSCode使配置生效${NC}"
}

# 配置Claude Desktop
configure_claude() {
    local config_file="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
    
    echo ""
    echo "配置Claude Desktop MCP服务器..."
    
    # 创建目录
    mkdir -p "$(dirname "$config_file")"
    
    # 读取现有配置或创建新配置
    if [ -f "$config_file" ]; then
        node <<NODEJS
const fs = require('fs');
const configFile = '$config_file';
const newServer = $MCP_CONFIG;

let config = {};
try {
    config = JSON.parse(fs.readFileSync(configFile, 'utf8'));
} catch (e) {
    config = { mcpServers: {} };
}

if (!config.mcpServers) {
    config.mcpServers = {};
}

config.mcpServers['qiankun-strategy'] = newServer['qiankun-strategy'];

fs.writeFileSync(configFile, JSON.stringify(config, null, 2));
console.log('✅ Claude Desktop配置已更新');
NODEJS
    else
        echo "{\"mcpServers\": $MCP_CONFIG}" | node -e "console.log(JSON.stringify(JSON.parse(require('fs').readFileSync(0, 'utf-8')), null, 2))" > "$config_file"
        echo -e "${GREEN}✅ Claude Desktop配置已创建${NC}"
    fi
    
    echo -e "${YELLOW}📍 配置文件:${NC} $config_file"
    echo -e "${YELLOW}🔄 请重启Claude Desktop使配置生效${NC}"
}

# 显示配置信息
show_config() {
    echo ""
    echo "=================================="
    echo "📋 MCP配置信息"
    echo "=================================="
    echo ""
    echo "请手动添加以下配置到你的MCP客户端配置文件中:"
    echo ""
    echo -e "${YELLOW}MCP服务器路径:${NC}"
    echo "$MCP_BUILD_PATH"
    echo ""
    echo -e "${YELLOW}配置JSON:${NC}"
    echo "$MCP_CONFIG" | node -e "console.log(JSON.stringify(JSON.parse(require('fs').readFileSync(0, 'utf-8')), null, 2))"
    echo ""
    echo -e "${YELLOW}常见配置文件位置:${NC}"
    echo "Kilo: ~/Library/Application Support/Code/User/globalStorage/shengsuan-cloud.kilo-ssy/settings/mcp_settings.json"
    echo "Claude Desktop: ~/Library/Application Support/Claude/claude_desktop_config.json"
    echo "Cursor: ~/Library/Application Support/Cursor/User/globalStorage/mcp/settings.json"
}

# 根据选择执行配置
case $choice in
    1)
        configure_kilo
        ;;
    2)
        configure_claude
        ;;
    3)
        configure_kilo
        configure_claude
        ;;
    4)
        show_config
        ;;
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo "=================================="
echo "✨ 安装完成!"
echo "=================================="
echo ""
echo -e "${GREEN}MCP服务器已准备就绪!${NC}"
echo ""
echo "📝 使用说明:"
echo "1. 确保后端服务已启动: ./start.sh"
echo "2. 重启对应的MCP客户端"
echo "3. 在对话中使用自然语言查询策略"
echo ""
echo "📖 示例查询:"
echo '  "帮我看一下rb2505的15分钟策略信号"'
echo '  "查rb2501、i2505、hc2501的日线"'
echo ""
echo -e "${YELLOW}📚 详细文档:${NC} mcp-server/README.md"
echo ""