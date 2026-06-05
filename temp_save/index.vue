<template>
  <scroll-view class="container" scroll-y>
    <view class="header">
      <text class="title">TTS 听书系统 (App)</text>
    </view>

    <!-- 配置与合成 -->
    <view class="card">
      <view class="section-title"><text>文本与配置</text></view>
      
      <textarea class="textarea" v-model="inputText" placeholder="粘贴文本，或点击下方按钮上传文件 (图片/TXT/PDF)"></textarea>
      <button class="btn upload-btn" @click="chooseFile">选择文件上传</button>
      
      <view class="config-row">
        <text>发音人:</text>
        <picker :range="voices" :value="voiceIndex" @change="onVoiceChange">
          <view class="picker-view">{{ voices[voiceIndex] }}</view>
        </picker>
      </view>
      
      <view class="config-row">
        <text>语速 ({{ rate }}x):</text>
        <slider class="slider-flex" :value="rate" min="0.5" max="2.0" step="0.1" @change="onRateChange" />
      </view>
      
      <button class="btn primary-btn" :disabled="isProcessing" @click="startSynthesize">
        {{ isProcessing ? processStatus : '开始合成' }}
      </button>
    </view>

    <!-- 播放器 -->
    <view class="card" v-if="audioUrl">
      <view class="section-title"><text>正在播放</text></view>
      <text class="now-playing">{{ nowPlayingTitle }}</text>
      
      <view class="progress-row">
        <text class="time">{{ formatTime(currentTime) }}</text>
        <slider class="slider-flex" :value="currentTime" :max="duration || 100" @change="seekAudio" block-size="12" />
        <text class="time">{{ formatTime(duration) }}</text>
      </view>
      
      <view class="controls">
        <button class="ctrl-btn" @click="skipAudio(-15)">-15s</button>
        <button class="ctrl-btn primary-btn" @click="togglePlay">{{ isPlaying ? '暂停' : '播放' }}</button>
        <button class="ctrl-btn" @click="skipAudio(15)">+15s</button>
      </view>
    </view>

    <!-- 历史记录 -->
    <view class="card">
      <view class="section-title"><text>播放历史</text></view>
      <view class="task-list">
        <view class="task-item" v-for="task in tasks" :key="task.id" :class="{ playing: currentTaskId === task.id }">
          <view class="task-info" @click="loadTrack(task)">
            <text class="task-name">{{ task.filename }}</text>
            <text class="task-meta">{{ task.status === 'completed' ? '✅' : '⏳' }} {{ task.voice }} · {{ formatDate(task.created_at) }}</text>
          </view>
          <button class="del-btn" @click.stop="deleteTask(task)">删</button>
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''

// 状态
const inputText = ref('')
const isProcessing = ref(false)
const processStatus = ref('')
const tasks = ref([])

const voices = ref(['zh-CN-XiaoxiaoNeural', 'zh-CN-YunxiNeural', 'zh-CN-YunjianNeural', 'zh-CN-XiaoyiNeural'])
const voiceIndex = ref(0)
const rate = ref(1.0)

// 播放器状态
const currentTaskId = ref(null)
const audioUrl = ref('')
const nowPlayingTitle = ref('')
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
let lastSaveTime = 0

// 原生后台音频管理器
const bgAudio = uni.getBackgroundAudioManager()

// 初始化
onMounted(() => {
  fetchHistory()
  setupAudioListeners()
})

onUnmounted(() => {
  saveProgress()
})

