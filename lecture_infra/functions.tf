data "archive_file" "ingest_function_zip" {
    type       = "zip"
    source_dir = "${path.module}/../lecture_ingest_function"
    output_path = "${path.module}/build/lecture_ingest_function.zip"
}
