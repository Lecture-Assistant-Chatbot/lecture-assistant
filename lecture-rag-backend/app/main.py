import os
import json
import asyncio
import logging
from typing import List

import httpx
import google.auth
from google.auth.transport.requests import Request
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from vertexai.preview.language_models import TextEmbeddingModel
from google.cloud import aiplatform
import vertexai

from .config import settings

# ---------- Logging ----------
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
log = logging.getLogger("rag")

# ---------- Pydantic models ----------
class QueryRequest(BaseModel):
    prompt: str

class QueryResponse(BaseModel):
    response: str

# ---------- Vertex init (idempotent) ----------
_vertexai_inited = False

def _init_vertexai_once():
    global _vertexai_inited
    if _vertexai_inited:
        return
    vertexai.init(project=settings.vertex_ai_project, location=settings.vertex_ai_location)
    _vertexai_inited = True
    log.info("Vertex AI initialized for project=%s location=%s", settings.vertex_ai_project, settings.vertex_ai_location)

# ---------- Embeddings ----------
async def get_query_embedding(text: str) -> List[float]:
    def _embed_sync() -> List[float]:
        _init_vertexai_once()
        model = TextEmbeddingModel.from_pretrained("text-embedding-005")
        emb = model.get_embeddings([text])[0]
        return emb.values

    try:
        vector = await asyncio.to_thread(_embed_sync)
    except Exception as e:
        raise RuntimeError(f"Embedding generation failed: {e}") from e

    if not isinstance(vector, list) or not vector:
        raise RuntimeError("Embedding API response did not include an embedding vector.")

    log.info("Generated embedding length=%d", len(vector))
    return vector

# ---------- Google access token (if you ever need one) ----------
async def fetch_google_access_token() -> str:
    def _refresh_token() -> str:
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not creds.valid:
            creds.refresh(Request())
        return creds.token
    return await asyncio.to_thread(_refresh_token)

# ---------- Matching Engine Vector Search ----------
async def vertex_ai_vector_search_texts(query_vector: List[float], neighbor_count: int = 4) -> list[str]:
    project_id = settings.vertex_ai_project
    location = settings.vertex_ai_location
    index_endpoint = settings.vertex_ai_index_endpoint
    deployed_index_id = settings.vertex_ai_deployed_index

    if not index_endpoint.startswith("projects/"):
        index_endpoint_name = f"projects/{project_id}/locations/{location}/indexEndpoints/{index_endpoint}"
    else:
        index_endpoint_name = index_endpoint

    def _find_neighbors_sync():
        # aiplatform.init not strictly required if using full resource names,
        # but it's harmless and helps local dev tooling.
        aiplatform.init(project=project_id, location=location)
        me_endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=index_endpoint_name)
        return me_endpoint.find_neighbors(
            deployed_index_id=deployed_index_id,
            queries=[query_vector],
            num_neighbors=neighbor_count,
            return_full_datapoint=True,
        )

    try:
        neighbors = await asyncio.to_thread(_find_neighbors_sync)
    except Exception as e:
        log.exception("Vector search failed via SDK")
        raise RuntimeError(f"Vector search failed via SDK: {e}") from e

    text_snippets: list[str] = []
    if neighbors and len(neighbors) > 0:
        for n in neighbors[0]:
            restricts = getattr(n, "restricts", None)
            if not restricts:
                continue
            for r in restricts:
                if getattr(r, "name", None) == "text":
                    tokens = getattr(r, "allow_tokens", []) or []
                    text_snippets.extend(tokens)

    log.info("Vector search returned %d text snippets", len(text_snippets))
    return text_snippets

async def vector_search(query: str) -> str:
    query_vector = await get_query_embedding(query)
    matched_contexts = await vertex_ai_vector_search_texts(query_vector)
    if not matched_contexts:
        return "No relevant context found via Vertex AI Vector Search."
    return "\n".join(matched_contexts)

# ---------- RAG prompt ----------
def construct_gemini_payload(query: str, context: str) -> dict:
    system_instruction = (
    "You are a concise and helpful lecture assistant. "
    "Answer the student's question using the provided lecture context. "
    "Keep your answer short and clear—no more than 4 sentences. "
    "If the student asks for clarification (like 'I don't understand this'), "
    "explain the same concept in simpler terms rather than giving a long summary. "
    "If the question is not related to the lecture, say: "
    "'I'm sorry, I don't have information about that topic in the lecture materials.'"
)

    user_prompt = f"Context:\n{context}\n\nUser Question:\n{query}\n"
    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
    }
    log.debug("--- Gemini Payload ---\n%s\n----------------------", json.dumps(payload, indent=2))
    return payload

# ---------- Gemini call (non-streaming) ----------
async def get_gemini_response_full(payload: dict) -> str:
    if not settings.gemini_api_key:
        return "Error: GEMINI_API_KEY not configured."

    api_url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        try:
            resp = await client.post(api_url, json=payload, headers={"Content-Type": "application/json"})
            if resp.status_code != 200:
                return f"Error: Received status {resp.status_code}\n{resp.text}"

            data = resp.json()
            text = (
                data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text")
            )
            return text or "Error: Could not parse text from API response."
        except httpx.ConnectError as e:
            return f"Connection Error: {e}"
        except Exception as e:
            return f"Unexpected Error: {e}"

# ---------- FastAPI app ----------
app = FastAPI(
    title="Custom RAG Endpoint (Vertex AI + Gemini)",
    description="Backend API for Retrieval-Augmented Generation using Vertex AI Vector Search and Gemini models.",
    version="1.0.0",
)

if settings.cors_allow_all:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
    )

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/api/v1/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    try:
        context = await vector_search(request.prompt)
    except Exception as exc:
        log.exception("Vector search failed")
        context = "No relevant context found via Vertex AI Vector Search."

    payload = construct_gemini_payload(request.prompt, context)
    full_response = await get_gemini_response_full(payload)
    return QueryResponse(response=full_response)

# ---------- Local dev entrypoint ----------
def _port():
    # Cloud Run injects $PORT; fallback for local dev
    return int(os.getenv("PORT", settings.port))

if __name__ == "__main__":
    import uvicorn
    log.info("Starting FastAPI on 0.0.0.0:%s", _port())
    uvicorn.run(app, host=settings.host, port=_port())
