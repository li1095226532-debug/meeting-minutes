# 🎙️ 会议纪要助手

> 浏览器录音 → 语音转文字 → AI 自动生成会议纪要

一个轻量级的会议记录工具，在浏览器中完成录音，后端自动将语音转为文字，再通过 AI 提炼出结构清晰的会议纪要。

---

## ✨ 功能特性

- **🎤 浏览器录音** — 无需安装 App，打开网页即用，支持暂停/继续
- **📝 语音转文字** — 支持三种后端：本地 GPU 加速 / 本地 CPU / 云端 API
- **🤖 AI 会议总结** — 调用 Claude API，自动提炼会议主题、讨论要点、决议、待办事项
- **🌐 多语言** — 支持中文、英文、自动检测
- **📂 文件上传** — 也支持直接上传已有的录音文件（webm/mp3/m4a/wav）
- **⚡ 实时反馈** — 录音波形显示、计时器、处理进度提示

---

## 📸 界面预览

```
┌─────────────────────────────────────────┐
│  🎙️ 会议纪要助手         语言:[中文 ▼] │
├────────────────┬────────────────────────┤
│   🔴 录音      │   📋 操作              │
│                │                        │
│    00:05:23    │  上传录音文件 [选择]   │
│   ● 录音中     │                        │
│  ▁▃▅▇▅▃▁     │  使用说明...          │
│                │                        │
│ [▶ 开始] [⏹ 停止] [⏸ 暂停] │         │
├────────────────┴────────────────────────┤
│  📝 转写文本                     [📋 复制] │
│  今天我们讨论了Q3的预算分配...           │
├─────────────────────────────────────────┤
│  ✨ 会议纪要                     [📋 复制] │
│  会议主题：Q3预算评审                    │
│  讨论要点：...                          │
│  待办事项：...                          │
└─────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 基础依赖（必装）
pip install fastapi uvicorn python-multipart python-dotenv anthropic

# 语音转文字（三选一）
pip install faster-whisper    # 推荐，需 Python 3.9+，GPU 加速
pip install openai-whisper    # 备选，支持 Python 3.8+，CPU
# 或设置 OPENAI_API_KEY 使用云端 API（无需本地模型）
```

> Windows 用户可直接运行 `setup.bat`，按提示选择安装方式。

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# AI 总结（必填）
ANTHROPIC_API_KEY=sk-ant-xxxxx

# 语音转文字后端（可选，默认自动检测）
WHISPER_BACKEND=auto
WHISPER_MODEL=medium
```

### 3. 启动服务

```bash
python server.py
# 浏览器打开 http://localhost:8866
```

---

## 🔧 语音转文字后端对比

| 后端 | Python 版本 | 速度 | 准确度 | 是否需要 API Key |
|------|------------|------|--------|-----------------|
| **faster-whisper** | ≥ 3.9 | ⚡ 快（GPU） | ⭐⭐⭐⭐ | ❌ 不需要 |
| **openai-whisper** | ≥ 3.8 | 🐢 慢（CPU） | ⭐⭐⭐⭐ | ❌ 不需要 |
| **OpenAI API** | 不限 | ⚡ 快（云端） | ⭐⭐⭐⭐⭐ | ✅ 需要 |

---

## 📁 项目结构

```
meeting-minutes/
├── server.py              # FastAPI 后端
├── templates/
│   └── index.html         # Web 前端界面
├── requirements.txt       # Python 依赖列表
├── setup.bat              # Windows 一键安装脚本
├── .env.example           # 环境变量模板
└── uploads/               # 录音文件暂存（自动创建）
```

---

## 🔌 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 前端页面 |
| `POST` | `/api/transcribe-and-summarize` | 上传音频 → 转写 + 总结 |
| `POST` | `/api/transcribe` | 仅语音转文字 |
| `POST` | `/api/summarize` | 仅文本总结 |

### 请求示例

```bash
# 上传录音并获取转写+总结
curl -X POST http://localhost:8866/api/transcribe-and-summarize \
  -F "audio=@recording.webm" \
  -F "language=zh" \
  -F "enable_summary=true"
```

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML5 + CSS3 + 原生 JavaScript（MediaRecorder API） |
| 后端 | Python FastAPI |
| 语音识别 | faster-whisper / openai-whisper / OpenAI Whisper |
| AI 总结 | Anthropic Claude API |
| 音频处理 | Web Audio API（浏览器端） |

---

## 📄 License

MIT
