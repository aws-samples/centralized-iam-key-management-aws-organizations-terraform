resource "aws_lambda_function" "notifier_rotation_lambda" {
  filename         = "${path.module}/code_sources/Lambda/notifier.zip"
  function_name    = var.notification_lambda_name
  role             = aws_iam_role.notifier_iam_role.arn
  handler          = "main.lambda_handler"
  source_code_hash = filemd5("${path.module}/code_sources/Lambda/notifier.zip")
  runtime          = "python3.8"
  timeout          = 300
  environment {
    variables = local.lambda_variables
  }
  dynamic "vpc_config" {
    for_each = var.run_lambda_in_vpc ? [1] : []
    content {
      subnet_ids         = [var.subnet_id]
      security_group_ids = [aws_security_group.this.id]
    }
  }
}

resource "aws_lambda_function" "access_key_rotation_lambda" {
  filename         = "${path.module}/code_sources/Lambda/access_key_auto_rotation.zip"
  function_name    = local.iam_access_rotation_lambda_name
  role             = data.aws_iam_role.rotation_execution_role.arn
  handler          = "main.lambda_handler"
  source_code_hash = filemd5("${path.module}/code_sources/Lambda/access_key_auto_rotation.zip")
  runtime          = "python3.8"
  timeout          = 400
  environment {
    variables = {
      DryRunFlag                   = var.dry_run_flag
      RotationPeriod               = var.rotation_period
      InactivePeriod               = var.inactive_period
      InactiveBuffer               = var.inactive_buffer
      RecoveryGracePeriod          = var.recovery_grace_period
      IAMExemptionGroup            = var.iam_exception_group
      IAMAssumedRoleName           = var.iam_role_name
      RoleSessionName              = "ASA-IAM-Access-Key-Rotation-Function"
      Partition                    = data.aws_partition.current.partition
      NotifierArn                  = aws_lambda_function.notifier_rotation_lambda.arn
      EmailTemplateEnforce         = var.email_template_enforcment
      EmailTemplateAudit           = var.email_template_audit
      ResourceOwnerTag             = var.resource_owner_tag
      StoreSecretsInCentralAccount = var.store_secrets_in_central_account
      CredentialReplicationRegions = var.credential_replication_region
      RunLambdaInVPC               = var.run_lambda_in_vpc
      OrgListAccount               = var.org_list_account
      OrgListRole                  = var.org_list_role
    }
  }
  dynamic "vpc_config" {
    for_each = var.run_lambda_in_vpc ? [1] : []
    content {
      subnet_ids         = [var.subnet_id]
      security_group_ids = [aws_security_group.this.id]
    }
  }
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.notifier_rotation_lambda.function_name
  principal     = data.aws_caller_identity.current.account_id
  source_arn    = "arn:${data.aws_partition.current.partition}:sts::${data.aws_caller_identity.current.account_id}:assumed-role/${var.execution_role_name}/${local.account_inventory_lambda_function_name}"
}


resource "aws_lambda_function" "account_inventory_lambda" {
  filename         = "${path.module}/code_sources/Lambda/account_inventory.zip"
  function_name    = local.account_inventory_lambda_function_name
  role             = aws_iam_role.account_inventory_role.arn
  handler          = "main.lambda_handler"
  source_code_hash = filemd5("${path.module}/code_sources/Lambda/account_inventory.zip")
  runtime          = "python3.8"
  timeout          = 300
  environment {
    variables = {
      LambdaRotationFunction = local.iam_access_rotation_lambda_name
      OrgListAccount         = var.org_list_account
      OrgListRole            = var.org_list_role
      RoleSessionName        = "ASA-IAM-Access-Account-Inventory-Function"
      RunLambdaInVPC         = var.run_lambda_in_vpc
    }
  }
  dynamic "vpc_config" {
    for_each = var.run_lambda_in_vpc ? [1] : []
    content {
      subnet_ids         = [var.subnet_id]
      security_group_ids = [aws_security_group.this.id]
    }
  }
}

resource "aws_lambda_permission" "account_inventory_trigger_lambda_permission" {
  depends_on    = [aws_lambda_function.account_inventory_lambda]
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.access_key_rotation_lambda.function_name
  principal     = data.aws_caller_identity.current.account_id
  source_arn    = "arn:${data.aws_partition.current.partition}:sts::${data.aws_caller_identity.current.account_id}:assumed-role/${var.execution_role_name}/${local.account_inventory_lambda_function_name}"
}


resource "aws_cloudwatch_event_rule" "rotation_cloudwatch_event_trigger_lambda" {
  depends_on          = [aws_lambda_function.account_inventory_lambda]
  name                = "capture-aws-sign-in"
  description         = "CloudWatch Event to trigger Access Key auto-rotation Lambda Function daily"
  schedule_expression = "rate(24 hours)"
}

resource "aws_cloudwatch_event_target" "cloudwatch_account_inventory_invocation_target" {
  target_id = local.account_inventory_lambda_function_name
  rule      = aws_cloudwatch_event_rule.rotation_cloudwatch_event_trigger_lambda.name
  arn       = aws_lambda_function.account_inventory_lambda.arn
}

resource "aws_lambda_permission" "event_bridge_lambda_trigger" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.account_inventory_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.rotation_cloudwatch_event_trigger_lambda.arn
}