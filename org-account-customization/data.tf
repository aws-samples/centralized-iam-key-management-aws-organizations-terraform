data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

data "aws_iam_policy_document" "org_list_assumerole_policy" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]
    principals {
      type = "AWS"
      identifiers = [
        "arn:${data.aws_partition.current.partition}:iam::${var.primary_account_id}:role/${var.account_execution_role_name}",
        "arn:${data.aws_partition.current.partition}:iam::${var.primary_account_id}:role/${var.execution_role_name}"
      ]
    }
  }
}

data "aws_iam_policy_document" "allow_list_orgs_policy" {
  statement {
    actions = [
      "organizations:ListAccounts",
      "organizations:ListAccountsForParent",
      "organizations:ListChildren",
    ]
    resources = [
      "*"
    ]
  }
  statement {
    actions = [
      "secretsmanager:PutResourcePolicy",
      "secretsmanager:PutSecretValue",
      "secretsmanager:DescribeSecret",
      "secretsmanager:CreateSecret",
      "secretsmanager:GetResourcePolicy",
      "secretsmanager:ReplicateSecretToRegions",
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:secretsmanager:*:${data.aws_caller_identity.current.account_id}:secret:*"
    ]
  }
}
