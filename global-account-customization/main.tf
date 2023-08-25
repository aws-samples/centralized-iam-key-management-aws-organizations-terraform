resource "aws_iam_role" "this" {
  name               = var.iam_role_name
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy_document.json
}

resource "aws_iam_role_policy" "this" {
  name   = "${var.iam_role_name}-policy"
  role   = aws_iam_role.this.id
  policy = data.aws_iam_policy_document.this.json
}


resource "aws_iam_group" "this" {
  name = var.iam_exception_group
}


## Rotation Lambda function role

resource "aws_iam_role" "rotation_execution_role" {
  count              = var.primary_account_id == data.aws_caller_identity.current.account_id ? 1 : 0
  name               = var.execution_role_name
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy_document.json
  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEC2FullAccess"
  ]
}

resource "aws_iam_role_policy" "execution_role_policy" {
  count  = var.primary_account_id == data.aws_caller_identity.current.account_id ? 1 : 0
  name   = "rotation-function-permission"
  role   = aws_iam_role.rotation_execution_role[0].id
  policy = data.aws_iam_policy_document.rotation_iam_role_policy.json
}