# 🚀 Lecture Assistant Chatbot API (Vertex AI + Gemini + FastAPI)

This service implements a **Retrieval-Augmented Generation (RAG)** pipeline using:
- **Vertex AI Text Embeddings** (`text-embedding-005`)
- **Vertex AI Matching Engine** for vector search
- **Gemini API (Generative Language API)** for final responses
- **FastAPI** for serving a REST endpoint

It’s fully configurable via environment variables and deployable on **Google Cloud Run** with no secrets hard-coded.

---

## 🧩 Project Structure

```
lecture-rag-backend/
├─ app/
│  ├─ main.py               # FastAPI app entrypoint
│  ├─ config.py             # Centralized config (Pydantic-based)
│  └─ __init__.py
├─ requirements.txt         # Python dependencies
├─ Dockerfile               # Cloud Run container
├─ .dockerignore
├─ .env.example             # Example local configuration
└─ README.md                # This guide
```

---

## ⚙️ Prerequisites

- Python 3.10+ (recommended: 3.11)
- `gcloud` CLI installed and authenticated (`gcloud auth login`)
- Access to a Google Cloud project with:
  - **Vertex AI API enabled**
  - **Cloud Run API enabled**
  - (Optional) **Secret Manager** for API keys
- A deployed **Matching Engine index** and **endpoint**
- A valid **Gemini API key**

---

## 🧪 Local Development

### 1. Clone & enter the project

```bash
git clone https://github.com/Lecture-Assistant-Chatbot/lecture-assistant.git
cd -lecture-rag-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Copy and fill the `.env` file

```bash
cp .env.example .env
```

Edit `.env` and fill in your project-specific details:

```bash
# Vertex AI
VERTEX_AI_PROJECT=your-gcp-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_INDEX_ENDPOINT=your-vector-search-endpoint
VERTEX_AI_DEPLOYED_INDEX=your-deployed-index-id

# Gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash-preview-09-2025

# Misc
LOG_LEVEL=info
CORS_ALLOW_ALL=true
HTTP_TIMEOUT_SECONDS=60
```

### 5. Run the server locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Test locally

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/query"   -H "Content-Type: application/json"   -d '{"prompt": "What is a stateful microservice?"}'
```

Or open Swagger docs at:  
👉 [http://localhost:8000/docs](http://localhost:8000/docs)

### 7. Troubleshooting (local)
| Issue | Solution |
|-------|-----------|
| `google.auth.exceptions.DefaultCredentialsError` | Run `gcloud auth application-default login` |
| Embeddings or search fail | Verify Vertex AI Index Endpoint & Deployed Index |
| Gemini API errors | Check your API key and model name |

---

## ☁️ Deploying to Cloud Run (Production)

### 1. Enable APIs

```bash
gcloud services enable run.googleapis.com aiplatform.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
```

### 2. Build the container

```bash
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/lecture-rag-backend
```

### 3. (Optional but recommended) Store your Gemini API key securely

```bash
echo -n "YOUR_GEMINI_API_KEY" | \
gcloud secrets create GEMINI_API_KEY --data-file=-
```

### 4. Deploy to Cloud Run

```bash
gcloud run deploy lecture-rag-backend   --image gcr.io/$GOOGLE_CLOUD_PROJECT/lecture-rag-backend   --region us-central1   --platform managed   --allow-unauthenticated   --set-env-vars VERTEX_AI_PROJECT=$GOOGLE_CLOUD_PROJECT   --set-env-vars VERTEX_AI_LOCATION=us-central1   --set-env-vars VERTEX_AI_INDEX_ENDPOINT=your-vector-search-endpoint   --set-env-vars VERTEX_AI_DEPLOYED_INDEX=your-deployed-index-id   --set-env-vars GEMINI_MODEL=gemini-2.5-flash-preview-09-2025
```

If using Secret Manager:

```bash
gcloud run services update lecture-rag-backend   --region us-central1   --update-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

### 5. Verify deployment

```bash
gcloud run services describe lecture-rag-backend --region us-central1   --format='value(status.url)'
```

Then test:

```bash
curl -X POST "$(gcloud run services describe lecture-rag-backend --region us-central1 --format='value(status.url)')/api/v1/query"   -H "Content-Type: application/json"   -d '{"prompt": "Explain function state in cloud environments."}'
```

### 6. Monitor logs

```bash
gcloud logs read "projects/$GOOGLE_CLOUD_PROJECT/logs/run.googleapis.com%2Fstdout" --limit=50
```

### 7. Update service later

If you make code changes:

```bash
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/lecture-rag-backend
gcloud run deploy rag-cloudrun   --image gcr.io/$GOOGLE_CLOUD_PROJECT/lecture-rag-backend   --region us-central1
```

---

## 🔒 Security & Configuration Tips

- **Never** hard-code secrets — always use environment variables or Secret Manager.
- Assign Cloud Run a **service account** with:
  - `roles/aiplatform.user`
  - `roles/vertexai.admin`
  - `roles/secretmanager.secretAccessor` (if using secrets)
- Use **IAM-based access control** for private APIs instead of `--allow-unauthenticated`.
- For production, disable full-origin CORS by setting `CORS_ALLOW_ALL=false`.

---

## 🧰 Endpoints Summary

| Endpoint | Method | Description |
|-----------|--------|-------------|
| `/api/v1/query` | `POST` | Main RAG query endpoint |
| `/healthz` | `GET` | Health check |
| `/docs` | `GET` | Interactive Swagger UI |
| `/openapi.json` | `GET` | OpenAPI spec |

---

## 🧾 Example Request / Response

**Request**

```json
{
  "prompt": "Explain what local storage options exist for stateful functions."
}
```

**Response**

```json
{
  "response": "Stateful functions can persist data in cookies, sensor memory, databases, or distributed key-value stores..."
}
```

---

## 🧹 Cleanup

To delete Cloud Run service and images:

```bash
gcloud run services delete lecture-rag-backend --region us-central1
gcloud container images delete gcr.io/$GOOGLE_CLOUD_PROJECT/lecture-rag-backend --force-delete-tags
```

---

## ✅ Summary of Key Variables

| Variable | Description |
|-----------|-------------|
| `VERTEX_AI_PROJECT` | GCP Project ID |
| `VERTEX_AI_LOCATION` | Vertex AI region (e.g., `us-central1`) |
| `VERTEX_AI_INDEX_ENDPOINT` | Matching Engine index endpoint ID |
| `VERTEX_AI_DEPLOYED_INDEX` | Deployed index ID |
| `GEMINI_API_KEY` | Gemini API key (store in Secret Manager) |
| `GEMINI_MODEL` | Model name (default: `gemini-2.5-flash-preview-09-2025`) |
| `PORT` | Automatically injected by Cloud Run |
| `LOG_LEVEL` | Logging level (`info`, `debug`, etc.) |
| `CORS_ALLOW_ALL` | Enable all CORS origins (default `true`) |

---

## 🧠 Developer Notes

- The service uses **Application Default Credentials (ADC)** for all Vertex API calls.
- It’s fully async for scalable concurrency under Cloud Run’s autoscaling model.
- Use `gcloud auth application-default login` locally to enable ADC.
- Logging goes automatically to **Cloud Logging** in production.
