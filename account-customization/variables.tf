variable "s3_bucket_name" {
  type        = string
  description = "Name of the S3 Bucket where the templates and code is present"
}

variable "s3_bucket_prefix" {
  type        = string
  description = "Prefix where the resources will be stored"
  default     = "code_sources"
}

variable "admin_email_address" {
  type        = string
  description = "Email address that will be used to send email"
}

variable "resource_owner_tag" {
  type        = string
  description = "Tag key used to indicate the owner of IAM user resource"
}

variable "notifier_execution_role" {
  type        = string
  description = "Name of execution role for Lambda function that will send notifications"
}

variable "iam_exception_group" {
  type = string
}

variable "iam_role_name" {
  type = string
}

variable "execution_role_name" {
  type = string
}

variable "inventory_execution_role_name" {
  type = string
}

variable "org_list_account" {
  type = string
}

variable "org_list_role" {
  type = string
}

variable "email_template_enforcment" {
  type        = string
  description = ""
}

variable "email_template_audit" {
  type = string
}

variable "smtp_user_param_name" {
  type    = string
  default = null
}

variable "smtp_password_param_name" {
  type    = string
  default = null
}

variable "rotation_period" {
  type    = number
  default = 90
}

variable "inactive_period" {
  type    = number
  default = 100
}

variable "inactive_buffer" {
  type    = number
  default = 10
}

variable "recovery_grace_period" {
  type    = number
  default = 10
}

variable "dry_run_flag" {
  type    = bool
  default = true
}

variable "store_secrets_in_central_account" {
  type    = bool
  default = false
}

variable "credential_replication_region" {
  type = string
}

variable "run_lambda_in_vpc" {
  type    = bool
  default = false
}

variable "vpc_id" {
  type    = string
  default = null
}

variable "vpc_cidr" {
  type    = string
  default = null
}

variable "subnet_id" {
  type = string
}

variable "create_endpoint_sg" {
  type    = bool
  default = true
}

variable "create_smtp_endpoint" {
  type    = bool
  default = true
}

variable "create_ssm_endpoint" {
  type    = bool
  default = true
}

variable "create_sts_endpoint" {
  type    = bool
  default = true
}

variable "create_s3_endpoint" {
  type    = bool
  default = true
}

variable "create_secretsmanager_endpoint" {
  type    = bool
  default = true
}

variable "notification_lambda_name" {
  type        = string
  description = "Name of the Lambda function that is used to send notifications"
  default     = "iam-access-notifier-lambda"
}