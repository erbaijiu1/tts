# TTS 智能语音合成微服务 (Text-to-Speech Service)

基于 FastAPI + Edge-TTS + Vue 3 的文本/文档/图片语音合成系统。支持长图智能切片 OCR 提取、停顿可调的高自然度语音合成、题目自定义与行内修改、全文保存回填及轻量连接池优化。

---

## 目录结构

```text
tts/
├── backend/                  # 后端 FastAPI 服务源码
│   ├── Dockerfile            # 后端 Docker 镜像构建文件
│   ├── main.py               # 核心 API 路由与启动入口
│   ├── database.py           # 数据库连接池配置 (超轻量 pool_size=1)
│   ├── models.py             # 数据库模型 (AudioTask，含 full_text)
│   ├── ocr_processor.py      # 长图切片与多模态大模型 OCR
│   ├── pdf_processor.py      # PDF 文本提取与排版清洗
│   └── requirements.txt      # Python 依赖清单
├── frontend/                 # 前端 Vue 3 + Vite 源码
│   ├── src/
│   │   ├── App.vue           # 播放器与任务管理单文件组件
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── dist/                 # 前端打包产物 (供 Nginx 静态挂载)
├── docker-compose.yml        # TTS 插件化 Compose 定义
├── .env.example              # 环境变量配置模板
└── README.md                 # 部署与使用说明
```

---

## 线上部署指南 (Git Clone 部署方式)

线上服务器通常以插件宿主模式或独立微服务模式运行。标准上线流程如下：

### 1. 拉取代码

将仓库克隆至服务器对应目录（例如 `/data/code/toP/tts`）：

```bash
cd /data/code/toP
git clone <git-repo-url> tts
cd tts
```

---

### 2. 准备环境变量文件

根据实际环境配置环境变量。在项目父级目录或指定路径创建 `tts.env`（或项目根目录 `.env`）：

```bash
cp .env.example ../tts.env
vim ../tts.env
```

**关键配置项说明：**

| 变量名 | 默认值 / 示例 | 说明 |
| :--- | :--- | :--- |
| `PROJECT_NAME` | `tts` | 服务前缀路径 |
| `APP_PORT` | `8009` | 后端服务内部监听端口 |
| `DB_HOST` | `mysql_db` | MySQL 主机名（容器网络中使用服务名） |
| `DB_PORT` | `3306` | MySQL 端口 |
| `DB_USER` | `root` | 数据库用户名 |
| `DB_PASSWORD` | `Gmcc@123` | 数据库密码（支持特殊字符自动 URL 转义） |
| `DB_NAME` | `tts_db` | 数据库名（服务启动会自动建表） |
| `LLM_API_KEY` | `sk-xxxx` | 阿里 DashScope / OpenAI 兼容 API Key |
| `LLM_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | 大模型 Base URL |
| `LLM_MODEL_NAME` | `qwen-vl-plus` | OCR 使用的多模态视觉大模型 |
| `HUNYUAN_API_KEY` | `sk-xxxx` | 腾讯混元 API Key (备用) |

---

### 3. 构建前端静态产物

在服务器或 CI/CD 构建环境中编译前端：

```bash
cd frontend
npm install
npm run build
cd ..
```

构建完成后，产物将生成在 `frontend/dist/` 目录中。

---

### 4. 接入宿主网关 (local_dev_env / 线上网关)

#### (1) 在总入口 `docker-compose.yml` 中启用插件

在宿主 Compose 的 `include` 列表中加入本服务配置：

```yaml
include:
  - ../toP/tts/docker-compose.yml
```

并在宿主 Nginx 服务中增加挂载配置：

```yaml
services:
  nginx:
    volumes:
      # 挂载 tts 前端静态页面
      - ../toP/tts/frontend/dist:/usr/share/nginx/html/tts/html:ro
```

#### (2) 配置 Nginx 路由插件

在宿主网关的 `nginx/locations/tts.conf` 文件中写入：

```nginx
# TTS 前端静态页面
location /tts/html/ {
    auth_request /auth_verify;
    auth_request_set $user_id $upstream_http_x_user_id;

    alias /usr/share/nginx/html/tts/html/;
    try_files $uri $uri/ /tts/html/index.html;
}

# TTS 后端 API
location /tts/api/ {
    auth_request /auth_verify;
    auth_request_set $user_id $upstream_http_x_user_id;

    set $tts_backend "tts-backend:8009";
    proxy_pass http://$tts_backend;
    
    proxy_set_header X-User-Id $user_id;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    
    # 增加超时时间，防止超长长图 OCR 耗时导致 504 超时
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    proxy_read_timeout 600;
}

# TTS 后端静态音频资源
location /tts/static/ {
    auth_request /auth_verify;
    auth_request_set $user_id $upstream_http_x_user_id;

    set $tts_backend "tts-backend:8009";
    proxy_pass http://$tts_backend;
    
    proxy_set_header X-User-Id $user_id;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

### 5. 启动服务与重载网关

在宿主环境目录（如 `local_dev_env`）执行：

```bash
# 1. 启动/重新构建 tts-backend 服务
docker compose up -d --build tts-backend

# 2. 检查并平滑重载 Nginx
docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
```

---

## 核心特性与架构设计

1. **超轻量数据库连接池**
   - 采用 `pool_size=1, max_overflow=2, pool_recycle=300, pool_pre_ping=True`。
   - 平时仅占用 1 个连接，空闲时 0 资源浪费，且通过 `pre_ping` 彻底解决空闲超时导致的断连问题。

2. **全文持久化与安全无损热迁移**
   - 数据库模型 `AudioTask` 增加了 `full_text`（LONGTEXT）字段。
   - 服务每次启动均自动执行安全平滑迁移（`ALTER TABLE audio_tasks ADD COLUMN full_text LONGTEXT NULL;`），无须手动执行 DDL。

3. **题目自定义与行内修改**
   - **生成前**：支持自定义朗读标题；不填则自动根据文本首行智能命名。
   - **生成后**：历史记录标题支持原地点击修改，实时调用 `PATCH /tts/api/tasks/{id}` 接口无缝同步至数据库及播放器。

4. **历史文本回填与复制**
   - 历史记录卡片支持点击「原文」按钮弹出完整文本弹窗，支持一键复制，或一键「填入左侧编辑器」进行二次编辑与合成。
