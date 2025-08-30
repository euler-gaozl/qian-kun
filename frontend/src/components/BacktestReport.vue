<template>
  <div class="backtest-report">
    <el-divider />
    
    <h2>回测报告</h2>
    
    <!-- 统计指标 -->
    <div class="statistics-section">
      <h3>统计指标</h3>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-statistic title="总收益" :value="data.statistics.total_profit">
            <template #suffix>
              <span :style="{ color: data.statistics.total_profit >= 0 ? '#67c23a' : '#f56c6c' }">
                元
              </span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="8">
          <el-statistic title="收益率" :value="data.statistics.total_return">
            <template #suffix>
              <span :style="{ color: data.statistics.total_return >= 0 ? '#67c23a' : '#f56c6c' }">
                %
              </span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="8">
          <el-statistic title="胜率" :value="data.statistics.win_rate">
            <template #suffix>%</template>
          </el-statistic>
        </el-col>
      </el-row>
      
      <el-divider />
      
      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="初始资金">
          {{ formatNumber(data.statistics.initial_capital) }} 元
        </el-descriptions-item>
        <el-descriptions-item label="最终资金">
          {{ formatNumber(data.statistics.final_capital) }} 元
        </el-descriptions-item>
        <el-descriptions-item label="最大回撤">
          {{ data.statistics.max_drawdown.toFixed(2) }}%
        </el-descriptions-item>
        <el-descriptions-item label="总交易次数">
          {{ data.statistics.total_trades }}
        </el-descriptions-item>
        <el-descriptions-item label="盈利次数">
          {{ data.statistics.winning_trades }}
        </el-descriptions-item>
        <el-descriptions-item label="亏损次数">
          {{ data.statistics.losing_trades }}
        </el-descriptions-item>
        <el-descriptions-item label="盈亏比">
          {{ data.statistics.profit_factor.toFixed(2) }}
        </el-descriptions-item>
        <el-descriptions-item label="夏普比率">
          {{ data.statistics.sharpe_ratio.toFixed(2) }}
        </el-descriptions-item>
        <el-descriptions-item label="平均盈利">
          {{ formatNumber(data.statistics.avg_profit) }} 元
        </el-descriptions-item>
        <el-descriptions-item label="平均亏损">
          {{ formatNumber(data.statistics.avg_loss) }} 元
        </el-descriptions-item>
        <el-descriptions-item label="最大连续盈利">
          {{ data.statistics.max_consecutive_wins }} 次
        </el-descriptions-item>
        <el-descriptions-item label="最大连续亏损">
          {{ data.statistics.max_consecutive_losses }} 次
        </el-descriptions-item>
      </el-descriptions>
    </div>
    
    <!-- 权益曲线图表 -->
    <div class="chart-section" v-if="data.equity_curve && data.equity_curve.length > 0">
      <h3>权益曲线</h3>
      <div ref="equityChart" style="width: 100%; height: 400px;"></div>
    </div>
    
    <!-- 交易记录 -->
    <div class="trades-section">
      <h3>交易记录</h3>
      <el-table 
        :data="data.trades" 
        style="width: 100%"
        max-height="500"
        stripe
      >
        <el-table-column prop="trade_id" label="交易ID" width="80" fixed />
        <el-table-column prop="direction" label="方向" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.direction === '多' ? 'success' : 'danger'" size="small">
              {{ scope.row.direction }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="open_time" label="开仓时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.open_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="open_price" label="开仓价格" width="100">
          <template #default="scope">
            {{ scope.row.open_price.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="手数" width="80">
          <template #default="scope">
            {{ scope.row.quantity }}
          </template>
        </el-table-column>
        <el-table-column prop="close_time" label="平仓时间" width="180">
          <template #default="scope">
            {{ scope.row.close_time ? formatDateTime(scope.row.close_time) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="close_price" label="平仓价格" width="100">
          <template #default="scope">
            {{ scope.row.close_price ? scope.row.close_price.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="profit" label="盈亏" width="120" fixed="right">
          <template #default="scope">
            <span v-if="scope.row.profit !== null" :style="{ color: scope.row.profit >= 0 ? '#67c23a' : '#f56c6c' }">
              {{ scope.row.profit >= 0 ? '+' : '' }}{{ scope.row.profit.toFixed(2) }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="profit_pct" label="收益率" width="100" fixed="right">
          <template #default="scope">
            <span v-if="scope.row.profit_pct !== null" :style="{ color: scope.row.profit_pct >= 0 ? '#67c23a' : '#f56c6c' }">
              {{ scope.row.profit_pct >= 0 ? '+' : '' }}{{ scope.row.profit_pct.toFixed(2) }}%
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" fixed="right">
          <template #default="scope">
            <el-tag :type="scope.row.status === '已平仓' ? 'info' : 'warning'" size="small">
              {{ scope.row.status }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 回测参数 -->
    <div class="parameters-section">
      <h3>回测参数</h3>
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="品种">
          {{ data.parameters.symbol.toUpperCase() }}
        </el-descriptions-item>
        <el-descriptions-item label="合约">
          {{ data.parameters.contract }}
        </el-descriptions-item>
        <el-descriptions-item label="周期">
          {{ data.parameters.period }}
        </el-descriptions-item>
        <el-descriptions-item label="MA周期">
          {{ data.parameters.ma_period }}
        </el-descriptions-item>
        <el-descriptions-item label="开始日期">
          {{ data.start_date }}
        </el-descriptions-item>
        <el-descriptions-item label="结束日期">
          {{ data.end_date }}
        </el-descriptions-item>
        <el-descriptions-item label="仓位比例">
          {{ data.parameters.position_pct }}%
        </el-descriptions-item>
        <el-descriptions-item label="执行耗时">
          {{ data.execution_time }}秒
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
})

const equityChart = ref(null)
let chartInstance = null

// 格式化数字
const formatNumber = (num) => {
  return new Intl.NumberFormat('zh-CN').format(num.toFixed(2))
}

// 格式化日期时间
const formatDateTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 绘制权益曲线图
const drawEquityChart = () => {
  if (!equityChart.value || !props.data.equity_curve) return
  
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  chartInstance = echarts.init(equityChart.value)
  
  const timestamps = props.data.equity_curve.map(item => formatDateTime(item.timestamp))
  const equityValues = props.data.equity_curve.map(item => item.equity)
  const capitalValues = props.data.equity_curve.map(item => item.capital)
  
  const option = {
    title: {
      text: '账户权益变化',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['总权益', '可用资金'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: timestamps,
      axisLabel: {
        rotate: 45,
        interval: Math.floor(timestamps.length / 10)
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value) => {
          return (value / 10000).toFixed(0) + '万'
        }
      }
    },
    series: [
      {
        name: '总权益',
        type: 'line',
        data: equityValues,
        smooth: true,
        lineStyle: {
          width: 2
        },
        itemStyle: {
          color: '#409eff'
        }
      },
      {
        name: '可用资金',
        type: 'line',
        data: capitalValues,
        smooth: true,
        lineStyle: {
          width: 1,
          type: 'dashed'
        },
        itemStyle: {
          color: '#67c23a'
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

// 监听数据变化重新绘制图表
watch(() => props.data, () => {
  nextTick(() => {
    drawEquityChart()
  })
}, { deep: true })

// 组件挂载时绘制图表
onMounted(() => {
  nextTick(() => {
    drawEquityChart()
  })
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    if (chartInstance) {
      chartInstance.resize()
    }
  })
})
</script>

<style scoped>
.backtest-report {
  margin-top: 30px;
  padding: 20px;
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.backtest-report h2 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #303133;
  text-align: center;
}

.backtest-report h3 {
  margin-top: 30px;
  margin-bottom: 20px;
  color: #606266;
  border-left: 3px solid #409eff;
  padding-left: 10px;
}

.statistics-section,
.chart-section,
.trades-section,
.parameters-section {
  margin-bottom: 30px;
}

.el-statistic {
  text-align: center;
}
</style>
