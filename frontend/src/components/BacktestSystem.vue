<template>
  <div class="backtest-system">
    <el-form :model="form" label-width="120px" :rules="rules" ref="formRef">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="品种" prop="symbol">
            <el-select v-model="form.symbol" placeholder="请选择品种" filterable>
              <el-option
                v-for="item in symbols"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="操作周期" prop="period">
            <el-select v-model="form.period" placeholder="请选择周期">
              <el-option
                v-for="item in periods"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="合约" prop="contract">
            <el-select v-model="form.contract" placeholder="请选择合约">
              <el-option
                v-for="item in contracts"
                :key="item"
                :label="item"
                :value="item"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="均线周期" prop="ma_period">
            <el-select v-model="form.ma_period" placeholder="请选择均线周期">
              <el-option
                v-for="i in 7"
                :key="i + 14"
                :label="`MA${i + 14}`"
                :value="i + 14"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="回测日期" prop="dateRange">
            <el-date-picker
              v-model="form.dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              :unlink-panels="true"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="使用连续合约">
            <el-switch v-model="form.use_continuous" />
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="初始资金" prop="initial_capital">
            <el-input-number
              v-model="form.initial_capital"
              :min="10000"
              :max="100000000"
              :step="10000"
              controls-position="right"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="开仓比例(%)" prop="position_pct">
            <el-input-number
              v-model="form.position_pct"
              :min="1"
              :max="100"
              :step="5"
              controls-position="right"
            />
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          <el-icon><DataAnalysis /></el-icon>
          开始回测
        </el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
    
    <!-- 回测报告显示区域 -->
    <BacktestReport v-if="backtestResult" :data="backtestResult" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import BacktestReport from './BacktestReport.vue'

// 表单数据
const form = reactive({
  symbol: '',
  period: '',
  contract: '',
  ma_period: 16,
  dateRange: [],
  initial_capital: 100000,
  position_pct: 10,
  use_continuous: false
})

// 表单验证规则
const rules = {
  symbol: [{ required: true, message: '请选择品种', trigger: 'change' }],
  period: [{ required: true, message: '请选择操作周期', trigger: 'change' }],
  contract: [{ required: true, message: '请选择合约', trigger: 'change' }],
  ma_period: [{ required: true, message: '请选择均线周期', trigger: 'change' }],
  dateRange: [{ required: true, message: '请选择回测日期范围', trigger: 'change' }],
  initial_capital: [{ required: true, message: '请输入初始资金', trigger: 'blur' }],
  position_pct: [{ required: true, message: '请输入开仓比例', trigger: 'blur' }]
}

const formRef = ref()
const loading = ref(false)
const backtestResult = ref(null)
const symbols = ref([])

// 操作周期选项
const periods = [
  { value: '5m', label: '5分钟' },
  { value: '15m', label: '15分钟' },
  { value: '30m', label: '30分钟' },
  { value: '60m', label: '60分钟' },
  { value: '120m', label: '120分钟' },
  { value: '240m', label: '240分钟' },
  { value: '1d', label: '日线' },
  { value: '2d', label: '2日' }
]

// 合约列表
const contracts = ref([])

// 生成合约列表
const generateContracts = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = now.getMonth() + 1
  const contracts_list = []
  
  for (let i = 0; i < 12; i++) {
    let contractMonth = month + i
    let contractYear = year
    
    if (contractMonth > 12) {
      contractMonth -= 12
      contractYear += 1
    }
    
    const yearStr = contractYear.toString().slice(-2)
    const monthStr = contractMonth.toString().padStart(2, '0')
    contracts_list.push(yearStr + monthStr)
  }
  
  contracts.value = contracts_list
}

