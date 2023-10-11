# data "aws_iam_policy_document" "iam_access_key_rotation_bucket_policy" {
#   statement {
#     sid = "AWSBucketPermissionsCheck"
#     principals {
#       type        = "*"
#       identifiers = ["*"]
#     }
#     actions = [
#       "s3:GetObject",
#       "s3:ListBucket"
#     ]
#     resources = [
#       aws_s3_bucket.iam_rotation_resources_bucket.arn,
#       "${aws_s3_bucket.iam_rotation_resources_bucket.arn}/${var.s3_bucket_prefix}/*"
#     ]
#     condition {
#       test = "StringEquals"
#       values = [
#         data.aws_organizations_organization.org_data.id
#       ]
#       variable = "aws:PrincipalOrgID"
#     }
#   }
# }

resource "aws_s3_bucket" "iam_rotation_resources_bucket" {
  
  bucket = var.s3_bucket_name
}

resource "aws_s3_bucket_public_access_block" "this" {
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

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  count  = var.kms_key_arn != null ? 1 : 0
  bucket = aws_s3_bucket.iam_rotation_resources_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  # checkov:skip=CKV_AWS_300: False positive as incomplete multipart upload configuration is present and is based on user input
  count  = var.lifecycle_rules != null ? 1 : 0
  bucket = aws_s3_bucket.iam_rotation_resources_bucket.id
  dynamic "rule" {
    for_each = var.lifecycle_rules

    content {
      id     = try(rule.value.id, null)
      status = try(rule.value.enabled ? "Enabled" : "Disabled", tobool(rule.value.status) ? "Enabled" : "Disabled", title(lower(rule.value.status)))
      dynamic "abort_incomplete_multipart_upload" {
        for_each = try([rule.value.abort_incomplete_multipart_upload_days], [])
        content {
          days_after_initiation = try(rule.value.abort_incomplete_multipart_upload_days, null)
        }
      }
      dynamic "expiration" {
        for_each = try(flatten([rule.value.expiration]), [])

        content {
          date                         = try(expiration.value.date, null)
          days                         = try(expiration.value.days, null)
          expired_object_delete_marker = try(expiration.value.expired_object_delete_marker, null)
        }
      }

      dynamic "transition" {
        for_each = try(flatten([rule.value.transition]), [])

        content {
          date          = try(transition.value.date, null)
          days          = try(transition.value.days, null)
          storage_class = transition.value.storage_class
        }
      }
      dynamic "noncurrent_version_expiration" {
        for_each = try(flatten([rule.value.noncurrent_version_expiration]), [])

        content {
          newer_noncurrent_versions = try(noncurrent_version_expiration.value.newer_noncurrent_versions, null)
          noncurrent_days           = try(noncurrent_version_expiration.value.days, noncurrent_version_expiration.value.noncurrent_days, null)
        }
      }
      dynamic "noncurrent_version_transition" {
        for_each = try(flatten([rule.value.noncurrent_version_transition]), [])

        content {
          newer_noncurrent_versions = try(noncurrent_version_transition.value.newer_noncurrent_versions, null)
          noncurrent_days           = try(noncurrent_version_transition.value.days, noncurrent_version_transition.value.noncurrent_days, null)
          storage_class             = noncurrent_version_transition.value.storage_class
        }
      }

      dynamic "filter" {
        for_each = [for v in try(flatten([rule.value.filter]), []) : v if max(length(keys(v)), length(try(rule.value.filter.tags, rule.value.filter.tag, []))) == 1]

        content {
          object_size_greater_than = try(filter.value.object_size_greater_than, null)
          object_size_less_than    = try(filter.value.object_size_less_than, null)
          prefix                   = try(filter.value.prefix, null)

          dynamic "tag" {
            for_each = try(filter.value.tags, filter.value.tag, [])

            content {
              key   = tag.key
              value = tag.value
            }
          }
        }
      }

      dynamic "filter" {
        for_each = [for v in try(flatten([rule.value.filter]), []) : v if max(length(keys(v)), length(try(rule.value.filter.tags, rule.value.filter.tag, []))) > 1]

        content {
          and {
            object_size_greater_than = try(filter.value.object_size_greater_than, null)
            object_size_less_than    = try(filter.value.object_size_less_than, null)
            prefix                   = try(filter.value.prefix, null)
            tags                     = try(filter.value.tags, filter.value.tag, null)
          }
        }
      }
    }
  }
}

resource "aws_s3_bucket_logging" "this" {
  count         = var.logging_bucket != null ? 1 : 0
  bucket        = aws_s3_bucket.iam_rotation_resources_bucket.id
  target_bucket = var.logging_bucket
  target_prefix = try(var.logging_bucket_prefix, null)
}
