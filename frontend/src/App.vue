<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="aside-menu">
      <div class="logo-box">
        <h2>DocBridge AI</h2>
        <span class="sub-title">情报中枢 v1.0</span>
      </div>
      <el-menu default-active="1" background-color="#2c3e50" text-color="#fff" active-text-color="#409eff">
        <el-menu-item index="1"><el-icon><Document /></el-icon><span>文档雷达 (RAG)</span></el-menu-item>
        <el-menu-item index="2"><el-icon><UploadFilled /></el-icon><span>多模态摄入</span></el-menu-item>
        <el-menu-item index="3"><el-icon><Warning /></el-icon><span>风险拦截网</span></el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left"><span>物理坐标：下诺夫哥罗德 | 雷达状态：在线自动轮询中...</span></div>
        <div class="header-right">
          <el-avatar size="small" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" />
          <span style="margin-left: 10px; font-weight: bold;">统帅</span>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <el-card class="box-card">
          <template #header>
            <div class="card-header">
              <span>全语境情报池 (真实数据实时映射)</span>
              <el-upload action="#" :http-request="customUpload" :show-file-list="false" accept=".pdf,.docx,.txt">
                <el-button type="primary" :loading="isUploading"><el-icon><Upload /></el-icon> 物理摄入</el-button>
              </el-upload>
            </div>
          </template>
          
          <el-table :data="tableData" style="width: 100%" stripe>
            <el-table-column prop="id" label="编号" width="70" />
            <el-table-column prop="filename" label="物理文件名" />
            <el-table-column prop="language" label="语种" width="100" />
            <el-table-column prop="status" label="认知状态" width="160">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)">{{ formatStatus(scope.row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="摄入时间戳" width="180" />
            <el-table-column label="战略指令" width="120">
              <template #default="scope">
                <!-- 【重大升级】：按钮解锁，点击触发调阅 -->
                <el-button 
                  link 
                  type="primary" 
                  size="small"
                  :disabled="scope.row.status !== 'completed'"
                  @click="viewIntelligence(scope.row)"
                >
                  调阅情报
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 【全新兵器】：高维情报展示弹窗 -->
        <el-dialog v-model="dialogVisible" :title="'情报调阅: ' + currentDocName" width="60%">
          <div v-if="currentResult">
            <h3 style="color: #409eff;"><el-icon><DataAnalysis /></el-icon> 核心摘要 (Summary)</h3>
            <p style="line-height: 1.6; color: #303133;">{{ currentResult.summary }}</p>
            
            <el-divider />
            
            <h3 style="color: #f56c6c;"><el-icon><WarningFilled /></el-icon> 风险雷达 (Risk Points)</h3>
            <div style="background-color: #fef0f0; padding: 15px; border-radius: 4px; color: #f56c6c; white-space: pre-wrap; line-height: 1.6;">
              {{ currentResult.risk_points.raw_report || currentResult.risk_points }}
            </div>
          </div>
          <template #footer>
            <span class="dialog-footer">
              <el-button type="primary" @click="dialogVisible = false">关闭卷宗</el-button>
            </span>
          </template>
        </el-dialog>

      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

const tableData = ref([])
const isUploading = ref(false)
let pollingTimer = null

// 弹窗状态管理
const dialogVisible = ref(false)
const currentResult = ref(null)
const currentDocName = ref("")

const fetchDocuments = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/documents/`)
    if (res.data.status === 'success') tableData.value = res.data.data
  } catch (error) {
    console.error("雷达连接失败:", error)
  }
}

const customUpload = async (options) => {
  isUploading.value = true
  const formData = new FormData()
  formData.append('file', options.file)
  try {
    const res = await axios.post(`${API_BASE_URL}/upload/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    ElMessage.success(res.data.message || '文件摄入成功！')
    fetchDocuments()
  } catch (error) {
    ElMessage.error('摄入失败，防线可能受损！')
  } finally {
    isUploading.value = false
  }
}

// 【新增核心动作】：向网关索要详细报告
const viewIntelligence = async (row) => {
  currentDocName.value = row.filename
  try {
    const res = await axios.get(`${API_BASE_URL}/documents/${row.id}/result`)
    if (res.data.status === 'success') {
      currentResult.value = res.data
      dialogVisible.value = true
    }
  } catch (error) {
    ElMessage.error('调阅失败，情报可能尚未落盘或已损坏。')
  }
}

const formatStatus = (status) => {
  const map = { 'uploaded': '待命', 'processing': '劳工解析中...', 'completed': '认知完成', 'failed_auth': '密钥阻断 (需真密钥)', 'failed': '解析溃散' }
  return map[status] || status
}

const getStatusType = (status) => {
  const map = { 'processing': 'warning', 'completed': 'success', 'failed_auth': 'danger', 'failed': 'danger', 'uploaded': 'info' }
  return map[status] || 'info'
}

onMounted(() => {
  fetchDocuments()
  pollingTimer = setInterval(fetchDocuments, 5000)
})

onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer)
})
</script>

<style scoped>
/* 保持原有样式不变 */
.layout-container { height: 100vh; width: 100vw; }
.aside-menu { background-color: #2c3e50; color: white; }
.logo-box { height: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; border-bottom: 1px solid #1a252f; background-color: #1a252f; }
.logo-box h2 { margin: 0; font-size: 18px; color: #409eff; }
.sub-title { font-size: 12px; color: #909399; }
.header { background-color: #fff; border-bottom: 1px solid #dcdfe6; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; }
.header-left { font-family: 'Courier New', Courier, monospace; color: #606266; }
.header-right { display: flex; align-items: center; }
.main-content { background-color: #f0f2f5; padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; font-weight: bold; }
</style>