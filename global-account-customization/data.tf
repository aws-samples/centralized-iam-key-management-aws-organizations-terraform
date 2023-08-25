data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_organizations_organization" "org_data" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "assume_role_policy_document" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]
    principals {
      type        = "AWS"
      identifiers = local.assume_role_principal
    }
  }
}

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

## Rotation role policy
data "aws_iam_policy_document" "rotation_iam_role_policy" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:iam::*:role/${var.iam_role_name}",
      "arn:${data.aws_partition.current.partition}:iam::*:role/${var.org_list_role}"
    ]
    condition {
      test = "StringEquals"
      values = [
        data.aws_organizations_organization.org_data.id
      ]
      variable = "aws:PrincipalOrgID"
    }
  }
  statement {
    actions = [
      "lambda:InvokeFunction"
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.notification_lambda_name}"
      # aws_lambda_function.access_key_rotation_lambda.arn
    ]
  }
  statement {
    actions = [
      "secretsmanager:PutResourcePolicy",
      "secretsmanager:PutSecretValue",
      "secretsmanager:DescribeSecret",
      "secretsmanager:CreateSecret",
      "secretsmanager:GetResourcePolicy",
      "secretsmanager:ReplicateSecretToRegions"
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:secretsmanager:*:${data.aws_caller_identity.current.account_id}:secret:*"
    ]
  }
}

data "aws_iam_policy_document" "this" {
  statement {
    actions = [
      "iam:List*",
      "iam:CreatePolicy",
      "iam:CreateAccessKey",
      "iam:DeleteAccessKey",
      "iam:UpdateAccessKey",
      "iam:PutUserPolicy",
      "iam:GetUserPolicy",
      "iam:GetAccessKeyLastUsed",
      "iam:GetUser"
    ]
    resources = [
      "*",
    ]
  }

  statement {
    actions = [
      "iam:AttachUserPolicy",
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:user/*",
    ]
  }

  statement {
    actions = [
      "secretsmanager:PutResourcePolicy",
      "secretsmanager:PutSecretValue",
      "secretsmanager:DescribeSecret",
      "secretsmanager:CreateSecret",
      "secretsmanager:GetResourcePolicy",
      "secretsmanager:ReplicateSecretToRegions"
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:secretsmanager:*:${data.aws_caller_identity.current.account_id}:secret:*",
    ]
  }

  statement {
    actions = [
      "iam:GetGroup",
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:group/${var.iam_exception_group}",
    ]
  }
}