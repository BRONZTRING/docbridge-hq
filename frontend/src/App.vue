<template>
  <!-- 🔐 身份验证闸门 (未登录时显示) -->
  <div v-if="!isAuthenticated" class="auth-container">
    <div class="auth-box">
      <div class="auth-header">
        <h2><el-icon><Odometer /></el-icon> DocBridge AI</h2>
        <p>战略情报中枢 - 身份验证系统</p>
      </div>
      
      <el-form @submit.prevent="handleAuth" class="auth-form">
        <el-input v-model="authForm.username" placeholder="输入统帅代号 (Username)" class="mb-4" size="large" prefix-icon="User" />
        <el-input v-model="authForm.password" placeholder="输入绝密口令 (Password)" class="mb-4" type="password" show-password size="large" prefix-icon="Lock" />
        
        <el-button type="primary" native-type="submit" :loading="isAuthLoading" class="auth-btn" size="large">
          {{ isLoginMode ? '验证兵符 (登录)' : '铸造兵符 (注册)' }}
        </el-button>
        
        <div class="auth-switch">
          <span v-if="isLoginMode">尚无兵符？ <a href="#" @click.prevent="isLoginMode = false">申请铸造</a></span>
          <span v-else>已有兵符？ <a href="#" @click.prevent="isLoginMode = true">返回验证</a></span>
        </div>
      </el-form>
    </div>
  </div>

  <!-- 🌐 核心大阵 (已登录时显示) -->
  <el-container v-else class="layout-container">
    <el-aside width="220px" class="aside-menu">
      <div class="logo-box">
        <h2>DocBridge AI</h2>
        <span class="sub-title">情报中枢 v1.0</span>
      </div>
      <el-menu default-active="1" background-color="#2c3e50" text-color="#fff" active-text-color="#409eff">
        <el-menu-item index="1" @click="viewGlobalChat = false"><el-icon><Document /></el-icon><span>文档雷达</span></el-menu-item>
        <el-menu-item index="2" @click="viewGlobalChat = true"><el-icon><Odometer /></el-icon><span style="color:#67c23a; font-weight:bold;">全局统帅部</span></el-menu-item>
        <el-menu-item index="3"><el-icon><UploadFilled /></el-icon><span>多模态摄入</span></el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left"><span>物理坐标：下诺夫哥罗德 | 雷达状态：在线自动轮询中...</span></div>
        <div class="header-right">
          <el-avatar size="small" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" />
          <span style="margin-left: 10px; font-weight: bold; margin-right: 20px;">{{ currentUser }}</span>
          <el-button type="danger" size="small" plain @click="logout"><el-icon><SwitchButton /></el-icon> 销毁兵符</el-button>
        </div>
      </el-header>
      
      <el-main class="main-content">
        <!-- 文档列表视图 -->
        <el-card v-if="!viewGlobalChat" class="box-card">
          <template #header>
            <div class="card-header">
              <span>全语境情报池 (仅展示属于您的机密卷宗)</span>
              <el-upload action="#" :http-request="customUpload" :show-file-list="false" accept=".pdf,.docx,.txt">
                <el-button type="primary" :loading="isUploading"><el-icon><Upload /></el-icon> 物理摄入</el-button>
              </el-upload>
            </div>
          </template>
          
          <el-table :data="tableData" style="width: 100%" stripe>
            <el-table-column prop="id" label="编号" width="70" />
            <el-table-column prop="filename" label="物理文件名" />
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

        <!-- 全局战略统帅部视图 -->
        <el-card v-if="viewGlobalChat" class="box-card" style="border: 2px solid #67c23a;">
          <template #header>
            <div class="card-header">
              <span style="color:#67c23a; font-size:18px;"><el-icon><Odometer /></el-icon> 全局战略统帅部 (跨文档检索 + 合规隐私屏蔽)</span>
            </div>
          </template>
          <div class="chat-container" style="height: 65vh;">
            <div class="chat-history">
              <div v-if="globalChatHistory.length === 0" class="empty-chat">统帅，大模型已加载完毕。您现在的提问将检索您名下的所有卷宗（自动启动合规拦截网）。</div>
              <div v-for="(msg, index) in globalChatHistory" :key="index" :class="['chat-bubble-wrapper', msg.role]">
                <div class="chat-bubble">
                  <span v-if="msg.role === 'ai'" style="font-weight:bold; color: #409eff; display:block; margin-bottom:5px;">[全局参谋总长]</span>
                  <span v-else style="font-weight:bold; color: #67c23a; display:block; margin-bottom:5px;">[{{ currentUser }}]</span>
                  <div style="white-space: pre-wrap; line-height: 1.5;">{{ msg.content }}</div>
                </div>
              </div>
            </div>
            <div class="chat-input-area">
              <el-input v-model="globalChatInput" placeholder="输入全局检索指令 (支持中俄英日)... 按回车发送" @keyup.enter="sendGlobalChatMessage" :disabled="isGlobalChatting">
                <template #append><el-button @click="sendGlobalChatMessage" :loading="isGlobalChatting" type="success">发送指令</el-button></template>
              </el-input>
            </div>
          </div>
        </el-card>

        <!-- 局部审讯弹窗 -->
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
            <el-tab-pane label="局部审讯室" name="chat">
              <div class="chat-container">
                <div class="chat-history">
                  <div v-if="chatHistory.length === 0" class="empty-chat">您可以就这份文献提出任何问题。</div>
                  <div v-for="(msg, index) in chatHistory" :key="index" :class="['chat-bubble-wrapper', msg.role]">
                    <div class="chat-bubble">
                      <span v-if="msg.role === 'ai'" style="font-weight:bold; color: #409eff; display:block; margin-bottom:5px;">[AI 参谋]</span>
                      <span v-else style="font-weight:bold; color: #67c23a; display:block; margin-bottom:5px;">[{{ currentUser }}]</span>
                      <div style="white-space: pre-wrap; line-height: 1.5;">{{ msg.content }}</div>
                    </div>
                  </div>
                </div>
                <div class="chat-input-area">
                  <el-input v-model="chatInput" placeholder="按回车发送..." @keyup.enter="sendChatMessage" :disabled="isChatting">
                    <template #append><el-button @click="sendChatMessage" :loading="isChatting" type="primary">发送</el-button></template>
                  </el-input>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-dialog>

        <!-- 战报视窗插件 -->
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

