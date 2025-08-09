# NutriPrecision-AI — Audio Backend (FastAPI)

Endpoints:
- POST /api/stt — Speech-to-Text (OpenAI /v1/audio/transcriptions)
- POST /api/tts — Text-to-Speech (OpenAI /v1/audio/speech)
- GET  /health

## 1) Configurar
1. Criar ambiente:
   - `python -m venv .venv`
   - `source .venv/bin/activate`  (Windows: `.venv\Scripts\activate`)
   - `pip install -r requirements.txt`
2. Duplicar `.env.example` para `.env` e preencher `OPENAI_API_KEY`.

## 2) Rodar
- `uvicorn main:app --reload --port 8000`

## 3) Testar do Frontend
- Defina `http://localhost:8000` como Backend URL.
- Envie áudio (arquivo) ou grave.
- Use o botão "Ouvir Resumo (TTS)" para sintetizar o texto.

## Referências (OpenAI Docs)
- Text-to-Speech (/v1/audio/speech): platform.openai.com/docs/guides/text-to-speech
- Speech-to-Text (/v1/audio/transcriptions): platform.openai.com/docs/guides/speech-to-text
- Modelos de áudio: platform.openai.com/docs/guides/audio