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
  description = "IAM group to exclude from evaluation"
}

variable "iam_role_name" {
  type = string
  description = "IAM role name"
}

variable "execution_role_name" {
  type = string
  description = "Role used for Execution"
}

variable "inventory_execution_role_name" {
  type = string
  description = "Inventory execution role"
}

variable "org_list_account" {
  type = string
  description = "Account from which ORG list account should be performed"
}

variable "org_list_role" {
  type = string
  description = "Role that is used to perform ORG list account"
}

variable "email_template_enforcment" {
  type        = string
  description = "Environment variable value that constraints email template enforcement"
}

variable "email_template_audit" {
  type = string
  description = "Environment variable value that constraints email template Audit"
}

variable "smtp_user_param_name" {
  type    = string
  default = null
  description = "SMTP user SSM parameter name"
}

variable "smtp_password_param_name" {
  type    = string
  default = null
  description = "SMTP password SSM parameter name"
}

variable "rotation_period" {
  type    = number
  default = 90
  description = "After how long the rotation need to be performed"
}

variable "inactive_period" {
  type    = number
  default = 100
  description = "After how many days access key should be completely removed"
}

variable "inactive_buffer" {
  type    = number
  default = 10
  description = "Buffer period before access key is deleted"
}

variable "recovery_grace_period" {
  type    = number
  default = 10
  description = "Grace period for recovery"
}

variable "dry_run_flag" {
  type    = bool
  default = true
  description = "Environment variable that defines whether to perform dry run or implement actual execution"
}

variable "store_secrets_in_central_account" {
  type    = bool
  default = false
  description = "Whether to save the newly generated access and secret key in central account or individual account"
}

variable "credential_replication_region" {
  type = string
  description = "To which region secret credentials generated need to be replicated"
}

variable "run_lambda_in_vpc" {
  type    = bool
  default = false
  description = "Whether to run lambda in VPC or not"
}

variable "vpc_id" {
  type    = string
  default = null
  description = "VPC ID that need to be used if Lambda need to be run in VPC"
}

variable "vpc_cidr" {
  type    = string
  default = null
  description = "CIDR of VPC"
}

variable "subnet_id" {
  type = string
  default = null
  description = "Subnet ID's in which lambda need to be run"
}

variable "create_endpoint_sg" {
  type    = bool
  default = true
  description = "Whether to create endpoint with security group"
}

variable "create_smtp_endpoint" {
  type    = bool
  default = true
  description = "Whether to create SMTP endpoint or not"
}

variable "create_ssm_endpoint" {
  type    = bool
  default = true
  description = "Whether to create SSM endpoint or not"
}

variable "create_sts_endpoint" {
  type    = bool
  default = true
  description = "Whether to create STS endpoint or not"
}

variable "create_s3_endpoint" {
  type    = bool
  default = true
  description = "Whether to create S3 endpoint or not"
}

variable "create_secretsmanager_endpoint" {
  type    = bool
  default = true
  description = "Whether to create secrets manager endpoint or not"
}

variable "notification_lambda_name" {
  type        = string
  description = "Name of the Lambda function that is used to send notifications"
  default     = "iam-access-notifier-lambda"
}

variable "kms_key_arn" {
  type        = string
  default     = null
  description = "KMS key used for encrypting S3 bucket"
}

variable "logging_bucket" {
  type        = string
  default     = null
  description = "Name of loggign bucket"
}

variable "lifecycle_rules" {
  type        = any
  default     = null
  description = "Lifecycle rules to move object to different storage classes"
}

variable "logging_bucket_prefix" {
  type        = string
  default     = null
  description = "Prefix that need to be used for logging configuration"
}
