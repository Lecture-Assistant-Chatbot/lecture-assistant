# 📘 Vertex AI PDF Embedding Cloud Function

This Cloud Function automatically processes uploaded PDF files from a **Google Cloud Storage** bucket.  
It extracts text, chunks it, generates embeddings using **Vertex AI’s `text-embedding-005`** model, and upserts those embeddings into a **Vertex AI Vector Search Index**.

---

## ⚙️ Features

- 🧾 Extracts text from PDFs using `pdfplumber`
- ✂️ Splits text into 1500-character chunks
- 🧠 Generates text embeddings via Vertex AI
- 📈 Uploads embeddings to a Matching Engine Vector Search Index
- 🪣 Triggered automatically when a file is uploaded to your Cloud Storage bucket

---

## 📁 Project Structure

```
.
├── main.py
├── requirements.txt
└── README.md
```

---

## 📦 Requirements

`requirements.txt`

```
google-cloud-storage
google-cloud-aiplatform
vertexai
pdfplumber
```

---

## 🔧 Environment Variables

These must be set before deploying:

| Variable     | Description |
|---------------|-------------|
| `PROJECT_ID`  | Your Google Cloud project ID |
| `LOCATION`    | Region for Vertex AI (e.g., `us-central1`) |
| `INDEX_ID`    | Your Vertex AI Vector Search Index ID |

---

## 🚀 Deployment (Cloud Function 2nd Gen)

Run these commands to deploy:

```bash

gcloud auth login

--set-env-vars

```

✅ Replace **`YOUR_BUCKET_NAME`** with your Cloud Storage bucket name.

---

## 🧠 How It Works

1. A PDF file is uploaded to the configured Cloud Storage bucket.
2. The function triggers automatically.
3. It downloads the PDF, extracts its text, and splits it into smaller chunks.
4. Each chunk is embedded using the Vertex AI `text-embedding-005` model.
5. The generated embeddings are upserted into the specified Vertex AI Vector Search Index.

---

## 🪄 Logs and Monitoring

View logs in Cloud Console under **Cloud Functions → Logs**,  
or run the command below:

```bash
gcloud functions logs read process_lecture --region=us-central1
```

---

## ⚠️ Notes

- Only `.pdf` files are processed; other files are skipped automatically.  
- `/tmp` is an ephemeral storage; files are deleted after processing.  
- Each embedding vector has 768 dimensions (from the `text-embedding-005` model).  
- The function batches embeddings (100 per request) for safe upsertion to Vertex AI.

---

## 🧹 Clean Up

To remove the function and avoid billing:

```bash
gcloud functions delete process_lecture --region=us-central1
```

---

## ✅ Summary

| Component | Service |
|------------|----------|
| **Compute Service** | Cloud Functions (2nd Gen) |
| **Persistence Service** | Vertex AI Vector Search |
| **Additional Cloud Service** | Cloud Storage |

---