// 获取品种列表
const fetchSymbols = async () => {
  try {
    const response = await axios.get('/api/symbols')
    if (response.data.success) {
      symbols.value = response.data.data
    }
  } catch (error) {
    console.error('获取品种列表失败:', error)
    // 使用默认品种列表
    // 中金所品种（大写）
    const cffexSymbols = [
      { value: 'IF', label: '沪深300 (IF)' },
      { value: 'IC', label: '中证500 (IC)' },
      { value: 'IH', label: '上证50 (IH)' },
      { value: 'IM', label: '中证1000 (IM)' },
      { value: 'TS', label: '2年期国债 (TS)' },
      { value: 'TF', label: '5年期国债 (TF)' },
      { value: 'T', label: '10年期国债 (T)' },
      { value: 'TL', label: '30年期国债 (TL)' }
    ]
    
    // 其他交易所品种（小写）
    const otherSymbols = [
      { value: 'rb', label: '螺纹钢 (rb)' },
      { value: 'cu', label: '铜 (cu)' },
      { value: 'al', label: '铝 (al)' },
      { value: 'zn', label: '锌 (zn)' },
      { value: 'au', label: '黄金 (au)' },
      { value: 'ag', label: '白银 (ag)' },
      { value: 'i', label: '铁矿石 (i)' },
      { value: 'j', label: '焦炭 (j)' },
      { value: 'jm', label: '焦煤 (jm)' },
      { value: 'm', label: '豆粕 (m)' },
      { value: 'y', label: '豆油 (y)' },
      { value: 'a', label: '豆一 (a)' },
      { value: 'b', label: '豆二 (b)' },
      { value: 'p', label: '棕榈油 (p)' },
      { value: 'c', label: '玉米 (c)' },
      { value: 'cs', label: '玉米淀粉 (cs)' },
      { value: 'l', label: '塑料 (l)' },
      { value: 'v', label: 'PVC (v)' },
      { value: 'pp', label: '聚丙烯 (pp)' },
      { value: 'eg', label: '乙二醇 (eg)' },
      { value: 'eb', label: '苯乙烯 (eb)' },
      { value: 'pg', label: 'LPG (pg)' },
      { value: 'ta', label: 'PTA (ta)' },
      { value: 'ma', label: '甲醇 (ma)' },
      { value: 'cf', label: '棉花 (cf)' },
      { value: 'sr', label: '白糖 (sr)' },
      { value: 'rm', label: '菜粕 (rm)' },
      { value: 'oi', label: '菜油 (oi)' },
      { value: 'fg', label: '玻璃 (fg)' },
      { value: 'sa', label: '纯碱 (sa)' },
      { value: 'ur', label: '尿素 (ur)' },
      { value: 'zc', label: '动力煤 (zc)' },
      { value: 'sf', label: '硅铁 (sf)' },
      { value: 'sm', label: '锰硅 (sm)' },
      { value: 'ap', label: '苹果 (ap)' },
      { value: 'cj', label: '红枣 (cj)' },
      { value: 'pk', label: '花生 (pk)' },
      { value: 'pf', label: '短纤 (pf)' },
      { value: 'wh', label: '强麦 (wh)' },
      { value: 'pm', label: '普麦 (pm)' },
      { value: 'ri', label: '早籼稻 (ri)' },
      { value: 'lr', label: '晚籼稻 (lr)' },
      { value: 'jr', label: '粳稻 (jr)' },
      { value: 'rs', label: '菜籽 (rs)' },
      { value: 'sp', label: '纸浆 (sp)' },
      { value: 'ru', label: '橡胶 (ru)' },
      { value: 'nr', label: '20号胶 (nr)' },
      { value: 'fu', label: '燃油 (fu)' },
      { value: 'bu', label: '沥青 (bu)' },
      { value: 'hc', label: '热卷 (hc)' },
      { value: 'ss', label: '不锈钢 (ss)' },
      { value: 'wr', label: '线材 (wr)' },
      { value: 'pb', label: '铅 (pb)' },
      { value: 'ni', label: '镍 (ni)' },
      { value: 'sn', label: '锡 (sn)' },
      { value: 'ao', label: '氧化铝 (ao)' },
      { value: 'bc', label: '国际铜 (bc)' },
      { value: 'lu', label: '低硫燃油 (lu)' },
      { value: 'sc', label: '原油 (sc)' },
      { value: 'ec', label: '合成橡胶 (ec)' },
      { value: 'lc', label: '碳酸锂 (lc)' },
      { value: 'si', label: '工业硅 (si)' }
    ]
    
    symbols.value = [...cffexSymbols, ...otherSymbols]
  }
}

// 提交表单
const handleSubmit = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return
  
  if (!form.dateRange || form.dateRange.length !== 2) {
    ElMessage.error('请选择回测日期范围')
    return
  }
  
  loading.value = true
  backtestResult.value = null
  
  try {
    const requestData = {
      symbol: form.symbol,
      period: form.period,
      contract: form.contract,
      ma_period: form.ma_period,
      start_date: form.dateRange[0],
      end_date: form.dateRange[1],
      initial_capital: form.initial_capital,
      position_pct: form.position_pct,
      use_continuous: form.use_continuous
    }
    
    const response = await axios.post('/api/backtest', requestData)
    backtestResult.value = response.data
    ElMessage.success('回测完成')
    
    // 滚动到报告区域
    setTimeout(() => {
      const reportElement = document.querySelector('.backtest-report')
      if (reportElement) {
        reportElement.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }, 100)
  } catch (error) {
    console.error('回测失败:', error)
    ElMessage.error(error.response?.data?.message || '回测失败，请检查参数后重试')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value.resetFields()
  backtestResult.value = null
}

// 设置默认日期范围（最近3个月）
const setDefaultDateRange = () => {
  const end = new Date()
  const start = new Date()
  start.setMonth(start.getMonth() - 3)
  
  form.dateRange = [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ]
}

// 组件挂载时执行
onMounted(() => {
  generateContracts()
  fetchSymbols()
  setDefaultDateRange()
})
</script>

<style scoped>
.backtest-system {
  padding: 20px;
}

.el-input-number {
  width: 100%;
}
</style>
