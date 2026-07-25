"""
会议纪要程序 - 后端服务
功能：接收录音 → 语音转文字 → AI总结提炼

语音转文字支持三种后端（自动选择）：
  1. faster-whisper（推荐，需要 Python 3.9+ 和 CUDA）
  2. openai-whisper（备选，支持 Python 3.8+，CPU 运行）
  3. OpenAI Whisper API（需要 OPENAI_API_KEY）
"""
import os
import sys
import uuid
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

# ---------- 配置 ----------
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL", "medium")  # tiny/base/small/medium/large
WHISPER_BACKEND = os.getenv("WHISPER_BACKEND", "auto")     # auto / faster-whisper / openai-whisper / openai-api

app = FastAPI(title="会议纪要助手", version="1.0.0")

# ---------- STT 后端自动检测 ----------
_stt_backend = None
_whisper_model = None

def _detect_stt_backend():
    """检测可用的语音转文字后端"""
    global _stt_backend

    forced = os.getenv("WHISPER_BACKEND", "auto")
    if forced != "auto":
        backends = {
            "openai-api":      ("OpenAI Whisper API", _check_openai_api),
            "faster-whisper":  ("faster-whisper",     lambda: _check_import("faster_whisper")),
            "openai-whisper":  ("openai-whisper",     lambda: _check_import("whisper")),
        }
        if forced in backends:
            name, checker = backends[forced]
            if checker():
                _stt_backend = forced
                print(f"[后端] 使用 {name}")
                return
            print(f"[错误] {name} 不可用，请先安装")
            sys.exit(1)

    # 自动检测：faster-whisper > openai-whisper > OpenAI API
    if _check_import("faster_whisper"):
        _stt_backend = "faster-whisper"
        print("[后端] 自动选择 faster-whisper")
        return
    if _check_import("whisper"):
        _stt_backend = "openai-whisper"
        print("[后端] 自动选择 openai-whisper")
        return
    if os.getenv("OPENAI_API_KEY"):
        _stt_backend = "openai-api"
        print("[后端] 使用 OpenAI Whisper API")
        return

    print("=" * 55)
    print("  未找到可用的语音转文字后端！请任选其一：")
    print("  1. pip install faster-whisper   (推荐，需 Python 3.9+)")
    print("  2. pip install openai-whisper   (支持 Python 3.8，CPU)")
    print("  3. 设置 OPENAI_API_KEY 环境变量 (使用云端 API)")
    print("=" * 55)
    sys.exit(1)

def _check_import(pkg: str) -> bool:
    try:
        __import__(pkg)
        return True
    except ImportError:
        return False

def _check_openai_api() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and _check_import("openai")


def get_whisper_model():
    """延迟加载 Whisper 模型"""
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    if _stt_backend == "faster-whisper":
        from faster_whisper import WhisperModel
        print(f"[模型] 加载 faster-whisper: {WHISPER_MODEL_SIZE} ...")
        _whisper_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device=os.getenv("WHISPER_DEVICE", "auto"),
            compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "auto"),
        )
    elif _stt_backend == "openai-whisper":
        import whisper
        print(f"[模型] 加载 openai-whisper: {WHISPER_MODEL_SIZE} ...")
        _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)

    print(f"[模型] 加载完成")
    return _whisper_model


# ========== API 端点 ==========

@app.get("/", response_class=HTMLResponse)
async def index():
    """返回前端页面"""
    html_path = Path(__file__).parent / "templates" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.post("/api/transcribe-and-summarize")