// ==========================================
// 🔐 身份验证与 JWT 拦截器逻辑
// ==========================================
const isAuthenticated = ref(!!localStorage.getItem('docbridge_token'))
const currentUser = ref(localStorage.getItem('docbridge_user') || '未命名统帅')
const isLoginMode = ref(true)
const authForm = ref({ username: '', password: '' })
const isAuthLoading = ref(false)

// Axios 全局拦截器：每次请求自动带上 JWT 兵符
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('docbridge_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Axios 响应拦截器：发现 401 (兵符过期或伪造)，自动打回登录页
axios.interceptors.response.use(res => res, err => {
  if (err.response && err.response.status === 401) {
    if (isAuthenticated.value) {
      ElMessage.error('兵符已失效，请重新验证身份！')
      logout()
    }
  }
  return Promise.reject(err)
})

const handleAuth = async () => {
  if (!authForm.value.username || !authForm.value.password) {
    return ElMessage.warning('代号与口令不可为空！')
  }
  
  isAuthLoading.value = true
  const formData = new FormData()
  formData.append('username', authForm.value.username)
  formData.append('password', authForm.value.password)

  try {
    if (isLoginMode.value) {
      const res = await axios.post(`${API_BASE_URL}/auth/login`, formData)
      localStorage.setItem('docbridge_token', res.data.access_token)
      localStorage.setItem('docbridge_user', authForm.value.username)
      isAuthenticated.value = true
      currentUser.value = authForm.value.username
      ElMessage.success('兵符验证成功，大阵已为您展开！')
      fetchDocuments()
      startPolling() // 登录后启动轮询
    } else {
      await axios.post(`${API_BASE_URL}/auth/register`, formData)
      ElMessage.success('兵符铸造成功！请切换至验证页面登录。')
      isLoginMode.value = true
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '通讯中断，验证失败')
  } finally {
    isAuthLoading.value = false
  }
}

const logout = () => {
  localStorage.removeItem('docbridge_token')
  localStorage.removeItem('docbridge_user')
  isAuthenticated.value = false
  currentUser.value = ''
  tableData.value = []
  stopPolling()
}

// ==========================================
// 🌐 核心业务逻辑
// ==========================================
const tableData = ref([])
const isUploading = ref(false)
let pollingTimer = null

const viewGlobalChat = ref(false)
const dialogVisible = ref(false)
const activeTab = ref('summary')
const currentResult = ref(null)
const currentDocId = ref(null)
const currentDocName = ref("")

const chatHistory = ref([])
const chatInput = ref("")
const isChatting = ref(false)

const globalChatHistory = ref([])
const globalChatInput = ref("")
const isGlobalChatting = ref(false)

const fetchDocuments = async () => {
  if (!isAuthenticated.value) return;
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
  const historyToSend = chatHistory.value.map(item => ({ role: item.role, content: item.content }))
  chatHistory.value.push({ role: 'user', content: query })
  chatInput.value = ""; isChatting.value = true
  try {
    const res = await axios.post(`${API_BASE_URL}/chat`, { query: query, document_id: currentDocId.value, history: historyToSend })
    if (res.data.status === 'success') chatHistory.value.push({ role: 'ai', content: res.data.answer })
  } catch (error) { chatHistory.value.push({ role: 'ai', content: '【通讯中断】' }) }
  finally { isChatting.value = false }
}

const sendGlobalChatMessage = async () => {
  if (!globalChatInput.value.trim() || isGlobalChatting.value) return;
  const query = globalChatInput.value
  const historyToSend = globalChatHistory.value.map(item => ({ role: item.role, content: item.content }))
  globalChatHistory.value.push({ role: 'user', content: query })
  globalChatInput.value = ""; isGlobalChatting.value = true
  try {
    const res = await axios.post(`${API_BASE_URL}/chat`, { query: query, history: historyToSend })
    if (res.data.status === 'success') globalChatHistory.value.push({ role: 'ai', content: res.data.answer })
  } catch (error) { globalChatHistory.value.push({ role: 'ai', content: '【通讯中断】' }) }
  finally { isGlobalChatting.value = false }
}

const formatStatus = (status) => {
  const map = { 'uploaded': '待命', 'processing': '劳工解析中...', 'completed': '认知完成', 'failed_auth': '阻断(核查日志)', 'failed': '解析溃散' }
  return map[status] || status
}
const getStatusType = (status) => {
  const map = { 'processing': 'warning', 'completed': 'success', 'failed_auth': 'danger', 'failed': 'danger', 'uploaded': 'info' }
  return map[status] || 'info'
}

const startPolling = () => {
  if (!pollingTimer) pollingTimer = setInterval(fetchDocuments, 5000)
}
const stopPolling = () => {
  if (pollingTimer) { clearInterval(pollingTimer); pollingTimer = null }
}

onMounted(() => {
  if (isAuthenticated.value) {
    fetchDocuments(); startPolling()
  }
})
onUnmounted(() => { stopPolling() })
</script>

<style scoped>
/* 身份验证门面样式 */
.auth-container { height: 100vh; width: 100vw; display: flex; justify-content: center; align-items: center; background: radial-gradient(circle at center, #2c3e50 0%, #1a252f 100%); }
.auth-box { background: rgba(255, 255, 255, 0.05); padding: 40px; border-radius: 12px; box-shadow: 0 15px 35px rgba(0,0,0,0.5); width: 400px; border: 1px solid rgba(103, 194, 58, 0.3); backdrop-filter: blur(10px); }
.auth-header { text-align: center; margin-bottom: 30px; }
.auth-header h2 { margin: 0; font-size: 24px; color: #67c23a; display: flex; align-items: center; justify-content: center; gap: 10px; }
.auth-header p { color: #909399; font-size: 14px; margin-top: 10px; }
.auth-btn { width: 100%; margin-top: 10px; font-weight: bold; background-color: #67c23a; border-color: #67c23a; }
.auth-btn:hover { background-color: #85ce61; border-color: #85ce61; }
.auth-switch { text-align: center; margin-top: 20px; font-size: 13px; color: #a8abb2; }
.auth-switch a { color: #409eff; text-decoration: none; font-weight: bold; }
.mb-4 { margin-bottom: 20px; }

/* 核心大阵原有样式 */
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