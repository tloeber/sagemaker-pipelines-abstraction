resource "aws_sagemaker_pipeline" "sm_pipeline" {
  pipeline_name         = local.pipeline_name
  pipeline_display_name = local.pipeline_name
  role_arn              = aws_iam_role.sagemaker_pipelines_role.arn
  pipeline_definition_s3_location {
    bucket     = aws_s3_bucket.bucket.bucket
    object_key = "pipeline_definitions/{local.pipeline_name}.json"
  }
}

locals {
  pipeline_name = "${var.project_name}-v${var.project_version}"
}
