<template>
  <div class="app-container">
    <!-- Background glow gradients -->
    <div class="glow glow-1"></div>
    <div class="glow glow-2"></div>

    <!-- Header Section -->
    <header class="app-header">
      <div class="logo-area">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
          </svg>
        </div>
        <div class="logo-text">
          <h1>TTS 本地听书系统</h1>
          <p>Local Audiobook Station (MVP)</p>
        </div>
      </div>
      <div class="system-status">
        <span class="status-indicator animate-pulse"></span>
        <span class="status-text">系统就绪</span>
      </div>
    </header>

    <!-- Main Grid Layout -->
    <main class="app-main-grid">
      <!-- Left Column: Input, Cleaning & TTS Configurations -->
      <section class="grid-col input-panel">
        <div class="card glass-card">
          <!-- Mode Tabs -->
          <div class="tabs-container">
            <button 
              class="tab-btn" 
              :class="{ active: activeTab === 'text' }"
              @click="activeTab = 'text'"
            >
              文本输入
            </button>
            <button 
              class="tab-btn" 
              :class="{ active: activeTab === 'pdf' }"
              @click="activeTab = 'pdf'"
            >
              PDF 听书
            </button>
          </div>

          <!-- Tab Contents -->
          <div class="tab-content">
            <!-- Text Mode -->
            <div v-if="activeTab === 'text'" class="text-input-mode">
              <div class="input-header">
                <label>输入待朗读的文本</label>
                <span class="char-count">{{ textInput.length }} 字</span>
              </div>
              <textarea 
                v-model="textInput"
                placeholder="在此输入或粘贴你想要转换的文本段落..."
                rows="10"
                class="styled-textarea"
              ></textarea>
            </div>

            <!-- PDF Mode -->
            <div v-if="activeTab === 'pdf'" class="pdf-upload-mode">
              <div 
                class="upload-dropzone"
                :class="{ dragging: isDragging, 'has-file': uploadedFile }"
                @dragover.prevent="isDragging = true"
                @dragleave="isDragging = false"
                @drop.prevent="handleFileDrop"
                @click="triggerFileSelect"
              >
                <input 
                  id="pdfFileInput"
                  type="file" 
                  ref="fileInput" 
                  @change="handleFileSelect" 
                  accept=".pdf,application/pdf"
                  style="display: none;" 
                />
                
                <div class="dropzone-inner" v-if="!uploadedFile && !uploading">
                  <div class="upload-icon">
                    <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v12m0 0l-3-3m3 3l3-3m-9-6a9 9 0 1118 0c0 .347-.02.688-.06 1.025M12 3c-4.97 0-9 4.03-9 9a8.96 8.96 0 002.32 6" />
                    </svg>
                  </div>
                  <p class="main-msg">拖拽 PDF 文件到此处，或<span>点击上传</span></p>
                  <p class="sub-msg">仅支持 PDF 格式文件</p>
                </div>

                <div class="dropzone-inner" v-else-if="uploading">
                  <div class="spinner"></div>
                  <p class="main-msg">正在提取与清洗 PDF 文本...</p>
                  <p class="sub-msg">提取段落与段落去重中</p>
                </div>

                <div class="dropzone-inner" v-else>
                  <div class="file-success-icon">
                    <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="#10b981" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p class="main-msg file-name">{{ uploadedFile.name }}</p>
                  <p class="sub-msg text-success">解析成功 ({{ cleanedText.length }} 字)</p>
                  <button class="re-upload-btn" @click.stop="resetUpload">重新上传</button>
                </div>
              </div>

              <!-- Cleaned Text Preview -->
              <div v-if="cleanedText" class="cleaned-preview-area">
                <div class="preview-header">
                  <label>排版清洗后的文本预览 (支持编辑微调)</label>
                  <button class="btn-clear-preview" @click="cleanedText = ''">清除</button>
                </div>
                <textarea 
                  v-model="cleanedText"
                  class="styled-textarea preview-textarea"
                  rows="8"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- TTS Configurations -->
          <div class="settings-divider">TTS 朗读配置</div>
          
          <div class="settings-grid">
            <div class="control-group">
              <label>发音人 (Voice)</label>
              <select v-model="voice" class="styled-select">
                <option value="zh-CN-XiaoxiaoNeural">晓晓 (女声 - 柔和自然)</option>
                <option value="zh-CN-YunxiNeural">云希 (男声 - 故事朗读)</option>
                <option value="zh-CN-YunjianNeural">云健 (男声 - 文艺抒情)</option>
                <option value="zh-CN-YunyangNeural">云扬 (男声 - 专业新闻)</option>
                <option value="zh-CN-XiaoyiNeural">晓伊 (女声 - 活泼俏皮)</option>
                <option value="zh-HK-HiuMaanNeural">晓曼 (粤语女声)</option>
                <option value="zh-TW-HsiaoChenNeural">晓臻 (闽南普通话女声)</option>
              </select>
            </div>

            <div class="control-group">
              <label>朗读语速 (Speed)</label>
              <div class="speed-presets">
                <button 
                  v-for="preset in speedPresets" 
                  :key="preset.value"
                  class="preset-btn"
                  :class="{ active: speedRate === preset.rate }"
                  @click="speedRate = preset.rate"
                >
                  {{ preset.label }}
                </button>
              </div>
            </div>

            <div class="control-group">
              <label>句尾停顿时间 (Pause)</label>
              <div class="input-range-container">
                <input 
                  type="range" 
                  min="300" 
                  max="2000" 
                  step="100" 
                  v-model.number="sentencePause" 
                  class="styled-range"
                />
                <span class="range-val">{{ sentencePause }} ms</span>
              </div>
            </div>

            <div class="control-group">
              <label>段落/分点停顿时间</label>
              <div class="input-range-container">
                <input 
                  type="range" 
                  min="800" 
                  max="4000" 
                  step="100" 
                  v-model.number="paragraphPause" 
                  class="styled-range"
                />
                <span class="range-val">{{ paragraphPause }} ms</span>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="action-bar">
            <button 
              v-if="activeTab === 'text'" 
              class="secondary-btn glow-on-hover"
              @click="cleanTextInput"
              :disabled="!textInput.trim()"
            >
              一键排版清洗
            </button>
            
            <button 
              class="primary-btn glow-on-hover"
              :class="{ pulse: synthesizing }"
              @click="startSynthesis"
              :disabled="synthesizing || getActiveText().length === 0"
            >
              <span v-if="synthesizing" class="btn-loader"></span>
              {{ synthesizing ? '正在异步生成 MP3...' : '开始生成语音' }}
            </button>
          </div>
        </div>
      </section>

      <!-- Right Column: Player & Synthesis History -->
      <section class="grid-col player-panel">
        <!-- Premium Custom Audio Player -->
        <div class="card glass-card player-card">
          <div class="player-header">
            <h3>正在播放</h3>
            <span class="badge" v-if="audioUrl">Local MP3</span>
          </div>

          <div class="track-info" v-if="nowPlayingTitle">
            <div class="track-title">{{ nowPlayingTitle }}</div>
            <div class="track-meta">
              <span>发音: {{ formatVoice(nowPlayingVoice) }}</span>
              <span>语速: {{ formatSpeed(nowPlayingRate) }}</span>
            </div>
          </div>
          <div class="track-info-empty" v-else>
            暂无播放中的音频，请在左侧生成或在下方选择历史任务
          </div>

          <component 
            is="audio"
            ref="audioPlayer" 
            :src="audioUrl"
            @timeupdate="updateAudioProgress"
            @loadedmetadata="onAudioLoaded"
            @ended="onAudioEnded"
          ></component>

          <!-- Player Controls -->
          <div class="player-controls-wrapper" :class="{ disabled: !audioUrl }">
            <!-- Progress Slider -->
            <div class="progress-bar-container">
              <span class="time-label">{{ formatTime(currentTime) }}</span>
              <input 
                type="range" 
                min="0" 
                :max="duration || 100" 
                step="0.1"
                :value="currentTime" 
                @input="seekAudio"
                class="styled-range progress-slider"
                :disabled="!audioUrl"
              />
              <span class="time-label">{{ formatTime(duration) }}</span>
            </div>

            <!-- Buttons bar -->
            <div class="controls-bar">
              <!-- Playback Rate Selector -->
              <div class="rate-select-btn" @click="togglePlayRate">
                {{ playbackRate }}x
              </div>

              <!-- Main Play/Pause -->
              <button class="play-btn" @click="togglePlay" :disabled="!audioUrl">
                <svg v-if="!isPlaying" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                  <path d="M8 5v14l11-7z" />
                </svg>
                <svg v-else viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                </svg>
              </button>

              <!-- Mute / Volume Slider -->
              <div class="volume-container">
                <button class="volume-btn" @click="toggleMute">
                  <svg v-if="isMuted || volume === 0" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 9.75L19.5 12m0 0l2.25 2.25M19.5 12l2.25-2.25M19.5 12l-2.25 2.25m-10.5-6L4.5 9H2.25A.75.75 0 001.5 9.75v4.5c0 .414.336.75.75.75h2.25l2.75 2.25c.49.4 1.25.05 1.25-.6V5.6c0-.65-.76-1-1.25-.6z" />
                  </svg>
                  <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19.114 5.636a9 9 0 010 12.728M16.463 8.288a5.25 5.25 0 010 7.424M6.75 8.25l4.72-4.72a.75.75 0 011.28.53v15.88a.75.75 0 01-1.28.53l-4.72-4.72H4.51c-.88 0-1.704-.507-1.938-1.354A9.01 9.01 0 012.25 12c0-.83.112-1.633.322-2.396C2.806 8.756 3.63 8.25 4.51 8.25H6.75z" />
                  </svg>
                </button>
                <input 
                  type="range" 
                  min="0" 
                  max="1" 
                  step="0.05" 
                  v-model="volume"
                  @input="adjustVolume"
                  class="styled-range volume-slider"
                />
              </div>
            </div>
          </div>

          <!-- Download Action -->
          <div class="download-container" v-if="audioUrl">
            <a :href="audioUrl" download class="btn-download glow-on-hover">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              下载 MP3 音频文件
            </a>
          </div>
        </div>

        <!-- History Log Tasks -->
        <div class="card glass-card history-card">
          <div class="history-header">
            <h3>生成历史</h3>
            <button class="refresh-btn" @click="fetchHistory">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
            </button>
          </div>

          <div class="history-list" v-if="tasks.length > 0">
            <div 
              v-for="task in tasks" 
              :key="task.id" 
              class="history-item"
              :class="{ active: audioUrl === task.audio_url }"
              @click="loadTrack(task)"
            >
              <div class="item-play-icon">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              <div class="item-details">
                <div class="item-title">{{ task.filename }}</div>
                <div class="item-preview">{{ task.text_snippet }}</div>
                <div class="item-meta">
                  <span>{{ formatVoice(task.voice) }}</span>
                  <span>语速 {{ formatSpeed(task.rate) }}</span>
                  <span>{{ formatDate(task.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="history-empty" v-else>
            暂无生成记录，试着在左侧合成一段文字吧！
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script>
export default {
  data() {
    return {
      activeTab: 'text',
      textInput: '',
      cleanedText: '',
      
      // Upload variables
      isDragging: false,
      uploadedFile: null,
      uploading: false,
      
      // Synthesize parameters
      voice: 'zh-CN-XiaoxiaoNeural',
      speedRate: '+0%',
      sentencePause: 800,
      paragraphPause: 1500,
      synthesizing: false,
      
      // Speed rate presets mapping
      speedPresets: [
        { label: '0.8x 慢速', rate: '-20%' },
        { label: '1.0x 正常', rate: '+0%' },
        { label: '1.2x 推荐', rate: '+20%' },
        { label: '1.5x 快速', rate: '+50%' },
        { label: '2.0x 极速', rate: '+100%' }
      ],
      
      // Audio player variables
      audioUrl: '',
      nowPlayingTitle: '',
      nowPlayingVoice: '',
      nowPlayingRate: '',
      isPlaying: false,
      currentTime: 0,
      duration: 0,
      playbackRate: 1.0,
      volume: 0.8,
      isMuted: false,
      previousVolume: 0.8,
      
      // Tasks history
      tasks: []
    };
  },
  mounted() {
    this.fetchHistory();
  },
  methods: {
    // Utility helpers
    getActiveText() {
      if (this.activeTab === 'text') {
        return this.textInput;
      } else {
        return this.cleanedText;
      }
    },
    formatVoice(voiceId) {
      const mapping = {
        'zh-CN-XiaoxiaoNeural': '晓晓 (女声)',
        'zh-CN-YunxiNeural': '云希 (男声)',
        'zh-CN-YunjianNeural': '云健 (男声)',
        'zh-CN-YunyangNeural': '云扬 (男声)',
        'zh-CN-XiaoyiNeural': '晓伊 (女声)',
        'zh-HK-HiuMaanNeural': '晓曼 (粤语)',
        'zh-TW-HsiaoChenNeural': '晓臻 (闽南)'
      };
      return mapping[voiceId] || voiceId;
    },
    formatSpeed(rate) {
      if (!rate) return '1.0x';
      if (rate === '+0%') return '1.0x';
      if (rate === '-20%') return '0.8x';
      if (rate === '+20%') return '1.2x';
      if (rate === '+50%') return '1.5x';
      if (rate === '+100%') return '2.0x';
      return rate;
    },
    formatTime(seconds) {
      if (isNaN(seconds) || seconds === null) return '00:00';
      const m = Math.floor(seconds / 60).toString().padStart(2, '0');
      const s = Math.floor(seconds % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
    },
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      const m = (date.getMonth() + 1).toString().padStart(2, '0');
      const d = date.getDate().toString().padStart(2, '0');
      const h = date.getHours().toString().padStart(2, '0');
      const min = date.getMinutes().toString().padStart(2, '0');
      return `${m}-${d} ${h}:${min}`;
    },
    
    // Text Cleaning
    cleanTextInput() {
      if (!this.textInput.trim()) return;
      
      // Simple frontend mock clean if backend not called:
      // Remove double spacing and normalize paragraph ends
      let cleaned = this.textInput
        .replace(/\r\n/g, '\n')
        .replace(/[ \t]+/g, ' ')
        // Remove line breaks inside sentences for Chinese characters
        .replace(/([\u4e00-\u9fa5]+)\n([\u4e00-\u9fa5]+)/g, '$1$2')
        .trim();
        
      this.textInput = cleaned;
      uni.showToast({
        title: '文本已清洗',
        icon: 'success'
      });
    },

    // File Upload handling
    triggerFileSelect() {
      if (this.uploading) return;
      const input = this.$refs.fileInput?.$el || this.$refs.fileInput;
      if (input && typeof input.click === 'function') {
        input.click();
      } else {
        const fallback = document.getElementById('pdfFileInput');
        if (fallback) fallback.click();
      }
    },
    handleFileSelect(e) {
      const files = e.target.files;
      if (files.length > 0) {
        this.uploadFile(files[0]);
      }
    },
    handleFileDrop(e) {
      this.isDragging = false;
      let file = null;
      if (e.dataTransfer.items) {
        for (let i = 0; i < e.dataTransfer.items.length; i++) {
          if (e.dataTransfer.items[i].kind === 'file') {
            file = e.dataTransfer.items[i].getAsFile();
            break;
          }
        }
      } else if (e.dataTransfer.files.length > 0) {
        file = e.dataTransfer.files[0];
      }

      if (file) {
        const isPdf = file.type === 'application/pdf' || (file.name && file.name.toLowerCase().endsWith('.pdf'));
        if (isPdf) {
          this.uploadFile(file);
        } else {
          uni.showToast({
            title: '仅支持 PDF 文件',
            icon: 'error'
          });
        }
      }
    },
    resetUpload() {
      this.uploadedFile = null;
      this.cleanedText = '';
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = '';
      }
    },
    async uploadFile(file) {
      this.uploadedFile = file;
      this.uploading = true;
      
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const response = await fetch('/tts/api/upload', {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          throw new Error('PDF 文本解析失败，请检查文件格式。');
        }
        
        const data = await response.json();
        this.cleanedText = data.cleaned_text;
      } catch (err) {
        console.error(err);
        uni.showModal({
          title: '上传失败',
          content: err.message || '网络连接失败，请重试。',
          showCancel: false
        });
        this.resetUpload();
      } finally {
        this.uploading = false;
      }
    },

    // Speech Synthesis
    async startSynthesis() {
      const text = this.getActiveText();
      if (!text.trim()) {
        uni.showToast({
          title: '输入文本不能为空',
          icon: 'none'
        });
        return;
      }

      this.synthesizing = true;
      const filename = this.activeTab === 'pdf' && this.uploadedFile 
        ? this.uploadedFile.name 
        : `文段朗读 ${new Date().toLocaleTimeString()}`;
        
      try {
        const response = await fetch('/tts/api/synthesize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            text: text,
            filename: filename,
            voice: this.voice,
            rate: this.speedRate,
            sentence_pause_ms: this.sentencePause,
            paragraph_pause_ms: this.paragraphPause
          })
        });

        if (!response.ok) {
          throw new Error('合成任务失败，语音服务暂时不可用。');
        }

        const data = await response.json();
        
        // Auto-play the synthesized track
        this.loadTrack({
          filename: data.filename,
          audio_url: data.audio_url,
          voice: this.voice,
          rate: this.speedRate
        });
        
        uni.showToast({
          title: '合成成功！',
          icon: 'success'
        });
        
        // Refresh synthesis history list
        this.fetchHistory();
      } catch (err) {
        console.error(err);
        uni.showModal({
          title: '语音合成失败',
          content: err.message || '服务器连接失败，请稍后重试。',
          showCancel: false
        });
      } finally {
        this.synthesizing = false;
      }
    },

    // History Log loading
    async fetchHistory() {
      try {
        const response = await fetch('/tts/api/tasks');
        if (response.ok) {
          this.tasks = await response.json();
        }
      } catch (err) {
        console.warn('获取合成历史失败', err);
      }
    },
    loadTrack(task) {
      this.audioUrl = task.audio_url;
      this.nowPlayingTitle = task.filename;
      this.nowPlayingVoice = task.voice;
      this.nowPlayingRate = task.rate;
      
      // Load and autoplay
      this.$nextTick(() => {
        const player = this.$refs.audioPlayer;
        if (player) {
          player.load();
          player.play();
          this.isPlaying = true;
        }
      });
    },

    // Hidden Audio Player controls
    togglePlay() {
      const player = this.$refs.audioPlayer;
      if (!player || !this.audioUrl) return;
      
      if (this.isPlaying) {
        player.pause();
        this.isPlaying = false;
      } else {
        player.play();
        this.isPlaying = true;
      }
    },
    seekAudio(e) {
      const player = this.$refs.audioPlayer;
      if (!player) return;
      const targetTime = parseFloat(e.target.value);
      player.currentTime = targetTime;
      this.currentTime = targetTime;
    },
    updateAudioProgress() {
      const player = this.$refs.audioPlayer;
      if (!player) return;
      this.currentTime = player.currentTime;
    },
    onAudioLoaded() {
      const player = this.$refs.audioPlayer;
      if (!player) return;
      this.duration = player.duration;
      // Sync initial playback speed and volume
      player.playbackRate = this.playbackRate;
      player.volume = this.isMuted ? 0 : this.volume;
    },
    onAudioEnded() {
      this.isPlaying = false;
      this.currentTime = 0;
    },
    togglePlayRate() {
      const rates = [1.0, 1.2, 1.5, 1.8, 2.0, 0.8];
      const currentIndex = rates.indexOf(this.playbackRate);
      const nextIndex = (currentIndex + 1) % rates.length;
      this.playbackRate = rates[nextIndex];
      
      const player = this.$refs.audioPlayer;
      if (player) {
        player.playbackRate = this.playbackRate;
      }
    },
    toggleMute() {
      this.isMuted = !this.isMuted;
      const player = this.$refs.audioPlayer;
      if (player) {
        player.volume = this.isMuted ? 0 : this.volume;
      }
    },
    adjustVolume() {
      this.isMuted = false;
      const player = this.$refs.audioPlayer;
      if (player) {
        player.volume = this.volume;
      }
    }
  }
};
</script>

