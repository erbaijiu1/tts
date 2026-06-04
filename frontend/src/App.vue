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
          <h1>TTS 听书系统</h1>
          <p>Audiobook Station</p>
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
              <div class="llm-toggle-container">
                <label class="toggle-switch">
                  <input type="checkbox" v-model="isLLMMode" />
                  <span class="slider round"></span>
                </label>
                <span class="toggle-label" @click="isLLMMode = !isLLMMode" style="cursor:pointer;">开启大模型深度清洗 (适用于带水印/乱码的PDF或图片)</span>
              </div>
              
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
                  accept=".pdf,application/pdf,image/png,image/jpeg,image/webp,image/*"
                  style="display: none;"
                />
                
                <div class="dropzone-inner" v-if="!uploadedFile && !uploading">
                  <div class="upload-icon">
                    <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v12m0 0l-3-3m3 3l3-3m-9-6a9 9 0 1118 0c0 .347-.02.688-.06 1.025M12 3c-4.97 0-9 4.03-9 9a8.96 8.96 0 002.32 6" />
                    </svg>
                  </div>
                  <p class="main-msg">拖拽 PDF 或图片文件到此处，或<span>点击上传</span></p>
                  <p class="sub-msg">支持 PDF 和常见图片格式文件</p>
                </div>

                <div class="dropzone-inner" v-else-if="uploading">
                  <div class="upload-progress-ring">
                    <div class="spinner" :style="(isLLMMode || (uploadedFile && uploadedFile.type.startsWith('image/'))) ? 'width: 48px; height: 48px; border-width: 4px;' : ''"></div>
                    <div v-if="(isLLMMode || (uploadedFile && uploadedFile.type.startsWith('image/'))) && uploadProgress > 0" class="ring-text">{{ uploadProgress }}%</div>
                  </div>
                  <p class="main-msg">{{ (isLLMMode || (uploadedFile && uploadedFile.type.startsWith('image/'))) ? `正在进行深度清洗与提取...` : '正在提取文件文本...' }}</p>
                  <p class="sub-msg">{{ (isLLMMode || (uploadedFile && uploadedFile.type.startsWith('image/'))) ? '此过程可能需要几分钟，请耐心等待' : '提取段落与段落去重中' }}</p>
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
              <div v-if="uploadedFile" class="cleaned-preview-area">
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
              class="primary-btn glow-on-hover progress-button"
              :class="{ pulse: synthesizing }"
              @click="startSynthesis"
              :disabled="synthesizing || getActiveText().length === 0"
            >
              <div v-if="synthesizing" class="btn-progress-bar" :style="{ width: synthesisProgress + '%' }"></div>
              <span class="btn-content">
                <span v-if="synthesizing" class="btn-loader"></span>
                {{ synthesizing ? (synthesisProgress > 0 ? `正在合成中... ${synthesisProgress}%` : '建立连接与分块中...') : '开始生成语音' }}
              </span>
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
              <div class="rate-select-wrapper" @click="showRateMenu = !showRateMenu">
                <div class="rate-select-btn">
                  {{ Number.isInteger(playbackRate) ? playbackRate + '.0' : playbackRate }}x
                </div>
                <div class="rate-menu" v-if="showRateMenu">
                  <div class="rate-item" v-for="rate in [0.75, 1.0, 1.25, 1.5, 2.0]" :key="rate" 
                       @click.stop="setPlayRate(rate); showRateMenu = false" :class="{active: playbackRate === rate}">
                    {{ Number.isInteger(rate) ? rate + '.0' : rate }}x
                  </div>
                </div>
              </div>

              <!-- Rewind 10s -->
              <button class="skip-btn" @click="skipAudio(-10)" :disabled="!audioUrl" title="后退10秒">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/>
                </svg>
              </button>

              <!-- Main Play/Pause -->
              <button class="play-btn" @click="togglePlay" :disabled="!audioUrl">
                <svg v-if="!isPlaying" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                  <path d="M8 5v14l11-7z" />
                </svg>
                <svg v-else viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                  <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                </svg>
              </button>

              <!-- Fast Forward 10s -->
              <button class="skip-btn" @click="skipAudio(10)" :disabled="!audioUrl" title="快进10秒">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                  <path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z"/>
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
            <a href="#" @click.prevent="downloadAudio" class="btn-download glow-on-hover">
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
              <!-- Delete button -->
              <button
                class="delete-task-btn"
                title="删除此记录"
                @click.stop="confirmDeleteTask(task)"
              >
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
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
      isLLMMode: false,
      uploadedFile: null,
      uploading: false,
      uploadProgress: 0,

      // Synthesize parameters
      voice: 'zh-CN-XiaoxiaoNeural',
      speedRate: '+0%',
      sentencePause: 800,
      paragraphPause: 1500,
      synthesizing: false,
      synthesisProgress: 0,
      progressInterval: null,

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
      showRateMenu: false,
      volume: 0.8,
      isMuted: false,
      previousVolume: 0.8,
      
      // Tasks history
      tasks: []
    };
  },
  mounted() {
    this.fetchHistory();
    window.addEventListener('beforeunload', this.saveProgress);
  },
  beforeUnmount() {
    window.removeEventListener('beforeunload', this.saveProgress);
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
      alert('文本已清洗');
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
        const isImage = file.type.startsWith('image/') || (file.name && /\.(png|jpe?g|webp)$/i.test(file.name));
        if (isPdf || isImage) {
          this.uploadFile(file);
        } else {
          alert('仅支持 PDF 和图片文件');
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
      this.uploadProgress = 0;

      const reqId = Math.random().toString(36).substring(2, 10);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('mode', this.isLLMMode ? 'llm' : 'standard');
      formData.append('req_id', reqId);

      const isImage = file.type.startsWith('image/') || (file.name && /\.(png|jpe?g|webp)$/i.test(file.name));
      const requiresLLM = this.isLLMMode || isImage;

      const progressInterval = setInterval(async () => {
        if (!requiresLLM) return;
        try {
          const res = await fetch(`/tts/api/progress/${reqId}`);
          if (res.ok) {
            const data = await res.json();
            this.uploadProgress = data.progress;
          }
        } catch (e) {}
      }, 1000);

      try {
        const response = await fetch('/tts/api/upload', {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          throw new Error('文件解析失败，请检查文件格式或重试。');
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
        clearInterval(progressInterval);
        this.uploadProgress = 0;
      }
    },

    // Speech Synthesis
    async startSynthesis() {
      const text = this.getActiveText();
      if (!text.trim()) {
        alert('语音合成提交失败: 输入文本不能为空');
        return;
      }

      this.synthesizing = true;
      this.synthesisProgress = 0;
      const reqId = Math.random().toString(36).substring(2, 10);

      this.progressInterval = setInterval(async () => {
        try {
          const res = await fetch(`/tts/api/progress/${reqId}`);
          if (res.ok) {
            const data = await res.json();
            this.synthesisProgress = data.progress;
          }
        } catch (e) {}
      }, 1000);

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
            paragraph_pause_ms: this.paragraphPause,
            req_id: reqId
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
        if (this.progressInterval) {
          clearInterval(this.progressInterval);
          this.progressInterval = null;
        }
        this.synthesisProgress = 0;
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
      if (this.audioUrl && this.isPlaying) {
        this.saveProgress();
      }
      this.audioUrl = task.audio_url;
      this.nowPlayingTitle = task.filename;
      this.nowPlayingVoice = task.voice;
      this.nowPlayingRate = task.rate;
      this._hasRestoredProgress = false;
      
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

    // Delete Task logic
    confirmDeleteTask(task) {
      if (confirm(`确定要删除历史记录 "${task.filename}" 及对应的音频文件吗？\n删除后无法恢复。`)) {
        this.deleteTask(task);
      }
    },
    async deleteTask(task) {
      try {
        const response = await fetch(`/tts/api/tasks/${task.id}`, {
          method: 'DELETE'
        });

        if (!response.ok) {
          throw new Error('删除失败，可能记录已被删除或网络异常');
        }

        // Remove from list
        this.tasks = this.tasks.filter(t => t.id !== task.id);

        // Stop playing if the deleted task is currently playing
        if (this.audioUrl === task.audio_url) {
          const player = this.$refs.audioPlayer;
          if (player) {
            player.pause();
          }
          this.audioUrl = '';
          this.nowPlayingTitle = '';
          this.nowPlayingVoice = '';
          this.nowPlayingRate = '';
          this.isPlaying = false;
          this.currentTime = 0;
          this.duration = 0;
        }
      } catch (err) {
        console.error(err);
        alert(err.message);
      }
    },

    // Hidden Audio Player controls
    togglePlay() {
      const player = this.$refs.audioPlayer;
      if (!player || !this.audioUrl) return;
      
      if (this.isPlaying) {
        player.pause();
        this.isPlaying = false;
        this.lastPausedTime = Date.now();
        this.saveProgress();
      } else {
        // 如果暂停时间超过5秒，在恢复播放时稍微后退2秒以帮助上下文衔接
        if (this.lastPausedTime) {
          const pausedDuration = Date.now() - this.lastPausedTime;
          if (pausedDuration > 5000) {
            let targetTime = player.currentTime - 2;
            if (targetTime < 0) targetTime = 0;
            player.currentTime = targetTime;
            this.currentTime = targetTime;
          }
          this.lastPausedTime = null;
        }

        player.play();
        this.isPlaying = true;
      }
    },
    setPlayRate(rate) {
      this.playbackRate = rate;
      const player = this.$refs.audioPlayer;
      if (player) {
        player.playbackRate = this.playbackRate;
      }
      this.showRateMenu = false;
    },
    seekAudio(e) {
      const player = this.$refs.audioPlayer;
      if (!player) return;
      const targetTime = parseFloat(e.target.value);
      player.currentTime = targetTime;
      this.currentTime = targetTime;
    },
    skipAudio(seconds) {
      const player = this.$refs.audioPlayer;
      if (!player) return;
      let targetTime = player.currentTime + seconds;
      if (targetTime < 0) targetTime = 0;
      if (targetTime > this.duration) targetTime = this.duration;
      player.currentTime = targetTime;
      this.currentTime = targetTime;
    },
    updateAudioProgress() {
      const player = this.$refs.audioPlayer;
      if (!player) return;
      this.currentTime = player.currentTime;
      
      const now = Date.now();
      if (!this._lastSaveTime || now - this._lastSaveTime > 3000) {
        this.saveProgress();
        this._lastSaveTime = now;
      }
    },
    onAudioLoaded() {
      const player = this.$refs.audioPlayer;
      if (!player) return;
      this.duration = player.duration;
      // Sync initial playback speed and volume
      player.playbackRate = this.playbackRate;
      player.volume = this.isMuted ? 0 : this.volume;

      // 恢复进度
      if (this.audioUrl && !this._hasRestoredProgress) {
        const key = `tts_progress_${encodeURIComponent(this.audioUrl)}`;
        const savedTime = localStorage.getItem(key);
        if (savedTime) {
          const t = parseFloat(savedTime);
          if (t > 0 && t < this.duration - 2) {
            player.currentTime = t;
            this.currentTime = t;
          }
        }
        this._hasRestoredProgress = true;
      }
    },
    onAudioEnded() {
      this.isPlaying = false;
      this.clearProgress();
    },
    saveProgress() {
      if (!this.audioUrl || !this.currentTime) return;
      const key = `tts_progress_${encodeURIComponent(this.audioUrl)}`;
      localStorage.setItem(key, this.currentTime.toString());
    },
    clearProgress() {
      if (!this.audioUrl) return;
      const key = `tts_progress_${encodeURIComponent(this.audioUrl)}`;
      localStorage.removeItem(key);
    },
    async downloadAudio() {
      if (!this.audioUrl) return;
      try {
        let fetchUrl = this.audioUrl;
        try {
          const parsed = new URL(this.audioUrl);
          fetchUrl = parsed.pathname; // This forces the browser to route through the proxy/same-origin
        } catch (e) {
          // If already relative, do nothing
        }

        const response = await fetch(fetchUrl);
        if (!response.ok) throw new Error('Fetch failed');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        let baseName = this.nowPlayingTitle || '听书音频';
        // Remove file extension if exists
        baseName = baseName.replace(/\.[^/.]+$/, '');
        a.download = `${baseName}.mp3`;

        document.body.appendChild(a);
        a.click();

        setTimeout(() => {
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        }, 100);
      } catch (err) {
        console.error('Download failed', err);
        // Fallback
        const a = document.createElement('a');
        a.href = this.audioUrl;
        let baseName = this.nowPlayingTitle || '听书音频';
        a.download = `${baseName.replace(/\.[^/.]+$/, '')}.mp3`;
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }
    }
  }
};
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700;800&display=swap');

/* Fresh Bright Hardware (Teenage Engineering / Braun inspired) */
:root {
  --bg-main: #F2F4F6;       /* Light grey background */
  --bg-panel: #FFFFFF;      /* Pure white plastic panels */
  --bg-screen: #E8ECEF;     /* LCD screen background */
  
  --text-main: #111111;     /* High contrast black */
  --text-muted: #555555;    /* Secondary text */
  --text-screen: #0022DD;   /* LCD text (blueish) */
  
  --border-color: #111111;  /* Stark black borders */
  --border-width: 2.5px;    /* Thick, bold borders */
  
  --accent-primary: #FF4747; /* Punchy Red */
  --accent-secondary: #0066FF; /* Vibrant Blue */
  --accent-tertiary: #FFC000; /* Bright Yellow */
  --accent-success: #00CC66; /* Mint Green */
  
  --shadow-hard: 4px 4px 0px var(--border-color);
  --shadow-hard-hover: 6px 6px 0px var(--border-color);
  
  --font-ui: 'Chakra Petch', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  background-color: var(--bg-main);
  /* Subtle dot grid for the plastic texture look */
  background-image: radial-gradient(circle at 50% 50%, #D0D5DB 1.5px, transparent 1.5px);
  background-size: 16px 16px; 
  color: var(--text-main);
  font-family: var(--font-ui);
  min-height: 100vh;
  overflow-x: hidden;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
  width: 12px;
  height: 12px;
}
::-webkit-scrollbar-track {
  background: var(--bg-main);
  border-left: var(--border-width) solid var(--border-color);
}
::-webkit-scrollbar-thumb {
  background: var(--accent-secondary);
  border: var(--border-width) solid var(--border-color);
  border-radius: 0; /* Blocky */
}
::-webkit-scrollbar-thumb:hover {
  background: var(--accent-primary);
}

html, body, #app {
  height: 100%;
  width: 100%;
}

#app {
  display: flex;
  justify-content: center;
}

.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 30px;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
}

