<template>
  <div>
    <!-- 悬浮唤醒按钮 -->
    <button @click="isOpen = !isOpen" class="fixed bottom-6 right-6 bg-slate-800 text-green-400 p-3 rounded-full shadow-2xl hover:bg-slate-700 transition z-50 border border-green-500/30 flex items-center gap-2">
      <span v-if="!isOpen">📡 军机战报</span>
      <span v-else>❌ 关闭战报</span>
    </button>

    <!-- 战报终端控制台 -->
    <div v-if="isOpen" class="fixed bottom-20 right-6 w-[600px] h-[400px] bg-slate-900 border border-green-500/50 rounded-xl shadow-2xl flex flex-col z-50 overflow-hidden">
      <div class="bg-slate-800 p-2 text-xs text-gray-400 font-bold border-b border-green-500/30 flex justify-between items-center">
        <span>[终端] worker.log 实时映射</span>
        <span class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            连通
        </span>
      </div>
      <div ref="logContainer" class="flex-1 p-4 overflow-y-auto font-mono text-[11px] text-green-400 whitespace-pre-wrap leading-relaxed">
        <div v-for="(log, idx) in logs" :key="idx" class="border-b border-gray-800/50 pb-1 mb-1">{{ log }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';

const isOpen = ref(false);
const logs = ref([]);
const logContainer = ref(null);
let ws = null;

const connectWs = () => {
  ws = new WebSocket('ws://localhost:8000/api/v1/ws/logs');
  ws.onmessage = (event) => {
    logs.value.push(event.data);
    if (logs.value.length > 200) logs.value.shift(); // 仅保留最近 200 条战报
    nextTick(() => {
      if (logContainer.value) {
        logContainer.value.scrollTop = logContainer.value.scrollHeight;
      }
    });
  };
  ws.onclose = () => {
    setTimeout(connectWs, 3000); // 断线自动重连
  };
};

onMounted(() => {
  connectWs();
});

onUnmounted(() => {
  if (ws) ws.close();
});
</script>