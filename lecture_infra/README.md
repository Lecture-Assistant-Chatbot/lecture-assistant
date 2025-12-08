# Infrastructure (Terraform)

Terraform configuration to provision the lecture assistant stack on GCP: Vertex AI Matching Engine, Cloud Function for ingest, Cloud Run for the API, Artifact Registry, and required IAM/Services.

## Files

- `providers.tf` – Google provider setup
- `variables.tf` – Input variables
- `terraform.tfvars.example` – Sample values to copy
- `main.tf` – Core resources (APIs, storage bucket, index, Cloud Run, IAM)
- `functions.tf` (if present) – Additional function-related resources

## Prerequisites

- Terraform CLI
- `gcloud` CLI authenticated to your project
- GCP project with billing enabled

## Quick start

1) Copy vars file and edit values:
```bash
cp terraform.tfvars.example terraform.tfvars
```
Key variables:
- `project_id`: GCP project
- `region`: e.g. `us-central1`
- `lecture_bucket_name`: bucket to store lecture PDFs and function source
- `artifact_repo_id`: Artifact Registry repo for the API image
- `cloud_run_image`: fully qualified image for the API (built by Cloud Build)
- `vertex_index_dimensions`: embedding dimensions (768 for `text-embedding-005`)

2) Initialize and review:
```bash
terraform init
terraform plan
```

3) Apply:
```bash
terraform apply
```

## What gets created (high level)

- Enables required APIs (Vertex AI, Cloud Run, Cloud Functions, Artifact Registry, Pub/Sub, Cloud Build, IAM, Storage, Logging).
- GCS bucket for lecture PDFs and function source.
- Vertex AI index and endpoint (public) with a deployed index.
- Cloud Function (2nd gen) to process PDFs and upsert embeddings.
- Artifact Registry Docker repo and Cloud Build step to build the backend image.
- Cloud Run service for the FastAPI backend with env vars wired to Vertex AI resources.
- Service accounts and IAM bindings for Vertex AI access, logging, and storage.

## Tear down

```bash
terraform destroy
```

> Note: `force_destroy` is enabled on the bucket to allow cleanup; remove if you need stricter retention.