<style scoped>
/* Main Styling Rules */
.app-container {
  min-height: 100vh;
  position: relative;
  background-color: #0b0f19;
  padding: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;
}

/* Background glows */
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  z-index: 0;
  opacity: 0.15;
  pointer-events: none;
}
.glow-1 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #6366f1, #312e81);
  top: -100px;
  left: -100px;
}
.glow-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #3b82f6, #1d4ed8);
  bottom: -150px;
  right: -100px;
}

/* Header */
.app-header {
  width: 100%;
  max-width: 1200px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  z-index: 10;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 20px;
}
.logo-area {
  display: flex;
  align-items: center;
  gap: 15px;
}
.logo-icon {
  background: linear-gradient(135deg, #4f46e5, #3b82f6);
  color: white;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 15px rgba(79, 70, 229, 0.35);
}
.logo-text h1 {
  font-size: 22px;
  font-weight: 700;
  margin: 0;
  color: #f8fafc;
  letter-spacing: 0.5px;
}
.logo-text p {
  font-size: 11px;
  color: #64748b;
  margin: 2px 0 0 0;
}
.system-status {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.2);
  padding: 6px 14px;
  border-radius: 20px;
}
.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #10b981;
}
.status-text {
  font-size: 12px;
  color: #10b981;
  font-weight: 500;
}
.animate-pulse {
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.1); }
}

