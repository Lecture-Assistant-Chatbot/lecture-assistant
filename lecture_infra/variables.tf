variable "project_id" {
    description = "GCP project ID"
    type        = string
}

variable "region" {
    description = "Default region (use one that supports Vertex AI + Cloud Run)"
    type        = string
    default     = "us-central1"
}

variable "lecture_bucket_name" {
    description = "Bucket where lecture PDFs & function code live"
    type        = string
    default     = "my-lecture-bucket"
}

variable "cloud_run_image" {
    description = "Container image for your Cloud Run app"
    type        = string
    # Example: "us-central1-docker.pkg.dev/PROJECT/REPO/lecture-assistant:latest"
}

variable "vertex_index_dimensions" {
    description = "Embedding dimension (must match your model)"
    type        = number
    default     = 768
}
