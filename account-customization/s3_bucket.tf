data "aws_iam_policy_document" "iam_access_key_rotation_bucket_policy" {
  statement {
    sid = "AWSBucketPermissionsCheck"
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.iam_rotation_resources_bucket.arn,
      "${aws_s3_bucket.iam_rotation_resources_bucket.arn}/${var.s3_bucket_prefix}/*"
    ]
    condition {
      test = "StringEquals"
      values = [
        data.aws_organizations_organization.org_data.id
      ]
      variable = "aws:PrincipalOrgID"
    }
  }
}

resource "aws_s3_bucket" "iam_rotation_resources_bucket" {
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.iam_rotation_resources_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "example" {
  bucket = aws_s3_bucket.iam_rotation_resources_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.iam_rotation_resources_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "iam_resource_objects" {
  count  = length(local.file_sources)
  bucket = aws_s3_bucket.iam_rotation_resources_bucket.id
  key    = "${var.s3_bucket_prefix}/${local.s3_object_paths[count.index]}"
  source = "${path.module}/${local.file_sources[count.index]}"
  etag   = filemd5("${path.module}/${local.file_sources[count.index]}")
}