import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
STT_MODEL = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")
TTS_VOICE = os.getenv("TTS_VOICE", "alloy")

app = FastAPI(title="NutriPrecision-AI Audio Backend", version="0.1.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSIn(BaseModel):
    text: str
    voice: str | None = None
    format: str | None = "mp3"

@app.get("/", response_class=HTMLResponse)
async def index():
    return """<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>NutriPrecision-AI — Backend</title>
<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto;padding:24px;line-height:1.45} code{background:#f4f4f4;padding:2px 4px;border-radius:4px}</style>
</head>
<body>
  <h1>NutriPrecision-AI — Backend</h1>
  <p>Seu serviço está ativo. Endpoints:</p>
  <ul>
    <li><code>GET /health</code></li>
    <li><code>POST /api/stt</code> — enviar áudio para transcrição</li>
    <li><code>POST /api/tts</code> — texto para voz (MP3)</li>
    <li><a href="/docs">/docs</a> — Swagger</li>
    <li><a href="/redoc">/redoc</a> — ReDoc</li>
  </ul>
  <p>Dica: use esta URL no campo <b>Backend URL</b> do Modo 1 no app (canvas).</p>
</body>
</html>"""

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/api/stt")
async def stt(audio: UploadFile = File(...)):
    if not OPENAI_API_KEY:
        return JSONResponse({"error": "Missing OPENAI_API_KEY"}, status_code=500)

    data = await audio.read()
    files = {
        "file": (audio.filename or "audio.webm", data, audio.content_type or "audio/webm"),
        "model": (None, STT_MODEL),
    }

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    url = f"{OPENAI_BASE_URL}/audio/transcriptions"

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, files=files)
        if resp.status_code >= 400:
            return JSONResponse({"error": resp.text}, status_code=resp.status_code)
        j = resp.json()
        return {"text": j.get("text", ""), "raw": j}

@app.post("/api/tts")
async def tts(inp: TTSIn):
    if not OPENAI_API_KEY:
        return JSONResponse({"error": "Missing OPENAI_API_KEY"}, status_code=500)

    voice = inp.voice or TTS_VOICE
    fmt = (inp.format or "mp3").lower()
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{OPENAI_BASE_URL}/audio/speech"
    payload = {
        "model": TTS_MODEL,
        "voice": voice,
        "input": inp.text,
        "format": fmt
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            return JSONResponse({"error": resp.text}, status_code=resp.status_code)
        def iter_bytes():
            yield resp.content
        media_type = "audio/mpeg" if fmt == "mp3" else "audio/wav"
        return StreamingResponse(iter_bytes(), media_type=media_type)