/* Main Layout Grid */
.app-main-grid {
  width: 100%;
  max-width: 1200px;
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 30px;
  z-index: 10;
}
.grid-col {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

/* Glassmorphism Cards */
.card {
  border-radius: 20px;
  padding: 24px;
  position: relative;
  overflow: hidden;
}
.glass-card {
  background: rgba(17, 25, 40, 0.65);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}

/* Tabs */
.tabs-container {
  display: flex;
  background: rgba(0, 0, 0, 0.25);
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 20px;
}
.tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  color: #94a3b8;
  padding: 10px 0;
  font-size: 14px;
  font-weight: 500;
  border-radius: 9px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.tab-btn.active {
  background: rgba(255, 255, 255, 0.08);
  color: #f8fafc;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* Form Styles */
.input-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  color: #94a3b8;
}
.styled-textarea {
  width: 100%;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 14px;
  color: #e2e8f0;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  transition: border-color 0.3s;
}
.styled-textarea:focus {
  border-color: rgba(99, 102, 241, 0.5);
}

/* Drag Zone */
.upload-dropzone {
  border: 2px dashed rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.01);
}
.upload-dropzone.dragging {
  border-color: #6366f1;
  background: rgba(99, 102, 241, 0.08);
}
.upload-dropzone.has-file {
  border-style: solid;
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.03);
}
.dropzone-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.upload-icon, .file-success-icon {
  margin-bottom: 5px;
}
.upload-icon svg {
  stroke: #64748b;
  transition: stroke 0.3s;
}
.upload-dropzone:hover .upload-icon svg {
  stroke: #6366f1;
}
.main-msg {
  font-size: 15px;
  color: #e2e8f0;
  font-weight: 500;
  margin: 0;
}
.main-msg span {
  color: #6366f1;
  text-decoration: underline;
  margin-left: 4px;
}
.file-name {
  max-width: 90%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sub-msg {
  font-size: 12px;
  color: #64748b;
  margin: 0;
}
.text-success {
  color: #10b981 !important;
  font-weight: 500;
}
.re-upload-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  padding: 6px 16px;
  font-size: 12px;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 10px;
  transition: all 0.2s;
}
.re-upload-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #f8fafc;
}

