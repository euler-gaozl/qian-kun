/**
 * 配置管理模块
 */

import { z } from 'zod';

/**
 * 配置模式定义
 */
const configSchema = z.object({
  BACKEND_API_URL: z.string().url().default('http://localhost:8000'),
});

export type Config = z.infer<typeof configSchema>;

function validateConfig(): Config {
  try {
    return configSchema.parse({
      BACKEND_API_URL: process.env.QIANKUN_API_URL || process.env.BACKEND_API_URL,
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errorMessages = error.errors.map(err =>
        `  - ${err.path.join('.')}: ${err.message}`
      ).join('\n');
      
      throw new Error(
        `MCP配置验证失败:\n${errorMessages}\n\n` +
        `请检查MCP配置中的 QIANKUN_API_URL 环境变量`
      );
    }
    throw error;
  }
}

export const appConfig = validateConfig();

export function printConfigSummary(): void {
  console.error('MCP配置:');
  console.error(`  后端API: ${appConfig.BACKEND_API_URL}`);
  console.error('  超时: 5分钟');
  console.error('');
}