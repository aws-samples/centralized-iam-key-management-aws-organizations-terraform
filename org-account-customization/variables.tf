variable "org_list_role" {
  type        = string
  description = "Name of IAM role that is used to list org accounts"
}

variable "account_execution_role_name" {
  type        = string
  description = "Role name which is going to perform execution operationEnter the name of the Account Lambda Execution Role that will assume the role to list accounts."
}

variable "execution_role_name" {
  type        = string
  description = "Enter the name of the Rotation Lambda Execution Role that will assume the role to list accounts."
}

variable "primary_account_id" {
  type        = string
  description = "Account ID where entire solution is deployed"
}