/* Hardware Header */
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 20px 30px;
  background: var(--bg-panel);
  border: var(--border-width) solid var(--border-color);
  border-radius: 8px;
  margin-bottom: 30px;
  box-shadow: var(--shadow-hard);
  position: relative;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-left: 10px;
}
.logo-icon {
  color: #fff;
  background: var(--accent-primary);
  padding: 10px;
  border-radius: 8px;
  border: var(--border-width) solid var(--border-color);
  box-shadow: 2px 2px 0 #111;
}
.logo-text h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: 1px;
  text-transform: uppercase;
}
.logo-text p {
  margin: 2px 0 0 0;
  font-size: 13px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  letter-spacing: 2px;
  font-weight: 700;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-screen);
  padding: 8px 15px;
  border-radius: 4px;
  border: var(--border-width) solid var(--border-color);
}
.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--accent-success);
  border: 2px solid var(--border-color);
}
.status-indicator.animate-pulse {
  animation: ledPulse 2s infinite;
}
@keyframes ledPulse {
  0% { opacity: 0.4; }
  50% { opacity: 1; }
  100% { opacity: 0.4; }
}
.status-text {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 800;
  color: var(--text-main);
  text-transform: uppercase;
}

/* Grid Layout */
.app-main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  flex: 1;
  width: 100%;
}

