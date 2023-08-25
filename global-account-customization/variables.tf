variable "iam_role_name" {
  type        = string
  description = "Name of the IAM role that main notifier will use"
}

variable "execution_role_name" {
  type        = string
  description = "Execution role that need to be used"
}

variable "iam_exception_group" {
  type        = string
  description = "Name of the IAM Group for which the users in the group should be excluded from IAM access key rotation"
}

variable "primary_account_id" {
  type        = string
  description = "Primary account from which entire execution will be done"
}

variable "iam_access_rotation_lambda_name" {
  type        = string
  description = "Name of IAM access keys rotation lambda"
}

variable "org_list_role" {
  type        = string
  description = "IAM Role name to list organizations"
}

variable "notification_lambda_name" {
  type        = string
  description = "Name of the Lambda function that is used to send notifications"
  default     = "iam-access-notifier-lambda"
}