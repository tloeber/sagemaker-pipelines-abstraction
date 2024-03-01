resource "aws_s3_bucket" "bucket" {
  bucket = var.project_name

  #   tags = {
  #     Name        = var.bucket_name
  #     Environment = var.environment
  #   }
}

resource "aws_s3_bucket_policy" "bucket_policy" {
  bucket = aws_s3_bucket.bucket.id
  policy = data.aws_iam_policy_document.bucket_policy.json
}

resource "aws_s3_bucket_server_side_encryption_configuration" "sse" {
  bucket = aws_s3_bucket.bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

data "aws_iam_policy_document" "bucket_policy" {
  statement {
    sid     = "DenyAllPublicAccess"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      "${aws_s3_bucket.bucket.arn}",
      "${aws_s3_bucket.bucket.arn}/*"
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}