.grid-col {
  min-width: 0;
}

/* Hardware Panels */
.glass-card {
  background: var(--bg-panel);
  border: var(--border-width) solid var(--border-color);
  border-radius: 12px;
  padding: 30px;
  box-shadow: var(--shadow-hard);
  display: flex;
  flex-direction: column;
  position: relative;
}

/* Panel Labels */
.glass-card::before {
  content: 'UNIT-01';
  position: absolute;
  top: -12px;
  left: 20px;
  background: var(--accent-tertiary);
  padding: 2px 10px;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 800;
  color: var(--text-main);
  border: var(--border-width) solid var(--border-color);
  border-radius: 4px;
}
.player-card::before {
  content: 'AUDIO-OUT';
  background: var(--accent-secondary);
  color: #fff;
}
.history-card::before {
  content: 'LOG-DATA';
  background: var(--bg-screen);
}

/* Tabs like mechanical buttons */
.tabs-container {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
}
.tab-btn {
  flex: 1;
  background: var(--bg-main);
  color: var(--text-muted);
  border: var(--border-width) solid var(--border-color);
  padding: 12px;
  font-family: var(--font-ui);
  font-weight: 700;
  font-size: 16px;
  cursor: pointer;
  border-radius: 6px;
  box-shadow: 2px 2px 0 var(--border-color);
  transition: all 0.1s;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.tab-btn:active {
  transform: translate(2px, 2px);
  box-shadow: 0 0 0 var(--border-color);
}
.tab-btn.active {
  background: var(--accent-tertiary);
  color: var(--text-main);
  transform: translate(2px, 2px);
  box-shadow: 0 0 0 var(--border-color);
}

/* LCD Screens for Inputs */
.input-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
}
.styled-textarea {
  width: 100%;
  background: var(--bg-screen);
  border: var(--border-width) solid var(--border-color);
  color: var(--text-screen);
  padding: 15px;
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.6;
  resize: vertical;
  border-radius: 6px;
  box-shadow: inset 2px 2px 0 rgba(0,0,0,0.1);
  outline: none;
}
.styled-textarea:focus {
  background: #fff;
  border-color: var(--accent-secondary);
}
.styled-textarea::placeholder {
  color: #99A1AA;
}

