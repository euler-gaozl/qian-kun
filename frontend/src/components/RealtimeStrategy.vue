<template>
  <div class="realtime-strategy">
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
      
      <el-form-item>
        <el-button type="primary" @click="handleSubmit" :loading="loading">
          <el-icon><Promotion /></el-icon>
          发起请求
        </el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
    
    <!-- 结果显示区域 -->
    <el-divider v-if="result" />
    <div v-if="result" class="result-container">
      <h3>策略信号</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="合约代码">
          {{ result.instrument }}
        </el-descriptions-item>
        <el-descriptions-item label="操作周期">
          {{ result.period }}
        </el-descriptions-item>
        <el-descriptions-item label="操作建议">
          <el-tag :type="getActionType(result.action)">
            {{ result.action }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="建议开仓价">
          {{ result.price > 0 ? result.price.toFixed(2) : '市价' }}
        </el-descriptions-item>
        <el-descriptions-item label="建议平仓价">
          {{ result.close_price ? result.close_price.toFixed(2) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="MA值">
          {{ result.ma_value ? result.ma_value.toFixed(2) : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="信号强度">
          <el-tag :type="getStrengthType(result.signal_strength)">
            {{ result.signal_strength || '-' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="生成时间" :span="2">
          {{ formatTime(result.timestamp) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 表单数据
const form = reactive({
  symbol: '',
  period: '',
  contract: '',
  ma_period: 16
})

// 表单验证规则
const rules = {
  symbol: [{ required: true, message: '请选择品种', trigger: 'change' }],
  period: [{ required: true, message: '请选择操作周期', trigger: 'change' }],
  contract: [{ required: true, message: '请选择合约', trigger: 'change' }],
  ma_period: [{ required: true, message: '请选择均线周期', trigger: 'change' }]
}

const formRef = ref()
const loading = ref(false)
const result = ref(null)
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

// 合约列表（根据当前时间动态生成）
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
  
  loading.value = true
  result.value = null
  
  try {
    const response = await axios.post('/api/realtime', form)
    result.value = response.data
    ElMessage.success('策略信号生成成功')
  } catch (error) {
    console.error('请求失败:', error)
    ElMessage.error(error.response?.data?.message || '请求失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  formRef.value.resetFields()
  result.value = null
}

// 获取操作类型标签样式
const getActionType = (action) => {
  const map = {
    '多': 'success',
    '空': 'danger',
    '平仓': 'warning',
    '观望': 'info'
  }
  return map[action] || 'info'
}

// 获取信号强度标签样式
const getStrengthType = (strength) => {
  const map = {
    '强': 'success',
    '中': 'warning',
    '弱': 'info'
  }
  return map[strength] || 'info'
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 组件挂载时执行
onMounted(() => {
  generateContracts()
  fetchSymbols()
})
</script>

<style scoped>
.realtime-strategy {
  padding: 20px;
}

.result-container {
  margin-top: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.result-container h3 {
  margin-top: 0;
  margin-bottom: 20px;
  color: #303133;
}
</style>