/* Spinner Loader */
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(99, 102, 241, 0.15);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s infinite linear;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Preview text */
.cleaned-preview-area {
  margin-top: 20px;
}
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.preview-header label {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
}
.btn-clear-preview {
  background: transparent;
  border: none;
  color: #ef4444;
  font-size: 12px;
  cursor: pointer;
}
.preview-textarea {
  border-color: rgba(16, 185, 129, 0.15);
  background: rgba(16, 185, 129, 0.01);
}

/* Configurations */
.settings-divider {
  margin: 25px 0 15px 0;
  font-size: 12px;
  color: #6366f1;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.settings-divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: rgba(99, 102, 241, 0.2);
}
.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 25px;
}
.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.control-group label {
  font-size: 13px;
  color: #94a3b8;
}
.styled-select {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 10px 12px;
  border-radius: 10px;
  color: #f1f5f9;
  outline: none;
  font-size: 13px;
  cursor: pointer;
}
.speed-presets {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}
.preset-btn {
  flex: 1;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.05);
  color: #94a3b8;
  padding: 8px 4px;
  font-size: 11px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}
.preset-btn:hover {
  background: rgba(255, 255, 255, 0.05);
}
.preset-btn.active {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.5);
  color: #f8fafc;
}
.input-range-container {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 8px 12px;
  border-radius: 10px;
}
.styled-range {
  flex: 1;
  accent-color: #6366f1;
  height: 4px;
  cursor: pointer;
}
.range-val {
  font-size: 12px;
  font-weight: 600;
  color: #e2e8f0;
  min-width: 50px;
  text-align: right;
}

