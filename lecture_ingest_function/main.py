import os
import json
import pdfplumber
from google.cloud import storage, aiplatform
from vertexai.preview.language_models import TextEmbeddingModel
import vertexai


def split_text_into_chunks(text, max_chars=1500):
    """Split text into chunks for embedding."""
    paragraphs = text.split("\n")
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) > max_chars:
            chunks.append(current.strip())
            current = p
        else:
            current += "\n" + p
    if current:
        chunks.append(current.strip())
    return [c for c in chunks if c.strip()]


def process_lecture(event, context):
    """Triggered when a file is uploaded to the bucket."""
    bucket_name = event['bucket']
    file_name = event['name']
    print(f"Processing {file_name} from bucket {bucket_name}")

    # Only process PDF files
    if not file_name.endswith(".pdf"):
        print("Not a PDF. Skipping.")
        return

    # === LOAD CONFIG FROM ENV ===
    PROJECT_ID = os.getenv("PROJECT_ID")
    LOCATION = os.getenv("LOCATION", "us-central1")
    INDEX_ID = os.getenv("INDEX_ID")

    if not (PROJECT_ID and INDEX_ID):
        print("Missing environment variables PROJECT_ID or INDEX_ID.")
        return

    # === INITIALIZE STORAGE ===
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    local_path = f"/tmp/{os.path.basename(file_name)}"
    blob.download_to_filename(local_path)
    print(f"Downloaded {file_name} to {local_path}")

    # === EXTRACT TEXT ===
    try:
        with pdfplumber.open(local_path) as pdf:
            text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    except Exception as e:
        print(f"Failed to extract text: {e}")
        os.remove(local_path)
        return

    # === CHUNK TEXT ===
    chunks = split_text_into_chunks(text)
    print(f"Chunked into {len(chunks)} segments.")

    # === EMBEDDING MODEL ===
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    model = TextEmbeddingModel.from_pretrained("text-embedding-005")

    datapoints = []
    base_id = os.path.basename(file_name)

    for i, chunk in enumerate(chunks):
        try:
            vector = model.get_embeddings([chunk])[0].values
            datapoint = {
                "datapoint_id": f"{base_id}-chunk-{i}",
                "feature_vector": vector,
                "restricts": [
                    {"namespace": "source_file", "allow_list": [base_id]},
                    {"namespace": "text", "allow_list": [chunk[:1000]]}
                ]
            }
            datapoints.append(datapoint)
        except Exception as e:
            print(f"Embedding failed for chunk {i}: {e}")

    print(f"Generated {len(datapoints)} embeddings for {file_name}")

    # === UPSERT TO VECTOR SEARCH ===
    if not datapoints:
        print("No datapoints generated. Skipping upload.")
        os.remove(local_path)
        return

    try:
        print(f"Connecting to Index: {INDEX_ID}")
        index = aiplatform.MatchingEngineIndex(index_name=INDEX_ID)

        batch_size = 100
        for i in range(0, len(datapoints), batch_size):
            batch = datapoints[i : i + batch_size]
            print(f"Upserting batch {i//batch_size + 1} ...")
            index.upsert_datapoints(datapoints=batch)

        print(f"Successfully upserted {len(datapoints)} datapoints.")
    except Exception as e:
        print(f"Upsert failed: {e}")
    finally:
        try:
            os.remove(local_path)
            print(f"Cleaned up {local_path}")
        except Exception as e:
            print(f"Cleanup failed: {e}")

    print("Processing complete.")