/* PDF Upload Mode */
.llm-toggle-container {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  background: #fff;
  padding: 12px 15px;
  border: var(--border-width) solid var(--border-color);
  border-radius: 6px;
  box-shadow: 2px 2px 0 var(--border-color);
}
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 28px;
}
.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: var(--bg-screen);
  transition: .2s;
  border: var(--border-width) solid var(--border-color);
  border-radius: 20px;
}
.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 2px;
  background-color: #fff;
  border: 2px solid var(--border-color);
  transition: .2s;
  border-radius: 50%;
}
input:checked + .slider {
  background-color: var(--accent-secondary);
}
input:checked + .slider:before {
  transform: translateX(20px);
}
.toggle-label {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  color: var(--text-main);
}

.upload-dropzone {
  border: var(--border-width) dashed var(--border-color);
  background: var(--bg-main);
  padding: 40px 20px;
  text-align: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}
.upload-dropzone.dragging {
  background: var(--accent-tertiary);
  border-style: solid;
}
.upload-icon {
  color: var(--text-main);
  margin-bottom: 15px;
}
.main-msg {
  font-family: var(--font-ui);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-main);
  margin: 0 0 8px 0;
}
.main-msg span {
  color: var(--accent-secondary);
  text-decoration: underline;
}
.sub-msg {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  margin: 0;
}

