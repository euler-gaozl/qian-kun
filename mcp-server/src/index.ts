#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import axios from "axios";

// 从环境变量获取后端API地址
const API_BASE_URL = process.env.QIANKUN_API_URL || "http://localhost:8000";

// 定义查询参数schema
const QuerySchema = z.object({
  symbol: z.string().describe("品种代码，如rb(螺纹钢)、i(铁矿石)、hc(热卷)等"),
  contract: z.string().length(4).describe("合约代码，4位数字，如2501"),
  period: z.enum(["5m", "15m", "30m", "60m", "120m", "240m", "1d", "2d"]).describe("操作周期"),
  ma_period: z.number().min(15).max(21).optional().default(16).describe("均线周期，15-21之间，默认16"),
});

const BatchQuerySchema = z.object({
  queries: z.array(QuerySchema).describe("查询列表，支持批量查询多个品种/合约/周期组合"),
});

// 定义响应类型
interface StrategyResponse {
  instrument: string;
  period: string;
  action: string;
  price: number;
  timestamp: string;
  ma_value?: number;
  signal_strength?: string;
  close_price?: number;
}

interface BatchQueryResult {
  success: boolean;
  total_queries: number;
  results: StrategyResponse[];
  errors: Array<{
    query: any;
    error: string;
  }>;
  timestamp: string;
}

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * 查询单个策略信号
 */
async function querySingleStrategy(query: z.infer<typeof QuerySchema>): Promise<StrategyResponse> {
  try {
    const response = await apiClient.post("/api/realtime", query);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(
        `API错误: ${error.response?.data?.message || error.message}`
      );
    }
    throw error;
  }
}

/**
 * 批量查询策略信号
 */
async function batchQueryStrategy(
  queries: z.infer<typeof QuerySchema>[]
): Promise<BatchQueryResult> {
  const results: StrategyResponse[] = [];
  const errors: Array<{ query: any; error: string }> = [];

  // 顺序执行每个查询（可以改为并发以提高性能）
  for (const query of queries) {
    try {
      const result = await querySingleStrategy(query);
      results.push(result);
    } catch (error) {
      errors.push({
        query,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  return {
    success: errors.length === 0,
    total_queries: queries.length,
    results,
    errors,
    timestamp: new Date().toISOString(),
  };
}

/**
 * 格式化结果为易读的文本
 */
function formatResults(result: BatchQueryResult): string {
  const lines: string[] = [];
  
  lines.push("=".repeat(80));
  lines.push(`📊 乾坤期货策略查询结果`);
  lines.push(`查询时间: ${new Date(result.timestamp).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}`);
  lines.push(`总查询数: ${result.total_queries} | 成功: ${result.results.length} | 失败: ${result.errors.length}`);
  lines.push("=".repeat(80));
  lines.push("");

  // 显示成功的结果
  if (result.results.length > 0) {
    lines.push("✅ 查询成功:");
    lines.push("");
    
    result.results.forEach((r, idx) => {
      lines.push(`【${idx + 1}】${r.instrument} - ${r.period}`);
      lines.push(`   操作建议: ${getActionEmoji(r.action)} ${r.action}`);
      lines.push(`   信号强度: ${getStrengthEmoji(r.signal_strength)} ${r.signal_strength || "N/A"}`);
      
      if (r.price > 0) {
        lines.push(`   建议价格: ¥${r.price.toFixed(2)}`);
      }
      
      if (r.ma_value) {
        lines.push(`   MA值: ${r.ma_value.toFixed(2)}`);
      }
      
      if (r.close_price) {
        lines.push(`   建议平仓价: ¥${r.close_price.toFixed(2)}`);
      }
      
      lines.push("");
    });
  }

  // 显示错误
  if (result.errors.length > 0) {
    lines.push("❌ 查询失败:");
    lines.push("");
    
    result.errors.forEach((err, idx) => {
      lines.push(`【${idx + 1}】${err.query.symbol}${err.query.contract} - ${err.query.period}`);
      lines.push(`   错误: ${err.error}`);
      lines.push("");
    });
  }

  lines.push("=".repeat(80));
  
  return lines.join("\n");
}

/**
 * 获取操作建议的emoji
 */
function getActionEmoji(action: string): string {
  const emojiMap: Record<string, string> = {
    "多": "📈",
    "空": "📉",
    "平仓": "💰",
    "观望": "⏸️",
  };
  return emojiMap[action] || "❓";
}

/**
 * 获取信号强度的emoji
 */
function getStrengthEmoji(strength?: string): string {
  const emojiMap: Record<string, string> = {
    "强": "🔥",
    "中": "⚡",
    "弱": "💧",
  };
  return strength ? (emojiMap[strength] || "❓") : "❓";
}

// 创建MCP服务器
const server = new Server(
  {
    name: "qiankun-strategy-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// 注册工具列表处理器
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "query_realtime_strategy",
        description: 
          "批量查询期货品种的实时交易策略信号。支持同时查询多个品种、合约和周期组合，" +
          "一次性返回所有结果。适合多轮查询场景，例如查询多个品种的不同周期信号。\n\n" +
          "支持的品种包括：rb(螺纹钢)、i(铁矿石)、hc(热卷)、IC(中证500)、IF(沪深300)等。\n" +
          "支持的周期：5m, 15m, 30m, 60m, 120m, 240m, 1d, 2d",
        inputSchema: {
          type: "object",
          properties: {
            queries: {
              type: "array",
              description: "查询列表，每个查询包含品种、合约、周期等参数",
              items: {
                type: "object",
                properties: {
                  symbol: {
                    type: "string",
                    description: "品种代码，如rb(螺纹钢)、i(铁矿石)、hc(热卷)等",
                  },
                  contract: {
                    type: "string",
                    description: "合约代码，4位数字，如2501表示2025年1月",
                  },
                  period: {
                    type: "string",
                    enum: ["5m", "15m", "30m", "60m", "120m", "240m", "1d", "2d"],
                    description: "操作周期",
                  },
                  ma_period: {
                    type: "number",
                    description: "均线周期，15-21之间，默认16",
                    minimum: 15,
                    maximum: 21,
                  },
                },
                required: ["symbol", "contract", "period"],
              },
            },
          },
          required: ["queries"],
        },
      },
    ],
  };
});

// 注册工具调用处理器
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "query_realtime_strategy") {
    try {
      // 验证输入参数
      const parsed = BatchQuerySchema.safeParse(request.params.arguments);
      
      if (!parsed.success) {
        return {
          content: [
            {
              type: "text",
              text: `参数验证失败: ${parsed.error.message}`,
            },
          ],
          isError: true,
        };
      }

      // 执行批量查询
      const result = await batchQueryStrategy(parsed.data.queries);
      
      // 格式化结果
      const formattedText = formatResults(result);
      
      return {
        content: [
          {
            type: "text",
            text: formattedText,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `查询失败: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
        isError: true,
      };
    }
  }

  return {
    content: [
      {
        type: "text",
        text: `未知工具: ${request.params.name}`,
      },
    ],
    isError: true,
  };
});

// 启动服务器
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("乾坤期货策略MCP服务器已启动");
  console.error(`API地址: ${API_BASE_URL}`);
}

main().catch((error) => {
  console.error("服务器启动失败:", error);
  process.exit(1);
});