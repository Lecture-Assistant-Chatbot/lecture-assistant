# Lecture Assistant Chatbot Monorepo

End-to-end stack for a lecture assistant chatbot built on Google Cloud. PDFs are ingested and embedded with Vertex AI, stored in Matching Engine, served via a FastAPI RAG API, and surfaced through a React chat UI.

## Repository layout

- `lecture-rag-backend/` – FastAPI RAG API (Vertex AI embeddings + Matching Engine + Gemini).
- `lecture-rag-frontend/` – React chat client that calls the backend.
- `lecture_ingest_function/` – Cloud Function that ingests PDFs, generates embeddings, and upserts to Matching Engine.
- `lecture_infra/` – Terraform to provision cloud resources (Vertex AI index/endpoint, Cloud Run, Artifact Registry, IAM, bucket).
- `bruno-api-collection/` – Bruno API collection for manual API testing.

## How it fits together

1) Upload a lecture PDF to the configured Cloud Storage bucket.  
2) The ingest Cloud Function extracts text, chunks it, and writes embeddings to Vertex AI Matching Engine.  
3) The backend receives chat queries, fetches nearest chunks from Matching Engine, and calls Gemini for a grounded response.  
4) The frontend calls the backend to display the conversation.

## Quick start (local)

- Backend: see `lecture-rag-backend/README.md` (uvicorn on port 8000).  
- Frontend: see `lecture-rag-frontend/README.md` (npm start on port 3000; point `src/config.js` at the backend).  
- Bruno collection: import `bruno-api-collection/lecture-assistant-chatbot` to issue sample queries.

## Deploying to GCP

- Use `lecture_infra/` Terraform to provision core resources and deploy Cloud Run + the ingest function.  
- Ensure Vertex AI APIs are enabled and set the correct `cloud_run_image` in `terraform.tfvars` (built from `lecture-rag-backend`).  
- The ingest function expects `PROJECT_ID`, `LOCATION`, and `INDEX_ID` env vars; Terraform wires these for you.

## Testing and verification

- Backend: hit `/healthz` or `/docs` locally or on Cloud Run.  
- Frontend: confirm you can send/receive messages against the backend.  
- Ingest: upload a PDF to the bucket and watch Cloud Function logs; new chunks should appear in Matching Engine.

## Cleaning up

- Remove deployed resources with `terraform destroy` from `lecture_infra/`.  
- Delete Cloud Run images and any leftover storage objects if needed.
