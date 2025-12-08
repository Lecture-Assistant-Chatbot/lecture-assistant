# Lecture Assistant Chatbot API (FastAPI + Vertex AI + Gemini)

Backend service that powers the lecture assistant chatbot. It performs Retrieval-Augmented Generation (RAG) using Vertex AI embeddings and Matching Engine, then calls Gemini for the final answer. Ships as a FastAPI app deployable to Cloud Run.

## Project structure

```
lecture-rag-backend/
├─ app/
│  ├─ main.py        # FastAPI app and RAG flow
│  ├─ config.py      # Pydantic settings loaded from environment
│  └─ __init__.py
├─ requirements.txt  # Python dependencies
├─ Dockerfile        # Cloud Run image
├─ .env.example      # Sample local configuration
└─ README.md
```

## Prerequisites

- Python 3.10+ (3.11 recommended)
- `gcloud` CLI authenticated to your GCP project
- Vertex AI enabled with:
  - A Matching Engine index and deployed endpoint
  - Access to Gemini via Vertex AI Generative Language API

## Local development

1) Create and activate a virtualenv
```bash
python -m venv .venv
.\.venv\Scripts\activate   # PowerShell
```

2) Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3) Configure environment
```bash
cp .env.example .env
```
Then set the values in `.env` (see table below).

4) Run the API
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5) Smoke test
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"What is a stateful microservice?\"}"
```
Docs: http://localhost:8000/docs

## Environment variables

| Name | Description |
| --- | --- |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI region (e.g. `us-central1`) |
| `GOOGLE_GENAI_USE_VERTEXAI` | Keep `true` to use Vertex-hosted Gemini |
| `VERTEX_AI_INDEX_ENDPOINT` | Matching Engine index endpoint ID (or full resource name) |
| `VERTEX_AI_DEPLOYED_INDEX` | Deployed index ID |
| `GEMINI_MODEL` | Gemini model name (default `gemini-2.5-flash`) |
| `LOG_LEVEL` | `info`, `debug`, etc. |
| `CORS_ALLOW_ALL` | `true` to allow all origins locally |
| `HTTP_TIMEOUT_SECONDS` | HTTP timeout for SDK calls |

## Deploy to Cloud Run

1) Enable required APIs (one time)
```bash
gcloud services enable run.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

2) Build and push the image
```bash
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/lecture-rag-backend
```

3) Deploy
```bash
gcloud run deploy lecture-rag-backend \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/lecture-rag-backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT \
  --set-env-vars GOOGLE_CLOUD_LOCATION=us-central1 \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true \
  --set-env-vars VERTEX_AI_INDEX_ENDPOINT=your-index-endpoint-id \
  --set-env-vars VERTEX_AI_DEPLOYED_INDEX=your-deployed-index-id \
  --set-env-vars GEMINI_MODEL=gemini-2.5-flash
```

5) Verify and call
```bash
gcloud run services describe lecture-rag-backend --region us-central1 --format='value(status.url)'
curl -X POST "$SERVICE_URL/api/v1/query" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"Explain function state in cloud environments.\"}"
```

## Endpoints

| Path | Method | Purpose |
| --- | --- | --- |
| `/api/v1/query` | POST | RAG query endpoint |
| `/healthz` | GET | Health check |
| `/docs` | GET | Swagger UI |
| `/openapi.json` | GET | OpenAPI spec |

## Troubleshooting

- `google.auth.exceptions.DefaultCredentialsError`: run `gcloud auth application-default login`.
- Empty vector search results: check `VERTEX_AI_INDEX_ENDPOINT` and `VERTEX_AI_DEPLOYED_INDEX`.
- Gemini errors: verify model name and project/region access.
