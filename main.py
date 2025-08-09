import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import httpx

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
STT_MODEL = os.getenv("STT_MODEL", "gpt-4o-mini-transcribe")
TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")
TTS_VOICE = os.getenv("TTS_VOICE", "alloy")

app = FastAPI(title="NutriPrecision-AI Audio Backend", version="0.1.0")

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

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/api/stt")
async def stt(audio: UploadFile = File(...)):
    """Send audio to OpenAI Audio Transcriptions (Speech-to-text)."""
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
    """Generate speech (mp3) from text using OpenAI Text-to-Speech."""
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