/* Action Bar */
.action-bar {
  display: flex;
  gap: 15px;
}
.action-bar button {
  flex: 1;
}

/* Buttons */
.primary-btn {
  background: linear-gradient(135deg, #4f46e5, #3b82f6);
  color: white;
  border: none;
  padding: 12px 0;
  font-size: 15px;
  font-weight: 600;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
}
.primary-btn:hover:not(:disabled) {
  opacity: 0.95;
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.45);
}
.primary-btn:disabled {
  background: #334155;
  color: #64748b;
  cursor: not-allowed;
  box-shadow: none;
}
.secondary-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
  padding: 12px 0;
  font-size: 15px;
  font-weight: 500;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.secondary-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}
.secondary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-loader {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s infinite linear;
}

/* Audio Player */
.player-card {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
  border-color: rgba(99, 102, 241, 0.15);
}
.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.player-header h3 {
  font-size: 16px;
  font-weight: 700;
  color: #f8fafc;
  margin: 0;
}
.badge {
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.25);
  color: #818cf8;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
}
.track-info {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}
.track-title {
  font-size: 15px;
  font-weight: 600;
  color: #f1f5f9;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.track-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #64748b;
}
.track-info-empty {
  text-align: center;
  padding: 30px 10px;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 12px;
  color: #64748b;
  font-size: 13px;
  margin-bottom: 20px;
  line-height: 1.5;
}
.player-controls-wrapper {
  transition: opacity 0.3s;
}
.player-controls-wrapper.disabled {
  opacity: 0.4;
  pointer-events: none;
}
.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}
.time-label {
  font-size: 11px;
  color: #64748b;
  font-family: monospace;
  min-width: 35px;
}
.progress-slider {
  height: 6px !important;
  accent-color: #6366f1;
}
.controls-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 10px;
}
.rate-select-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 6px 12px;
  border-radius: 20px;
  color: #cbd5e1;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  min-width: 50px;
  text-align: center;
  transition: all 0.2s;
}
.rate-select-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: white;
}
.play-btn {
  background: white;
  color: #0b0f19;
  border: none;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(255, 255, 255, 0.15);
  transition: all 0.2s ease;
}
.play-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(255, 255, 255, 0.25);
}
.play-btn:active {
  transform: scale(0.98);
}
.volume-container {
  display: flex;
  align-items: center;
  gap: 8px;
}
.volume-btn {
  background: transparent;
  border: none;
  color: #cbd5e1;
  cursor: pointer;
  padding: 4px;
}
.volume-slider {
  width: 70px;
  height: 4px !important;
}

