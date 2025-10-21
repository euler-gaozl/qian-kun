#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import axios from "axios";
import { appConfig, printConfigSummary } from "./config.js";

// 从配置模块获取后端API地址
const API_BASE_URL = appConfig.BACKEND_API_URL;

// 定义查询参数schema
const QuerySchema = z.object({
  symbol: z.string().describe("品种代码，如rb(螺纹钢)、i(铁矿石)、hc(热卷)等"),
  contract: z.string().length(4).describe("合约代码，4位数字，如2501"),
  period: z.enum(["5m", "15m", "30m", "60m", "120m", "240m", "1d", "2d"]).describe("操作周期"),
  ma_period: z.number().min(15).max(21).optional().default(16).describe("均线周期，15-21之间，默认16"),
});

// 定义AI分析参数schema（调用后端API）
const AIAnalysisSchema = z.object({
  symbol: z.string().describe("品种代码，如 rb（螺纹钢）、cf（棉花）"),
  contract: z.string().length(4).describe("合约代码，4位数字，如 2501、2601"),
  period: z.string().default("1d").describe("K线周期，如 5m, 15m, 30m, 60m, 120m, 240m, 1d, 2d"),
  query: z.string().optional().describe("自定义分析问题，如'分析当前走势和支撑阻力位'"),
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
  timeout: 300000, // 5分钟超时，确保AI分析有足够时间完成
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
 * 使用AI分析策略（调用后端API）
 */
async function analyzeStrategyWithAI(params: z.infer<typeof AIAnalysisSchema>): Promise<string> {
  try {
    // 直接调用后端的AI分析API
    const response = await apiClient.post("/api/ai-analysis", {
      symbol: params.symbol,
      contract: params.contract,
      period: params.period,
      query: params.query,
    });

    const data = response.data;

    // 检查分析是否成功
    if (!data.success) {
      throw new Error(data.error || "AI分析失败");
    }

    // 格式化返回结果
    return formatAIAnalysisResult(
      data.symbol,
      data.period,
      data.analysis,
      {
        kline_count: data.kline_count,
        timestamp: data.timestamp,
      }
    );
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorMsg = error.response?.data?.message || error.message;
      throw new Error(`后端API错误: ${errorMsg}`);
    }
    throw new Error(`AI分析失败: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * 格式化AI分析结果
 */
function formatAIAnalysisResult(
  symbol: string,
  interval: string,
  analysisContent: string,
  metadata?: any
): string {
  const lines: string[] = [];

  lines.push("=".repeat(80));
  lines.push("🤖 AI策略分析报告");
  lines.push("=".repeat(80));
  lines.push("");
  lines.push(`📊 合约: ${symbol}`);
  lines.push(`⏱️  周期: ${interval}`);
  const timestamp = metadata?.timestamp || new Date().toISOString();
  lines.push(`🕐 分析时间: ${new Date(timestamp).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}`);

  if (metadata?.kline_count) {
    lines.push(`📊 K线数量: ${metadata.kline_count}根`);
  }

  lines.push("");
  lines.push("=".repeat(80));
  lines.push("");
  lines.push(analysisContent);
  lines.push("");
  lines.push("=".repeat(80));
  lines.push("");
  lines.push("⚠️  风险提示:");
  lines.push("本分析由AI模型生成，仅供参考。市场有风险，投资需谨慎。");
  lines.push("请结合实际情况和自身风险承受能力做出投资决策。");
  lines.push("=".repeat(80));

  return lines.join("\n");
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
      {
        name: "analyze_strategy_with_ai",
        description:
          "使用AI大模型分析期货合约的K线数据，提供专业的技术分析和交易建议。" +
          "AI会综合分析K线形态、趋势方向、支撑阻力位等多个维度，给出详细的市场分析报告。\n\n" +
          "使用场景：\n" +
          "- 需要深入的技术分析时\n" +
          "- 想了解当前市场趋势和形态\n" +
          "- 寻求交易信号和关键价位建议\n" +
          "- 评估市场风险和机会\n\n" +
          "注意：AI分析仅供参考，市场有风险，投资需谨慎。",
        inputSchema: {
          type: "object",
          properties: {
            symbol: {
              type: "string",
              description: "品种代码，如 rb（螺纹钢）、cf（棉花）、i（铁矿石）",
            },
            contract: {
              type: "string",
              description: "合约代码，4位数字，如 2501、2601",
            },
            period: {
              type: "string",
              description: "K线周期，如 5m, 15m, 30m, 60m, 120m, 240m, 1d, 2d",
              default: "1d",
            },
            query: {
              type: "string",
              description: "自定义分析问题（可选），如'当前是否适合做多？'、'识别关键支撑位'等。不提供则进行综合分析。",
            },
          },
          required: ["symbol", "contract"],
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

  if (request.params.name === "analyze_strategy_with_ai") {
    try {
      // 验证输入参数
      const parsed = AIAnalysisSchema.safeParse(request.params.arguments);
      
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

      // 执行AI分析
      const result = await analyzeStrategyWithAI(parsed.data);
      
      return {
        content: [
          {
            type: "text",
            text: result,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `AI分析失败: ${error instanceof Error ? error.message : String(error)}`,
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
  console.error(`后端API地址: ${API_BASE_URL}`);
  console.error("");
  // 打印配置摘要
  printConfigSummary();
}

main().catch((error) => {
  console.error("服务器启动失败:", error);
  process.exit(1);
});