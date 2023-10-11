locals {
  smtp_details = var.run_lambda_in_vpc ? {
    SMTPUserParamName     = var.smtp_user_param_name
    SMTPPasswordParamName = var.smtp_password_param_name
  } : {}
  lambda_variables = merge({
    ADMIN_EMAIL      = var.admin_email_address
    S3_BUCKET_NAME   = var.s3_bucket_name
    S3_BUCKET_PREFIX = var.s3_bucket_prefix
    RunLambdaInVPC   = var.run_lambda_in_vpc


  }, local.smtp_details)
  account_inventory_lambda_function_name = "account-inventory-lambda"
  iam_access_rotation_lambda_name        = "iam-access-rotation-lambda"
  file_sources                           = ["code_sources/Lambda/access_key_auto_rotation.zip", "code_sources/Lambda/account_inventory.zip", "code_sources/Lambda/notifier.zip", "code_sources/Template/iam-auto-key-rotation-enforcement.html"]
  s3_object_paths                        = ["Lambda/access_key_auto_rotation.zip", "Lambda/account_inventory.zip", "Lambda/notifier.zip", "Template/iam-auto-key-rotation-enforcement.html"]
}
