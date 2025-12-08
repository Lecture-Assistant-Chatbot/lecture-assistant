# Enable the core APIs you need
resource "google_project_service" "services" {
    for_each = toset([
        "aiplatform.googleapis.com",        # Vertex AI API
        "logging.googleapis.com",           # Cloud Logging API
        "cloudfunctions.googleapis.com",    # Cloud Functions API
        "eventarc.googleapis.com",          # Eventarc API
        "run.googleapis.com",               # Cloud Run Admin API
        "artifactregistry.googleapis.com",  # Artifact Registry API
        "pubsub.googleapis.com",            # Cloud Pub/Sub API
        "cloudbuild.googleapis.com",        # Cloud Build API
        "iam.googleapis.com",               # IAM API
        "storage.googleapis.com",           # Cloud Storage API
        "containerregistry.googleapis.com", # Container Registry API
    ])

    project = var.project_id
    service = each.value

    # Allow terraform destroy to disable services and their dependents
    disable_on_destroy        = true
    disable_dependent_services = true
}

# GCS bucket for lecture PDFs & function code
resource "google_storage_bucket" "lectures" {
    name                        = var.lecture_bucket_name
    location                    = var.region
    uniform_bucket_level_access = true

    # 👇 allow Terraform to delete non-empty bucket
    force_destroy = true
}

# Empty streaming index – embeddings will be written at runtime
resource "google_vertex_ai_index" "lecture_index" {
    region       = var.region
    display_name = "lecture-index"
    description  = "Vector index for lecture chunks"

    metadata {
        # For an empty streaming index we omit contents_delta_uri
        config {
        dimensions                  = var.vertex_index_dimensions
        approximate_neighbors_count = 150
        distance_measure_type       = "DOT_PRODUCT_DISTANCE"

        algorithm_config {
            tree_ah_config {
            leaf_node_embedding_count    = 5000
            leaf_nodes_to_search_percent = 3
            }
        }
        }
    }

    index_update_method = "STREAM_UPDATE"

    depends_on = [google_project_service.services]
}

# Create a Vertex AI Index Endpoint to serve the index
resource "google_vertex_ai_index_endpoint" "lecture_endpoint" {
    display_name            = "lecture-index-endpoint"
    description             = "Public endpoint for lecture vector search"
    region                  = var.region
    public_endpoint_enabled = true

    depends_on = [google_project_service.services]
}  

# Deploy index to the endpoint
resource "google_vertex_ai_index_endpoint_deployed_index" "lecture_deployment" {
    index_endpoint = google_vertex_ai_index_endpoint.lecture_endpoint.id
    deployed_index_id = "lecture_index_deployment"
    index             = google_vertex_ai_index.lecture_index.id

    dedicated_resources {
        min_replica_count = 1
        max_replica_count = 1

        machine_spec {
        machine_type = "e2-standard-16"
        }
    }

    depends_on = [google_vertex_ai_index_endpoint.lecture_endpoint]
}

# Upload Cloud Function source code zip to GCS
resource "google_storage_bucket_object" "ingest_function_source" {
    name   = "functions/ingest-lecture.zip"
    bucket = google_storage_bucket.lectures.name

    # Use the zip created by archive_file
    source = data.archive_file.ingest_function_zip.output_path
}

# Service account for Cloud Function
resource "google_service_account" "function_sa" {
    account_id   = "lecture-ingest-sa"
    display_name = "Cloud Function service account for lecture ingestion"
}

# Allow function to read lecture PDFs from the bucket
resource "google_storage_bucket_iam_member" "function_lectures_read" {
    bucket = google_storage_bucket.lectures.name
    role   = "roles/storage.objectViewer"
    member = "serviceAccount:${google_service_account.function_sa.email}"
}

# Allow function to write to Vertex AI index
resource "google_project_iam_member" "function_vertexai_user" {
    project = var.project_id
    role    = "roles/aiplatform.user"
    member  = "serviceAccount:${google_service_account.function_sa.email}"
}

# Allow function to write logs to Cloud Logging
resource "google_project_iam_member" "function_logging" {
    project = var.project_id
    role    = "roles/logging.logWriter"
    member  = "serviceAccount:${google_service_account.function_sa.email}"
}