// 工具函数
const formatTime = (sec) => {
  if (!sec || isNaN(sec)) return '00:00'
  const m = Math.floor(sec / 60).toString().padStart(2, '0')
  const s = Math.floor(sec % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return dateStr.substring(5, 16).replace('T', ' ')
}

// ----------------- 音频控制逻辑 -----------------
function setupAudioListeners() {
  bgAudio.onPlay(() => { isPlaying.value = true })
  bgAudio.onPause(() => { isPlaying.value = false; saveProgress() })
  bgAudio.onStop(() => { isPlaying.value = false; saveProgress() })
  bgAudio.onEnded(() => { isPlaying.value = false; clearProgress() })
  
  bgAudio.onTimeUpdate(() => {
    currentTime.value = bgAudio.currentTime
    if (!duration.value && bgAudio.duration) {
      duration.value = bgAudio.duration
    }
    
    // 每 3 秒自动保存一次
    const now = Date.now()
    if (now - lastSaveTime > 3000) {
      saveProgress()
      lastSaveTime = now
    }
  })

  // 原生系统中心或耳机的上一首/下一首按键映射为快退/快进
  bgAudio.onNext(() => { skipAudio(15) })
  bgAudio.onPrev(() => { skipAudio(-15) })
}

function loadTrack(task) {
  if (currentTaskId.value && isPlaying.value) saveProgress()
  
  currentTaskId.value = task.id
  nowPlayingTitle.value = task.filename
  
  // 拼接完整的线上音频 URL
  const fullUrl = task.audio_url.startsWith('http') ? task.audio_url : `${apiBaseUrl}${task.audio_url}`
  audioUrl.value = fullUrl
  
  // 设置原生后台播放信息（这会使手机锁屏显示音频名称）
  bgAudio.title = task.filename
  bgAudio.singer = 'TTS 听书系统'
  bgAudio.epname = '有声书'
  
  // 恢复进度
  const saved = uni.getStorageSync(`tts_progress_${task.id}`)
  if (saved) {
    const t = parseFloat(saved)
    if (t > 0) bgAudio.startTime = t
  } else {
    bgAudio.startTime = 0
  }

  // 赋值 src 会自动开始播放
  bgAudio.src = fullUrl
}

function togglePlay() {
  if (!audioUrl.value) return
  if (isPlaying.value) {
    bgAudio.pause()
  } else {
    bgAudio.play()
  }
}

function seekAudio(e) {
  const target = parseFloat(e.detail.value)
  bgAudio.seek(target)
  currentTime.value = target
}

function skipAudio(seconds) {
  let targetTime = currentTime.value + seconds
  if (targetTime < 0) targetTime = 0
  if (duration.value && targetTime > duration.value) targetTime = duration.value
  bgAudio.seek(targetTime)
}

function saveProgress() {
  if (!currentTaskId.value || !currentTime.value) return
  uni.setStorageSync(`tts_progress_${currentTaskId.value}`, currentTime.value.toString())
}

function clearProgress() {
  if (!currentTaskId.value) return
  uni.removeStorageSync(`tts_progress_${currentTaskId.value}`)
}

// ----------------- 网络请求与业务 -----------------
function onVoiceChange(e) {
  voiceIndex.value = e.detail.value
}
function onRateChange(e) {
  rate.value = e.detail.value
}

// 选择文件上传
function chooseFile() {
  uni.chooseMessageFile ? chooseMessageFile() : chooseImageOrVideo()
}

// 微信小程序等平台有专门的文件选择
function chooseMessageFile() {
  uni.chooseMessageFile({
    count: 1,
    type: 'all',
    success: (res) => {
      uploadFile(res.tempFiles[0].path)
    }
  })
}

// App/H5 平台选择
function chooseImageOrVideo() {
  uni.chooseImage({
    count: 1,
    success: (res) => {
      uploadFile(res.tempFilePaths[0])
    }
  })
}

function uploadFile(filePath) {
  isProcessing.value = true
  processStatus.value = '正在上传识别中...'
  
  uni.uploadFile({
    url: `${apiBaseUrl}/tts/api/upload`,
    filePath: filePath,
    name: 'file',
    success: (uploadFileRes) => {
      try {
        const data = JSON.parse(uploadFileRes.data)
        pollProgress(data.request_id, 'upload')
      } catch (e) {
        uni.showToast({ title: '解析响应失败', icon: 'none' })
        isProcessing.value = false
      }
    },
    fail: (err) => {
      console.error(err)
      uni.showToast({ title: '上传失败', icon: 'none' })
      isProcessing.value = false
    }
  })
}

// 提交文本进行合成
function startSynthesize() {
  if (!inputText.value.trim()) {
    uni.showToast({ title: '请输入文本', icon: 'none' })
    return
  }
  
  isProcessing.value = true
  processStatus.value = '正在请求合成...'
  
  uni.request({
    url: `${apiBaseUrl}/tts/api/synthesize`,
    method: 'POST',
    data: {
      text: inputText.value,
      voice: voices.value[voiceIndex.value],
      rate: rate.value
    },
    success: (res) => {
      if (res.data && res.data.request_id) {
        pollProgress(res.data.request_id, 'synthesize')
      } else {
        uni.showToast({ title: '合成请求失败', icon: 'none' })
        isProcessing.value = false
      }
    },
    fail: () => {
      uni.showToast({ title: '网络错误', icon: 'none' })
      isProcessing.value = false
    }
  })
}

// 轮询进度
function pollProgress(reqId, type) {
  const interval = setInterval(() => {
    uni.request({
      url: `${apiBaseUrl}/tts/api/progress/${reqId}`,
      success: (res) => {
        const data = res.data
        if (data.status === 'completed') {
          clearInterval(interval)
          isProcessing.value = false
          processStatus.value = ''
          
          if (type === 'upload' && data.result) {
            inputText.value = data.result
            uni.showToast({ title: '解析完成', icon: 'success' })
          } else if (type === 'synthesize') {
            uni.showToast({ title: '合成完成', icon: 'success' })
            fetchHistory()
          }
        } else if (data.status === 'failed') {
          clearInterval(interval)
          isProcessing.value = false
          processStatus.value = '处理失败: ' + (data.error || '未知错误')
          uni.showToast({ title: '处理失败', icon: 'none' })
        } else {
          processStatus.value = `处理中... ${data.progress}%`
        }
      },
      fail: () => {
        clearInterval(interval)
        isProcessing.value = false
        uni.showToast({ title: '查询进度异常', icon: 'none' })
      }
    })
  }, 2000)
}

function fetchHistory() {
  uni.request({
    url: `${apiBaseUrl}/tts/api/tasks`,
    success: (res) => {
      if (res.data) {
        tasks.value = res.data
      }
    }
  })
}

function deleteTask(task) {
  uni.showModal({
    title: '确认删除',
    content: `是否删除 "${task.filename}"？`,
    success: function (res) {
      if (res.confirm) {
        uni.request({
          url: `${apiBaseUrl}/tts/api/tasks/${task.id}`,
          method: 'DELETE',
          success: () => {
            tasks.value = tasks.value.filter(t => t.id !== task.id)
            if (currentTaskId.value === task.id) {
              bgAudio.stop()
              audioUrl.value = ''
              nowPlayingTitle.value = ''
            }
          }
        })
      }
    }
  })
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 20rpx;
  box-sizing: border-box;
}

.header {
  padding: 30rpx 0;
  text-align: center;
}
.title {
  font-size: 40rpx;
  font-weight: bold;
  color: #2c3e50;
}

.card {
  background-color: #ffffff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
}

.section-title {
  font-size: 32rpx;
  font-weight: bold;
  margin-bottom: 20rpx;
  color: #34495e;
  border-left: 8rpx solid #3b82f6;
  padding-left: 16rpx;
}

.textarea {
  width: 100%;
  height: 200rpx;
  background-color: #f8fafc;
  border: 2rpx solid #e2e8f0;
  border-radius: 12rpx;
  padding: 16rpx;
  font-size: 28rpx;
  box-sizing: border-box;
  margin-bottom: 20rpx;
}

.btn {
  border-radius: 12rpx;
  font-size: 30rpx;
  margin-top: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
.primary-btn {
  background-color: #3b82f6;
  color: white;
}
.upload-btn {
  background-color: #e2e8f0;
  color: #475569;
  margin-bottom: 20rpx;
  margin-top: 0;
}

.config-row {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
  font-size: 28rpx;
  color: #475569;
}
.picker-view {
  margin-left: 20rpx;
  padding: 10rpx 20rpx;
  background: #f1f5f9;
  border-radius: 8rpx;
  color: #3b82f6;
}

.slider-flex {
  flex: 1;
  margin: 0 20rpx;
}

.now-playing {
  font-size: 30rpx;
  font-weight: 600;
  color: #1e293b;
  display: block;
  margin-bottom: 20rpx;
  text-align: center;
}

.progress-row {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}
.time {
  font-size: 24rpx;
  color: #64748b;
  width: 80rpx;
  text-align: center;
}

.controls {
  display: flex;
  justify-content: space-around;
  align-items: center;
}
.ctrl-btn {
  flex: 1;
  margin: 0 10rpx;
  font-size: 28rpx;
}

.task-list {
  display: flex;
  flex-direction: column;
}
.task-item {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 1rpx solid #f1f5f9;
}
.task-item.playing {
  background-color: #eff6ff;
  border-radius: 8rpx;
  padding: 20rpx 10rpx;
}
.task-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.task-name {
  font-size: 28rpx;
  color: #1e293b;
  margin-bottom: 8rpx;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.task-meta {
  font-size: 24rpx;
  color: #94a3b8;
}
.del-btn {
  margin-left: 20rpx;
  background-color: #fee2e2;
  color: #ef4444;
  font-size: 24rpx;
  padding: 0 20rpx;
  height: 60rpx;
  line-height: 60rpx;
}
</style>
