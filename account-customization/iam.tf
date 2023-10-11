## Role to allow Lambda function to access SES service to send email and S3 to get email template
resource "aws_iam_role" "notifier_iam_role" {
  name               = var.notifier_execution_role
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy_document.json
  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonSSMFullAccess",
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEC2FullAccess"
  ]
}

resource "aws_iam_role_policy" "notifier_policy" {
  name   = "allow-notifier-get-email-policy"
  role   = aws_iam_role.notifier_iam_role.id
  policy = data.aws_iam_policy_document.notifier_iam_role_policy.json
}

# Inventory execution role

resource "aws_iam_role" "account_inventory_role" {
  name               = var.inventory_execution_role_name
  path               = "/"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy_document.json
  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEC2FullAccess"
  ]
}

resource "aws_iam_role_policy" "account_inventory_role_policy" {
  name   = "allow-orgs-access-policy"
  role   = aws_iam_role.account_inventory_role.id
  policy = data.aws_iam_policy_document.allow_orgs_access_policy.json
}