# Cloud Function to process uploaded lecture PDFs
resource "google_cloudfunctions2_function" "ingest_lecture" {
    name     = "process-lecture"
    location = var.region

    build_config {
        runtime     = "python311"
        entry_point = "process_lecture"

        source {
        storage_source {
            bucket = google_storage_bucket.lectures.name
            object = google_storage_bucket_object.ingest_function_source.name
        }
        }
    }

    service_config {
        service_account_email = google_service_account.function_sa.email

        available_memory   = "2G"   # 2GB
        timeout_seconds    = 540
        min_instance_count = 1
        max_instance_count = 5

        environment_variables = {
            PROJECT_ID = var.project_id
            LOCATION   = var.region
            INDEX_ID   = google_vertex_ai_index.lecture_index.name
        }
    }

    # Trigger whenever a lecture PDF is uploaded
    event_trigger {
        trigger_region = var.region
        event_type     = "google.cloud.storage.object.v1.finalized"

        event_filters {
        attribute = "bucket"
        value     = google_storage_bucket.lectures.name
        }
    }

    depends_on = [
        google_project_service.services,
        google_vertex_ai_index.lecture_index
    ]
}

resource "google_artifact_registry_repository" "api_repo" {
    project       = var.project_id
    location      = var.region
    repository_id = var.artifact_repo_id
    format        = "DOCKER"

    description = "Repository for Lecture Assistant Cloud Run API image"

    depends_on = [google_project_service.services]
}

resource "null_resource" "build_cloud_run_image" {
    # If you change the tag in var.cloud_run_image, this will rebuild
    triggers = {
        image = var.cloud_run_image
    }

    provisioner "local-exec" {
        command = "cd ../lecture-rag-backend && gcloud builds submit --tag ${var.cloud_run_image}"
    }

    depends_on = [google_artifact_registry_repository.api_repo]
}


# Service account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
    account_id   = "lecture-api-sa"
    display_name = "Lecture API Cloud Run SA"
}

# Allow Cloud Run service to call Vertex AI (Gemini + embeddings + vector search)
resource "google_project_iam_member" "cloud_run_vertexai" {
    project = var.project_id
    role    = "roles/aiplatform.user"
    member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

# Allow Cloud Run service to write logs to Cloud Logging
resource "google_project_iam_member" "cloud_run_logging" {
    project = var.project_id
    role    = "roles/logging.logWriter"
    member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_cloud_run_v2_service" "lecture_api" {
    name     = "lecture-api"
    location = var.region

    ingress = "INGRESS_TRAFFIC_ALL"

    template {
        service_account = google_service_account.cloud_run_sa.email

        containers {
        image = var.cloud_run_image   # image we built above

        # env vars matching your config.py
        env {
            name  = "GOOGLE_CLOUD_PROJECT"
            value = var.project_id
        }
        env {
            name  = "GOOGLE_CLOUD_LOCATION"
            value = var.region
        }
        env {
            name  = "GOOGLE_GENAI_USE_VERTEXAI"
            value = "true"
        }
        env {
            name  = "VERTEX_AI_INDEX_ENDPOINT"
            value = google_vertex_ai_index_endpoint.lecture_endpoint.name
        }
        env {
            name  = "VERTEX_AI_DEPLOYED_INDEX"
            value = google_vertex_ai_index_endpoint_deployed_index.lecture_deployment.deployed_index_id
        }
        env {
            name  = "GEMINI_MODEL"
            value = "gemini-2.5-flash"
        }
        env {
            name  = "LOG_LEVEL"
            value = "info"
        }
        }
    }

    depends_on = [
        google_project_service.services,
        null_resource.build_cloud_run_image,  # build image before deploying
        google_vertex_ai_index_endpoint.lecture_endpoint,
        google_vertex_ai_index_endpoint_deployed_index.lecture_deployment,
    ]
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
    project  = var.project_id
    location = var.region
    name     = google_cloud_run_v2_service.lecture_api.name

    role   = "roles/run.invoker"
    member = "allUsers"

    depends_on = [google_cloud_run_v2_service.lecture_api]
}