/* Settings Grid */
.settings-divider {
  margin: 35px 0 20px;
  border-bottom: var(--border-width) solid var(--border-color);
  padding: 10px 0;
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 800;
  color: var(--text-main);
  text-transform: uppercase;
}
.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 25px;
  margin-bottom: 30px;
}
.control-group label {
  display: block;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  margin-bottom: 10px;
  text-transform: uppercase;
}

/* Hardware Select */
.styled-select {
  width: 100%;
  background: var(--bg-main);
  color: var(--text-main);
  border: var(--border-width) solid var(--border-color);
  padding: 12px 15px;
  font-family: var(--font-ui);
  font-weight: 700;
  font-size: 15px;
  border-radius: 6px;
  appearance: none;
  outline: none;
  cursor: pointer;
  box-shadow: 2px 2px 0 var(--border-color);
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23111' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 16px;
}
.styled-select:focus {
  background: #fff;
  border-color: var(--accent-secondary);
}

/* Preset Buttons */
.speed-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.preset-btn {
  flex: 1;
  background: #fff;
  border: var(--border-width) solid var(--border-color);
  color: var(--text-main);
  padding: 8px;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 11px;
  cursor: pointer;
  min-width: 45px;
  border-radius: 4px;
  box-shadow: 2px 2px 0 var(--border-color);
  transition: all 0.1s;
}
.preset-btn:active {
  transform: translate(2px, 2px);
  box-shadow: 0 0 0 var(--border-color);
}
.preset-btn.active {
  background: var(--accent-secondary);
  color: #fff;
  transform: translate(2px, 2px);
  box-shadow: 0 0 0 var(--border-color);
}

