<template>
  <div id="app">
    <el-container>
      <el-header>
        <h1>乾坤量化交易系统</h1>
      </el-header>
      <el-main>
        <el-tabs v-model="activeTab" type="card">
          <el-tab-pane label="实时策略" name="realtime">
            <RealtimeStrategy />
          </el-tab-pane>
          <el-tab-pane label="回测系统" name="backtest">
            <BacktestSystem />
          </el-tab-pane>
        </el-tabs>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import RealtimeStrategy from './components/RealtimeStrategy.vue'
import BacktestSystem from './components/BacktestSystem.vue'

const activeTab = ref('realtime')
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.el-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
}

.el-main {
  padding: 20px;
}

.el-tabs {
  background-color: white;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>
