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
                <el-button link type="primary" size="small" :disabled="scope.row.status !== 'completed'" @click="viewIntelligence(scope.row)">
                  调阅情报
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-dialog v-model="dialogVisible" :title="'卷宗调阅: ' + currentDocName" width="65%" top="5vh">
          <el-tabs v-model="activeTab" class="custom-tabs">
            
            <el-tab-pane label="核心简报" name="summary">
              <div v-if="currentResult" class="scroll-pane">
                <h3 style="color: #409eff;"><el-icon><DataAnalysis /></el-icon> 核心摘要 (Summary)</h3>
                <p style="line-height: 1.6; color: #303133;">{{ currentResult.summary }}</p>
                <el-divider />
                <h3 style="color: #f56c6c;"><el-icon><WarningFilled /></el-icon> 风险雷达 (Risk Points)</h3>
                <div class="risk-box">{{ currentResult.risk_points.raw_report || currentResult.risk_points }}</div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="RAG 审讯室" name="chat">
              <div class="chat-container">
                <div class="chat-history">
                  <div v-if="chatHistory.length === 0" class="empty-chat">统帅，大模型已加载完毕。您可以就这份文献提出任何问题。</div>
                  <div v-for="(msg, index) in chatHistory" :key="index" :class="['chat-bubble-wrapper', msg.role]">
                    <div class="chat-bubble">
                      <span v-if="msg.role === 'ai'" style="font-weight:bold; color: #409eff; display:block; margin-bottom:5px;">[AI 参谋]</span>
                      <span v-else style="font-weight:bold; color: #67c23a; display:block; margin-bottom:5px;">[统帅]</span>
                      <div style="white-space: pre-wrap; line-height: 1.5;">{{ msg.content }}</div>
                    </div>
                  </div>
                </div>
                <div class="chat-input-area">
                  <el-input v-model="chatInput" placeholder="输入统帅指令 (支持中俄英日)... 按回车发送" @keyup.enter="sendChatMessage" :disabled="isChatting">
                    <template #append><el-button @click="sendChatMessage" :loading="isChatting" type="primary">发送</el-button></template>
                  </el-input>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-dialog>
        <LogViewer />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import LogViewer from './components/LogViewer.vue'

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'

const tableData = ref([])
const isUploading = ref(false)
let pollingTimer = null

const dialogVisible = ref(false)
const activeTab = ref('summary')
const currentResult = ref(null)
const currentDocId = ref(null)
const currentDocName = ref("")

const chatHistory = ref([])
const chatInput = ref("")
const isChatting = ref(false)

const fetchDocuments = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/documents/`)
    if (res.data.status === 'success') tableData.value = res.data.data
  } catch (error) {}
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
  } finally { isUploading.value = false }
}

const viewIntelligence = async (row) => {
  currentDocId.value = row.id; currentDocName.value = row.filename; activeTab.value = 'summary'; chatHistory.value = []
  try {
    const res = await axios.get(`${API_BASE_URL}/documents/${row.id}/result`)
    if (res.data.status === 'success') { currentResult.value = res.data; dialogVisible.value = true }
  } catch (error) { ElMessage.error('调阅失败。') }
}

const sendChatMessage = async () => {
  if (!chatInput.value.trim() || isChatting.value) return;
  const query = chatInput.value
  
  // 【战术升级】：在推入新问题前，提取现有历史记录打包发送
  const historyToSend = chatHistory.value.map(item => ({ role: item.role, content: item.content }))
  
  chatHistory.value.push({ role: 'user', content: query })
  chatInput.value = ""; isChatting.value = true
  try {
    const res = await axios.post(`${API_BASE_URL}/documents/${currentDocId.value}/chat`, { 
        query: query,
        history: historyToSend  // 发送历史矩阵
    })
    if (res.data.status === 'success') chatHistory.value.push({ role: 'ai', content: res.data.answer })
  } catch (error) { chatHistory.value.push({ role: 'ai', content: '【通讯中断】未能获取大模型响应。' }) }
  finally { isChatting.value = false }
}

const formatStatus = (status) => {
  const map = { 'uploaded': '待命', 'processing': '劳工解析中...', 'completed': '认知完成', 'failed_auth': '阻断(需核查日志)', 'failed': '解析溃散' }
  return map[status] || status
}

const getStatusType = (status) => {
  const map = { 'processing': 'warning', 'completed': 'success', 'failed_auth': 'danger', 'failed': 'danger', 'uploaded': 'info' }
  return map[status] || 'info'
}

onMounted(() => { fetchDocuments(); pollingTimer = setInterval(fetchDocuments, 5000) })
onUnmounted(() => { if (pollingTimer) clearInterval(pollingTimer) })
</script>

<style scoped>
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
.scroll-pane { max-height: 60vh; overflow-y: auto; padding-right: 10px; }
.risk-box { background-color: #fef0f0; padding: 15px; border-radius: 4px; color: #f56c6c; white-space: pre-wrap; line-height: 1.6; }
.chat-container { display: flex; flex-direction: column; height: 60vh; border: 1px solid #ebeef5; border-radius: 4px; background-color: #fafafa;}
.chat-history { flex: 1; overflow-y: auto; padding: 20px; }
.empty-chat { text-align: center; color: #909399; margin-top: 50px; font-style: italic; }
.chat-bubble-wrapper { margin-bottom: 15px; display: flex; }
.chat-bubble-wrapper.user { justify-content: flex-end; }
.chat-bubble-wrapper.ai { justify-content: flex-start; }
.chat-bubble { max-width: 80%; padding: 12px 16px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
.chat-bubble-wrapper.user .chat-bubble { background-color: #e1f3d8; border-bottom-right-radius: 0; }
.chat-bubble-wrapper.ai .chat-bubble { background-color: #fff; border-bottom-left-radius: 0; border: 1px solid #ebeef5;}
.chat-input-area { padding: 15px; background-color: #fff; border-top: 1px solid #ebeef5; }
</style>