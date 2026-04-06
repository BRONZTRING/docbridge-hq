<template>
  <el-container class="layout-container">
    <!-- 侧边导航栏 -->
    <el-aside width="220px" class="aside-menu">
      <div class="logo-box">
        <h2>DocBridge AI</h2>
        <span class="sub-title">情报中枢 v1.0</span>
      </div>
      <el-menu
        default-active="1"
        background-color="#2c3e50"
        text-color="#fff"
        active-text-color="#409eff"
      >
        <el-menu-item index="1">
          <el-icon><Document /></el-icon>
          <span>文档雷达 (RAG)</span>
        </el-menu-item>
        <el-menu-item index="2">
          <el-icon><UploadFilled /></el-icon>
          <span>多模态摄入</span>
        </el-menu-item>
        <el-menu-item index="3">
          <el-icon><Warning /></el-icon>
          <span>风险拦截网</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主操作区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <span>物理坐标：下诺夫哥罗德 (Nizhny Novgorod)</span>
        </div>
        <div class="header-right">
          <el-avatar size="small" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" />
          <span style="margin-left: 10px; font-weight: bold;">统帅</span>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <!-- Week1 核心目标：文件列表展示骨架 -->
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>四语境情报池 (待分析)</span>
              <el-button type="primary">
                <el-icon><Upload /></el-icon> 物理摄入
              </el-button>
            </div>
          </template>
          
          <el-table :data="tableData" style="width: 100%" stripe>
            <el-table-column prop="filename" label="文件名" />
            <el-table-column prop="language" label="语种探测" width="120" />
            <el-table-column prop="status" label="认知状态" width="150">
              <template #default="scope">
                <el-tag :type="scope.row.status === '已上传' ? 'info' : 'success'">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="date" label="时间戳" width="180" />
            <el-table-column label="战略指令" width="150">
              <template #default>
                <el-button link type="primary" size="small">启动认知链</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'

// 模拟的静态数据，为 Week 2 对接 FastAPI 做准备
const tableData = ref([
  {
    filename: 'Роснефть_合同草案.pdf',
    language: 'ru (俄文)',
    status: '已上传',
    date: '2026-04-05',
  },
  {
    filename: 'Toyota_Supply_Agreement.docx',
    language: 'ja (日文/N1)',
    status: '处理中...',
    date: '2026-04-05',
  },
  {
    filename: 'Web3_Tokenomics_Whitepaper.md',
    language: 'en (英文)',
    status: '已完成',
    date: '2026-04-04',
  }
])
</script>

<style scoped>
.layout-container {
  height: 100vh;
  width: 100vw;
}
.aside-menu {
  background-color: #2c3e50;
  color: white;
}
.logo-box {
  height: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #1a252f;
  background-color: #1a252f;
}
.logo-box h2 {
  margin: 0;
  font-size: 18px;
  color: #409eff;
}
.sub-title {
  font-size: 12px;
  color: #909399;
}
.header {
  background-color: #fff;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}
.header-left {
  font-family: 'Courier New', Courier, monospace;
  color: #606266;
}
.header-right {
  display: flex;
  align-items: center;
}
.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>