/* Sliders */
.input-range-container {
  display: flex;
  align-items: center;
  gap: 15px;
  background: #fff;
  padding: 10px 15px;
  border: var(--border-width) solid var(--border-color);
  border-radius: 6px;
  box-shadow: 2px 2px 0 var(--border-color);
}
.styled-range {
  flex: 1;
  appearance: none;
  height: 6px;
  background: var(--bg-main);
  border: 1px solid var(--border-color);
  border-radius: 3px;
  outline: none;
}
.styled-range::-webkit-slider-thumb {
  appearance: none;
  width: 16px;
  height: 24px;
  background: var(--accent-tertiary);
  border: 2px solid var(--border-color);
  border-radius: 4px;
  cursor: pointer;
}
.range-val {
  font-family: var(--font-mono);
  font-weight: 800;
  font-size: 12px;
  color: var(--accent-secondary);
  min-width: 50px;
  text-align: right;
}

/* Action Buttons */
.action-bar {
  display: flex;
  gap: 15px;
  margin-top: auto;
}
.primary-btn, .secondary-btn {
  padding: 16px 20px;
  font-family: var(--font-ui);
  font-size: 16px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1px;
  border: var(--border-width) solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.1s;
  box-shadow: 4px 4px 0 var(--border-color);
  position: relative;
  overflow: hidden;
}
.primary-btn:active, .secondary-btn:active {
  transform: translate(4px, 4px);
  box-shadow: 0 0 0 var(--border-color);
}
.primary-btn {
  flex: 2;
  background: var(--accent-primary);
  color: #fff;
}
.primary-btn:disabled {
  background: var(--bg-screen);
  color: var(--text-muted);
  cursor: not-allowed;
  transform: translate(4px, 4px);
  box-shadow: 0 0 0 var(--border-color);
}
.secondary-btn {
  flex: 1;
  background: #fff;
  color: var(--text-main);
}

/* Player LCD */
.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: var(--border-width) solid var(--border-color);
  padding-bottom: 12px;
}
.player-header h3 {
  margin: 0;
  font-family: var(--font-ui);
  font-size: 18px;
  font-weight: 800;
  color: var(--text-main);
  text-transform: uppercase;
}
.badge {
  background: var(--accent-secondary);
  color: #fff;
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 800;
  padding: 4px 8px;
  border: 2px solid var(--border-color);
  border-radius: 4px;
}

.track-info {
  background: var(--bg-screen);
  border: var(--border-width) solid var(--border-color);
  border-radius: 8px;
  padding: 25px;
  margin-bottom: 30px;
  box-shadow: inset 3px 3px 0 rgba(0,0,0,0.05);
  position: relative;
}
.track-info::before {
  content: 'TRACK INFO';
  position: absolute;
  top: 8px; left: 10px;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 800;
  color: var(--text-muted);
}
.track-title {
  font-family: var(--font-ui);
  font-size: 22px;
  font-weight: 700;
  color: var(--text-screen);
  margin-bottom: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: center;
}
.track-meta {
  display: flex;
  justify-content: space-between;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  color: var(--text-main);
}

/* Hardware Controls */
.player-controls-wrapper {
  background: #fff;
  border: var(--border-width) solid var(--border-color);
  border-radius: 8px;
  padding: 25px;
  box-shadow: 2px 2px 0 var(--border-color);
}
.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 30px;
}
.time-label {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 800;
  color: var(--text-main);
  min-width: 50px;
}

.controls-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.play-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--accent-tertiary);
  border: var(--border-width) solid var(--border-color);
  color: var(--text-main);
  box-shadow: 3px 3px 0 var(--border-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.1s;
}
.play-btn:active {
  transform: translate(3px, 3px);
  box-shadow: 0 0 0 var(--border-color);
}
.skip-btn {
  background: #fff;
  border: var(--border-width) solid var(--border-color);
  color: var(--text-main);
  width: 44px;
  height: 44px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 2px 2px 0 var(--border-color);
}
.skip-btn:active {
  transform: translate(2px, 2px);
  box-shadow: 0 0 0 var(--border-color);
}

