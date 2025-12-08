# Lecture PDF Ingest Function (Vertex AI Embeddings)

Cloud Function (2nd gen) that ingests PDFs from a Cloud Storage bucket, chunks the text, creates embeddings with Vertex AI `text-embedding-005`, and upserts them into a Matching Engine index.

## What it does

1) Triggered when a PDF is uploaded to the configured bucket.  
2) Downloads the file to `/tmp`, extracts text with `pdfplumber`.  
3) Splits text into 1500-character chunks.  
4) Generates embeddings with Vertex AI.  
5) Upserts embeddings into Vertex AI Vector Search (Matching Engine).

## Structure

```
lecture_ingest_function/
├─ main.py          # Function entrypoint
├─ requirements.txt # Cloud Function dependencies
└─ README.md
```

## Requirements

- GCP project with Vertex AI and Cloud Functions APIs enabled
- Cloud Storage bucket to trigger on PDF uploads
- Matching Engine index ID to upsert into
- Python 3.11 runtime (function uses `python311`)

## Environment variables

| Name | Description |
| --- | --- |
| `PROJECT_ID` | GCP project ID |
| `LOCATION` | Vertex AI region (e.g. `us-central1`) |
| `INDEX_ID` | Vertex AI Vector Search index ID |

## Deploy (Cloud Functions 2nd gen)

Replace the placeholders before running:
```bash
gcloud auth login
gcloud functions deploy process_lecture \
  --runtime=python311 \
  --region=us-central1 \
  --trigger-event=google.storage.object.finalize \
  --trigger-resource=YOUR_BUCKET_NAME \
  --entry-point=process_lecture \
  --memory=2GB \
  --timeout=540s \
  --min-instances=1 \
  --set-env-vars PROJECT_ID=YOUR_PROJECT_ID,LOCATION=us-central1,INDEX_ID=YOUR_INDEX_ID
```

Logs:
```bash
gcloud functions logs read process_lecture --region=us-central1
```

Cleanup:
```bash
gcloud functions delete process_lecture --region=us-central1
```