async def transcribe_and_summarize(
    audio: UploadFile = File(...),
    language: str = "zh",
    enable_summary: bool = True,
):
    """一站式接口：上传音频 → 语音转文字 → AI总结"""
    # 1. 保存音频
    ext = Path(audio.filename).suffix if audio.filename else ".webm"
    audio_id = uuid.uuid4().hex[:8]
    audio_path = UPLOAD_DIR / f"{audio_id}_{datetime.now():%Y%m%d_%H%M%S}{ext}"

    audio_bytes = await audio.read()
    if len(audio_bytes) < 1024:
        raise HTTPException(400, "音频文件过小，请检查录音是否正常")

    audio_path.write_bytes(audio_bytes)
    print(f"[上传] {audio_path} ({len(audio_bytes) / 1024:.1f} KB)")

    # 2. 语音转文字
    print(f"[转写] 开始 (语言: {language})...")
    transcript = await run_transcription(str(audio_path), language)
    print(f"[转写] 完成，{len(transcript)} 字符")

    if not transcript.strip():
        return JSONResponse({
            "success": True,
            "transcript": "",
            "summary": None,
            "warning": "未能识别到语音内容，请检查录音质量或语言设置",
        })

    # 3. AI 总结（可选）
    summary = None
    if enable_summary:
        print("[总结] 开始 AI 总结...")
        summary = await run_summary(transcript)
        print("[总结] 完成")

    return {
        "success": True,
        "transcript": transcript,
        "summary": summary,
        "audio_file": str(audio_path.name),
    }


@app.post("/api/transcribe")
async def transcribe_only(audio: UploadFile = File(...), language: str = "zh"):
    """仅语音转文字"""
    return await transcribe_and_summarize(audio, language, enable_summary=False)


@app.post("/api/summarize")
async def summarize_only(data: dict):
    """仅对已有文本做总结"""
    text = data.get("text", "")
    if not text.strip():
        raise HTTPException(400, "文本内容为空")
    summary = await run_summary(text)
    return {"success": True, "summary": summary}


# ========== 核心功能 ==========

async def run_transcription(audio_path: str, language: str) -> str:
    """语音转文字（自动选择后端）"""
    lang_param = None if language == "auto" else language

    # --- OpenAI Whisper API ---
    if _stt_backend == "openai-api":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(audio_path, "rb") as f:
            result = await asyncio.to_thread(
                lambda: client.audio.transcriptions.create(
                    model="whisper-1", file=f, language=lang_param,
                )
            )
        return result.text

    # --- 本地模型 ---
    model = get_whisper_model()

    if _stt_backend == "faster-whisper":
        segments, info = model.transcribe(
            audio_path, beam_size=5, language=lang_param,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        parts = []
        print(f"  [转写] 语言: {info.language}, 概率: {info.language_probability:.2%}")
        for seg in segments:
            parts.append(seg.text.strip())
            print(f"  [{seg.start:.1f}s-{seg.end:.1f}s] {seg.text.strip()}")
        return "\n".join(parts)

    elif _stt_backend == "openai-whisper":
        result = await asyncio.to_thread(
            model.transcribe, audio_path,
            language=lang_param, fp16=False,
        )
        for seg in result.get("segments", []):
            print(f"  [{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['text'].strip()}")
        return result["text"].strip()


async def run_summary(transcript: str) -> Optional[Dict[str, Any]]:
    """使用 Claude API 总结会议内容"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("[总结] 未设置 ANTHROPIC_API_KEY，跳过")
        return None

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        prompt = f"""你是一位专业的会议记录员。请根据以下会议录音转写，整理出结构清晰的会议纪要。

要求：
1. 用中文输出（除非原文主要是英文）
2. 按以下结构整理：
   - **会议主题**：一句话概括核心议题
   - **讨论要点**：列出主要讨论话题，每个 2-3 句话
   - **关键结论/决议**：达成的共识和决定
   - **待办事项**：需跟进的事项，尽量指明负责人
   - **下次计划**：后续安排或下次会议
3. 去除口语化冗余，提炼核心信息
4. 无法识别的项标注"（未提及）"

以下是会议录音转写文本：
---
{transcript}
---

请输出会议纪要："""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        return {
            "content": response.content[0].text,
            "model": response.model,
        }
    except Exception as e:
        print(f"[总结错误] {e}")
        return {"error": str(e)}


# ========== 启动 ==========

if __name__ == "__main__":
    import uvicorn

    # 在启动时检测 STT 后端
    _detect_stt_backend()

    print("=" * 50)
    print("  会议纪要助手 v1.0")
    print("  打开浏览器: http://localhost:8866")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8866)