.download-container {
  margin-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  padding-top: 15px;
}
.btn-download {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  background: rgba(99, 102, 241, 0.08);
  border: 1px solid rgba(99, 102, 241, 0.2);
  color: #818cf8;
  padding: 10px 0;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s;
}
.btn-download:hover {
  background: rgba(99, 102, 241, 0.18);
  border-color: rgba(99, 102, 241, 0.4);
  color: white;
}

/* History Card */
.history-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 300px;
  max-height: 400px;
}
.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.history-header h3 {
  font-size: 15px;
  font-weight: 700;
  color: #f8fafc;
  margin: 0;
}
.refresh-btn {
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.2s;
}
.refresh-btn:hover {
  color: #cbd5e1;
  background: rgba(255, 255, 255, 0.05);
}
.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  flex: 1;
  padding-right: 2px;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  padding: 10px 14px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.history-item:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.08);
  transform: translateX(4px);
}
.history-item.active {
  background: rgba(99, 102, 241, 0.08);
  border-color: rgba(99, 102, 241, 0.25);
}
.item-play-icon {
  background: rgba(255, 255, 255, 0.05);
  color: #cbd5e1;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: all 0.2s;
}
.history-item:hover .item-play-icon {
  background: #6366f1;
  color: white;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.35);
}
.item-details {
  flex: 1;
  min-width: 0;
}
.item-title {
  font-size: 13px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-preview {
  font-size: 11px;
  color: #64748b;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-meta {
  display: flex;
  gap: 12px;
  font-size: 10px;
  color: #475569;
}
.history-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  flex: 1;
  color: #475569;
  font-size: 13px;
  text-align: center;
  padding: 20px;
}

/* Animations */
.glow-on-hover {
  transition: all 0.3s;
}
.glow-on-hover:hover {
  box-shadow: 0 0 15px rgba(99, 102, 241, 0.25);
}

/* Responsive constraints */
@media (max-width: 900px) {
  .app-main-grid {
    grid-template-columns: 1fr;
  }
  .app-container {
    padding: 15px;
  }
  .settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