.rate-select-wrapper {
  position: relative;
}
.rate-select-btn {
  background: #fff;
  border: var(--border-width) solid var(--border-color);
  color: var(--text-main);
  font-family: var(--font-mono);
  font-weight: 800;
  font-size: 14px;
  padding: 10px 14px;
  border-radius: 6px;
  cursor: pointer;
  box-shadow: 2px 2px 0 var(--border-color);
}
.rate-select-btn:active {
  transform: translate(2px, 2px);
  box-shadow: 0 0 0 var(--border-color);
}
.rate-menu {
  position: absolute;
  bottom: 110%;
  left: 50%;
  transform: translateX(-50%);
  background: #fff;
  border: var(--border-width) solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 8px;
  width: 70px;
  box-shadow: 4px 4px 0 var(--border-color);
  overflow: hidden;
}
.rate-menu::after {
  content: '';
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  height: 10px;
}
.rate-item {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  color: var(--text-main);
  padding: 10px;
  text-align: center;
  cursor: pointer;
  border-bottom: 1px solid var(--border-color);
}
.rate-item:last-child {
  border-bottom: none;
}
.rate-item:hover {
  background: var(--bg-main);
}
.rate-item.active {
  color: #fff;
  background: var(--accent-secondary);
}

.volume-container {
  display: flex;
  align-items: center;
  gap: 12px;
}
.volume-btn {
  background: none;
  border: none;
  color: var(--text-main);
  cursor: pointer;
}
.volume-slider {
  width: 90px;
}

/* Download Button */
.download-container {
  margin-top: 30px;
}
.btn-download {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: #fff;
  border: var(--border-width) solid var(--border-color);
  color: var(--text-main);
  text-decoration: none;
  padding: 15px;
  font-family: var(--font-ui);
  font-weight: 800;
  font-size: 15px;
  border-radius: 8px;
  box-shadow: 3px 3px 0 var(--border-color);
  transition: all 0.1s;
}
.btn-download:active {
  transform: translate(3px, 3px);
  box-shadow: 0 0 0 var(--border-color);
}

/* History Log */
.history-card {
  margin-top: 30px;
}
.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: var(--border-width) solid var(--border-color);
  padding-bottom: 12px;
}
.history-header h3 {
  margin: 0;
  font-family: var(--font-ui);
  font-size: 16px;
  font-weight: 800;
  color: var(--text-main);
}
.refresh-btn {
  background: var(--bg-main);
  border: var(--border-width) solid var(--border-color);
  border-radius: 4px;
  padding: 4px;
  color: var(--text-main);
  cursor: pointer;
  box-shadow: 1px 1px 0 var(--border-color);
}
.refresh-btn:active {
  transform: translate(1px, 1px);
  box-shadow: 0 0 0;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 5px;
}
.history-item {
  background: #fff;
  border: var(--border-width) solid var(--border-color);
  padding: 15px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 15px;
  cursor: pointer;
  transition: all 0.1s;
  box-shadow: 2px 2px 0 var(--border-color);
}
.history-item:active {
  transform: translate(2px, 2px);
  box-shadow: 0 0 0 var(--border-color);
}
.history-item.active {
  background: var(--bg-main);
  border-color: var(--accent-secondary);
}
.item-play-icon {
  color: var(--text-muted);
}
.history-item.active .item-play-icon {
  color: var(--accent-secondary);
}
.item-details {
  flex: 1;
  min-width: 0;
}
.item-title {
  font-family: var(--font-ui);
  font-weight: 700;
  font-size: 15px;
  color: var(--text-main);
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-preview {
  font-family: var(--font-ui);
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-meta {
  display: flex;
  gap: 15px;
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 11px;
  color: var(--text-muted);
}
.delete-task-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
}
.delete-task-btn:hover {
  color: var(--accent-primary);
}

@media (max-width: 900px) {
  .app-main-grid {
    grid-template-columns: 1fr;
  }
}

</style>
