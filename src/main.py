"""FastAPI application entry point for Geetopadesha."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.answer_generator import AnswerGenerator
from src.embedder import Embedder
from src.models import GeetaResponse, HealthStatus, QueryRequest
from src.prompt_builder import PromptBuilder
from src.query_handler import QueryHandler
from src.response_formatter import ResponseFormatter
from src.vector_store import VectorStore

load_dotenv()

# ---------------------------------------------------------------------------
# Rate limiter (per IP)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Geetopadesha",
    description="AI-powered spiritual guidance grounded in the Bhagavad Gita",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Serve the web UI
_static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(os.path.join(_static_dir, "index.html"))


@app.get("/sw.js", include_in_schema=False)
async def service_worker():
    """Serve service worker from root scope (required for PWA)."""
    return FileResponse(
        os.path.join(_static_dir, "sw.js"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/"},
    )


# ---------------------------------------------------------------------------
# Dependency: build the handler once at startup
# ---------------------------------------------------------------------------
_handler: QueryHandler | None = None


def _get_handler() -> QueryHandler:
    global _handler
    if _handler is None:
        embedder = Embedder()
        vector_store = VectorStore(persist_directory=os.getenv("CHROMA_DIR", ".chroma"))
        prompt_builder = PromptBuilder()
        answer_generator = AnswerGenerator(
            model=os.getenv("LLM_MODEL", "gpt-4o"),
        )
        formatter = ResponseFormatter()
        _handler = QueryHandler(
            embedder=embedder,
            vector_store=vector_store,
            prompt_builder=prompt_builder,
            answer_generator=answer_generator,
            response_formatter=formatter,
        )
    return _handler


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/query", response_model=GeetaResponse)
@limiter.limit("60/minute")
async def query(request: Request, body: QueryRequest) -> GeetaResponse:
    """Submit a natural language question and receive a Gita-grounded answer."""
    handler = _get_handler()
    return handler.handle_query(body)


class TranslateRequest(BaseModel):
    text: str
    language: str  # e.g. "hi", "te", "bn", "or", "kn", "ta", "ml"


_LANG_NAMES = {
    "hi": "Hindi", "te": "Telugu", "bn": "Bengali",
    "or": "Odia", "kn": "Kannada", "ta": "Tamil", "ml": "Malayalam",
}


@app.post("/translate")
@limiter.limit("60/minute")
async def translate(request: Request, body: TranslateRequest) -> JSONResponse:
    """Translate an answer text into a regional Indian language."""
    lang_name = _LANG_NAMES.get(body.language)
    if not lang_name:
        return JSONResponse(status_code=400, content={"detail": f"Unsupported language: {body.language}"})

    handler = _get_handler()
    from src.models import Prompt
    prompt = Prompt(
        systemInstruction=(
            f"You are a translator. Translate the following spiritual text into {lang_name}. "
            "Keep the warm, friendly tone. Preserve verse references like 'BG 2.47' as-is. "
            "Output only the translated text, nothing else."
        ),
        verseContext="",
        userQuery=body.text,
        fullText=body.text,
    )
    try:
        translated = handler._answer_generator.generate(prompt)
        return JSONResponse(content={"translated": translated})
    except Exception as exc:
        return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.get("/health", response_model=HealthStatus)
async def health() -> HealthStatus:
    """Check the health of all downstream components."""
    handler = _get_handler()
    return handler.health_check()


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={"detail": exc.errors()})


@app.exception_handler(RuntimeError)
async def runtime_exception_handler(request: Request, exc: RuntimeError):
    msg = str(exc)
    if "Answer generation failed" in msg:
        return JSONResponse(status_code=503, content={"detail": msg})
    return JSONResponse(status_code=500, content={"detail": msg})
