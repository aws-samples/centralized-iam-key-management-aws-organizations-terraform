locals {
  assume_role_principal = var.primary_account_id == data.aws_caller_identity.current.account_id ? [aws_iam_role.rotation_execution_role[0].arn] : ["arn:${data.aws_partition.current.partition}:iam::${var.primary_account_id}:role/${var.execution_role_name}"]
}