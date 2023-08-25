data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}
data "aws_organizations_organization" "org_data" {}

data "aws_iam_policy_document" "lambda_assume_role_policy_document" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "notifier_iam_role_policy" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:s3:::${var.s3_bucket_name}/${var.s3_bucket_prefix}/Template/*",
    ]
  }
  statement {
    actions = [
      "ses:SendEmail",
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:ses:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:identity/*",
    ]
  }
}

data "aws_iam_policy_document" "allow_orgs_access_policy" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:iam::${var.org_list_account}:role/${var.org_list_role}"
    ]
  }
  statement {
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      aws_lambda_function.access_key_rotation_lambda.arn
    ]
  }
}

data "aws_iam_role" "rotation_execution_role" {
  name = var.execution_role_name
}